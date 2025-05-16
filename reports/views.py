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
    Mentorship
    )
from collections import defaultdict
from django.db.models import Q
from django.contrib import messages

from .utility import (
    get_combined_attendance,
    get_batchwise_attendance,
    get_combined_homework,
    get_batchwise_homework,
    get_monthly_calendar,
    get_chapters_from_questions,
    calculate_testwise_remarks,
    calculate_marks,
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
    
    batches = Batch.objects.filter(class_name=student.class_enrolled).order_by('-created_at')
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
    
    

    calendar_data = get_monthly_calendar(student, start_date, end_date)
    # for month_cal in calendar_data:
    #     print(month_cal)
    #     print()
    return render(request, 'reports/student_report.html', {
        'student': student,
        'combined_attendance': combined_attendance,
        'batchwise_attendance': batchwise_attendance,
        'combined_homework': combined_homework,
        'batchwise_homework': batchwise_homework,
        # 'current_month': calendar_data['calendar'],
        # 'current_month_name': calendar_data['month_name'],
        # 'current_month_present_count': calendar_data['present_count'],
        # 'current_month_total_count': calendar_data['present_count'] + calendar_data['absent_count'],
        # 'current_month_percentage': calendar_data['percentage'],
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
    
    batches = Batch.objects.filter(class_name=student.class_enrolled).order_by('-created_at')
    batch_wise_tests = {}

    for batch in batches:
        tests = Test.objects.filter(batch=batch).order_by('-date')
        test_reports = []

        for test in tests:
            test_chapters = get_chapters_from_questions(test)
            responses = QuestionResponse.objects.filter(test=test, student=student).select_related('question', 'remark')

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
            })

        batch_wise_tests[batch] = test_reports

    combined_attendance = get_combined_attendance(student, start_date, end_date)
    batchwise_attendance = get_batchwise_attendance(student,start_date, end_date)
    combined_homework = get_combined_homework(student, start_date, end_date)
    batchwise_homework = get_batchwise_homework(student, start_date, end_date)
    calendar_data = get_monthly_calendar(student, start_date, end_date)

    return render(request, 'reports/student_report.html', {
        'student': student,
        'combined_attendance': combined_attendance,
        'batchwise_attendance': batchwise_attendance,
        'combined_homework': combined_homework,
        'batchwise_homework': batchwise_homework,
        # 'current_month': calendar_data['calendar'],
        # 'current_month_name': calendar_data['month_name'],
        # 'current_month_present_count': calendar_data['present_count'],
        # 'current_month_total_count': calendar_data['present_count'] + calendar_data['absent_count'],
        # 'current_month_percentage': calendar_data['percentage'],
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

    mentor = getattr(request.user, 'mentor_profile', None)
    
    if not mentor and not request.user.is_superuser:
        messages.error(request, "You are not authorized to view this page.")
        return redirect('staff_dashboard')

    for class_name in classes:
        if mentor:
            mentorships = mentor.mentorships.filter(
                active=True,
                student__class_enrolled=class_name
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

    return render(request, "reports/mentor_students.html", {
        'class_mentorships': class_mentorships,
    })

    batches = Batch.objects.all()
    batch = None
    students = None
    student = None
    students_list = {}

    if batch and student:

        chapters = {
            question.chapter_no: question.chapter_name
            for question in TestQuestion.objects.prefetch_related('test__batch').filter(test__batch=batch).order_by('chapter_no')
        }
        question_responses = QuestionResponse.objects.prefetch_related('remark', 'question').filter(test__batch=batch, student=student).select_related('question')


        test_reports = []
        tests = Test.objects.filter(batch=batch)

        students = Student.objects.prefetch_related('batches__test', 'batches').filter(batches=batch)

        for test in tests:
            testwise_questions = TestQuestion.objects.prefetch_related('test__batch', 'test').filter(test__batch=batch, test=test).order_by('chapter_no')
            test_chapters = {
                question.chapter_no: question.chapter_name
                for question in testwise_questions
            }
            testwise_responses = QuestionResponse.objects.prefetch_related('question', 'remark').filter(test=test, student=student)

            chapter_wise_test_remarks = defaultdict(lambda: [0] * len(test_chapters))
            


            for response in testwise_responses:
                ch_no = response.question.chapter_no
                remark = response.remark
                if not remark:
                    continue
                chapter_index = list(test_chapters.keys()).index(ch_no)
                chapter_wise_test_remarks[remark][chapter_index] += 1 * (response.question.max_marks - response.marks_obtained)

            chapter_wise_test_remarks = dict(chapter_wise_test_remarks)

            max_marks = 0
            total_marks = []
            marks_deducted = []
            marks_obtained = []
            remarks = defaultdict(float)

            for ch_no in test_chapters:
                total_test_marks = 0
                total_marks_obtained = 0
                for response in testwise_responses.filter(question__chapter_no=ch_no):

                    total_test_marks += response.question.max_marks
                    total_marks_obtained += response.marks_obtained
                    if response.remark:
                        remarks[response.remark] += 1 * (response.question.max_marks - response.marks_obtained)
            
                if total_test_marks > max_marks:
                    max_marks = total_test_marks
                total_marks.append(total_test_marks)
                marks_deducted.append(total_test_marks-total_marks_obtained)
                marks_obtained.append(total_marks_obtained)

            remarks_sum = sum(remarks.values())
            if remarks_sum:
                remarks = {key: round((value/remarks_sum)*100, 1) for key, value in remarks.items()}

            test_reports.append({
                'test' : test,
                'chapters': test_chapters,
                'marks_total' : total_marks,
                'marks_deducated' : marks_deducted,
                'marks_obtained' : marks_obtained,
                'remarks': dict(sorted(remarks.items(), key=lambda d: d[1], reverse=True)),
                'max_marks': max_marks,
                'marks': {
                    'percentage': (sum(marks_obtained)/(sum(total_marks) or 1)) * 100,
                    'obtained_marks': sum(marks_obtained),
                    'max_marks': sum(total_marks),
                    },
                'chapter_wise_test_remarks': chapter_wise_test_remarks,
            })


        remarks_count = dict(sorted(remarks_count.items(), key=lambda d: d[1], reverse=True))
        marks_progress = {result.test : result.percentage for result in TestResult.objects.filter(student=student, test__batch=batch)}


        return render(request, "center/chapterwise_student_report.html", {
            'batches': batches,
            'batch': batch,
            # 'chapter_wise_remarks': chapter_wise_remarks,
            'chapters': chapters,

            'remarks_count': remarks_count,
            'tests': test_reports,

            'all_tests': sorted(tests, key=lambda test: test.name),
            'marks_progress': marks_progress,
        })

    return render(request, "center/chapterwise_student_report.html", {
        'batches': batches,
        'batch': batch,
        'students': students,
        'student': student,
        'students_list':students_list
    })