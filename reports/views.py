from django.shortcuts import render, redirect
import calendar
from datetime import date, timedelta, datetime
from django.contrib.auth.decorators import login_required
from registration.models import (
    ClassName, 
    Student, 
    Batch, 
    Attendance, 
    Homework,
    TestQuestion,
    QuestionResponse,
    Test,
    TestResult,
    Mentor,
    Mentorship,
    Teacher,
    ReportPeriod,

    MentorRemark,
    Action, ActionSuggested,

    ReportNegative,
    ReportPositive,
    Recommendation,
    StudentTestRemark,
    StudentRemark,
    )
from django.utils import timezone
from collections import defaultdict
from django.db.models import Q, Prefetch
from django.contrib import messages
from django.db.models import Count

from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, HttpResponseBadRequest
from django.template.loader import render_to_string
from django.utils.dateparse import parse_date



from .utility import (
    get_combined_attendance,
    get_batchwise_attendance,
    get_combined_homework,
    get_batchwise_homework,
    get_monthly_calendar,
    get_chapters_from_questions,
    calculate_testwise_remarks,
    calculate_marks,
    generate_group_report_data_v2,
    generate_single_student_report_data,

    get_marks_percentage,
    get_batchwise_marks,
    get_student_test_report,
    get_student_retest_report,
    has_report,
    compare_student_performance_by_week,
)

from .teachers_utility import (
    get_teacher_attendance_performance,
    get_teacher_batchwise_attendance_performance,
    get_teacher_combined_homework_performance,
    get_teacher_batchwise_homework_performance,
    get_teacher_marks_percentage,
    get_teacher_batchwise_marks_performance
)

@login_required(login_url='login')
def student_report(request, stu_id):
    student = Student.objects.filter(stu_id=stu_id).first()
    if stu_id and not student:
        messages.error(request, "Invalid Student")
        return redirect('batchwise_students')

    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')

    if start_date_str and end_date_str:
        try:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
        except ValueError:
            messages.error(request, "Invalid date format")
            return redirect('student_report', stu_id=stu_id)
    else:
        period = ReportPeriod.objects.all().order_by('-start_date').first()
        if period:
            start_date = period.start_date
            end_date = period.end_date
        else:
            today = date.today()
            start_date = today.replace(day=1)
            end_date = today
    
    batches = student.batches.all().filter(class_name=student.class_enrolled).exclude(
            Q(class_name__name__in=['CLASS 9', 'CLASS 10']) &
            Q(section__name='CBSE') &
            Q(subject__name__in=['MATH', 'SCIENCE'])
        ).order_by('-created_at')

    combined_attendance = get_combined_attendance(student, start_date, end_date)
    batchwise_attendance = get_batchwise_attendance(student,start_date, end_date)
    combined_homework = get_combined_homework(student, start_date, end_date)
    batchwise_homework = get_batchwise_homework(student, start_date, end_date)
    combined_marks = get_marks_percentage(student, start_date, end_date)
    batchwise_marks = get_batchwise_marks(student, start_date, end_date)

    # calendar_data = get_monthly_calendar(student, start_date, end_date)
    return render(request, 'reports/student_report.html', {
        'student': student,
        'combined_attendance': combined_attendance,
        'batchwise_attendance': batchwise_attendance,
        'combined_homework': combined_homework,
        'batchwise_homework': batchwise_homework,
        'combined_marks': combined_marks,
        'batchwise_marks': batchwise_marks,

        # 'calendar_data': calendar_data,
        'start_date': start_date,
        'end_date': end_date,

        # 'batch_wise_tests': batch_wise_tests,
        'batches': batches,
    })


@login_required(login_url='login')
def student_attendance_report(request, stu_id):
    student = Student.objects.filter(stu_id=stu_id).first()
    if stu_id and not student:
        messages.error(request, "Invalid Student")
        return redirect('student_report', stu_id=stu_id)

    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')

    if start_date_str and end_date_str:
        try:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
        except ValueError:
            messages.error(request, "Invalid date format")
            return redirect('student_report', stu_id=stu_id)
    else:
        period = ReportPeriod.objects.all().order_by('-start_date').first()
        if period:
            start_date = period.start_date
            end_date = period.end_date
        else:
            today = date.today()
            start_date = today.replace(day=1)
            end_date = today
    
    batches = student.batches.all().filter(class_name=student.class_enrolled).exclude(
            Q(class_name__name__in=['CLASS 9', 'CLASS 10']) &
            Q(section__name='CBSE') &
            Q(subject__name__in=['MATH', 'SCIENCE'])
        ).order_by('-created_at')
    
    calendar_data = get_monthly_calendar(student, start_date, end_date)
    combined_attendance = get_combined_attendance(student, start_date, end_date)
    batchwise_attendance = get_batchwise_attendance(student,start_date, end_date)

    return render(request, 'reports/student_attendance_report.html', {
        'student': student,
        'combined_attendance': combined_attendance,
        'batchwise_attendance': batchwise_attendance,

        'calendar_data': calendar_data,
        'start_date': start_date,
        'end_date': end_date,

        'batches': batches,
    })


@login_required(login_url='login')
def student_homework_report(request, stu_id):
    student = Student.objects.filter(stu_id=stu_id).first()
    if stu_id and not student:
        messages.error(request, "Invalid Student")
        return redirect('student_report', stu_id=stu_id)

    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')

    if start_date_str and end_date_str:
        try:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
        except ValueError:
            messages.error(request, "Invalid date format")
            return redirect('student_report', stu_id=stu_id)
    else:
        period = ReportPeriod.objects.all().order_by('-start_date').first()
        if period:
            start_date = period.start_date
            end_date = period.end_date
        else:
            today = date.today()
            start_date = today.replace(day=1)
            end_date = today
    
    batches = student.batches.all().filter(class_name=student.class_enrolled).exclude(
            Q(class_name__name__in=['CLASS 9', 'CLASS 10']) &
            Q(section__name='CBSE') &
            Q(subject__name__in=['MATH', 'SCIENCE'])
        ).order_by('-created_at')
    
    combined_homework = get_combined_homework(student, start_date, end_date)
    batchwise_homework = get_batchwise_homework(student, start_date, end_date)

    return render(request, 'reports/student_homework_report.html', {
        'student': student,
        'combined_homework': combined_homework,
        'batchwise_homework': batchwise_homework,

        'start_date': start_date,
        'end_date': end_date,

        'batches': batches,
    })


@login_required(login_url='login')
def student_test_summary_report(request, stu_id):
    student = Student.objects.filter(stu_id=stu_id).first()
    if stu_id and not student:
        messages.error(request, "Invalid Student")
        return redirect('student_report', stu_id=stu_id)

    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')

    if start_date_str and end_date_str:
        try:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
        except ValueError:
            messages.error(request, "Invalid date format")
            return redirect('student_report', stu_id=stu_id)
    else:
        period = ReportPeriod.objects.all().order_by('-start_date').first()
        if period:
            start_date = period.start_date
            end_date = period.end_date
        else:
            today = date.today()
            start_date = today.replace(day=1)
            end_date = today
    
    batches = student.batches.all().filter(class_name=student.class_enrolled).exclude(
            Q(class_name__name__in=['CLASS 9', 'CLASS 10']) &
            Q(section__name='CBSE') &
            Q(subject__name__in=['MATH', 'SCIENCE'])
        ).order_by('-created_at')
    
    combined_marks = get_marks_percentage(student, start_date, end_date)
    batchwise_marks = get_batchwise_marks(student, start_date, end_date)

    return render(request, 'reports/student_test_summary_report.html', {
        'student': student,
        'combined_marks': combined_marks,
        'batchwise_marks': batchwise_marks,

        'start_date': start_date,
        'end_date': end_date,

        'batches': batches,
    })




@login_required(login_url='login')
def student_personal_report(request, stu_id):
    student = Student.objects.filter(stu_id=stu_id).first()
    if stu_id and not student:
        messages.error(request, "Invalid Student")
        return redirect('staff_dashboard')

    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')

    if start_date_str and end_date_str:
        try:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
        except ValueError:
            messages.error(request, "Invalid date format")
            return redirect('student_personal_report', stu_id=stu_id)
    else:
        period = ReportPeriod.objects.all().order_by('-start_date').first()
        if period:
            start_date = period.start_date
            end_date = period.end_date
        else:
            today = date.today()
            start_date = today.replace(day=1)
            end_date = today

    # Use same batch filtering logic as student_report
    batches = student.batches.all().filter(class_name=student.class_enrolled).exclude(
        Q(class_name__name__in=['CLASS 9', 'CLASS 10']) &
        Q(section__name='CBSE') &
        Q(subject__name__in=['MATH', 'SCIENCE'])
    ).order_by('-created_at')
    batch_wise_tests = {}

    for batch in batches:
        tests = Test.objects.filter(batch=batch, date__range=(start_date, end_date)).order_by('-date')
        test_reports = []

        for test in tests:
            test_chapters = get_chapters_from_questions(test)
            responses = QuestionResponse.objects.filter(test=test, student=student).select_related('question', 'remark')
            test_result = TestResult.objects.filter(test=test, student=student).first()

            # If no responses and no result, mark as absent (same as student_report)
            if not responses.exists() and not test_result:
                test_reports.append({
                    'test': test,
                    'chapters': test_chapters,
                    'absent': True,
                })
                continue

            chapter_remarks = calculate_testwise_remarks(responses, test_chapters)
            marks_data = calculate_marks(responses, test_chapters)

            test_reports.append({
                'test': test,
                'chapters': test_chapters,
                'marks_total': marks_data['total'],
                'marks_deducated': marks_data['deducted'],
                'marks_obtained': marks_data['obtained'],
                'remarks': marks_data['remarks'],
                'max_marks': marks_data['max_marks'],
                'marks': {
                    'percentage': marks_data['percentage'],
                    'obtained_marks': marks_data['obtained_total'],
                    'max_marks': marks_data['total_max'],
                },
                'chapter_wise_test_remarks': chapter_remarks,
                'absent': False,
            })

        batch_wise_tests[batch] = test_reports

    combined_attendance = get_combined_attendance(student, start_date, end_date)
    batchwise_attendance = get_batchwise_attendance(student, start_date, end_date)
    combined_homework = get_combined_homework(student, start_date, end_date)
    batchwise_homework = get_batchwise_homework(student, start_date, end_date)

    # Add marks summary as in student_report
    combined_marks = get_marks_percentage(student, start_date, end_date)
    batchwise_marks = get_batchwise_marks(student, start_date, end_date)

    calendar_data = get_monthly_calendar(student, start_date, end_date)
    return render(request, 'reports/student_report.html', {
        'student': student,
        'combined_attendance': combined_attendance,
        'batchwise_attendance': batchwise_attendance,
        'combined_homework': combined_homework,
        'batchwise_homework': batchwise_homework,
        'combined_marks': combined_marks,
        'batchwise_marks': batchwise_marks,
        'calendar_data': calendar_data,
        'start_date': start_date,
        'end_date': end_date,
        'batch_wise_tests': batch_wise_tests,
        'batches': batches,
    })


@login_required(login_url='login')
def batchwise_students(request):
    batches = Batch.objects.all().order_by('-created_at')
    batch_students = [
        {'batch': batch, 'students': Student.objects.filter(batches=batch).order_by('-created_at', 'user__first_name', 'user__last_name').distinct()} for batch in batches
    ]
    
    count = Student.objects.all().distinct().count()
    
    return render(request, "reports/batchwise_students.html", {
        'batch_students': batch_students,
        'count': count,
    })

@login_required(login_url='login')
def mentor_students(request):
    classes = ClassName.objects.all()
    class_mentorships = {}

    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')

    if start_date_str and end_date_str:
        try:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
        except ValueError:
            messages.error(request, "Invalid date format")
            return redirect('mentor_students')
    else:
        period = ReportPeriod.objects.all().order_by('-start_date').first()
        if period:
            start_date = period.start_date
            end_date = period.end_date
        else:
            today = date.today()
            start_date = today.replace(day=1)
            end_date = today

    mentor = getattr(request.user, 'mentor_profile', None)
    
    if not mentor and not request.user.is_superuser:
        messages.error(request, "You are not authorized to view this page.")
        return redirect('staff_dashboard')

    for class_name in classes:
        if mentor:
            mentorships = mentor.mentorships.filter(
                active=True,
                student__class_enrolled=class_name,
                student__active=True,
            ).order_by(
                '-created_at',
                'student__user__first_name',
                'student__user__last_name'
            ).distinct()
        else:
            mentorships = Mentorship.objects.filter(
                active=True,
                student__class_enrolled=class_name,
                student__active=True,
            )
        class_mentorships[class_name] = mentorships
    
    # students = generate_group_report_data_v2(request, start_date, end_date)

    return render(request, "reports/mentor_students.html", {
        'class_mentorships': class_mentorships,
        # 'students': students,
        'start_date': start_date,
        'end_date': end_date,
    })


@login_required(login_url='login')
def teacher_students(request):
    teacher = getattr(request.user, 'teachers', None)

    if not (teacher or request.user.is_superuser):
        messages.error(request, "You are not authorized to view this page.")
        return redirect('staff_dashboard')

    classes = ClassName.objects.all().order_by('created_at')
    class_students = {}

    for class_name in classes:
        # batches for this class assigned to the teacher (or all batches if superuser)
        if teacher:
            batches = teacher.batches.filter(class_name=class_name).order_by('-created_at')
        else:
            batches = Batch.objects.filter(class_name=class_name).order_by('-created_at')

        # build batchwise student lists and a deduplicated classwise list
        class_student_set = []
        seen = set()
        for batch in batches:
            students_qs = Student.objects.filter(batches=batch, active=True).order_by(
                '-created_at', 'user__first_name', 'user__last_name'
            ).distinct()
            students = list(students_qs)
            for s in students:
                if s.stu_id not in seen:
                    seen.add(s.stu_id)
                    class_student_set.append(s)

        # only add classes that have at least one batch or student
        if class_student_set:
            class_students[class_name] = class_student_set

    return render(request, 'reports/teacher_students.html', {
        'teacher': teacher,
        'class_students': class_students,
    })

@login_required(login_url='login')
def regular_absent_students(request):
    latest_date_str = request.GET.get('latest_date')
    n_days = request.GET.get('n_days', 2)  # default 3 days if not provided

    try:
        latest_date = datetime.strptime(latest_date_str, "%Y-%m-%d").date() if latest_date_str else date.today()
        n_days = int(n_days)
    except (ValueError, TypeError):
        messages.error(request, "Invalid date or number of days.")
        return redirect('some_dashboard_or_form_page')
    
    earliest_date = latest_date - timedelta(days=n_days*2)

    data = defaultdict(lambda: defaultdict(list))
    batches = Batch.objects.prefetch_related(
        Prefetch(
            'attendance',
            queryset=Attendance.objects.filter(date__lte=latest_date, date__gte=latest_date - timedelta(days=n_days*2))
            .select_related('student', 'student__user', 'student__class_enrolled')
            .order_by('-date'),
            to_attr='recent_attendance'
        )
    )

    for batch in batches:
        student_attendance_map = defaultdict(list)

        for att in batch.recent_attendance:
            student_attendance_map[att.student].append(att)
            if len(student_attendance_map[att.student]) == n_days:
                continue  # only need last n

        for student, records in student_attendance_map.items():
            if len(records) < n_days:
                continue

            if not batch in student.batches.all():
                continue

            if all(not att.is_present for att in records[:n_days]):
                class_name = student.class_enrolled.name if student.class_enrolled else "Unknown"
                data[class_name][batch].append(student)

    # Convert defaultdicts to normal dicts/lists for template compatibility
    data = {
        class_name: {
            batch_name: list(students)
            for batch_name, students in batch_map.items()
        }
        for class_name, batch_map in data.items()
    }

    return render(request, 'reports/consistent_absentees.html', {
        'absentees': data,
        'n_days': n_days,
        'latest_date': latest_date,
        'earliest_date': earliest_date,
    })


@login_required(login_url='login')
def teachers_list(request):
    teachers = Teacher.objects.all().order_by('user__first_name', 'user__last_name')
    
    return render(request, 'reports/teachers_list.html', {
        'teachers': teachers,
    })

@login_required(login_url='login')
def teacher_report(request, teacher_id):
    teacher = Teacher.objects.filter(id=teacher_id).first()
    if not teacher:
        messages.error(request, "Invalid Teacher")
        return redirect('teachers_list')

    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')

    if start_date_str and end_date_str:
        try:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
        except ValueError:
            messages.error(request, "Invalid date format")
            return redirect('teacher_report', teacher_id=teacher_id)
    else:
        period = ReportPeriod.objects.all().order_by('-start_date').first()
        if period:
            start_date = period.start_date
            end_date = period.end_date
        else:
            today = date.today()
            start_date = today.replace(day=1)
            end_date = today

    combined_attendance = get_teacher_attendance_performance(teacher, start_date, end_date)
    batchwise_attendance = get_teacher_batchwise_attendance_performance(teacher,start_date, end_date)
    combined_homework = get_teacher_combined_homework_performance(teacher, start_date, end_date)
    batchwise_homework = get_teacher_batchwise_homework_performance(teacher, start_date, end_date)
    combined_marks = get_teacher_marks_percentage(teacher, start_date, end_date)
    batchwise_marks = get_teacher_batchwise_marks_performance(teacher, start_date, end_date)

    return render(request, 'reports/teacher_report.html', {
        'teacher': teacher,
        'start_date': start_date,
        'end_date': end_date,

        'batches': teacher.batches.all().exclude(
            Q(class_name__name__in=['CLASS 9', 'CLASS 10']) &
            Q(section__name='CBSE') &
            Q(subject__name__in=['MATH', 'SCIENCE'])
        ),

        'combined_attendance': combined_attendance,
        'batchwise_attendance': batchwise_attendance,
        'combined_homework': combined_homework,
        'batchwise_homework': batchwise_homework,
        'combined_marks': combined_marks,
        'batchwise_marks': batchwise_marks,
    })

@login_required(login_url='login')
def mentor_remarks(request, mentor_id, student_id):
    mentor = Mentor.objects.filter(id=mentor_id).first()
    student = Student.objects.filter(stu_id=student_id).first()
    student_remarks = StudentRemark.objects.filter(student=student).order_by('-created_at')

    if not mentor or not student:
        messages.error(request, "Invalid Mentor or Student")
        return redirect('mentor_students')

    # Date range handling
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    if start_date and end_date:
        try:
            start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
            end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
        except ValueError:
            messages.error(request, "Invalid date format")
            return redirect('mentor_students')
    else:
        period = ReportPeriod.objects.all().order_by('-start_date').first()
        if period:
            start_date, end_date = period.start_date, period.end_date
        else:
            today = date.today()
            start_date, end_date = today.replace(day=1), today

    # Data prep
    stu_performance = generate_single_student_report_data(student, start_date, end_date)   
    student_test_report = get_student_test_report(student, start_date, end_date)
    student_retest_report = get_student_retest_report(student)

    batches = student.batches.all().filter(class_name=student.class_enrolled).exclude(
        Q(class_name__name__in=['CLASS 9', 'CLASS 10']) &
        Q(section__name='CBSE') &
        Q(subject__name__in=['MATH', 'SCIENCE'])
    ).order_by('-created_at')

    remark = MentorRemark.objects.filter(
        mentor=mentor, student=student,
        start_date=start_date, end_date=end_date
    ).order_by('-created_at').first()

    recommendation = Recommendation.objects.filter(student=student, active=True).order_by('-date').first()

    if request.method == 'POST':
        mentor_remark = request.POST.get('mentor_remark')
        parent_remark = request.POST.get('parent_remark')

        mentor_negatives = request.POST.getlist('n_remark_mentor[]')
        mentor_positives = request.POST.getlist('p_remark_mentor[]')
        parent_negatives = request.POST.getlist('n_remark_parent[]')
        parent_positives = request.POST.getlist('p_remark_parent[]')

        if not remark:
            # Create new remark
            remark = MentorRemark.objects.create(
                mentor=mentor, student=student,
                start_date=start_date, end_date=end_date,
                mentor_remark=mentor_remark, parent_remark=parent_remark
            )
        else:
            # Update existing remark
            remark.mentor_remark = mentor_remark
            remark.parent_remark = parent_remark
            remark.mentor_positive.clear()
            remark.mentor_negative.clear()
            remark.parent_positive.clear()
            remark.parent_negative.clear()

        # Add positives and negatives
        for pos_id in mentor_positives:
            if pos_id:
                try:
                    remark.mentor_positive.add(ReportPositive.objects.get(id=pos_id))
                except ReportPositive.DoesNotExist:
                    continue

        for neg_id in mentor_negatives:
            if neg_id:
                try:
                    remark.mentor_negative.add(ReportNegative.objects.get(id=neg_id))
                except ReportNegative.DoesNotExist:
                    continue

        for pos_id in parent_positives:
            if pos_id:
                try:
                    remark.parent_positive.add(ReportPositive.objects.get(id=pos_id))
                except ReportPositive.DoesNotExist:
                    continue

        for neg_id in parent_negatives:
            if neg_id:
                try:
                    remark.parent_negative.add(ReportNegative.objects.get(id=neg_id))
                except ReportNegative.DoesNotExist:
                    continue

        # Assign recommendation only if not already assigned
        if recommendation and not remark.recommendation:
            recommendation.active = False
            recommendation.save()
            remark.recommendation = recommendation

        remark.save()

        # Handle ActionSuggested per batch
        for batch in student.batches.all():
            action_ids = request.POST.getlist(f'actions_{batch.id}')
            if action_ids:
                actions = Action.objects.filter(id__in=action_ids)
                action_suggested, _ = ActionSuggested.objects.get_or_create(
                    student=student, batch=batch, mentor_remark=remark
                )
                action_suggested.action.set(actions)
                action_suggested.save()
            else:
                ActionSuggested.objects.filter(student=student, batch=batch, mentor_remark=remark).delete()

        messages.success(request, "Remark saved successfully.")
        return redirect('mentor_remarks', mentor_id=mentor.id, student_id=student.stu_id)

    # For GET: Display label only
    recommendation_label = dict(Recommendation.ACTION_CHOICES).get(recommendation.action, '') if recommendation else ''
    if remark and remark.recommendation:
        recommendation_label = dict(Recommendation.ACTION_CHOICES).get(remark.recommendation.action, '') if remark.recommendation else ''


    return render(request, 'reports/mentor_remarks.html', {
        'mentor': mentor,
        'student': student,
        'remark': remark,
        'start_date': start_date,
        'end_date': end_date,
        'actions': Action.objects.all(),
        'stu_performance': stu_performance,
        'batches': batches,
        'student_test_report': student_test_report,
        'student_retest_report': student_retest_report,
        'has_report': has_report(student, start_date, end_date),
        'recommendation': recommendation,
        'recommendation_label': recommendation_label,
        'positives': ReportPositive.objects.all().order_by('name'),
        'negatives': ReportNegative.objects.all().order_by('name'),
        'student_remarks': student_remarks,
    })


def suggested_actions(request):
    # Optimize DB hits
    suggested_actions = ActionSuggested.objects.select_related(
        'student__user', 'batch'
    ).prefetch_related('action')

    # Structure: data[action][batch] = list of students
    data = defaultdict(lambda: defaultdict(list))

    for sg_action in suggested_actions:
        for action in sg_action.action.all():
            data[action][sg_action.batch].append(sg_action.student)

    data = {
        action: dict(batch_map)  # Convert inner defaultdict to dict
        for action, batch_map in data.items()
    }

    return render(request, 'reports/suggested_actions.html', {'data': dict(data)})


@login_required(login_url='login')
def compare_student_performance(request, class_id=None, batch_id=None):
    cls = None
    batch = None
    week = None
    tests = []
    students_list = []
    compare_result = {}

    if class_id and not ClassName.objects.filter(id=class_id).exists():
        messages.error(request, "Invalid Class")
        return redirect('compare_performance')

    if batch_id and not Batch.objects.filter(id=batch_id).exists():
        messages.error(request, "Invalid Batch")
        return redirect('compare_class', class_id=class_id)

    if class_id:
        cls = ClassName.objects.filter(id=class_id).first()
        batches = Batch.objects.filter(class_name=cls).order_by('created_at').exclude(
            Q(class_name__name__in=['CLASS 9', 'CLASS 10']) &
            Q(section__name='CBSE') &
            Q(subject__name__in=['MATH', 'SCIENCE'])
        )
    else:
        batches = None

    if batch_id:
        batch = Batch.objects.filter(id=batch_id).first()

    if batch_id and not batch:
        messages.error(request, "Invalid Batch")
        return redirect('compare_class', class_id=class_id)

    classes = ClassName.objects.all().order_by('created_at')


    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')

    if start_date_str and end_date_str:
        try:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
        except ValueError:
            messages.error(request, "Invalid date format")
            return redirect('mentor_students')
    else:
        period = ReportPeriod.objects.all().order_by('-start_date').first()
        if period:
            start_date = period.start_date
            end_date = period.end_date
        else:
            today = date.today()
            start_date = today.replace(day=1)
            end_date = today

    if batch:
        compare_result = compare_student_performance_by_week(batch, start_date, end_date)
        students_list = compare_result.get('students_list', [])
        tests = compare_result.get('tests', [])

    return render(request, 'reports/compare_student_performance.html', {
        'classes': classes,
        'batches': batches,
        'cls': cls,
        'batch': batch,
        'students_list': students_list,
        'compare_result': compare_result,
        'week': week,
        'tests': tests,
        'start_date': start_date,
        'end_date': end_date,
    })

@csrf_exempt
def update_recommendation(request):
    if request.method == "POST":

        try:
            action_raw = request.POST.get("action")  # value like "student_id:PTM"
            if not action_raw or ":" not in action_raw:
                return HttpResponseBadRequest("Invalid action format")

            student_id, action = action_raw.split(":", 1)

            # handle default (blank)
            if action == "" or not action.strip():
                action = None

            # You'll need to determine `date` (hardcoded, today's date, or from URL)
            date = timezone.now().date()

            student = Student.objects.get(stu_id=student_id)

            if not action:
                Recommendation.objects.filter(student=student, date=date).delete()
            else:
                latest_rec = Recommendation.objects.filter(student=student, date=date).order_by('-id').first()
                if latest_rec and latest_rec.active:
                    latest_rec.action = action
                    latest_rec.date = date
                    latest_rec.save()
                else:
                    Recommendation.objects.create(student=student, date=date, action=action, active=True)

            context = {
                "student": student,
                "recommendation": action
            }

            html = render_to_string("reports/recommendation_select.html", context)
            return HttpResponse(html)

        except Exception as e:
            import traceback
            traceback.print_exc()
            return HttpResponse(f"Server error: {e}", status=500)

    return HttpResponseBadRequest("Only POST allowed")


@csrf_exempt
def update_remark(request, test_id, student_id):
    if request.method == "POST":
        try:
            remark_text = request.POST.get("remark", "").strip()
            test = Test.objects.get(id=test_id)
            student = Student.objects.get(stu_id=student_id)

            # Update or create the remark
            if remark_text == "":
                # If remark is empty, delete existing remark if it exists
                StudentTestRemark.objects.filter(test=test, student=student).delete()
            
            # Otherwise, update or create the remark
            remark, created = StudentTestRemark.objects.update_or_create(
                test=test,
                student=student,
                defaults={'remark': remark_text}
            )

            context = {
                'remark': remark.remark,
                'test': test,
                'student': student,
            }
            html = render_to_string("reports/student_test_remark.html", context)
            return HttpResponse(html)

        except Student.DoesNotExist:
            return HttpResponseBadRequest("Invalid student ID")
        except Test.DoesNotExist:
            return HttpResponseBadRequest("Invalid test ID")
        except Exception as e:
            import traceback
            traceback.print_exc()
            return HttpResponse(f"Server error: {e}", status=500)
    return HttpResponseBadRequest("Only POST allowed")

@login_required(login_url='login')
def add_student_remarks(request, mentor_id, stu_id):
    student = Student.objects.filter(stu_id=stu_id).first()
    if stu_id and not student:
        messages.error(request, "Invalid Student")
        return redirect('student_report', stu_id=stu_id)

    if request.method == 'POST':
        remark_text = request.POST.get('student_remark')
        if remark_text:
            StudentRemark.objects.create(
                student=student,
                remark=remark_text,
                added_by=request.user
            )
            messages.success(request, "Remark added successfully")
            return redirect('mentor_remarks', mentor_id=mentor_id, student_id=stu_id)

    return redirect('mentor_remarks', mentor_id=mentor_id, student_id=stu_id)

@login_required(login_url='login')
def delete_student_remark(request, remark_id, mentor_id, stu_id):
    remark = StudentRemark.objects.filter(id=remark_id).first()
    if remark:
        remark.delete()
        messages.success(request, "Remark deleted successfully")
    else:
        messages.error(request, "Remark not found")
    return redirect('mentor_remarks', mentor_id=mentor_id, student_id=stu_id)