from django.utils import timezone
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .models import TestAssignment, TestAttempt, QuestionResponse, TestResult, Question
from .serializers import PaperSerializer, AnswerSerializer


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
    """GET /api/paper/<token>/ — returns paper metadata + questions (no answers)."""

    def get(self, request, token):
        assignment, error = _get_active_assignment(token)
        if error:
            return Response({'error': error}, status=status.HTTP_410_GONE)

        # If already submitted, don't serve the paper again
        try:
            attempt = assignment.attempt
            if attempt.submitted_at:
                return Response(
                    {'error': 'Test already submitted.', 'submitted': True},
                    status=status.HTTP_409_CONFLICT
                )
            # In-progress: return paper + time_remaining
            elapsed = (timezone.now() - attempt.started_at).total_seconds()
            time_remaining = max(0, assignment.paper.time_limit * 60 - int(elapsed))
            paper_data = PaperSerializer(assignment.paper).data
            return Response({
                'paper': paper_data,
                'student_name': assignment.inquiry.student_name,
                'started': True,
                'time_remaining': time_remaining,
            })
        except TestAttempt.DoesNotExist:
            pass

        paper_data = PaperSerializer(assignment.paper).data
        return Response({
            'paper': paper_data,
            'student_name': assignment.inquiry.student_name,
            'started': False,
            'time_remaining': assignment.paper.time_limit * 60,
        })


class StartAttemptAPI(APIView):
    """POST /api/start/<token>/ — creates TestAttempt; idempotent on refresh."""

    def post(self, request, token):
        assignment, error = _get_active_assignment(token)
        if error:
            return Response({'error': error}, status=status.HTTP_410_GONE)

        # Idempotent: if attempt already exists and not submitted, return it
        try:
            attempt = assignment.attempt
            if attempt.submitted_at:
                return Response(
                    {'error': 'Test already submitted.', 'submitted': True},
                    status=status.HTTP_409_CONFLICT
                )
            elapsed = (timezone.now() - attempt.started_at).total_seconds()
            time_remaining = max(0, assignment.paper.time_limit * 60 - int(elapsed))
            return Response({
                'attempt_id': attempt.id,
                'time_limit': assignment.paper.time_limit * 60,
                'time_remaining': time_remaining,
                'student_name': assignment.inquiry.student_name,
            })
        except TestAttempt.DoesNotExist:
            pass

        attempt = TestAttempt.objects.create(assignment=assignment)
        return Response({
            'attempt_id': attempt.id,
            'time_limit': assignment.paper.time_limit * 60,
            'time_remaining': assignment.paper.time_limit * 60,
            'student_name': assignment.inquiry.student_name,
        }, status=status.HTTP_201_CREATED)


class SubmitAttemptAPI(APIView):
    """POST /api/submit/<token>/ — scores answers and creates TestResult."""

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

        # Validate answers payload
        raw_answers = request.data.get('answers', [])
        serializer = AnswerSerializer(data=raw_answers, many=True)
        if not serializer.is_valid():
            return Response({'error': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        answers = {item['question_id']: (item.get('selected') or '').upper() for item in serializer.validated_data}
        questions = list(assignment.paper.questions.order_by('order'))
        marks_per = assignment.paper.marks_per_correct

        total_marks = 0
        max_marks = len(questions) * marks_per

        # Per-subject, per-difficulty, and per-type aggregation
        subject_scores = {}
        difficulty_scores = {}
        type_scores = {}

        with transaction.atomic():
            for q in questions:
                selected = answers.get(q.id, '')
                is_correct = selected == q.correct_answer if selected else False
                obtained = marks_per if is_correct else 0
                total_marks += obtained

                # Subject
                s = q.subject_tag
                if s not in subject_scores:
                    subject_scores[s] = {'obtained': 0, 'max': 0, 'correct': 0, 'attempted': 0}
                subject_scores[s]['max'] += marks_per
                subject_scores[s]['obtained'] += obtained
                if is_correct:
                    subject_scores[s]['correct'] += 1
                if selected:
                    subject_scores[s]['attempted'] += 1

                # Difficulty
                d = q.difficulty
                if d not in difficulty_scores:
                    difficulty_scores[d] = {'obtained': 0, 'max': 0, 'correct': 0, 'attempted': 0}
                difficulty_scores[d]['max'] += marks_per
                difficulty_scores[d]['obtained'] += obtained
                if is_correct:
                    difficulty_scores[d]['correct'] += 1
                if selected:
                    difficulty_scores[d]['attempted'] += 1

                # Question type
                t = q.question_type or 'Other'
                if t not in type_scores:
                    type_scores[t] = {'obtained': 0, 'max': 0, 'correct': 0, 'attempted': 0}
                type_scores[t]['max'] += marks_per
                type_scores[t]['obtained'] += obtained
                if is_correct:
                    type_scores[t]['correct'] += 1
                if selected:
                    type_scores[t]['attempted'] += 1

                QuestionResponse.objects.update_or_create(
                    attempt=attempt,
                    question=q,
                    defaults={
                        'selected_option': selected or None,
                        'is_correct': is_correct if selected else None,
                        'marks_obtained': obtained,
                    }
                )

            attempt.submitted_at = timezone.now()
            attempt.save(update_fields=['submitted_at'])

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
