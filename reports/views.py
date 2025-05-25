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
    Teacher
    )
from collections import defaultdict
from django.db.models import Q
from django.contrib import messages
from django.db.models import Count

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

    get_marks_percentage,
    get_batchwise_marks,
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
        today = date.today()
        start_date = today.replace(day=1)
        end_date = today
    
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

            # If no responses and no result, mark as absent
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
    batchwise_attendance = get_batchwise_attendance(student,start_date, end_date)
    combined_homework = get_combined_homework(student, start_date, end_date)
    batchwise_homework = get_batchwise_homework(student, start_date, end_date)
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
                student__class_enrolled=class_name
            )
        class_mentorships[class_name] = mentorships
    
    students = generate_group_report_data_v2(request, start_date, end_date)

    return render(request, "reports/mentor_students.html", {
        'class_mentorships': class_mentorships,
        'students': students,
        'start_date': start_date,
        'end_date': end_date,
    })


@login_required(login_url='login')
def regular_absent_students(request):
    start_date_str = request.GET.get('start_date')
    n_days = request.GET.get('n_days', 2)  # default 3 days if not provided

    try:
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date() if start_date_str else date.today()
        n_days = int(n_days)
    except (ValueError, TypeError):
        messages.error(request, "Invalid date or number of days.")
        return redirect('some_dashboard_or_form_page')

    end_date = start_date - timedelta(days=n_days - 1)
    # date_range = [start_date - timedelta(days=i) for i in range(n_days)]

    # Filter attendance marked as 'A' in this date range
    absent_students = Attendance.objects.filter(
        date__range=(end_date, start_date),
        is_present=False,
        student__active=True,
    ).values('student').annotate(
        absent_count=Count('id')
    ).filter(absent_count=n_days).values_list('student', flat=True)

    students = Student.objects.filter(id__in=absent_students).select_related('user', 'class_enrolled')

    # Group students class-wise
    classwise_data = {}
    for student in students:
        class_name = student.class_enrolled.name if student.class_enrolled else 'Unknown'
        classwise_data.setdefault(class_name, []).append(student)

    return render(request, 'reports/consistent_absentees.html', {
        'class_students': classwise_data,
        'start_date': start_date,
        'n_days': n_days,
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