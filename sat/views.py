import json
from collections import OrderedDict
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseNotAllowed, Http404
from django.utils import timezone

from center.models import ClassName
from inquiry_followup.models import Inquiry
from accounts.utility import generate_whatsapp_link
from marketing.models import Campaign

from .models import (
    TestPaper, Question, TestAssignment,
    TestAttempt, QuestionResponse, TestResult, SchoolTestSession
)


# ─────────────────────────────────────────────
# PAPER MANAGEMENT
# ─────────────────────────────────────────────

@login_required(login_url='login')
def paper_list(request):
    papers = TestPaper.objects.prefetch_related('questions').order_by('-created_at')
    return render(request, 'sat/paper_list.html', {'papers': papers})


@login_required(login_url='login')
def paper_create(request):
    classes = ClassName.objects.all().order_by('name')
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        class_id = request.POST.get('class_name') or None
        time_limit = request.POST.get('time_limit', 60)
        marks_per_correct = request.POST.get('marks_per_correct', 1)
        if not title:
            messages.error(request, 'Title is required.')
            return render(request, 'sat/paper_form.html', {'classes': classes})
        paper = TestPaper.objects.create(
            title=title,
            class_name_id=class_id,
            time_limit=int(time_limit),
            marks_per_correct=int(marks_per_correct),
        )
        messages.success(request, f'Paper "{paper.title}" created. Add questions below.')
        return redirect('sat:paper_detail', pk=paper.pk)
    return render(request, 'sat/paper_form.html', {'classes': classes})


@login_required(login_url='login')
def paper_detail(request, pk):
    paper = get_object_or_404(TestPaper, pk=pk)
    classes = ClassName.objects.all().order_by('name')

    if request.method == 'POST':
        action = request.POST.get('action')

        # ── Save paper meta ──
        if action == 'update_paper':
            paper.title = request.POST.get('title', paper.title).strip()
            class_id = request.POST.get('class_name') or None
            paper.class_name_id = class_id
            paper.time_limit = int(request.POST.get('time_limit', paper.time_limit))
            paper.marks_per_correct = int(request.POST.get('marks_per_correct', paper.marks_per_correct))
            paper.save()
            messages.success(request, 'Paper updated.')
            return redirect('sat:paper_detail', pk=pk)

        # ── Add new question ──
        elif action == 'add_question':
            next_order = paper.questions.count() + 1
            Question.objects.create(
                paper=paper,
                order=next_order,
                text=request.POST.get('text', '').strip(),
                option_a=request.POST.get('option_a', '').strip(),
                option_b=request.POST.get('option_b', '').strip(),
                option_c=request.POST.get('option_c', '').strip(),
                option_d=request.POST.get('option_d', '').strip(),
                option_e=request.POST.get('option_e', '').strip(),
                correct_answer=request.POST.get('correct_answer', 'A'),
                difficulty=request.POST.get('difficulty', 'L2'),
                subject_tag=request.POST.get('subject_tag', 'Other'),
                question_type=request.POST.get('question_type', 'Conceptual'),
            )
            messages.success(request, 'Question added.')
            return redirect('sat:paper_detail', pk=pk)

        # ── Edit existing question ──
        elif action == 'edit_question':
            q_id = request.POST.get('question_id')
            q = get_object_or_404(Question, pk=q_id, paper=paper)
            q.text = request.POST.get('text', q.text).strip()
            q.option_a = request.POST.get('option_a', q.option_a).strip()
            q.option_b = request.POST.get('option_b', q.option_b).strip()
            q.option_c = request.POST.get('option_c', q.option_c).strip()
            q.option_d = request.POST.get('option_d', q.option_d).strip()
            q.option_e = request.POST.get('option_e', q.option_e).strip()
            q.correct_answer = request.POST.get('correct_answer', q.correct_answer)
            q.difficulty = request.POST.get('difficulty', q.difficulty)
            q.subject_tag = request.POST.get('subject_tag', q.subject_tag)
            q.question_type = request.POST.get('question_type', q.question_type)
            q.order = int(request.POST.get('order', q.order))
            q.save()
            messages.success(request, f'Q{q.order} updated.')
            return redirect('sat:paper_detail', pk=pk)

        # ── Delete question ──
        elif action == 'delete_question':
            q_id = request.POST.get('question_id')
            q = get_object_or_404(Question, pk=q_id, paper=paper)
            q.delete()
            # Re-number remaining questions
            for idx, question in enumerate(paper.questions.order_by('order'), start=1):
                if question.order != idx:
                    question.order = idx
                    question.save(update_fields=['order'])
            messages.success(request, 'Question deleted and reordered.')
            return redirect('sat:paper_detail', pk=pk)

    questions = paper.questions.order_by('order')
    return render(request, 'sat/paper_detail.html', {
        'paper': paper,
        'questions': questions,
        'classes': classes,
        'difficulty_choices': Question.DIFFICULTY_CHOICES,
        'subject_choices': Question.SUBJECT_CHOICES,
        'answer_choices': Question.ANSWER_CHOICES,
        'question_type_choices': Question.QUESTION_TYPE_CHOICES,
    })


@login_required(login_url='login')
def paper_delete(request, pk):
    paper = get_object_or_404(TestPaper, pk=pk)
    if request.method == 'POST':
        title = paper.title
        paper.delete()
        messages.success(request, f'Paper "{title}" deleted.')
        return redirect('sat:paper_list')
    return render(request, 'sat/paper_confirm_delete.html', {'paper': paper})


@login_required(login_url='login')
def paper_reevaluate(request, pk):
    """
    Re-aggregate subject_scores, difficulty_scores, type_scores, and total_marks
    for every TestResult linked to this paper, using the current question tags
    and the already-stored QuestionResponse correctness data.
    """
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])

    paper = get_object_or_404(TestPaper, pk=pk)
    marks_per = paper.marks_per_correct
    max_marks = paper.questions.count() * marks_per

    # All results for this paper
    results = TestResult.objects.filter(
        attempt__assignment__paper=paper
    ).select_related('attempt').prefetch_related(
        'attempt__responses__question'
    )

    updated = 0
    for result in results:
        subject_scores = {}
        difficulty_scores = {}
        type_scores = {}
        total_marks = 0

        for resp in result.attempt.responses.select_related('question').all():
            q = resp.question
            obtained = resp.marks_obtained
            is_correct = resp.is_correct or False
            selected = resp.selected_option

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

        result.subject_scores = subject_scores
        result.difficulty_scores = difficulty_scores
        result.type_scores = type_scores
        result.total_marks = total_marks
        result.max_marks = max_marks
        result.save(update_fields=[
            'subject_scores', 'difficulty_scores', 'type_scores',
            'total_marks', 'max_marks',
        ])
        updated += 1

    messages.success(request, f'Re-evaluated {updated} result(s) for "{paper.title}".')
    return redirect('sat:paper_detail', pk=pk)


# ─────────────────────────────────────────────
# ASSIGNMENT MANAGEMENT
# ─────────────────────────────────────────────

@login_required(login_url='login')
def assignment_list(request):
    assignments = (
        TestAssignment.objects
        .select_related('inquiry', 'paper')
        .prefetch_related('attempt__result')
        .order_by('-created_at')
    )
    return render(request, 'sat/assignment_list.html', {'assignments': assignments})


@login_required(login_url='login')
def assignment_create(request):
    inquiry_id = request.GET.get('inquiry') or request.POST.get('inquiry_id')
    papers = TestPaper.objects.order_by('-created_at')
    inquiries = Inquiry.objects.order_by('student_name')
    preselected_inquiry = None
    if inquiry_id:
        preselected_inquiry = Inquiry.objects.filter(pk=inquiry_id).first()

    if request.method == 'POST':
        paper_id = request.POST.get('paper_id')
        inq_id = request.POST.get('inquiry_id')
        deadline_str = request.POST.get('deadline', '').strip()
        auto_release = request.POST.get('auto_release') == 'on'

        if not paper_id or not inq_id:
            messages.error(request, 'Paper and inquiry are required.')
            return render(request, 'sat/assignment_form.html', {
                'papers': papers, 'inquiries': inquiries,
                'preselected_inquiry': preselected_inquiry
            })

        deadline = None
        if deadline_str:
            from django.utils.dateparse import parse_datetime
            deadline = parse_datetime(deadline_str)

        assignment = TestAssignment.objects.create(
            paper_id=paper_id,
            inquiry_id=inq_id,
            deadline=deadline,
            auto_release=auto_release,
        )
        messages.success(request, f'Assignment created. Token: {assignment.token}')
        return redirect('sat:assignment_detail', pk=assignment.pk)

    return render(request, 'sat/assignment_form.html', {
        'papers': papers,
        'inquiries': inquiries,
        'preselected_inquiry': preselected_inquiry,
    })


@login_required(login_url='login')
def assignment_detail(request, pk):
    assignment = get_object_or_404(
        TestAssignment.objects.select_related('inquiry', 'paper'),
        pk=pk
    )
    attempt = getattr(assignment, 'attempt', None)
    result = getattr(attempt, 'result', None) if attempt else None

    test_url = request.build_absolute_uri(f'/test/{assignment.token}/')
    wa_message = (
        f"Dear {assignment.inquiry.student_name},\n\n"
        f"Your Scholarship Test has been scheduled.\n"
        f"Paper: {assignment.paper.title}\n"
        f"Time limit: {assignment.paper.time_limit} minutes\n\n"
        f"Click the link below to take the test:\n{test_url}\n\n"
        f"Best of luck! – BASU Nextgen Education"
    )
    wa_link = generate_whatsapp_link(wa_message, assignment.inquiry.phone)
    report_url = None
    if result:
        report_url = request.build_absolute_uri(f'/sat/report/{result.report_token}/')

    return render(request, 'sat/assignment_detail.html', {
        'assignment': assignment,
        'attempt': attempt,
        'result': result,
        'test_url': test_url,
        'wa_link': wa_link,
        'report_url': report_url,
    })


@login_required(login_url='login')
def assignment_reset(request, pk):
    """Delete the TestAttempt (and cascaded responses) so the student can restart."""
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])
    assignment = get_object_or_404(TestAssignment, pk=pk)
    attempt = getattr(assignment, 'attempt', None)
    if attempt:
        if hasattr(attempt, 'result'):
            messages.error(request, 'Cannot reset — result has already been generated.')
            return redirect('sat:assignment_detail', pk=pk)
        attempt.delete()
        messages.success(request, 'Attempt reset. Student can now restart the test.')
    else:
        messages.info(request, 'No attempt exists yet.')
    return redirect('sat:assignment_detail', pk=pk)


# ─────────────────────────────────────────────
# RESULT MANAGEMENT
# ─────────────────────────────────────────────

@login_required(login_url='login')
def result_list(request):
    results = (
        TestResult.objects
        .select_related('attempt__assignment__inquiry', 'attempt__assignment__paper')
        .order_by('-created_at')
    )
    return render(request, 'sat/result_list.html', {'results': results})


@login_required(login_url='login')
def result_delete(request, pk):
    """Delete the TestResult only — TestAttempt remains so the assignment can be reset/retaken."""
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])
    result = get_object_or_404(
        TestResult.objects.select_related('attempt__assignment__inquiry'),
        pk=pk
    )
    inquiry_name = result.attempt.assignment.inquiry.student_name
    result.delete()
    messages.success(request, f'Result for {inquiry_name} deleted. You can now reset the attempt if needed.')
    return redirect('sat:result_list')


@login_required(login_url='login')
def result_detail(request, pk):
    result = get_object_or_404(
        TestResult.objects.select_related(
            'attempt__assignment__inquiry',
            'attempt__assignment__paper',
        ),
        pk=pk
    )
    if request.method == 'POST':
        new_visibility = request.POST.get('visibility')
        if new_visibility in ('hold', 'shared'):
            result.visibility = new_visibility
            result.save(update_fields=['visibility'])
            messages.success(request, f'Visibility set to {new_visibility}.')
        return redirect('sat:result_detail', pk=pk)

    report_url = request.build_absolute_uri(f'/sat/report/{result.report_token}/')
    responses = (
        result.attempt.responses
        .select_related('question')
        .order_by('question__order')
    )
    return render(request, 'sat/result_detail.html', {
        'result': result,
        'responses': responses,
        'report_url': report_url,
    })


# ─────────────────────────────────────────────
# STUDENT-FACING TEST SHELL
# ─────────────────────────────────────────────

def test_shell(request, token):
    """Serves the minimal HTML shell that loads the React SPA."""
    # Validate token exists (don't leak info about deadlines here — React handles messaging)
    assignment = get_object_or_404(TestAssignment, token=token)
    return render(request, 'sat/test_shell.html', {'token': token})


# ─────────────────────────────────────────────
# REPORT (public shareable)
# ─────────────────────────────────────────────

def report_view(request, report_token):
    result = get_object_or_404(
        TestResult.objects.select_related(
            'attempt__assignment__inquiry',
            'attempt__assignment__paper',
        ),
        report_token=report_token
    )

    # Admins (logged-in staff) can always see; parents only if shared
    is_admin = request.user.is_authenticated
    if result.visibility == 'hold' and not is_admin:
        raise Http404("This report is not yet available.")

    responses = (
        result.attempt.responses
        .select_related('question')
        .order_by('question__order')
    )

    # Build subject & difficulty breakdowns for charts
    subject_data = result.subject_scores
    difficulty_data = result.difficulty_scores
    type_data = result.type_scores

    # Derive strengths (>=75% in subject) and gaps (<50%)
    strengths = [s for s, v in subject_data.items() if v.get('max', 0) > 0 and (v['obtained'] / v['max'] * 100) >= 75]
    gaps = [s for s, v in subject_data.items() if v.get('max', 0) > 0 and (v['obtained'] / v['max'] * 100) < 50]

    # Aggregate stats
    correct_count = responses.filter(is_correct=True).count()
    wrong_count = responses.filter(is_correct=False).count()
    unanswered_count = responses.filter(selected_option__isnull=True).count()
    total_q = responses.count()

    # Best / weakest subject
    subj_pcts = [
        (s, round(v['obtained'] / v['max'] * 100, 1) if v.get('max', 0) > 0 else 0)
        for s, v in subject_data.items()
    ]
    best_subj = max(subj_pcts, key=lambda x: x[1]) if subj_pcts else (None, 0)
    weak_subj = min(subj_pcts, key=lambda x: x[1]) if subj_pcts else (None, 0)

    # Best / weakest difficulty
    diff_pcts = [
        (d, round(v['obtained'] / v['max'] * 100, 1) if v.get('max', 0) > 0 else 0)
        for d, v in difficulty_data.items()
    ]
    best_diff = max(diff_pcts, key=lambda x: x[1]) if diff_pcts else (None, 0)
    weak_diff = min(diff_pcts, key=lambda x: x[1]) if diff_pcts else (None, 0)

    # Best / weakest question type (section)
    type_pcts = [
        (t, round(v['obtained'] / v['max'] * 100, 1) if v.get('max', 0) > 0 else 0)
        for t, v in type_data.items()
    ]
    best_type = max(type_pcts, key=lambda x: x[1]) if type_pcts else (None, 0)
    weak_type = min(type_pcts, key=lambda x: x[1]) if type_pcts else (None, 0)

    # JSON for charts (safe: data is from our own DB not user HTML input)
    subject_labels = json.dumps(list(subject_data.keys()))
    subject_pcts_json = json.dumps(
        [round(v['obtained'] / v['max'] * 100, 1) if v.get('max', 0) > 0 else 0
         for v in subject_data.values()]
    )
    diff_order = ['L1', 'L2', 'L3']
    diff_labels_json = json.dumps(
        [d + ' ' + {'L1': '(Easy)', 'L2': '(Moderate)', 'L3': '(Hard)'}.get(d, '') for d in diff_order if d in difficulty_data]
    )
    diff_correct_json = json.dumps([difficulty_data.get(d, {}).get('correct', 0) for d in diff_order if d in difficulty_data])
    diff_wrong_json = json.dumps([
        difficulty_data.get(d, {}).get('attempted', 0) - difficulty_data.get(d, {}).get('correct', 0)
        for d in diff_order if d in difficulty_data
    ])
    type_labels_json = json.dumps(list(type_data.keys()))
    type_pcts_json = json.dumps(
        [round(v['obtained'] / v['max'] * 100, 1) if v.get('max', 0) > 0 else 0
         for v in type_data.values()]
    )

    # Group responses by question_type for q-grid section headers and skill matrix
    def _band(pct):
        if pct >= 75:
            return ('band-strong', 'Strong')
        elif pct >= 60:
            return ('band-good', 'Good')
        elif pct >= 45:
            return ('band-avg', 'Average')
        return ('band-weak', 'Weak')

    qt_label_map = dict(Question.QUESTION_TYPE_CHOICES)
    type_map = OrderedDict()
    for r in responses:
        qt = r.question.question_type or 'Other'
        if qt not in type_map:
            type_map[qt] = []
        type_map[qt].append(r)

    type_groups = []
    for qt, rs in type_map.items():
        td = type_data.get(qt, {})
        pct = round(td.get('obtained', 0) / td['max'] * 100, 1) if td.get('max', 0) > 0 else 0
        bc, bl = _band(pct)
        type_groups.append({
            'type_key': qt,
            'type_label': qt_label_map.get(qt, qt),
            'responses': rs,
            'scores': td,
            'pct': pct,
            'band_class': bc,
            'band_label': bl,
        })

    return render(request, 'sat/report.html', {
        'result': result,
        'responses': responses,
        'subject_data': subject_data,
        'difficulty_data': difficulty_data,
        'type_data': type_data,
        'strengths': strengths,
        'gaps': gaps,
        'is_admin': is_admin,
        'correct_count': correct_count,
        'wrong_count': wrong_count,
        'unanswered_count': unanswered_count,
        'total_q': total_q,
        'best_subj': best_subj,
        'weak_subj': weak_subj,
        'best_diff': best_diff,
        'weak_diff': weak_diff,
        'best_type': best_type,
        'weak_type': weak_type,
        'subject_labels': subject_labels,
        'subject_pcts_json': subject_pcts_json,
        'diff_labels_json': diff_labels_json,
        'diff_correct_json': diff_correct_json,
        'diff_wrong_json': diff_wrong_json,
        'type_labels_json': type_labels_json,
        'type_pcts_json': type_pcts_json,
        'type_groups': type_groups,
        'subj_pcts': subj_pcts,
    })


# ─────────────────────────────────────────────
# SCHOOL TEST SESSION MANAGEMENT
# ─────────────────────────────────────────────

@login_required(login_url='login')
def session_list(request):
    sessions = (
        SchoolTestSession.objects
        .select_related('paper', 'campaign')
        .prefetch_related('assignments')
        .order_by('-date', '-created_at')
    )
    return render(request, 'sat/session_list.html', {'sessions': sessions})


@login_required(login_url='login')
def session_create(request):
    papers = TestPaper.objects.order_by('-created_at')
    campaigns = Campaign.objects.filter(is_active=True).order_by('name')

    if request.method == 'POST':
        paper_id = request.POST.get('paper_id', '').strip()
        campaign_id = request.POST.get('campaign_id', '').strip() or None
        school_name = request.POST.get('school_name', '').strip()
        date_str = request.POST.get('date', '').strip()

        if not school_name or not date_str:
            messages.error(request, 'School name and date are required.')
            return render(request, 'sat/session_form.html', {
                'papers': papers, 'campaigns': campaigns,
            })

        from django.utils.dateparse import parse_date
        date_obj = parse_date(date_str)
        if not date_obj:
            messages.error(request, 'Invalid date format.')
            return render(request, 'sat/session_form.html', {
                'papers': papers, 'campaigns': campaigns,
            })

        session = SchoolTestSession.objects.create(
            paper_id=paper_id or None,
            campaign_id=campaign_id,
            school_name=school_name,
            date=date_obj,
        )
        messages.success(request, f'School session created for {session.school_name}.')
        return redirect('sat:session_detail', pk=session.pk)

    return render(request, 'sat/session_form.html', {
        'papers': papers,
        'campaigns': campaigns,
    })


@login_required(login_url='login')
def session_detail(request, pk):
    session = get_object_or_404(
        SchoolTestSession.objects.select_related('paper', 'campaign'),
        pk=pk,
    )
    assignments = (
        session.assignments
        .select_related('inquiry', 'paper')
        .prefetch_related('attempt__result')
        .order_by('-created_at')
    )
    kiosk_url = request.build_absolute_uri(f'/sat/school/{session.session_code}/')
    return render(request, 'sat/session_detail.html', {
        'session': session,
        'assignments': assignments,
        'kiosk_url': kiosk_url,
    })


@login_required(login_url='login')
def session_toggle(request, pk):
    """Toggle is_active on a SchoolTestSession."""
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])
    session = get_object_or_404(SchoolTestSession, pk=pk)
    session.is_active = not session.is_active
    session.save(update_fields=['is_active'])
    state = 'activated' if session.is_active else 'deactivated'
    messages.success(request, f'Session {state}.')
    return redirect('sat:session_detail', pk=pk)


@login_required(login_url='login')
def session_delete(request, pk):
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])
    session = get_object_or_404(SchoolTestSession, pk=pk)
    if session.assignments.exists():
        messages.error(request, 'Cannot delete — students have already registered for this session.')
        return redirect('sat:session_detail', pk=pk)
    session.delete()
    messages.success(request, 'Session deleted.')
    return redirect('sat:session_list')


# ─────────────────────────────────────────────
# SCHOOL KIOSK (public self-registration)
# ─────────────────────────────────────────────

def school_kiosk(request, session_code):
    """
    Public kiosk view for school visits.
    Students enter their admission number, class, name, and phone,
    then are immediately redirected to the test.
    """
    session = get_object_or_404(SchoolTestSession, session_code=session_code)
    classes = ClassName.objects.all().order_by('name')
    error = None

    if request.method == 'POST':
        admission_number = request.POST.get('admission_number', '').strip()
        class_id = request.POST.get('class_name', '').strip()
        student_name = request.POST.get('student_name', '').strip()
        phone = request.POST.get('phone', '').strip()

        # Basic validation
        if not all([admission_number, class_id, student_name, phone]):
            error = 'All fields are required.'
        elif not session.is_active:
            error = 'This test session has been closed. Please contact your teacher.'
        else:
            class_obj = ClassName.objects.filter(pk=class_id).first()
            if not class_obj:
                error = 'Invalid class selected.'
            else:
                # Resolve paper: use the session's fixed paper, or auto-match by student's class
                paper = session.paper or TestPaper.objects.filter(
                    class_name=class_obj
                ).order_by('-created_at').first()
                if not paper:
                    error = f'No test paper is configured for {class_obj.name}. Please contact your teacher.'
                else:
                    existing_inquiry = Inquiry.objects.filter(phone=phone).first()

                    if existing_inquiry:
                        # Check if they already completed this paper
                        already_done = TestAssignment.objects.filter(
                            inquiry=existing_inquiry,
                            paper=paper,
                            attempt__submitted_at__isnull=False,
                        ).exists()
                        if already_done:
                            error = 'You have already completed this test. Please contact your teacher if this is a mistake.'
                        else:
                            # Reuse existing inquiry — update admission_number if not already set
                            if not existing_inquiry.admission_number:
                                existing_inquiry.admission_number = admission_number
                                existing_inquiry.save(update_fields=['admission_number'])
                            # Check for an unsubmitted assignment (in-progress) — reuse it
                            assignment = TestAssignment.objects.filter(
                                inquiry=existing_inquiry,
                                paper=paper,
                                school_session=session,
                            ).first()
                            if not assignment:
                                assignment = TestAssignment.objects.create(
                                    inquiry=existing_inquiry,
                                    paper=paper,
                                    school_session=session,
                                )
                            return redirect('test_shell', token=assignment.token)
                    else:
                        # New student — create Inquiry + TestAssignment
                        inquiry = Inquiry.objects.create(
                            student_name=student_name,
                            phone=phone,
                            admission_number=admission_number,
                            school=session.school_name,
                            address='',
                            inquiry_origin='walk_in',
                            campaign=session.campaign,
                        )
                        inquiry.classes.add(class_obj)
                        assignment = TestAssignment.objects.create(
                            inquiry=inquiry,
                            paper=paper,
                            school_session=session,
                        )
                        return redirect('test_shell', token=assignment.token)

    return render(request, 'sat/school_kiosk.html', {
        'session': session,
        'classes': classes,
        'error': error,
    })
