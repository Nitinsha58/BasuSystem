# services/student_report_service.py

import calendar
from datetime import date
from collections import defaultdict
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
    )

def get_combined_attendance(student, start_date, end_date):
    attendance_qs = Attendance.objects.filter(student=student, date__range=(start_date, end_date))

    total_present = attendance_qs.filter(is_present=True).count()
    total_absent = attendance_qs.filter(is_present=False).count()
    total_attendance = total_present + total_absent

    return {
        'present_count': total_present,
        'absent_count': total_absent,
        'present_percentage': round((total_present / total_attendance * 100) if total_attendance > 0 else 0, 1),
        'absent_percentage': round((total_absent / total_attendance * 100) if total_attendance > 0 else 0, 1),
    }

def get_batchwise_attendance(student, start_date, end_date):
    result = {}
    for batch in student.batches.all():
        attendance_qs = Attendance.objects.filter(
            student=student,
            batch=batch,
            date__range=(start_date, end_date)
        )
        present = attendance_qs.filter(is_present=True).count()
        absent = attendance_qs.filter(is_present=False).count()
        total = present + absent
        result[batch] = {
            'present_count': present,
            'absent_count': absent,
            'present_percentage': round((present / total * 100) if total > 0 else 0, 1),
            'absent_percentage': round((absent / total * 100) if total > 0 else 0, 1),
        }
    return result

def get_combined_homework(student, start_date, end_date):
    homework_qs = Homework.objects.filter(student=student, date__range=(start_date, end_date))
    total = homework_qs.count()
    completed = homework_qs.filter(status='Completed').count()
    partial = homework_qs.filter(status='Partial Done').count()
    pending = homework_qs.filter(status='Pending').count()

    return {
        'completed_percentage': round((completed / total * 100) if total > 0 else 0, 1),
        'partial_done_percentage': round((partial / total * 100) if total > 0 else 0, 1),
        'pending_percentage': round((pending / total * 100) if total > 0 else 0, 1),
    }


def get_batchwise_homework(student, start_date, end_date):
    result = {}
    for batch in student.batches.all():
        homework_qs = Homework.objects.filter(student=student, batch=batch, date__range=(start_date, end_date))
        total = homework_qs.count()
        completed = homework_qs.filter(status='Completed').count()
        partial = homework_qs.filter(status='Partial Done').count()
        pending = homework_qs.filter(status='Pending').count()
        result[batch] = {
            'completed_percentage': round((completed / total * 100) if total > 0 else 0, 1),
            'partial_done_percentage': round((partial / total * 100) if total > 0 else 0, 1),
            'pending_percentage': round((pending / total * 100) if total > 0 else 0, 1),
        }
    return result


def get_monthly_calendar(student):
    today = date.today()
    year, month = today.year, today.month
    first_weekday, total_days = calendar.monthrange(year, month)

    calendar_data = []
    week = [None] * first_weekday
    present_c, absent_c = 0, 0

    for day in range(1, total_days + 1):
        current_date = date(year, month, day)
        attendance = Attendance.objects.filter(student=student, date=current_date).first()
        homework = Homework.objects.filter(student=student, date=current_date).first()

        attendance_status = None
        if attendance:
            attendance_status = 'Present' if attendance.is_present else 'Absent'
            present_c += 1 if attendance.is_present else 0
            absent_c += 1 if not attendance.is_present else 0

        homework_status = homework.status if homework else None

        week.append({
            'date': current_date,
            'attendance': attendance_status,
            'homework': homework_status,
        })

        if len(week) == 7:
            calendar_data.append(week)
            week = []

    if week:
        while len(week) < 7:
            week.append(None)
        calendar_data.append(week)

    return {
        'calendar': calendar_data,
        'present_count': present_c,
        'absent_count': absent_c,
        'percentage': round((present_c / (present_c + absent_c) * 100) if (present_c + absent_c) > 0 else 0, 1),
        'month_name': calendar.month_name[month],
    }

from collections import defaultdict

def get_chapters_from_questions(test):
    questions = TestQuestion.objects.filter(test=test).order_by('chapter_no')
    return {
        q.chapter_no: q.chapter_name
        for q in questions
    }

def calculate_testwise_remarks(testwise_responses, test_chapters):
    chapter_wise_remarks = defaultdict(lambda: [0] * len(test_chapters))
    for response in testwise_responses:
        remark = response.remark
        if not remark:
            continue
        ch_no = response.question.chapter_no
        index = list(test_chapters.keys()).index(ch_no)
        chapter_wise_remarks[remark][index] += (
            response.question.max_marks - response.marks_obtained
        )
    return dict(chapter_wise_remarks)

def calculate_marks(testwise_responses, test_chapters):
    max_marks = 0
    total_marks = []
    marks_deducted = []
    marks_obtained = []
    remarks = defaultdict(float)

    for ch_no in test_chapters:
        total_test_marks = 0
        total_marks_obt = 0
        responses = testwise_responses.filter(question__chapter_no=ch_no)

        for r in responses:
            total_test_marks += r.question.max_marks
            total_marks_obt += r.marks_obtained
            if r.remark:
                remarks[r.remark] += r.question.max_marks - r.marks_obtained

        total_marks.append(total_test_marks)
        marks_deducted.append(total_test_marks - total_marks_obt)
        marks_obtained.append(total_marks_obt)
        max_marks = max(max_marks, total_test_marks)

    remarks_sum = sum(remarks.values())
    if remarks_sum:
        remarks = {
            k: round((v / remarks_sum) * 100, 1)
            for k, v in remarks.items()
        }

    return {
        'total': total_marks,
        'deducted': marks_deducted,
        'obtained': marks_obtained,
        'remarks': dict(sorted(remarks.items(), key=lambda d: d[1], reverse=True)),
        'max_marks': max_marks,
        'percentage': (sum(marks_obtained) / (sum(total_marks) or 1)) * 100,
        'obtained_total': sum(marks_obtained),
        'total_max': sum(total_marks),
    }
