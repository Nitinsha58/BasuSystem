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
    ReportPeriod,
    MentorRemark,
    Chapter
    )
from django.db.models import Q
from collections import defaultdict
from datetime import date, timedelta
import calendar

from django.db.models import Sum, Value, FloatField
from django.db.models.functions import Coalesce

from django.db import models 
from datetime import datetime
from django.contrib import messages
from django.shortcuts import render, redirect


def get_combined_attendance(student, start_date, end_date):
    excluded_batches = student.batches.all().filter(
        Q(class_name__name__in=['CLASS 9', 'CLASS 10']) &
        Q(section__name='CBSE') &
        Q(subject__name__in=['MATH', 'SCIENCE'])
    )

    # Only include attendance from student's date of joining (doj) onwards
    doj = getattr(student, 'doj', None)
    effective_start_date = max(start_date, doj) if doj else start_date

    attendance_qs = Attendance.objects.filter(
        student=student,
        date__range=(effective_start_date, end_date),
        batch__in=student.batches.all()
    ).exclude(batch__in=excluded_batches)

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
    # Only include attendance from student's date of joining (doj) onwards
    doj = getattr(student, 'doj', None)
    effective_start_date = max(start_date, doj) if doj else start_date

    for batch in student.batches.all().exclude(
            Q(class_name__name__in=['CLASS 9', 'CLASS 10']) &
            Q(section__name='CBSE') &
            Q(subject__name__in=['MATH', 'SCIENCE'])
        ):
        attendance_qs = Attendance.objects.filter(
            student=student,
            batch=batch,
            date__range=(effective_start_date, end_date)
        )
        present = attendance_qs.filter(is_present=True).count()
        absent = attendance_qs.filter(is_present=False).count()
        total = present + absent
        result[batch] = {
            'present_count': present,
            'absent_count': absent,
            'present_percentage': round((present / total * 100) if total > 0 else 0, 1),
            'absent_percentage': round((absent / total * 100) if total > 0 else 0, 1),
            'batch_calendar': get_batch_calendar(student, batch, start_date, end_date)
        }
    return result

def get_combined_homework(student, start_date, end_date):
    doj = getattr(student, 'doj', None)
    effective_start_date = max(start_date, doj) if doj else start_date

    # Exclude batches as in get_batchwise_homework
    excluded_batches = student.batches.all().filter(
        Q(class_name__name__in=['CLASS 9', 'CLASS 10']) &
        Q(section__name='CBSE') &
        Q(subject__name__in=['MATH', 'SCIENCE'])
    )
    homework_qs = Homework.objects.filter(
        student=student,
        date__range=(effective_start_date, end_date),
        batch__in=student.batches.all()
    ).exclude(batch__in=excluded_batches)

    total = homework_qs.count()
    completed = homework_qs.filter(status='Completed').count()
    partial = homework_qs.filter(status='Partial Done').count()
    pending = homework_qs.filter(status='Pending').count()

    return {
        'completed_percentage': round((completed / total * 100) if total > 0 else 0, 1),
        'partial_done_percentage': round((partial / total * 100) if total > 0 else 0, 1),
        'pending_percentage': round((pending / total * 100) if total > 0 else 0, 1),
        'completed_count': completed,
        'partial_done_count': partial,
        'pending_count': pending,
        'total_count': total,
    }


def get_batchwise_homework(student, start_date, end_date):
    doj = getattr(student, 'doj', None)
    effective_start_date = max(start_date, doj) if doj else start_date
    result = {}
    for batch in student.batches.all().exclude(
            Q(class_name__name__in=['CLASS 9', 'CLASS 10']) &
            Q(section__name='CBSE') &
            Q(subject__name__in=['MATH', 'SCIENCE'])
        ):
        homework_qs = Homework.objects.filter(student=student, batch=batch, date__range=(effective_start_date, end_date))
        total = homework_qs.count()
        completed = homework_qs.filter(status='Completed').count()
        partial = homework_qs.filter(status='Partial Done').count()
        pending = homework_qs.filter(status='Pending').count()
        result[batch] = {
            'completed_percentage': round((completed / total * 100) if total > 0 else 0, 1),
            'partial_done_percentage': round((partial / total * 100) if total > 0 else 0, 1),
            'pending_percentage': round((pending / total * 100) if total > 0 else 0, 1),
            'completed_count': completed,
            'partial_done_count': partial,
            'pending_count': pending,
            'total_count': total,
            'batch_calendar': get_batch_homework_calendar(student, batch, start_date, end_date)
        }
    return result


def get_batch_calendar(student, batch, start_date, end_date):
    monthly_data = []

    # Use student's DOJ if available
    start_date = max(start_date, student.doj) if getattr(student, 'doj', None) else start_date

    current = date(start_date.year, start_date.month, 1)
    last_date = date(end_date.year, end_date.month, calendar.monthrange(end_date.year, end_date.month)[1])

    while current <= last_date:
        year, month = current.year, current.month
        first_weekday, total_days = calendar.monthrange(year, month)
        first_weekday = (first_weekday + 1) % 7

        calendar_data = []
        week = [None] * first_weekday
        present_c, absent_c = 0, 0

        for day in range(1, total_days + 1):
            current_date = date(year, month, day)

            attendance_status = None
            if start_date <= current_date <= end_date:
                # Only consider attendance for this batch
                attendance = Attendance.objects.filter(student=student, batch=batch, date=current_date).first()
                if attendance:
                    attendance_status = 'Present' if attendance.is_present else 'Absent'
                    if attendance.is_present:
                        present_c += 1
                    else:
                        absent_c += 1
            week.append({
                'date': current_date,
                'attendance': attendance_status,
            })

            if len(week) == 7:
                calendar_data.append(week)
                week = []

        if week:
            while len(week) < 7:
                week.append(None)
            calendar_data.append(week)

        if len(calendar_data) == 5:
            calendar_data.append([None] * 7)

        monthly_data.append({
            'calendar': calendar_data,
            'present_count': present_c,
            'absent_count': absent_c,
            'percentage': round((present_c / (present_c + absent_c) * 100) if (present_c + absent_c) > 0 else 0, 1),
            'month_name': calendar.month_name[month],
            'year': year,
        })

        # Move to next month
        if month == 12:
            current = date(year + 1, 1, 1)
        else:
            current = date(year, month + 1, 1)

    return monthly_data

def get_batch_homework_calendar(student, batch, start_date, end_date):
    """
    Returns a monthly calendar for homework status for a student in a batch.
    Each day contains the homework status: 'Pending', 'Partial Done', 'Completed', or None.
    Also returns monthly counts and percentages for each status.
    Skips months with no homework data.
    """
    monthly_data = []

    # Use student's DOJ if available
    start_date = max(start_date, student.doj) if getattr(student, 'doj', None) else start_date

    current = date(start_date.year, start_date.month, 1)
    last_date = date(end_date.year, end_date.month, calendar.monthrange(end_date.year, end_date.month)[1])

    while current <= last_date:
        year, month = current.year, current.month
        first_weekday, total_days = calendar.monthrange(year, month)
        first_weekday = (first_weekday + 1) % 7

        calendar_data = []
        week = [None] * first_weekday
        pending_c, partial_c, completed_c = 0, 0, 0

        for day in range(1, total_days + 1):
            current_date = date(year, month, day)

            homework_status = None
            if start_date <= current_date <= end_date:
                # Only consider homework for this batch
                homework = Homework.objects.filter(student=student, batch=batch, date=current_date).first()
                if homework:
                    homework_status = homework.status
                    if homework_status == 'Pending':
                        pending_c += 1
                    elif homework_status == 'Partial Done':
                        partial_c += 1
                    elif homework_status == 'Completed':
                        completed_c += 1
            week.append({
                'date': current_date,
                'homework': homework_status,
            })

            if len(week) == 7:
                calendar_data.append(week)
                week = []

        if week:
            while len(week) < 7:
                week.append(None)
            calendar_data.append(week)

        if len(calendar_data) == 5:
            calendar_data.append([None] * 7)

        total = pending_c + partial_c + completed_c

        # Only append month if there is any homework data
        if total > 0:
            monthly_data.append({
                'calendar': calendar_data,
                'pending_count': pending_c,
                'partial_done_count': partial_c,
                'completed_count': completed_c,
                'pending_percentage': round((pending_c / total * 100) if total > 0 else 0, 1),
                'partial_done_percentage': round((partial_c / total * 100) if total > 0 else 0, 1),
                'completed_percentage': round((completed_c / total * 100) if total > 0 else 0, 1),
                'month_name': calendar.month_name[month],
                'year': year,
            })

        # Move to next month
        if month == 12:
            current = date(year + 1, 1, 1)
        else:
            current = date(year, month + 1, 1)

    return monthly_data


def get_batch_test_calendar(student, batch, start_date, end_date):
    """
    Returns a monthly calendar for test attendance (Present/Absent) for a student in a batch.
    Each day contains the test attendance status: 'Present', 'Absent', or None.
    Also returns monthly counts and percentages for each status.
    Skips months with no test data.
    """
    monthly_data = []

    # Use student's DOJ if available
    start_date = max(start_date, student.doj) if getattr(student, 'doj', None) else start_date

    current = date(start_date.year, start_date.month, 1)
    last_date = date(end_date.year, end_date.month, calendar.monthrange(end_date.year, end_date.month)[1])

    while current <= last_date:
        year, month = current.year, current.month
        first_weekday, total_days = calendar.monthrange(year, month)
        first_weekday = (first_weekday + 1) % 7

        calendar_data = []
        week = [None] * first_weekday
        present_c, absent_c = 0, 0

        for day in range(1, total_days + 1):
            current_date = date(year, month, day)

            test_status = None
            if start_date <= current_date <= end_date:
                # Only consider tests for this batch and date
                test = Test.objects.filter(batch=batch, date=current_date).first()
                if test:
                    from .utility import is_absent  # avoid circular import if needed
                    if is_absent(test, student):
                        test_status = 'Absent'
                        absent_c += 1
                    else:
                        test_status = 'Present'
                        present_c += 1
            week.append({
                'date': current_date,
                'attendance': test_status,
            })

            if len(week) == 7:
                calendar_data.append(week)
                week = []

        if week:
            while len(week) < 7:
                week.append(None)
            calendar_data.append(week)

        if len(calendar_data) == 5:
            calendar_data.append([None] * 7)

        total = present_c + absent_c

        # Only append month if there is any test data
        if total > 0:
            monthly_data.append({
                'calendar': calendar_data,
                'present_count': present_c,
                'absent_count': absent_c,
                'present_percentage': round((present_c / total * 100) if total > 0 else 0, 1),
                'absent_percentage': round((absent_c / total * 100) if total > 0 else 0, 1),
                'month_name': calendar.month_name[month],
                'year': year,
            })

        # Move to next month
        if month == 12:
            current = date(year + 1, 1, 1)
        else:
            current = date(year, month + 1, 1)

    return monthly_data


def get_monthly_calendar(student, start_date, end_date):
    monthly_data = []

    start_date = max(start_date, student.doj) if student.doj else start_date

    current = date(start_date.year, start_date.month, 1)
    last_date = date(end_date.year, end_date.month, calendar.monthrange(end_date.year, end_date.month)[1])

    while current <= last_date:
        year, month = current.year, current.month
        first_weekday, total_days = calendar.monthrange(year, month)
        first_weekday = (first_weekday + 1) % 7

        calendar_data = []
        week = [None] * first_weekday
        present_c, absent_c = 0, 0

        for day in range(1, total_days + 1):
            current_date = date(year, month, day)

            attendance_status = None
            if start_date <= current_date <= end_date:
                attendance = Attendance.objects.filter(student=student, date=current_date).first()
                if attendance:
                    attendance_status = 'Present' if attendance.is_present else 'Absent'
                    if attendance.is_present:
                        present_c += 1
                    else:
                        absent_c += 1
            # Fill the calendar day regardless of attendance
            week.append({
                'date': current_date,
                'attendance': attendance_status,
            })

            if len(week) == 7:
                calendar_data.append(week)
                week = []

        if week:
            while len(week) < 7:
                week.append(None)
            calendar_data.append(week)

        if len(calendar_data) == 5:
            calendar_data.append([None] * 7)

        monthly_data.append({
            'calendar': calendar_data,
            'present_count': present_c,
            'absent_count': absent_c,
            'percentage': round((present_c / (present_c + absent_c) * 100) if (present_c + absent_c) > 0 else 0, 1),
            'month_name': calendar.month_name[month],
            'year': year,
        })

        # Move to next month
        if month == 12:
            current = date(year + 1, 1, 1)
        else:
            current = date(year, month + 1, 1)

    return monthly_data

def is_absent(test, student):
    """
    Check if a student is absent for a given test.
    """
    # Check if test has any responses or results from other students
    test_has_responses = QuestionResponse.objects.filter(test=test).exclude(student=student).exists()
    test_has_results = TestResult.objects.filter(test=test).exclude(student=student).exists()

    test_has_activity = test_has_responses or test_has_results

    # Check if the student has participated
    student_has_response = QuestionResponse.objects.filter(test=test, student=student).exists()
    student_has_result = TestResult.objects.filter(test=test, student=student).exists()

    if test_has_activity and not (student_has_response or student_has_result):
        return True  # Student is absent
    return False  # Student is present or test has no activity at all

def get_marks_percentage(student, start_date, end_date):
    """
    Calculates the marks percentage and test attendance for a given student
    within the specified date range, excluding specific batches.
    """
    excluded_batches = student.batches.all().filter(
        Q(class_name__name__in=['CLASS 9', 'CLASS 10']) &
        Q(section__name='CBSE') &
        Q(subject__name__in=['MATH', 'SCIENCE'])
    )

    tests = Test.objects.filter(
        date__range=(start_date, end_date)
        ,batch__in=student.batches.all()
    ).exclude(batch__in=excluded_batches)

    total_max_marks = 0
    total_obtained_marks = 0
    present_count = 0
    absent_count = 0


    for test in tests:
        if is_absent(test, student):
            absent_count += 1
            continue

        present_count += 1

        test_result = TestResult.objects.filter(test=test, student=student).first()
        if test_result:
            total_max_marks += test.total_max_marks
            total_obtained_marks += test_result.total_marks_obtained

    if total_max_marks > 0:
        percentage_scored = round((total_obtained_marks / total_max_marks) * 100, 2)
        percentage_deducted = round(100 - percentage_scored, 2)
    else:
        percentage_scored = 0.0
        percentage_deducted = 0.0

    return {
        'scored': percentage_scored,
        'deducted': percentage_deducted,
        'present': present_count,
        'absent': absent_count,
        'present_percentage': round((present_count / (present_count + absent_count) * 100) if (present_count + absent_count) > 0 else 0, 2),
        'absent_percentage': round((absent_count / (present_count + absent_count) * 100) if (present_count + absent_count) > 0 else 0, 2),
    }

def get_batchwise_marks(student, start_date, end_date):
    """
    Calculates the marks percentage and test attendance (present/absent count) 
    for a given student in each batch within the specified date range.
    """
    result = {}

    for batch in student.batches.all().exclude(
        Q(class_name__name__in=['CLASS 9', 'CLASS 10']) &
        Q(section__name='CBSE') &
        Q(subject__name__in=['MATH', 'SCIENCE'])
    ):
        tests = Test.objects.filter(
            batch=batch,
            date__range=(start_date, end_date)
        )

        total_max_marks = 0
        total_obtained_marks = 0
        present_count = 0
        absent_count = 0

        for test in tests:
            responses = QuestionResponse.objects.filter(test=test, student=student)
            test_result = TestResult.objects.filter(test=test, student=student).first()

            if is_absent(test, student):
                absent_count += 1
                continue

            present_count += 1
            if test_result:
                total_max_marks += test.total_max_marks
                total_obtained_marks += test_result.total_marks_obtained

        if total_max_marks > 0:
            scored = round((total_obtained_marks / total_max_marks) * 100, 2)
            deducted = round(100 - scored, 2)
        else:
            scored = 0.0
            deducted = 0.0

        result[batch] = {
            'scored': round(scored, 2),
            'deducted': round(deducted, 2),
            'present': present_count or 0,
            'absent': absent_count or 0,
            'present_percentage': round((present_count / (present_count + absent_count) * 100) if (present_count + absent_count) > 0 else 0, 2),
            'absent_percentage': round((absent_count / (present_count + absent_count) * 100) if (present_count + absent_count) > 0 else 0, 2),
            'batch_calendar': get_batch_test_calendar(student, batch, start_date, end_date),
            'batch_summary': calculate_batchwise_chapter_remarks(student, batch, start_date, end_date),
        }

    return result


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

def calculate_batchwise_chapter_remarks(student, batch, start_date, end_date):
    """
    Calculates chapterwise remarks for all tests of a student in a batch within a date range.
    Returns a dict: {remark: [deducted_marks_per_chapter]}
    """
    chapters = {
        ch.chapter_no: ch.chapter_name
        for ch in Chapter.objects.filter(
            class_name=batch.class_name,
            subject=batch.subject
        ).order_by('chapter_no')
    }

    questions_responses = QuestionResponse.objects.filter(
        student=student,
        test__batch=batch,
        test__date__range=(start_date, end_date)
    ).select_related('question')

    chapter_wise_remarks = defaultdict(lambda: [0] * len(chapters))
    remarks_count = defaultdict(int)

    for response in questions_responses:
        remark = response.remark
        if not remark:
            continue
        ch_no = response.question.chapter_no
        if ch_no not in chapters:
            continue  # Skip if chapter is not in the batch
        idx = list(chapters.keys()).index(ch_no)
        chapter_wise_remarks[remark][idx] += ( response.question.max_marks - response.marks_obtained )
        remarks_count[remark] += 1
    
    total_remarks_sum = sum(remarks_count.values())
    if total_remarks_sum > 0:
        remarks_count = {
            k: round((v / total_remarks_sum) * 100, 1)
            for k, v in remarks_count.items()
        }
    chapter_wise_remarks = dict(sorted(chapter_wise_remarks.items(), key=lambda d: d[1], reverse=True))
    remarks_count = dict(sorted(remarks_count.items(), key=lambda d: d[1], reverse=True))

    return {
        'chapters': chapters,
        'remarks_count': remarks_count,
        'chapter_wise_remarks': chapter_wise_remarks,
    }

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



def calculate_attendance_percentage(student, batch, start_date, end_date) -> float:
    """
    Calculates the attendance percentage for a given student in a specific batch
    within the specified date range.
    """
    attendance_in_range = Attendance.objects.filter(
        student=student,
        batch=batch,
        date__range=(start_date, end_date)
    )
    total_sessions_for_student = attendance_in_range.count()
    present_sessions = attendance_in_range.filter(is_present=True).count()

    if total_sessions_for_student > 0:
        return round((present_sessions / total_sessions_for_student) * 100, 2)
    return 0.0

def calculate_homework_completion_percentage(student, batch, start_date, end_date) -> float:
    """
    Calculates the homework completion percentage for a given student in a specific batch
    within the specified date range.
    """
    homework_in_range = Homework.objects.filter(
        student=student,
        batch=batch,
        date__range=(start_date, end_date)
    )
    total_homeworks_for_student = homework_in_range.count()
    completed_homeworks = homework_in_range.filter(status='Completed').count()

    if total_homeworks_for_student > 0:
        return round((completed_homeworks / total_homeworks_for_student) * 100, 2)
    return 0.0

def calculate_test_scores_percentage(student, batch, start_date, end_date) -> float:
    """
    Calculates the test scores percentage for a given student in a specific batch
    within the specified date range.
    The percentage is (Total marks student obtained) / (Total max marks of ALL tests in batch for the period).
    """
    # Get all tests conducted by this batch within the date range
    relevant_tests_for_batch = Test.objects.filter(
        batch=batch,
        date__range=(start_date, end_date)
    )

    # Sum of max marks for ALL tests in this batch and date range
    total_max_marks_all_batch_tests_agg = relevant_tests_for_batch.aggregate(
        total=Coalesce(Sum('total_max_marks'), Value(0.0), output_field=FloatField())
    )
    total_max_marks_for_all_batch_tests = total_max_marks_all_batch_tests_agg['total']

    # Sum of marks obtained by THIS student in these relevant tests
    student_obtained_marks_agg = TestResult.objects.filter(
        student=student,
        test__in=relevant_tests_for_batch
    ).aggregate(
        total=Coalesce(Sum('total_marks_obtained'), Value(0.0), output_field=FloatField())
    )
    student_total_obtained_marks = student_obtained_marks_agg['total']

    if total_max_marks_for_all_batch_tests > 0:
        return round((student_total_obtained_marks / total_max_marks_for_all_batch_tests) * 100, 2)
    return 0.0


def has_report(student, start_date, end_date):
    """ check if student has any mentor report object in the given date range """
    return MentorRemark.objects.filter(
        student=student,
        start_date = start_date,
        end_date = end_date,
    ).exists()


def generate_group_report_data_v2(request, start_date: datetime.date, end_date: datetime.date,):
    """
    Generates a group report for students detailing their performance in various batches
    between a start date and an end date, using helper functions for calculations.

    Args:
        start_date_str: The start date for the report period in 'YYYY-MM-DD' format.
        end_date_str: The end date for the report period in 'YYYY-MM-DD' format.

    Returns:
        A list of dictionaries, where each dictionary represents a student and
        contains their performance data per batch.
        Returns a dictionary with an "error" key if date parsing fails.
    """
    report_data = []

    # Determine mentor from request if available
    mentor = getattr(request.user, 'mentor_profile', None)


    if request.user.is_superuser:
        students = Student.objects.filter(
            active=True,
            mentorships__active=True
        ).select_related('user').prefetch_related(
            models.Prefetch(
                'batches',
                queryset=Batch.objects.order_by('class_name__name', 'subject__name', 'section__name')
            )
        ).order_by('user__last_name', 'user__first_name').distinct()
    elif mentor:
        students = Student.objects.filter(
            active=True,
            mentorships__active=True,
            mentorships__mentor=mentor
        ).select_related('user').prefetch_related(
            models.Prefetch(
                'batches',
                queryset=Batch.objects.order_by('class_name__name', 'subject__name', 'section__name')
            )
        ).order_by('user__last_name', 'user__first_name').distinct()
    else:
        messages.error(request, "You are not authorized to view this page.")
        return redirect('staff_dashboard')

    for student in students:
        student_info = {
            'student_name': f"{student.user.first_name} {student.user.last_name}".strip() or student.user.phone,
            'student_id': str(student.stu_id),
            'student': student,
            'has_report': has_report(student, start_date, end_date),
            'batches_data': []
        }

        for batch in student.batches.all().exclude(
            Q(class_name__name__in=['CLASS 9', 'CLASS 10']) &
            Q(section__name='CBSE') &
            Q(subject__name__in=['MATH', 'SCIENCE'])
        ):
            batch_name = str(batch)
            
            # Call helper functions
            attendance_perc = calculate_attendance_percentage(student, batch, start_date, end_date)
            homework_perc = calculate_homework_completion_percentage(student, batch, start_date, end_date)
            test_scores_perc = calculate_test_scores_percentage(student, batch, start_date, end_date)

            batch_data = {
                'batch_name': batch_name,
                'batch_id': batch.id,
                'attendance': attendance_perc,
                'homework': homework_perc,
                'test_marks': test_scores_perc
            }
            
            student_info['batches_data'].append(batch_data)

        # if student_info['batches_data']:
        report_data.append(student_info)

    return report_data

def generate_single_student_report_data(student, start_date: date, end_date: date):
    """
    Generates a report for a single student detailing their performance in various batches
    between a start date and an end date, using helper functions for calculations.

    Args:
        student: The Student instance for whom the report is to be generated.
        start_date: The start date for the report period (datetime.date).
        end_date: The end date for the report period (datetime.date).

    Returns:
        A dictionary representing the student and their performance data per batch.
    """
    student_info = {
        'student_name': f"{student.user.first_name} {student.user.last_name}".strip() or student.user.phone,
        'student_id': str(student.stu_id),
        'student': student,
        'batches_data': []
    }

    for batch in student.batches.all().exclude(
        Q(class_name__name__in=['CLASS 9', 'CLASS 10']) &
        Q(section__name='CBSE') &
        Q(subject__name__in=['MATH', 'SCIENCE'])
    ):
        batch_name = str(batch)
        attendance_perc = calculate_attendance_percentage(student, batch, start_date, end_date)
        homework_perc = calculate_homework_completion_percentage(student, batch, start_date, end_date)
        test_scores_perc = calculate_test_scores_percentage(student, batch, start_date, end_date)

        batch_data = {
            'batch_name': batch_name,
            'batch_id': batch.id,
            'attendance': attendance_perc,
            'homework': homework_perc,
            'test_marks': test_scores_perc,
            'has_report': has_report(student, start_date, end_date)
        }
        student_info['batches_data'].append(batch_data)

    return student_info


def get_student_test_report(student, start_date, end_date):
    """
    Generates a detailed test report for a student with test scores.

    Args:
        student: The Student instance.
        start_date: Start of date range (datetime.date).
        end_date: End of date range (datetime.date).

    Returns:
        A dictionary with batch as key and a list of dicts
    """
    test_result = {}
    student_batches = student.batches.all().exclude(
        Q(class_name__name__in=['CLASS 9', 'CLASS 10']) &
        Q(section__name='CBSE') &
        Q(subject__name__in=['MATH', 'SCIENCE'])
    )

    for batch in student_batches:
        tests = Test.objects.filter(
            batch=batch,
            date__range=(start_date, end_date)
        ).order_by('date')

        doj = getattr(student, 'doj', None)
        if doj:
            tests = tests.filter(date__gte=doj)

        tests = tests.order_by('date')

        test_result[batch] = []
        for test in tests:
            result = TestResult.objects.filter(test=test, student=student).first()
            if not is_absent(test, student):
                marks_or_AB = result
            else:
                marks_or_AB = 'AB'
            test_result[batch].append({
                'test': test,
                'result': marks_or_AB
            })
            
    return test_result

def get_student_retest_report(student):
    """
    Generate retest suggestions for a student based on their test results.

    Args:
        student: The Student instance.

    Returns:
        A dictionary with batch as key and a list of dicts containing test, result, retest, and retest_marks.

        it should include test result for which student has mandatory retest, or has given optional retest by checking 
        if student has also given retest by checking test_type = 'retest' in TestResult model.
    """

    test_result = {}
    student_batches = student.batches.all().exclude(
        Q(class_name__name__in=['CLASS 9', 'CLASS 10']) &
        Q(section__name='CBSE') &
        Q(subject__name__in=['MATH', 'SCIENCE'])
    )
    for batch in student_batches:
        tests = Test.objects.filter(
            batch=batch
        )

        doj = getattr(student, 'doj', None)
        if doj:
            tests = tests.filter(date__gte=doj)

        tests = tests.order_by('date')

        test_result[batch] = []
        for test in tests:
            result = TestResult.objects.filter(test=test, student=student).first()
            is_student_absent = is_absent(test, student)
            
            retest_suggested = None # is true when student is absent from the test or has scored less than 50% marks
            retest_given = None # is true when student result has test_type = 'retest'

            if is_student_absent or (result and result.percentage < 50):
                retest_suggested = True
                # Check if student has given retest
                retest_result = TestResult.objects.filter(
                    test=test,
                    student=student,
                    test_type='retest'
                ).first()

                if retest_result:
                    retest_given = True
                    retest_marks = retest_result.total_marks_obtained
                else:
                    retest_given = False
                    retest_marks = None
            else:
                retest_suggested = False
                retest_given = False
                retest_marks = None

            if retest_suggested:
                test_result[batch].append({
                    'test': test,
                    'result': result if not is_student_absent else None,
                    'retest_suggested': retest_suggested,
                    'retest_given': retest_given,
                    'retest_marks': retest_marks
                })


    if not test_result:
        return {}

    # Sort each batch's test results by date
    for batch, results in test_result.items():
        results.sort(key=lambda x: x['test'].date)

    # Return the final test result dictionary
    return test_result

def compare_student_performance_by_week(batch, start_date, end_date):
    """
    For a given batch and week_number (1=current, 2=previous), returns:
    - tests in that week
    - for each student: their percentage in each test, and their average percentage for the week
    - also returns the average percentage for each test across all students
    - for each student: their attendance percentage for the week in this batch
    - for each student: their homework completion percentage (only 'Completed' status) for the week in this batch
    Considers student's join date (doj): if test is before join date, test value is blank.
    """
    tests = Test.objects.filter(batch=batch, date__range=(start_date, end_date)).order_by('date')
    students = Student.objects.filter(batches=batch, active=True)
    students_list = []

    # Pre-fetch all results for efficiency
    test_results = TestResult.objects.filter(test__in=tests, student__in=students)
    results_lookup = {(tr.student_id, tr.test_id): tr for tr in test_results}

    # Pre-fetch attendance for all students in this batch and week
    attendance_qs = Attendance.objects.filter(
        batch=batch,
        student__in=students,
        date__range=(start_date, end_date)
    )
    attendance_lookup = {}
    for att in attendance_qs:
        attendance_lookup.setdefault(att.student_id, []).append(att.is_present)

    # Pre-fetch homework for all students in this batch and week (only 'Completed')
    homework_qs = Homework.objects.filter(
        batch=batch,
        student__in=students,
        date__range=(start_date, end_date)
    )
    homework_lookup = {}
    for hw in homework_qs:
        homework_lookup.setdefault(hw.student_id, []).append(hw.status)

    for stu in students:
        stu_obj = {}
        total_marks_obtained = 0
        total_max_marks = 0
        doj = getattr(stu, 'doj', None)

        for test in tests:
            # If test is before student's join date, leave blank
            if doj and test.date < doj:
                stu_obj[test] = ''
                continue

            result = results_lookup.get((stu.id, test.id))
            if not result or result.percentage == 0:
                stu_obj[test] = -1
                continue

            total_marks_obtained += result.total_marks_obtained
            total_max_marks += result.total_max_marks
            stu_obj[test] = round(result.percentage, 1)

        # Attendance percentage for this week in this batch
        att_list = attendance_lookup.get(stu.id, [])
        total_att = len(att_list)
        present_att = sum(1 for x in att_list if x)
        attendance_perc = round((present_att / total_att) * 100, 1) if total_att > 0 else 0.0

        # Homework completion percentage (only 'Completed')
        hw_list = homework_lookup.get(stu.id, [])
        total_hw = len(hw_list)
        completed_hw = sum(1 for x in hw_list if x == 'Completed')
        homework_perc = round((completed_hw / total_hw) * 100, 1) if total_hw > 0 else 0.0

        stu_obj['student'] = {
            'stu': stu,
            'percentage': round((total_marks_obtained / (total_max_marks or 1)) * 100, 1),
            'attendance_percentage': attendance_perc,
            'attendance_present': present_att,
            'attendance_total': total_att,
            'homework_percentage': homework_perc,
            'homework_completed': completed_hw,
            'homework_total': total_hw,
        }
        students_list.append(stu_obj)

    students_list = sorted(students_list, key=lambda item: item['student']['percentage'], reverse=True)

    # Calculate average percentage for each test across all students
    test_averages = {}
    for test in tests:
        percentages = [
            stu_obj[test]
            for stu_obj in students_list
            if stu_obj.get(test, -1) not in ('', -1)
        ]
        if percentages:
            test_averages[test] = round(sum(percentages) / len(percentages), 1)
        else:
            test_averages[test] = None

    return {
        'tests': tests,
        'students_list': students_list,
        'test_averages': test_averages,
        'start_date': start_date,
        'end_date': end_date,
    }