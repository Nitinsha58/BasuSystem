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

    combined_attendance = get_combined_attendance(student, start_date, end_date)
    batchwise_attendance = get_batchwise_attendance(student,start_date, end_date)
    combined_homework = get_combined_homework(student, start_date, end_date)
    batchwise_homework = get_batchwise_homework(student, start_date, end_date)
    calendar_data = get_monthly_calendar(student)

    return render(request, 'reports/student_report.html', {
        'student': student,
        'combined_attendance': combined_attendance,
        'batchwise_attendance': batchwise_attendance,
        'combined_homework': combined_homework,
        'batchwise_homework': batchwise_homework,
        'current_month': calendar_data['calendar'],
        'current_month_name': calendar_data['month_name'],
        'current_month_present_count': calendar_data['present_count'],
        'current_month_total_count': calendar_data['present_count'] + calendar_data['absent_count'],
        'current_month_percentage': calendar_data['percentage'],
        'start_date': start_date,
        'end_date': end_date,
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
    # only show students who are active to current mentor/
    class_mentorships = {}
    mentor = Mentor.objects.filter(user=request.user).first()
    print(mentor)
    if not mentor and not request.user.is_superuser:
        messages.error(request, "You are not authorized to view this page.")
        return redirect('staff_dashboard')
    
    for class_name in classes:
        if request.user.mentor_profile:
            mentorships = mentor.mentorships.filter(active=True, student__class_enrolled=class_name)\
                        .order_by('-created_at', 'student__user__first_name', 'student__user__last_name')\
                        .distinct()
        else:
            mentorships = Mentorship.objects.filter(active=True, student__class_enrolled=class_name)\

        class_mentorships[class_name] = mentorships
    return render(request, "reports/mentor_students.html", {
        'class_mentorships': class_mentorships,
    })

@login_required(login_url='login')
def chapterwise_student_report(request, batch_id=None, student_id=None):
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

        chapter_wise_remarks = defaultdict(lambda: [0] * len(chapters))
        remarks_count = defaultdict(int)

        # Populate counts
        for response in question_responses:
            ch_no = response.question.chapter_no
            remark = response.remark
            if not remark:
                continue
            chapter_index = list(chapters.keys()).index(ch_no)
            chapter_wise_remarks[remark][chapter_index] += 1 * (response.question.max_marks - response.marks_obtained)
            remarks_count[remark] += 1 * (response.question.max_marks - response.marks_obtained)

        total_remarks_sum = sum(remarks_count.values())
        if total_remarks_sum:
            remarks_count = {key: round((value/total_remarks_sum)*100, 1) for key, value in remarks_count.items()}
        
        chapter_wise_remarks = dict(chapter_wise_remarks)
        remarks_count = dict(remarks_count)


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
            'chapter_wise_remarks': chapter_wise_remarks,
            'chapters': chapters,

            'remarks_count': remarks_count,
            'tests': test_reports,

            'student': student,
            'students': students,
            'students_list': students_list,
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