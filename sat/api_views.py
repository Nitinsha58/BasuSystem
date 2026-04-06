import random
from datetime import timedelta

from django.conf import settings
from django.utils import timezone
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .models import TestAssignment, TestAttempt, QuestionResponse, TestResult, Question
from .serializers import PaperSerializer, AnswerSerializer, QuestionSerializer


def _get_active_assignment(token):
    """Return the assignment or None. Validates deadline too."""
    try:
        assignment = TestAssignment.objects.select_related('paper', 'inquiry').get(token=token)
    except TestAssignment.DoesNotExist:
        return None, 'Invalid or expired test link.'

    # Deadline check — only block if not yet started
    if assignment.deadline and assignment.deadline < timezone.now():
        try:
            _ = assignment.attempt  # already started — allow completion
        except TestAttempt.DoesNotExist:
            return None, 'This test link has expired.'

    return assignment, None


class PaperDetailAPI(APIView):
    """GET /api/paper/<token>/ — returns paper metadata only (no questions)."""

    def get(self, request, token):
        assignment, error = _get_active_assignment(token)
        if error:
            return Response({'error': error}, status=status.HTTP_410_GONE)

        paper = assignment.paper
        total_questions = paper.questions.count()

        try:
            attempt = assignment.attempt
            if attempt.submitted_at:
                return Response(
                    {'error': 'Test already submitted.', 'submitted': True},
                    status=status.HTTP_409_CONFLICT
                )
            elapsed = (timezone.now() - attempt.started_at).total_seconds()
            time_remaining = max(0, paper.time_limit * 60 - int(elapsed))
            return Response({
                'title': paper.title,
                'class_label': paper.class_name.name if paper.class_name else '',
                'time_limit': paper.time_limit,
                'marks_per_correct': paper.marks_per_correct,
                'total_questions': total_questions,
                'student_name': assignment.inquiry.student_name,
                'started': True,
                'time_remaining': time_remaining,
            })
        except TestAttempt.DoesNotExist:
            pass

        return Response({
            'title': paper.title,
            'class_label': paper.class_name.name if paper.class_name else '',
            'time_limit': paper.time_limit,
            'marks_per_correct': paper.marks_per_correct,
            'total_questions': total_questions,
            'student_name': assignment.inquiry.student_name,
            'started': False,
            'time_remaining': paper.time_limit * 60,
        })


class StartAttemptAPI(APIView):
    """POST /api/start/<token>/ — creates TestAttempt with shuffled question order; idempotent."""

    def post(self, request, token):
        assignment, error = _get_active_assignment(token)
        if error:
            return Response({'error': error}, status=status.HTTP_410_GONE)

        paper = assignment.paper

        # Idempotent: if attempt already exists and not submitted, return it
        try:
            attempt = assignment.attempt
            if attempt.submitted_at:
                return Response(
                    {'error': 'Test already submitted.', 'submitted': True},
                    status=status.HTTP_409_CONFLICT
                )
            elapsed = (timezone.now() - attempt.started_at).total_seconds()
            time_remaining = max(0, paper.time_limit * 60 - int(elapsed))
            return Response({
                'attempt_id': attempt.id,
                'time_limit': paper.time_limit * 60,
                'time_remaining': time_remaining,
                'total_questions': len(attempt.question_order),
                'student_name': assignment.inquiry.student_name,
            })
        except TestAttempt.DoesNotExist:
            pass

        # Build shuffled question order
        question_ids = list(paper.questions.values_list('id', flat=True))
        random.shuffle(question_ids)

        attempt = TestAttempt.objects.create(assignment=assignment, question_order=question_ids)
        return Response({
            'attempt_id': attempt.id,
            'time_limit': paper.time_limit * 60,
            'time_remaining': paper.time_limit * 60,
            'total_questions': len(question_ids),
            'student_name': assignment.inquiry.student_name,
        }, status=status.HTTP_201_CREATED)


class SubmitAttemptAPI(APIView):
    """POST /api/submit/<token>/ — strict time gate, grades answers, creates TestResult."""

    def post(self, request, token):
        assignment, error = _get_active_assignment(token)
        if error:
            return Response({'error': error}, status=status.HTTP_410_GONE)

        try:
            attempt = assignment.attempt
        except TestAttempt.DoesNotExist:
            return Response({'error': 'Test not started yet.'}, status=status.HTTP_400_BAD_REQUEST)

        if attempt.submitted_at:
            return Response({'error': 'Already submitted.'}, status=status.HTTP_409_CONFLICT)

        # ── Strict server-side time gate ──────────────────────────────────────
        now = timezone.now()
        elapsed = (now - attempt.started_at).total_seconds()
        time_limit_seconds = assignment.paper.time_limit * 60
        grace = getattr(settings, 'SAT_SUBMIT_GRACE_SECONDS', 30)
        late_by = int(elapsed - time_limit_seconds)

        if elapsed > time_limit_seconds + grace:
            return Response(
                {
                    'error': 'submission_window_closed',
                    'message': 'The submission window has closed. Your test session has expired.',
                    'late_by': late_by,
                },
                status=status.HTTP_403_FORBIDDEN
            )
        # ─────────────────────────────────────────────────────────────────────

        # Validate incoming answers payload
        raw_answers = request.data.get('answers', [])
        serializer = AnswerSerializer(data=raw_answers, many=True)
        if not serializer.is_valid():
            return Response({'error': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        submitted_answers = {
            item['question_id']: (item.get('selected') or '').upper()
            for item in serializer.validated_data
        }

        # Merge with progressively-saved QuestionResponses (submitted payload takes priority)
        saved_responses = {
            r.question_id: r.selected_option or ''
            for r in attempt.responses.all()
        }
        saved_responses.update(submitted_answers)  # submitted payload wins
        answers = saved_responses

        questions = list(assignment.paper.questions.order_by('order'))
        marks_per = assignment.paper.marks_per_correct

        total_marks = 0
        max_marks = len(questions) * marks_per
        subject_scores = {}
        difficulty_scores = {}
        type_scores = {}

        with transaction.atomic():
            for q in questions:
                selected = answers.get(q.id, '')
                is_correct = selected == q.correct_answer if selected else False
                obtained = marks_per if is_correct else 0
                total_marks += obtained

                for bucket, key in [
                    (subject_scores, q.subject_tag),
                    (difficulty_scores, q.difficulty),
                    (type_scores, q.question_type or 'Other'),
                ]:
                    if key not in bucket:
                        bucket[key] = {'obtained': 0, 'max': 0, 'correct': 0, 'attempted': 0}
                    bucket[key]['max'] += marks_per
                    bucket[key]['obtained'] += obtained
                    if is_correct:
                        bucket[key]['correct'] += 1
                    if selected:
                        bucket[key]['attempted'] += 1

                QuestionResponse.objects.update_or_create(
                    attempt=attempt,
                    question=q,
                    defaults={
                        'selected_option': selected or None,
                        'is_correct': is_correct if selected else None,
                        'marks_obtained': obtained,
                    }
                )

            attempt.submitted_at = now
            attempt.late_by_seconds = late_by
            attempt.auto_submitted = bool(request.data.get('auto_submitted', False))
            attempt.save(update_fields=['submitted_at', 'late_by_seconds', 'auto_submitted'])

            result = TestResult.objects.create(
                attempt=attempt,
                total_marks=total_marks,
                max_marks=max_marks,
                subject_scores=subject_scores,
                difficulty_scores=difficulty_scores,
                type_scores=type_scores,
                visibility='shared' if assignment.auto_release else 'hold',
            )

        return Response({
            'report_token': result.report_token,
            'total_marks': total_marks,
            'max_marks': max_marks,
            'percentage': result.percentage,
            'auto_release': assignment.auto_release,
        }, status=status.HTTP_201_CREATED)


def _get_active_attempt(token):
    """Return (attempt, assignment, error) for an in-progress test."""
    try:
        assignment = TestAssignment.objects.select_related('paper', 'inquiry').get(token=token)
    except TestAssignment.DoesNotExist:
        return None, None, 'Invalid or expired test link.'
    try:
        attempt = assignment.attempt
    except TestAttempt.DoesNotExist:
        return None, assignment, 'Test not started yet.'
    if attempt.submitted_at:
        return None, assignment, 'Test already submitted.'
    return attempt, assignment, None


def _is_expired(attempt, paper):
    grace = getattr(settings, 'SAT_SUBMIT_GRACE_SECONDS', 30)
    elapsed = (timezone.now() - attempt.started_at).total_seconds()
    return elapsed > paper.time_limit * 60 + grace


class QuestionDetailAPI(APIView):
    """GET /api/question/<token>/<index>/ — returns one question by shuffled position."""

    def get(self, request, token, index):
        attempt, assignment, error = _get_active_attempt(token)
        if error:
            return Response({'error': error}, status=status.HTTP_410_GONE)

        order = attempt.question_order
        if not order:
            return Response({'error': 'Question order not set. Please restart the test.'}, status=status.HTTP_400_BAD_REQUEST)

        if index < 0 or index >= len(order):
            return Response({'error': 'Question index out of range.'}, status=status.HTTP_400_BAD_REQUEST)

        if _is_expired(attempt, assignment.paper):
            return Response({'error': 'Time expired.'}, status=status.HTTP_410_GONE)

        question_id = order[index]
        try:
            question = Question.objects.get(pk=question_id)
        except Question.DoesNotExist:
            return Response({'error': 'Question not found.'}, status=status.HTTP_404_NOT_FOUND)

        # Check if student already answered this question (progressive save)
        already_selected = None
        try:
            resp = attempt.responses.get(question_id=question_id)
            already_selected = resp.selected_option
        except QuestionResponse.DoesNotExist:
            pass

        return Response({
            'index': index,
            'total': len(order),
            'already_selected': already_selected,
            'question': QuestionSerializer(question).data,
        })


class SaveAnswerAPI(APIView):
    """POST /api/answer/<token>/ — progressively save one answer before final submit."""

    def post(self, request, token):
        attempt, assignment, error = _get_active_attempt(token)
        if error:
            return Response({'error': error}, status=status.HTTP_410_GONE)

        if _is_expired(attempt, assignment.paper):
            return Response({'error': 'Time expired.'}, status=status.HTTP_403_FORBIDDEN)

        order = attempt.question_order
        index = request.data.get('question_index')
        selected = (request.data.get('selected') or '').upper() or None

        if index is None or not isinstance(index, int):
            return Response({'error': 'question_index is required.'}, status=status.HTTP_400_BAD_REQUEST)

        if index < 0 or index >= len(order):
            return Response({'error': 'Question index out of range.'}, status=status.HTTP_400_BAD_REQUEST)

        valid_options = {'A', 'B', 'C', 'D', 'E', None}
        if selected not in valid_options:
            return Response({'error': 'Invalid option.'}, status=status.HTTP_400_BAD_REQUEST)

        question_id = order[index]
        try:
            question = Question.objects.get(pk=question_id, paper=assignment.paper)
        except Question.DoesNotExist:
            return Response({'error': 'Question not found.'}, status=status.HTTP_404_NOT_FOUND)

        # Save without grading — grading happens at final submit
        QuestionResponse.objects.update_or_create(
            attempt=attempt,
            question=question,
            defaults={'selected_option': selected, 'is_correct': None, 'marks_obtained': 0},
        )

        return Response({'saved': True, 'index': index})


class LogEventAPI(APIView):
    """POST /api/log-event/<token>/ — increment tab_switch or fullscreen_exit counter."""

    ALLOWED_EVENTS = {'tab_switch', 'fullscreen_exit'}

    def post(self, request, token):
        attempt, assignment, error = _get_active_attempt(token)
        if error:
            # Still log even if submitted (edge case: event fired just as auto-submit completed)
            return Response({'error': error}, status=status.HTTP_410_GONE)

        event = request.data.get('event')
        if event not in self.ALLOWED_EVENTS:
            return Response({'error': 'Invalid event.'}, status=status.HTTP_400_BAD_REQUEST)

        if event == 'tab_switch':
            attempt.tab_switch_count += 1
            attempt.save(update_fields=['tab_switch_count'])
        else:
            attempt.fullscreen_exit_count += 1
            attempt.save(update_fields=['fullscreen_exit_count'])

        return Response({
            'tab_switch_count': attempt.tab_switch_count,
            'fullscreen_exit_count': attempt.fullscreen_exit_count,
        })
