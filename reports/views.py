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
    Mentor,
    Subject,
    StudentEnrollment,
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

    get_subjectwise_attendance,
    get_subjectwise_homework,
    get_subjectwise_marks,
    get_subjectwise_attendance_calendar,
    get_subjectwise_homework_calendar,

    get_subject_test_reports,

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
    get_batch_performance_over_time,

    get_student_batches_qs,
)

from .teachers_utility import (
    get_teacher_attendance_performance,
    get_teacher_batchwise_attendance_performance,
    get_teacher_combined_homework_performance,
    get_teacher_batchwise_homework_performance,
    get_teacher_marks_percentage,
    get_teacher_batchwise_marks_performance,
    get_batches_test_performance,
    get_batches_attendance_performance,
    get_batches_homework_performance,
)

@login_required(login_url='login')
def student_report(request, stu_id):
    student = Student.objects.filter(stu_id=stu_id).first()
    if stu_id and not student:
        messages.error(request, "Invalid Student")
        return redirect('students_enrollment_list')

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
        period = ReportPeriod.objects.all().order_by('-end_date').first()
        if period:
            start_date = period.start_date
            end_date = period.end_date
        else:
            today = date.today()
            start_date = today.replace(day=1)
            end_date = today
    
    batches = get_student_batches_qs(student).exclude(
            Q(class_name__name__in=['CLASS 9', 'CLASS 10']) &
            Q(section__name='CBSE') &
            Q(subject__name__in=['MATH', 'SCIENCE'])
        ).order_by('-created_at')

    subjectwise_attendance = get_subjectwise_attendance(student, start_date, end_date)
    subjectwise_homework = get_subjectwise_homework(student, start_date, end_date)

    subjectwise_marks = get_subjectwise_marks(student, start_date, end_date)

    return render(request, 'reports/student_report.html', {
        'student': student,
        'subjectwise_attendance': subjectwise_attendance,
        'subjectwise_homework': subjectwise_homework,
        'subjectwise_marks': subjectwise_marks,
        'start_date': start_date,
        'end_date': end_date,
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
    
    batches = get_student_batches_qs(student).exclude(
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
def student_subject_attendance_report(request, stu_id, subject_id):
    student = Student.objects.filter(stu_id=stu_id).first()
    if stu_id and not student:
        messages.error(request, "Invalid Student")
        return redirect('student_report', stu_id=stu_id)
    
    subject = Subject.objects.filter(id=subject_id).first()
    if not subject:
        messages.error(request, "Invalid Subject")
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

    subject_attendance = get_subjectwise_attendance_calendar(student, subject, start_date, end_date)

    return render(request, 'reports/student_subject_attendance_report.html', {
        'student': student,
        'subject_attendance': subject_attendance,

        'start_date': start_date,
        'end_date': end_date,
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
    
    batches = get_student_batches_qs(student).exclude(
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
def student_subject_homework_report(request, stu_id, subject_id):
    student = Student.objects.filter(stu_id=stu_id).first()

    subject = Subject.objects.filter(id=subject_id).first()

    if stu_id and not student:
        messages.error(request, "Invalid Student")
        return redirect('student_report', stu_id=stu_id)

    if not subject:
        messages.error(request, "Invalid Subject")
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

    subject_homework = get_subjectwise_homework_calendar(student, subject, start_date, end_date)


    return render(request, 'reports/student_subject_homework_report.html', {
        'student': student,
        'subject_homework': subject_homework,
        'start_date': start_date,
        'end_date': end_date,

    })


@login_required(login_url='login')
def student_subject_test_summary_report(request, stu_id, subject_id):
    student = Student.objects.filter(stu_id=stu_id).first()
    subject = Subject.objects.filter(id=subject_id).first()

    if stu_id and not student:
        messages.error(request, "Invalid Student")
        return redirect('student_report', stu_id=stu_id)
    
    if not subject:
        messages.error(request, "Invalid Subject")
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

    
    subject_test_reports = get_subject_test_reports(student, subject, start_date, end_date)
    return render(request, 'reports/student_subject_test_summary_report.html', {
        'student': student,

        'start_date': start_date,
        'end_date': end_date,

        'subject_test_reports': subject_test_reports,

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
    
    batches = get_student_batches_qs(student).exclude(
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
        return redirect('students_enrollment_list')

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
        period = ReportPeriod.objects.all().order_by('-end_date').first()
        if period:
            start_date = period.start_date
            end_date = period.end_date
        else:
            today = date.today()
            start_date = today.replace(day=1)
            end_date = today
    
    batches = get_student_batches_qs(student).exclude(
            Q(class_name__name__in=['CLASS 9', 'CLASS 10']) &
            Q(section__name='CBSE') &
            Q(subject__name__in=['MATH', 'SCIENCE'])
        ).order_by('-created_at')

    subjectwise_attendance = get_subjectwise_attendance(student, start_date, end_date)
    subjectwise_homework = get_subjectwise_homework(student, start_date, end_date)
    subjectwise_marks = get_subjectwise_marks(student, start_date, end_date)

    return render(request, 'reports/student_report.html', {
        'student': student,
        'subjectwise_attendance': subjectwise_attendance,
        'subjectwise_homework': subjectwise_homework,
        'subjectwise_marks': subjectwise_marks,
        'start_date': start_date,
        'end_date': end_date,
        'batches': batches,
    })



@login_required(login_url='login')
def mentor_students(request):
    classes = ClassName.objects.all()
    mentorship_list = defaultdict(dict)

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
    
    for ment in Mentor.objects.all():
        if mentor and ment != mentor:
            continue
        for class_name in classes:
            if mentor:
                mentorships = mentor.mentorships.filter(
                    active=True,
                    student__active=True,
                ).filter(
                    Q(enrollment__class_name=class_name, enrollment__session__is_active=True, enrollment__active=True)
                    | Q(enrollment__isnull=True, student__enrollments__class_name=class_name, student__enrollments__session__is_active=True, student__enrollments__active=True)
                ).order_by(
                    '-created_at',
                    'student__user__first_name',
                    'student__user__last_name'
                ).distinct()
            else:
                mentorships = Mentorship.objects.filter(
                    active=True,
                    student__active=True,
                    mentor=ment,
                ).filter(
                    Q(enrollment__class_name=class_name, enrollment__session__is_active=True, enrollment__active=True)
                    | Q(enrollment__isnull=True, student__enrollments__class_name=class_name, student__enrollments__session__is_active=True, student__enrollments__active=True)
                )
            if mentorships.exists():
                mentorship_list[ment][class_name] = mentorships
    # students = generate_group_report_data_v2(request, start_date, end_date)

    return render(request, "reports/mentor_students.html", {
        'mentorship_list': dict(mentorship_list),
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
            batches = teacher.batches.filter(
                class_name=class_name,
                enrollment_links__enrollment__session__is_active=True,
                enrollment_links__enrollment__active=True,
            ).distinct().order_by('-created_at')
        else:
            batches = Batch.objects.filter(
                class_name=class_name,
                enrollment_links__enrollment__session__is_active=True,
                enrollment_links__enrollment__active=True,
            ).distinct().order_by('-created_at')

        # build batchwise student lists and a deduplicated classwise list
        class_student_set = []
        seen = set()
        for batch in batches:
            students_qs = Student.objects.filter(
                enrollments__batch_links__batch=batch,
                enrollments__session__is_active=True,
                enrollments__active=True,
                active=True,
            ).order_by(
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
    attendance_type = request.GET.get("type")

    attendance_type_choices = Attendance.ATTENDANCE_TYPE
    selected_type = attendance_type if attendance_type in dict(attendance_type_choices) else 'Regular'


    try:
        latest_date = datetime.strptime(latest_date_str, "%Y-%m-%d").date() if latest_date_str else date.today()
        n_days = int(n_days)
    except (ValueError, TypeError):
        messages.error(request, "Invalid date or number of days.")
        return redirect('some_dashboard_or_form_page')
    
    earliest_date = latest_date - timedelta(days=n_days*2)

    data = defaultdict(lambda: defaultdict(list))
    batches = Batch.objects.filter(
        enrollment_links__enrollment__session__is_active=True,
        enrollment_links__enrollment__active=True,
    ).distinct().prefetch_related(
        Prefetch(
            'attendance',
            queryset=Attendance.objects.filter(type=selected_type, date__lte=latest_date, date__gte=latest_date - timedelta(days=n_days*2))
            .select_related('student', 'student__user')
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

            # Ensure student belongs to this batch (session-aware)
            if not Batch.objects.filter(
                id=batch.id,
                enrollment_links__enrollment__student=student,
                enrollment_links__enrollment__session__is_active=True,
                enrollment_links__enrollment__active=True,
            ).exists():
                continue

            if all(not att.is_present for att in records[:n_days]):
                class_name = batch.class_name.name if batch.class_name else "Unknown"
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
        'type_choices': attendance_type_choices,
        'selected_type': selected_type,
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

        'batches': teacher.batches.filter(
            enrollment_links__enrollment__session__is_active=True,
            enrollment_links__enrollment__active=True,
        ).distinct().exclude(
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

    period = ReportPeriod.objects.all().order_by('-end_date').first()
    if period:
        start_date, end_date = period.start_date, period.end_date
    else:
        today = date.today()
        start_date, end_date = today.replace(day=1), today

    # Date range handling
    filter_start_date = request.GET.get('filter_start_date')
    filter_end_date = request.GET.get('filter_end_date')
    if filter_start_date and filter_end_date:
        try:
            filter_start_date = datetime.strptime(filter_start_date, "%Y-%m-%d").date()
            filter_end_date = datetime.strptime(filter_end_date, "%Y-%m-%d").date()
        except ValueError:
            messages.error(request, "Invalid date format")
            return redirect('mentor_students')
    else:
        filter_start_date = start_date
        filter_end_date = end_date

    # Data prep
    stu_performance = generate_single_student_report_data(student, filter_start_date, filter_end_date)   
    student_test_report = get_student_test_report(student, filter_start_date, filter_end_date)
    student_retest_report = get_student_retest_report(student, filter_start_date, filter_end_date)

    batches = get_student_batches_qs(student).order_by('-created_at')

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
        for batch in batches:
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
        'filter_start_date': filter_start_date,
        'filter_end_date': filter_end_date,
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

    if batch_id and not Batch.objects.filter(
        id=batch_id,
        enrollment_links__enrollment__session__is_active=True,
        enrollment_links__enrollment__active=True,
    ).exists():
        messages.error(request, "Invalid Batch")
        return redirect('compare_class', class_id=class_id)

    if class_id:
        cls = ClassName.objects.filter(id=class_id).first()
        batches = Batch.objects.filter(
            class_name=cls,
            enrollment_links__enrollment__session__is_active=True,
            enrollment_links__enrollment__active=True,
        ).distinct().order_by('created_at').exclude(
            Q(class_name__name__in=['CLASS 9', 'CLASS 10']) &
            Q(section__name='CBSE') &
            Q(subject__name__in=['MATH', 'SCIENCE'])
        )
    else:
        batches = None

    if batch_id:
        batch = Batch.objects.filter(
            id=batch_id,
            enrollment_links__enrollment__session__is_active=True,
            enrollment_links__enrollment__active=True,
        ).distinct().first()

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

from collections import defaultdict
from django.db.models import Count, Q, Max
from datetime import datetime, date

@login_required(login_url='login')
def batch_updated_list(request):
    date_str = request.GET.get('date')
    type = request.GET.get('type', 'Regular')

    if date_str:
        try:
            filter_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            messages.error(request, "Invalid date format")
            return redirect('batch_updated_list')
    else:
        # 🔥 Get latest attendance date
        filter_date = (
            Attendance.objects
            .aggregate(latest=Max('date'))
            .get('latest')
        ) or date.today()

    # Attendance aggregation
    attendance_qs = (
        Attendance.objects
        .filter(date=filter_date, type=type)
        .values('batch')
        .annotate(
            present=Count('id', filter=Q(is_present=True)),
            absent=Count('id', filter=Q(is_present=False)),
        )
    )
    attendance_map = {a['batch']: a for a in attendance_qs}

    # Homework aggregation
    homework_qs = (
        Homework.objects
        .filter(date=filter_date)
        .values('batch')
        .annotate(
            pending=Count('id', filter=Q(status='Pending')),
            partial=Count('id', filter=Q(status='Partial Done')),
            completed=Count('id', filter=Q(status='Completed')),
        )
    )
    homework_map = {h['batch']: h for h in homework_qs}

    # Relevant batches
    batches = (
        Batch.objects
        .filter(
            Q(id__in=attendance_map.keys()) |
            Q(id__in=homework_map.keys())
        )
        .select_related('class_name')
        .order_by('class_name__name')
    )

    batches_by_class = defaultdict(list)

    for batch in batches:
        class_name = batch.class_name.name if batch.class_name else "Unknown"

        attendance = attendance_map.get(batch.id)
        homework = homework_map.get(batch.id)

        batches_by_class[class_name].append({
            'batch': batch,
            'attendance': {
                'present': attendance['present'],
                'absent': attendance['absent'],
            } if attendance else {},
            'attendance_record_present': bool(attendance),
            'homework': {
                'pending': homework['pending'],
                'partial': homework['partial'],
                'completed': homework['completed'],
            } if homework else {},
            'homework_record_present': bool(homework),
        })
    
    return render(request, 'reports/batch_updated_list.html', {
        'batches_by_class': dict(batches_by_class),
        'filter_date': filter_date,
        'selected_type': type,
        'type_choices': Attendance.ATTENDANCE_TYPE,
    })


@login_required(login_url='login')
def admin_report(request):
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')

    if start_date_str and end_date_str:
        try:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
        except ValueError:
            messages.error(request, "Invalid date format")
            return redirect('staff_dashboard')
    else:
        period = ReportPeriod.objects.all().order_by('-start_date').first()
        if period:
            start_date = period.start_date
            end_date = period.end_date
        else:
            today = date.today()
            start_date = today.replace(day=1)
            end_date = today
    
    batches = Batch.objects.filter(
        enrollment_links__enrollment__session__is_active=True,
        enrollment_links__enrollment__active=True,
    ).distinct()

    batch_performance = get_batches_test_performance(
        start_date,
        end_date
    ) if batches else dict()

    batch_attendance = get_batches_attendance_performance(
        start_date,
        end_date
    ) if batches else dict()

    batch_homework = get_batches_homework_performance(
        start_date,
        end_date
    ) if batches else dict()

    # Merge all batch data and filter/sort based on GET parameters
    order_by = request.GET.get('order_by', 'test')  # Default sort by batch name
    order_type = request.GET.get('order_type', 'desc')  # Default ascending
    # filter_by = request.GET.get('filter_by', 'all')  # Default show all metrics

    batch_data = []
    for batch in batches:
        data = {
            'batch': batch,
            'attendance': batch_attendance.get(batch, 0),
            'homework': batch_homework.get(batch, 0), 
            'test': batch_performance.get(batch, 0)
        }
        batch_data.append(data)

    # # Filter data if needed
    # if filter_by == 'attendance':
    #     batch_data = [d for d in batch_data if d['attendance'] > 0]
    # elif filter_by == 'homework':
    #     batch_data = [d for d in batch_data if d['homework'] > 0]
    # elif filter_by == 'test':
    #     batch_data = [d for d in batch_data if d['test'] > 0]

    # Sort the data
    reverse = order_type == 'desc'
    if order_by == 'name':
        batch_data.sort(key=lambda x: x['batch'].name, reverse=reverse)
    elif order_by == 'attendance':
        batch_data.sort(key=lambda x: x['attendance'], reverse=reverse)
    elif order_by == 'homework':
        batch_data.sort(key=lambda x: x['homework'], reverse=reverse)
    elif order_by == 'test':
        batch_data.sort(key=lambda x: x['test'], reverse=reverse)

    return render(request, 'reports/admin_report.html', {
        'batch_data': batch_data,
        'order_by': order_by,
        'order_type': order_type,
        # 'filter_by': filter_by,
        'start_date': start_date,
        'end_date': end_date,
    })
    # return HttpResponse("Admin Report Page - Under Construction")

# @login_required(login_url='login')
# def teacher_report(request, teacher_id):
#     teacher = Teacher.objects.filter(id=teacher_id).first()
#     if not teacher:
#         messages.error(request, "Invalid Teacher")
#         return redirect('teachers_list')

#     start_date_str = request.GET.get('start_date')
#     end_date_str = request.GET.get('end_date')

#     if start_date_str and end_date_str:
#         try:
#             start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
#             end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
#         except ValueError:
#             messages.error(request, "Invalid date format")
#             return redirect('teacher_report', teacher_id=teacher_id)
#     else:
#         period = ReportPeriod.objects.all().order_by('-start_date').first()
#         if period:
#             start_date = period.start_date
#             end_date = period.end_date
#         else:
#             today = date.today()
#             start_date = today.replace(day=1)
#             end_date = today

#     combined_attendance = get_teacher_attendance_performance(teacher, start_date, end_date)
#     batchwise_attendance = get_teacher_batchwise_attendance_performance(teacher,start_date, end_date)
#     combined_homework = get_teacher_combined_homework_performance(teacher, start_date, end_date)
#     batchwise_homework = get_teacher_batchwise_homework_performance(teacher, start_date, end_date)
#     combined_marks = get_teacher_marks_percentage(teacher, start_date, end_date)
#     batchwise_marks = get_teacher_batchwise_marks_performance(teacher, start_date, end_date)

#     return render(request, 'reports/teacher_report.html', {
#         'teacher': teacher,
#         'start_date': start_date,
#         'end_date': end_date,

#         'batches': teacher.batches.all().exclude(
#             Q(class_name__name__in=['CLASS 9', 'CLASS 10']) &
#             Q(section__name='CBSE') &
#             Q(subject__name__in=['MATH', 'SCIENCE'])
#         ),

#         'combined_attendance': combined_attendance,
#         'batchwise_attendance': batchwise_attendance,
#         'combined_homework': combined_homework,
#         'batchwise_homework': batchwise_homework,
#         'combined_marks': combined_marks,
#         'batchwise_marks': batchwise_marks,
#     })

