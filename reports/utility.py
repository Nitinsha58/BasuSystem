# services/student_report_service.py

import calendar
from datetime import date
from collections import defaultdict
from registration.models import (
    ClassName, 
    Student, 
    StudentEnrollment,
    Batch, 
    Attendance, 
    Homework,
    TestQuestion,
    QuestionResponse,
    Test,
    TestResult,
    ReportPeriod,
    Recommendation,
    MentorRemark,
    Chapter,
    StudentTestRemark,
    StudentBatchLink,
    Subject,
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
from itertools import groupby


def _get_student_batches_qs(student):
    """Return a queryset of batches for the student's *current* enrollment.

    Preference order:
    1) StudentEnrollment (active session) via EnrollmentBatch (authoritative)
    2) StudentBatchLink (compat layer, driven from EnrollmentBatch)
    3) student.batches (legacy fallback while migration is in progress)
    """
    enrollment = StudentEnrollment.get_current_for_student(student)
    if enrollment:
        return Batch.objects.filter(enrollment_links__enrollment=enrollment).distinct()

    # compat layer: prefer links tied to the active enrollment/session
    active_links_qs = StudentBatchLink.objects.filter(
        student=student,
        active=True,
        enrollment__session__is_active=True,
        enrollment__active=True,
    )
    if active_links_qs.exists():
        return Batch.objects.filter(student_links__in=active_links_qs).distinct()

    # fallback: legacy links that don't have enrollment attached
    legacy_links_qs = StudentBatchLink.objects.filter(student=student, active=True, enrollment__isnull=True)
    if legacy_links_qs.exists():
        return Batch.objects.filter(student_links__in=legacy_links_qs).distinct()

    return student.current_batches()


def _get_student_subjects_qs(student):
    student_batches = _get_student_batches_qs(student)
    return Subject.objects.filter(batches__in=student_batches).distinct()


def get_student_batches_qs(student):
    """Public wrapper for enrollment-based batch lookup."""
    return _get_student_batches_qs(student)


def get_student_subjects_qs(student):
    """Public wrapper for enrollment-based subject lookup."""
    return _get_student_subjects_qs(student)


def get_combined_attendance(student, start_date, end_date):
    student_batches = _get_student_batches_qs(student)
    excluded_batches = student_batches.filter(
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
        batch__in=student_batches
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

def get_subjectwise_attendance(student, start_date, end_date):
    result = {}

    doj = getattr(student, 'doj', None)
    effective_start_date = max(start_date, doj) if doj else start_date

    subjects = _get_student_subjects_qs(student)

    for subject in subjects:
        attendance_qs = Attendance.objects.filter(
            student=student,
            batch__subject=subject,
            date__range=(effective_start_date, end_date)
        )

        present = attendance_qs.filter(is_present=True).count()
        absent = attendance_qs.filter(is_present=False).count()
        total = present + absent

        result[subject] = {
            'present_count': present,
            'absent_count': absent,
            'present_percentage': round((present / total * 100) if total else 0, 1),
            'absent_percentage': round((absent / total * 100) if total else 0, 1),
            'subject_calendar': get_subjectwise_attendance_calendar(
                student, subject, start_date, end_date
            )
        }

    return result


def get_batchwise_attendance(student, start_date, end_date):
    result = {}
    # Only include attendance from student's date of joining (doj) onwards
    doj = getattr(student, 'doj', None)
    effective_start_date = max(start_date, doj) if doj else start_date

    for batch in _get_student_batches_qs(student).exclude(
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

def get_subjectwise_attendance_calendar(student, subject, start_date, end_date):
    monthly_data = []

    # Use student's DOJ if available
    start_date = max(start_date, student.doj) if getattr(student, 'doj', None) else start_date

    attendance_qs = Attendance.objects.filter(
        student=student,
        batch__subject=subject,
        date__range=(start_date, end_date)
    )

    present = attendance_qs.filter(is_present=True).count()
    absent = attendance_qs.filter(is_present=False).count()
    total = present + absent
    

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
                # Only consider attendance for this subject
                attendance = Attendance.objects.filter(
                    student=student,
                    batch__subject=subject,
                    date=current_date
                ).first()
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
    
    return {
        'subject_calendar': monthly_data,
        'present_count': present,
        'absent_count': absent,
        'present_percentage': round((present / total * 100) if total > 0 else 0, 1),
        'absent_percentage': round((absent / total * 100) if total > 0 else 0, 1),
        'subject': subject,
    }

def get_subjectwise_homework_calendar(student, subject, start_date, end_date):
    monthly_data = []

    # Use student's DOJ if available
    start_date = max(start_date, student.doj) if getattr(student, 'doj', None) else start_date

    current = date(start_date.year, start_date.month, 1)
    last_date = date(end_date.year, end_date.month, calendar.monthrange(end_date.year, end_date.month)[1])

    homework_qs = Homework.objects.filter(
        student=student,
        batch__subject=subject,
        date__range=(start_date, end_date)
    )
    total_homework = homework_qs.count()
    completed_homework = homework_qs.filter(status='Completed').count()
    pending_homework = homework_qs.filter(status='Pending').count()
    partial_homework = homework_qs.filter(status='Partial Done').count()

    

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
                # Only consider homework for this subject
                homework = Homework.objects.filter(
                    student=student,
                    batch__subject=subject,
                    date=current_date
                ).first()
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

        monthly_data.append({
            'calendar': calendar_data,
            'pending_count': pending_c,
            'partial_done_count': partial_c,
            'completed_count': completed_c,
            'pending_percentage': round((pending_c / (pending_c + partial_c + completed_c) * 100) if (pending_c + partial_c + completed_c) > 0 else 0, 1),
            'partial_done_percentage': round((partial_c / (pending_c + partial_c + completed_c) * 100) if (pending_c + partial_c + completed_c) > 0 else 0, 1),
            'completed_percentage': round((completed_c / (pending_c + partial_c + completed_c) * 100) if (pending_c + partial_c + completed_c) > 0 else 0, 1),
            'month_name': calendar.month_name[month],
            'year': year,
        })
        # Move to next month
        if month == 12:
            current = date(year + 1, 1, 1)
        else:
            current = date(year, month + 1, 1)
    return {
        'subject': subject,
        'subject_calendar': monthly_data,
        'completed_count': completed_homework,
        'partial_done_count': partial_homework,
        'pending_count': pending_homework,
        'completed_percentage': round((completed_homework / total_homework * 100) if total_homework > 0 else 0, 1),
        'partial_done_percentage': round((partial_homework / total_homework * 100) if total_homework > 0 else 0, 1),
        'pending_percentage': round((pending_homework / total_homework * 100) if total_homework > 0 else 0, 1),
    }


def get_combined_homework(student, start_date, end_date):
    doj = getattr(student, 'doj', None)
    effective_start_date = max(start_date, doj) if doj else start_date

    student_batches = _get_student_batches_qs(student)

    # Exclude batches as in get_batchwise_homework
    excluded_batches = student_batches.filter(
        Q(class_name__name__in=['CLASS 9', 'CLASS 10']) &
        Q(section__name='CBSE') &
        Q(subject__name__in=['MATH', 'SCIENCE'])
    )
    homework_qs = Homework.objects.filter(
        student=student,
        date__range=(effective_start_date, end_date),
        batch__in=student_batches
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

def get_subjectwise_homework(student, start_date, end_date):
    doj = getattr(student, 'doj', None)
    effective_start_date = max(start_date, doj) if doj else start_date

    result = {}

    subjects = _get_student_subjects_qs(student)

    for subject in subjects:
        homework_qs = Homework.objects.filter(
            student=student,
            batch__subject=subject,
            date__range=(effective_start_date, end_date)
        )

        total = homework_qs.count()
        completed = homework_qs.filter(status='Completed').count()
        partial = homework_qs.filter(status='Partial Done').count()
        pending = homework_qs.filter(status='Pending').count()

        result[subject] = {
            'completed_percentage': round((completed / total * 100) if total else 0, 1),
            'partial_done_percentage': round((partial / total * 100) if total else 0, 1),
            'pending_percentage': round((pending / total * 100) if total else 0, 1),
            'completed_count': completed,
            'partial_done_count': partial,
            'pending_count': pending,
            'total_count': total,
        }

    return result


def get_batchwise_homework(student, start_date, end_date):
    doj = getattr(student, 'doj', None)
    effective_start_date = max(start_date, doj) if doj else start_date
    result = {}
    for batch in _get_student_batches_qs(student).exclude(
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

def get_subject_test_calendar(student, subject, start_date, end_date):
    monthly_data = []

    doj = getattr(student, 'doj', None)
    effective_start_date = max(start_date, doj) if doj else start_date

    # Accept either Subject instance or subject name
    if isinstance(subject, str):
        subject_obj = Subject.objects.filter(name=subject).first()
    else:
        subject_obj = subject

    # Only consider tests from the batches the student actually belongs to for this subject
    student_batches_for_subject = _get_student_batches_qs(student).filter(subject=subject_obj)

    tests = Test.objects.filter(
        batch__in=student_batches_for_subject,
        date__range=(effective_start_date, end_date)
    ).order_by('date')

    # Build a lookup of tests by date for fast per-day checks
    tests_by_date = {}
    for t in tests:
        tests_by_date.setdefault(t.date, []).append(t)

    current = date(effective_start_date.year, effective_start_date.month, 1)
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
            if effective_start_date <= current_date <= end_date:
                date_tests = tests_by_date.get(current_date, [])
                if date_tests:
                    # Was there activity on this date (by other students) in any of the tests?
                    date_has_activity = any(
                        QuestionResponse.objects.filter(test=t).exclude(student=student).exists() or
                        TestResult.objects.filter(test=t).exclude(student=student).exists()
                        for t in date_tests
                    )

                    # Did the student participate in any test on this date?
                    student_participated = any(
                        QuestionResponse.objects.filter(test=t, student=student).exists() or
                        TestResult.objects.filter(test=t, student=student).exists()
                        for t in date_tests
                    )

                    # Decide status per-date (not per-test)
                    if date_has_activity and not student_participated:
                        test_status = 'Absent'
                        absent_c += 1
                    elif student_participated:
                        test_status = 'Present'
                        present_c += 1
                    # else: no activity and student did not participate -> leave None

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

        monthly_data.append({
            'calendar': calendar_data,
            'present_count': present_c,
            'absent_count': absent_c,
            'present_percentage': round((present_c / (present_c + absent_c) * 100) if (present_c + absent_c) > 0 else 0, 1),
            'absent_percentage': round((absent_c / (present_c + absent_c) * 100) if (present_c + absent_c) > 0 else 0, 1),
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
    student_batches = _get_student_batches_qs(student)
    excluded_batches = student_batches.filter(
        Q(class_name__name__in=['CLASS 9', 'CLASS 10']) &
        Q(section__name='CBSE') &
        Q(subject__name__in=['MATH', 'SCIENCE'])
    )

    tests = Test.objects.filter(
        date__range=(start_date, end_date)
        ,batch__in=student_batches
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

    for batch in _get_student_batches_qs(student).exclude(
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

def get_subjectwise_marks(student, start_date, end_date):
    """
    Calculates the marks percentage and test attendance (present/absent count) 
    for a given student in each subject within the specified date range.
    """
    doj = getattr(student, 'doj', None)
    effective_start_date = max(start_date, doj) if doj else start_date
    
    result = {}
    
    # Use StudentBatchLink for accuracy
    student_batch_links = StudentBatchLink.objects.filter(
        student=student
    ).select_related('batch__class_name', 'batch__subject').order_by(
        'batch__class_name__name', 'batch__subject__name', '-active'
    )

    batches_by_class_subject = {}
    for link in student_batch_links:
        batch = link.batch
        class_name = batch.class_name.name
        subject_name = batch.subject.name
        key = f"{class_name} {subject_name}"

        if key not in batches_by_class_subject:
            batches_by_class_subject[key] = {
                'class': batch.class_name,
                'subject': batch.subject,
                'section': batch.section,
                'batches': []
            }

        batches_by_class_subject[key]['batches'].append({
            'batch_name': str(batch.section.name),
            'batch_id': batch.id,
            'active': bool(link.active),
        })

    # Process tests by class and subject
    for _, class_obj in batches_by_class_subject.items():
        # Only consider tests from the student's own batches for this class+subject
        student_batch_ids = StudentBatchLink.objects.filter(
            student=student,
            batch__subject=class_obj['subject'],
            batch__class_name=class_obj['class'],
        ).values_list('batch_id', flat=True)

        if not student_batch_ids:
            test_qs = Test.objects.none()
        else:
            test_qs = Test.objects.filter(
                batch_id__in=student_batch_ids,
                date__range=(effective_start_date, end_date)
            ).order_by('date')

        percent_sum = 0.0
        test_count = 0
        present_count = 0
        absent_count = 0

        # Group tests by date (we don't need the date variable itself)
        for _, group in groupby(test_qs, key=lambda t: t.date):
            date_tests = list(group)

            # Was there activity on this date (by other students)?
            date_has_activity = any(
                QuestionResponse.objects.filter(test=t).exclude(student=student).exists() or
                TestResult.objects.filter(test=t).exclude(student=student).exists()
                for t in date_tests
            )

            # Did the student participate in any test on this date?
            student_participated = any(
                QuestionResponse.objects.filter(test=t, student=student).exists() or
                TestResult.objects.filter(test=t, student=student).exists()
                for t in date_tests
            )

            # If there was activity but student did not participate => absent (count per date)
            if date_has_activity and not student_participated:
                absent_count += 1
                continue

            # If student participated, count as present (per date) and accumulate marks (per test)
            if student_participated:
                present_count += 1
                for t in date_tests:
                    test_result = TestResult.objects.filter(test=t, student=student).first()
                    if test_result and test_result.percentage is not None:
                        percent_sum += test_result.percentage
                        test_count += 1
                        
        if test_count > 0:
            scored = round((percent_sum / test_count), 2)
            deducted = round(100 - scored, 2)
        else:
            scored = 0.0
            deducted = 0.0

        # Store result using subject object as key
        subject_obj = class_obj['subject']
        result[subject_obj] = {
            'scored': round(scored, 2),
            'deducted': round(deducted, 2),
            'present': present_count or 0,
            'absent': absent_count or 0,
            'present_percentage': round((present_count / (present_count + absent_count) * 100) if (present_count + absent_count) > 0 else 0, 2),
            'absent_percentage': round((absent_count / (present_count + absent_count) * 100) if (present_count + absent_count) > 0 else 0, 2),
        }
    
        print(result)

    return result

def get_subjectwise_test_reports(student, start_date, end_date):
    doj = getattr(student, 'doj', None)
    effective_start_date = max(start_date, doj) if doj else start_date

    # All subjects the student actually belongs to
    student_batches = _get_student_batches_qs(student)
    subjects = student_batches.values_list('subject__name', flat=True).distinct()
    result = {}

    for subject_name in subjects:
        subject_obj = Subject.objects.filter(name=subject_name).first()

        # Get all batches the student belongs to for this subject
        student_batches_for_subject = student_batches.filter(subject__name=subject_name)

        # FIX: Only tests from student's batches (NOT all batches of that subject)
        tests_qs = Test.objects.filter(
            batch__in=student_batches_for_subject,
            date__range=(effective_start_date, end_date)
        ).order_by('date')

        # Group tests by their exam date
        tests_in_subject = {}
        for test_date, group in groupby(tests_qs, key=lambda t: t.date):
            tests_in_subject[test_date] = {
                'tests': list(group)
            }

        test_reports = []
        total_max_marks = 0
        total_obtained_marks = 0
        present_count = 0
        absent_count = 0

        # Process each test date group
        for test_date, test_group in tests_in_subject.items():
            tests = test_group['tests']

            selected_test = None
            selected_result = None

            # Prefer a test on this date where the student has a TestResult
            for test in tests:
                res = TestResult.objects.filter(test=test, student=student).first()
                if res:
                    selected_test = test
                    selected_result = res
                    break

            if not selected_test:
                # Student was absent for all tests on this date
                selected_test = tests[0]
                is_absent_status = True
            else:
                is_absent_status = False

            # Fetch responses for marks
            responses = QuestionResponse.objects.filter(
                test=selected_test,
                student=student
            ).select_related('question', 'remark')

            attendance_status = 'Absent' if is_absent_status else 'Present'

            # Compute chapters & marks
            test_chapters = get_chapters_from_questions(selected_test)
            marks_data = calculate_marks(responses, test_chapters)
            chapter_remarks = calculate_testwise_remarks(responses, test_chapters, is_objective=selected_test.objective)

            # Append test report
            test_reports.append({
                'test': selected_test,
                'result': selected_result,
                'is_absent': is_absent_status,
                'attendance_status': attendance_status,
                'marks_data': marks_data,
                'chapter_remarks': chapter_remarks,
            })

            # Update counts
            if is_absent_status:
                absent_count += 1
            else:
                present_count += 1
                if selected_result:
                    total_max_marks += selected_test.total_max_marks
                    total_obtained_marks += selected_result.total_marks_obtained

        # Calculate overall percentages
        if total_max_marks > 0:
            scored = round((total_obtained_marks / total_max_marks) * 100, 2)
            deducted = 100 - scored
        else:
            scored = 0.0
            deducted = 0.0

        result[subject_obj] = {
            'subject': subject_obj,
            'test_reports': test_reports,
            'subject_summary': calculate_subject_chapter_remarks(student, subject_obj, effective_start_date, end_date),
            'test_calendar': get_subject_test_calendar(student, subject_obj, effective_start_date, end_date),
            'scored': round(scored, 2),
            'deducted': round(deducted, 2),
            'present': present_count,
            'absent': absent_count,
            'present_percentage': round(
                (present_count / (present_count + absent_count) * 100)
                if (present_count + absent_count) > 0 else 0,
                2
            ),
            'absent_percentage': round(
                (absent_count / (present_count + absent_count) * 100)
                if (present_count + absent_count) > 0 else 0,
                2
            ),
        }

    return result

def get_subject_test_reports(student, subject, start_date, end_date):
    doj = getattr(student, 'doj', None)
    effective_start_date = max(start_date, doj) if doj else start_date

    # Accept either Subject instance or subject name
    if isinstance(subject, str):
        subject_obj = Subject.objects.filter(name=subject).first()
    else:
        subject_obj = subject

    # Only consider tests from the batches the student actually belongs to for this subject
    student_batches_for_subject = _get_student_batches_qs(student).filter(subject=subject_obj)
    tests = Test.objects.filter(
        batch__in=student_batches_for_subject,
        date__range=(effective_start_date, end_date)
    ).order_by('date')

    percent_sum = 0.0
    test_count = 0
    present_count = 0
    absent_count = 0

    # Group tests by date because student may have appeared in any one batch on that date
    for test_date, group in groupby(tests, key=lambda t: t.date):
        date_tests = list(group)

        # Was there activity on this date (by other students) in any of the tests?
        date_has_activity = any(
            QuestionResponse.objects.filter(test=t).exclude(student=student).exists() or
            TestResult.objects.filter(test=t).exclude(student=student).exists()
            for t in date_tests
        )

        # Did the student participate in any test on this date?
        student_participated = any(
            QuestionResponse.objects.filter(test=t, student=student).exists() or
            TestResult.objects.filter(test=t, student=student).exists()
            for t in date_tests
        )

        # If there was activity but the student did not participate => absent for that date
        if date_has_activity and not student_participated:
            absent_count += 1
            continue

        # If student participated in any test on that date, count as present and accumulate percentage
        if student_participated:
            present_count += 1
            for t in date_tests:
                test_result = TestResult.objects.filter(test=t, student=student).first()
                if test_result and test_result.percentage is not None:
                    percent_sum += test_result.percentage
                    test_count += 1

    if test_count > 0:
        scored = round((percent_sum / test_count), 2)
        deducted = round(100 - scored, 2)
    else:
        scored = 0.0
        deducted = 0.0


    result = {
        'subject': subject_obj,
        'test_reports': calculate_subject_tests_report(student, subject_obj, effective_start_date, end_date),
        'subject_summary': calculate_subject_chapter_remarks(student, subject_obj, effective_start_date, end_date),
        'subject_calendar': get_subject_test_calendar(student, subject_obj, effective_start_date, end_date),
        'scored': round(scored, 2),
        'deducted': round(deducted, 2),
        'present': present_count or 0,
        'absent': absent_count or 0,
        'present_percentage': round((present_count / (present_count + absent_count) * 100) if (present_count + absent_count) > 0 else 0, 2),
        'absent_percentage': round((absent_count / (present_count + absent_count) * 100) if (present_count + absent_count) > 0 else 0, 2),
    }

    return result


def calculate_subject_tests_report(student, subject, start_date, end_date):    
    """
    Generates detailed test reports for a student in a specific subject within a date range.
    """
    # Get all batches the student belongs to for this subject
    student_batches_for_subject = _get_student_batches_qs(student).filter(subject=subject)
    tests_qs = Test.objects.filter(
        batch__in=student_batches_for_subject,
        date__range=(start_date, end_date)
    ).order_by('date')

    test_reports = []
    for test in tests_qs:
        test_result = TestResult.objects.filter(test=test, student=student).first()
        responses = QuestionResponse.objects.filter(
            test=test,
            student=student
        ).select_related('question', 'remark')

        is_absent_status = is_absent(test, student)
        attendance_status = 'Absent' if is_absent_status else 'Present'

        # Compute chapters & marks
        test_chapters = get_chapters_from_questions(test)
        marks_data = calculate_marks(responses, test_chapters)
        chapter_remarks = calculate_testwise_remarks(responses, test_chapters, is_objective=test.objective)

        test_reports.append({
            'chapters': test_chapters,
            'test': test,
            'result': test_result,
            'is_absent': is_absent_status,
            'attendance_status': attendance_status,
            'marks_data': marks_data,
            'remarks': chapter_remarks,
        })
    return test_reports
   

def get_chapters_from_questions(test):
    questions = TestQuestion.objects.filter(test=test).order_by('chapter_no')
    return {
        q.chapter_no: q.chapter_name
        for q in questions
    }

def calculate_testwise_remarks(testwise_responses, test_chapters, is_objective=False):
    """
    Same structure as subject summary chapter-remarks, but for a single test.
    Returns:
        {
            'chapters': {1:'Algebra', 2:'Trigonometry'},
            'remarks_count': { 'Correct': 80.0, 'Calculation Issue': 20.0 },
            'chapter_wise_remarks': {
                'Correct': [5, 10],
                'Calculation Issue': [2, 0],
                ...
            }
        }
    """
    chapter_keys = list(test_chapters.keys())

    # Initialize same as subject summary
    chapter_wise_remarks = defaultdict(lambda: [0] * len(test_chapters))
    remarks_count = defaultdict(int)

    for response in testwise_responses:
        ch_no = response.question.chapter_no
        if ch_no not in chapter_keys:
            continue

        idx = chapter_keys.index(ch_no)

        if is_objective:
            maxm = response.question.max_marks
            obtained = response.marks_obtained

            if obtained > 0:
                remark = "Correct"
                chapter_wise_remarks[remark][idx] += obtained
                remarks_count[remark] += obtained

            elif obtained < 0:
                remark = "Incorrect"
                chapter_wise_remarks[remark][idx] += abs(maxm - obtained)
                remarks_count[remark] += abs(maxm - obtained)

                chapter_wise_remarks['Correct'][idx] += obtained
                remarks_count['Correct'] += obtained

            else:  # obtained == 0
                remark = "Not Attempted"
                chapter_wise_remarks[remark][idx] += maxm
                remarks_count[remark] += maxm

            continue  # skip the old subjective logic

        # Compute deducted marks for this response
        deducted = response.question.max_marks - response.marks_obtained

        # Add obtained marks to "Correct" (even if partial)
        chapter_wise_remarks['Correct'][idx] += response.marks_obtained
        remarks_count['Correct'] += response.marks_obtained

        # If nothing was deducted (full marks) we're done for this response
        if deducted == 0:
            continue

        # If there's no remark, skip adding deducted marks to any remark
        if not response.remark:
            continue

        # Add deducted marks to the specific remark for this mistake
        remark_name = response.remark.name
        chapter_wise_remarks[remark_name][idx] += deducted
        remarks_count[remark_name] += deducted

    # Convert remark count to percentages
    total = sum(remarks_count.values())
    if total > 0:
        remarks_count = {
            k: round((v / total) * 100, 1)
            for k, v in remarks_count.items()
        }

    # Sort for consistency
    chapter_wise_remarks = dict(sorted(
        chapter_wise_remarks.items(),
        key=lambda item: item[0] != 'Correct'
    ))
    remarks_count = dict(sorted(remarks_count.items(), key=lambda item: item[1], reverse=True))

    return {
        'chapters': test_chapters,
        'remarks_count': remarks_count,
        'chapter_wise_remarks': chapter_wise_remarks
    }


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
        ch_no = response.question.chapter_no
        if ch_no not in chapters:
            continue  # Skip if chapter is not in the batch
        idx = list(chapters.keys()).index(ch_no)
        
        # Check if student scored full marks (mark as "Correct")
        if response.marks_obtained >= response.question.max_marks:
            chapter_wise_remarks['Correct'][idx] += response.marks_obtained
            remarks_count['Correct'] += 1
        elif response.remark:
            chapter_wise_remarks[response.remark.name][idx] += (response.question.max_marks - response.marks_obtained)
            remarks_count[response.remark.name] += 1
    
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

def calculate_subject_chapter_remarks(student, subject, start_date, end_date):
    """
    Calculates chapterwise remarks for all tests of a student in a subject within a date range.
    Returns a dict: {remark: [deducted_marks_per_chapter]}
    """
    # Get all batches the student belongs to for this subject
    student_batches_for_subject = _get_student_batches_qs(student).filter(subject=subject)
    if not student_batches_for_subject.exists():
        chapters = {}
        chapter_wise_remarks = {}
        remarks_count = {}
    else:
        # Collect class_name ids for the student's batches of this subject
        class_ids = list(student_batches_for_subject.values_list('class_name_id', flat=True).distinct())

        # Chapters for the subject limited to the classes the student attends
        chapters = {
            ch.chapter_no: ch.chapter_name
            for ch in Chapter.objects.filter(
                subject=subject,
                class_name__id__in=class_ids
            ).order_by('chapter_no')
        }

        # Only tests from the student's batches for this subject in the date range
        tests_qs = Test.objects.filter(
            batch__in=student_batches_for_subject,
            date__range=(start_date, end_date)
        ).order_by('date')

        # Fetch all responses for these tests by the student
        questions_responses = QuestionResponse.objects.filter(
            student=student,
            test__in=tests_qs
        ).select_related('question', 'remark')

        chapter_wise_remarks = defaultdict(lambda: [0] * len(chapters))
        total_count = [0] * len(chapters)
        remarks_total = 0
        remarks_count = defaultdict(int)
        chapter_keys = list(chapters.keys())

        for response in questions_responses:
            ch_no = response.question.chapter_no
            if ch_no not in chapters:
                continue
            idx = chapter_keys.index(ch_no)

            # =============== OBJECTIVE TEST LOGIC (new) ===============
            if response.test.objective:
                obtained = response.marks_obtained

                if obtained > 0:
                    remark = "Correct"
                    chapter_wise_remarks[remark][idx] += obtained
                    remarks_count[remark] += obtained
                    total_count[idx] += obtained
                    remarks_total += obtained

                elif obtained < 0:
                    remark = "Incorrect"
                    chapter_wise_remarks[remark][idx] += abs(obtained)
                    remarks_count[remark] += abs(obtained)
                    total_count[idx] += abs(obtained)
                    remarks_total += abs(obtained)

                    chapter_wise_remarks['Correct'][idx] += obtained
                    remarks_count['Correct'] += obtained
                    total_count[idx] += obtained
                    remarks_total += obtained

                else:  # obtained == 0
                    remark = "Not Attempted"
                    chapter_wise_remarks[remark][idx] += response.question.max_marks
                    remarks_count[remark] += response.question.max_marks
                    total_count[idx] += response.question.max_marks
                    remarks_total += response.question.max_marks

                continue  # Skip subjective logic
            # ==========================================================

            # Full marks -> mark as Correct
            if response.marks_obtained >= response.question.max_marks:
                chapter_wise_remarks['Correct'][idx] += response.marks_obtained
                total_count[idx] += response.marks_obtained
                remarks_count['Correct'] += 1
                remarks_total += response.marks_obtained
                continue

            if not response.remark:
                continue

            remark_name = response.remark.name
            chapter_wise_remarks[remark_name][idx] += (response.question.max_marks - response.marks_obtained)
            total_count[idx] += (response.question.max_marks - response.marks_obtained)
            remarks_count[remark_name] += 1
            remarks_total += (response.question.max_marks - response.marks_obtained)

        total_remarks_sum = sum(remarks_count.values())
        if total_remarks_sum > 0:
            remarks_count = {
                k: round((v / total_remarks_sum) * 100, 1)
                for k, v in remarks_count.items()
            }

        # Sort remarks by their values (descending)
        chapter_wise_remarks = dict(sorted(
            chapter_wise_remarks.items(),
            key=lambda item: (item[0] != "Correct", item[1]),
        ))

        remarks_count = dict(sorted(remarks_count.items(), key=lambda item: item[1], reverse=True))

    # Normalize chapter_wise_remarks to percentages per chapter
    for chapter_idx in range(len(chapters)):
        chapter_total = sum(
        chapter_wise_remarks[remark][chapter_idx]
        for remark in chapter_wise_remarks
        )
        if chapter_total > 0:
            for remark in chapter_wise_remarks:
                chapter_wise_remarks[remark][chapter_idx] = round((chapter_wise_remarks[remark][chapter_idx] / chapter_total) * 100, 1)

    return {
        'chapters': chapters,
        'remarks_count': remarks_count,
        'chapter_wise_remarks': chapter_wise_remarks,
    }

def calculate_marks(testwise_responses, test_chapters):
    max_marks = 0
    total_marks = 0
    marks_deducted = 0
    marks_obtained = 0
    remarks = defaultdict(float)

    for ch_no in test_chapters:
        total_test_marks = 0
        total_marks_obt = 0
        responses = testwise_responses.filter(question__chapter_no=ch_no)

        for r in responses:
            total_test_marks += r.question.max_marks
            total_marks_obt += r.marks_obtained
            
            # Check if student scored full marks (mark as "Correct")
            if r.marks_obtained >= r.question.max_marks:
                remarks['Correct'] += r.marks_obtained
            elif r.remark:
                remarks[r.remark.name] += r.question.max_marks - r.marks_obtained

        max_marks += total_test_marks
        total_marks += total_test_marks
        marks_obtained += total_marks_obt
        marks_deducted += (total_test_marks - total_marks_obt)

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
        'percentage': (marks_obtained / (total_marks or 1)) * 100,
        'obtained_total': marks_obtained,
        'total_max': total_marks,
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

    percentage = round((present_sessions / total_sessions_for_student) * 100, 2) if total_sessions_for_student > 0 else 0.0
    
    return {
        'percentage': percentage,
        'present': present_sessions,
        'total': total_sessions_for_student
    }

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
        percentage = round((completed_homeworks / total_homeworks_for_student) * 100, 2)
        return {
            'percentage': percentage,
            'completed': completed_homeworks,
            'total': total_homeworks_for_student
        }
    return {
        'percentage': 0.0,
        'completed': 0,
        'total': 0
    }

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

        for batch in _get_student_batches_qs(student).exclude(
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
        student: The Student instance.
        start_date: Start of date range (datetime.date).
        end_date: End of date range (datetime.date).
    """

    # Get student's batches grouped by class and subject using StudentBatchLink (includes active flag)
    student_batch_links = StudentBatchLink.objects.filter(
        student=student
    ).select_related('batch__class_name', 'batch__subject').order_by(
        'batch__class_name__name', 'batch__subject__name', '-active'
    )

    batches_by_class_subject = {}
    for link in student_batch_links:
        batch = link.batch
        class_name = batch.class_name.name
        subject_name = batch.subject.name
        key = f"{class_name} {subject_name}"

        if key not in batches_by_class_subject:
            batches_by_class_subject[key] = {
                'batches': []
            }

        batches_by_class_subject[key]['batches'].append({
            'batch_name': str(batch.section.name),
            'batch_id': batch.id,
            'active': bool(link.active),
            'attendance': calculate_attendance_percentage(student, batch, start_date, end_date),
            'homework': calculate_homework_completion_percentage(student, batch, start_date, end_date),
            'test_marks': calculate_test_scores_percentage(student, batch, start_date, end_date),
        })

        print(batches_by_class_subject[key]['batches'][-1])
    return batches_by_class_subject


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
    student_batch_links = StudentBatchLink.objects.filter(
        student=student
    ).select_related('batch__class_name', 'batch__subject').order_by(
        'batch__class_name__name', 'batch__subject__name', '-active'
    )
    batches_by_class_subject = {}
    for link in student_batch_links:
        batch = link.batch
        class_name = batch.class_name.name
        subject_name = batch.subject.name
        key = f"{class_name} {subject_name}"

        if key not in batches_by_class_subject:
            batches_by_class_subject[key] = {
                'class': batch.class_name,
                'subject': batch.subject,
                'section': batch.section,
                'batches': []
            }

        batches_by_class_subject[key]['batches'].append({
            'batch_name': str(batch.section.name),
            'batch_id': batch.id,
            'active': bool(link.active),
        })

    for key in batches_by_class_subject:
        class_obj = batches_by_class_subject[key]['class']
        subject_obj = batches_by_class_subject[key]['subject']

        # Only include tests from the student's own batches for this class+subject
        student_batches_for_subject = _get_student_batches_qs(student).filter(
            subject=subject_obj,
            class_name=class_obj
        )

        if not student_batches_for_subject.exists():
            tests_qs = Test.objects.none()
        else:
            tests_qs = Test.objects.filter(
                batch__in=student_batches_for_subject,
                date__range=(start_date, end_date)
            ).order_by('date')

        # # Group tests by their exam date. Each item is a dict: {'date': date, 'tests': [Test, ...]}
        tests_in_subject = {}
        for test_date, group in groupby(tests_qs, key=lambda t: t.date):

            tests_in_subject[test_date] = {
                'tests': list(group)
            }

        test_data = []
        for test_date, test_group in tests_in_subject.items():
            tests = test_group['tests']
            # Prefer a test on this date where the student has a TestResult.
            selected_test = None
            selected_result = None

            for test in tests:
                res = TestResult.objects.filter(test=test, student=student).first()
                if res:
                    selected_test = test
                    selected_result = res
                    break

            if not selected_test:
                # No result found for any test on this date — pick one test (first) and mark absent
                selected_test = tests[0]
                # Treat as absent when there is no TestResult for the student
                is_abs = True
            else:
                is_abs = False

            test_data.append({
                'test': selected_test,
                'result': selected_result,
                'is_absent': is_abs
            })
        batches_by_class_subject[key]['tests'] = test_data

        # ---------------- ATTENDANCE ----------------
        attendance_qs = Attendance.objects.filter(
            student=student,
            batch__in=student_batches_for_subject,
            date__range=(start_date, end_date)
        )

        attendance_total = attendance_qs.count()
        attendance_present = attendance_qs.filter(is_present=True).count()

        attendance_percentage = (
            round((attendance_present / attendance_total) * 100, 2)
            if attendance_total else 0
        )

        # ---------------- HOMEWORK ----------------
        homework_qs = Homework.objects.filter(
            student=student,
            batch__in=student_batches_for_subject,
            date__range=(start_date, end_date)
        )

        homework_total = homework_qs.count()
        homework_done = homework_qs.filter(status="Completed").count()

        homework_percentage = (
            round((homework_done / homework_total) * 100, 2)
            if homework_total else 0
        )

        # ---------------- STORE DATA ----------------
        batches_by_class_subject[key].update(
            {
            'attendance': {
                'present': attendance_present,
                'total': attendance_total,
                'percentage': attendance_percentage
            },
            'homework': {
                'completed': homework_done,
                'total': homework_total,
                'percentage': homework_percentage
            }
        }
        )
            
    return batches_by_class_subject

def get_student_retest_report(student, start_date, end_date):
    """
    Generates a detailed retest report for a student with test scores.
    Args:
        student: The Student instance.
    Returns:
        A dictionary with batch as key and a list of dicts
    """
    student_batch_links = StudentBatchLink.objects.filter(
        student=student
    ).select_related('batch__class_name', 'batch__subject').order_by(
        'batch__class_name__name', 'batch__subject__name', '-active'
    )

    batches_by_class_subject = {}
    for link in student_batch_links:
        batch = link.batch
        class_name = batch.class_name.name
        subject_name = batch.subject.name
        key = f"{class_name} {subject_name}"

        if key not in batches_by_class_subject:
            batches_by_class_subject[key] = {
                'class': batch.class_name,
                'subject': batch.subject,
                'section': batch.section,
                'batches': []
            }

        batches_by_class_subject[key]['batches'].append({
            'batch_name': str(batch.section.name),
            'batch_id': batch.id,
            'active': bool(link.active),
        })

    doj = getattr(student, 'doj', None)
    effective_start_date = max(start_date, doj) if doj else start_date

    for key in batches_by_class_subject:
        class_obj = batches_by_class_subject[key]['class']
        subject_obj = batches_by_class_subject[key]['subject']

        # Only include tests from the student's own batches for this class+subject and within date range
        student_batches_for_subject = _get_student_batches_qs(student).filter(
            subject=subject_obj,
            class_name=class_obj
        )

        if not student_batches_for_subject.exists():
            tests_qs = Test.objects.none()
        else:
            tests_qs = Test.objects.filter(
                batch__in=student_batches_for_subject,
                date__range=(effective_start_date, end_date)
            ).order_by('date')

        # Group tests by their exam date
        tests_in_subject = {}
        for test_date, group in groupby(tests_qs, key=lambda t: t.date):
            tests_in_subject[test_date] = {
                'tests': list(group)
            }

        test_data = []
        for test_date, test_group in tests_in_subject.items():
            tests = test_group['tests']
            selected_test = None
            selected_result = None

            for test in tests:
                res = TestResult.objects.filter(test=test, student=student).first()
                if res:
                    selected_test = test
                    selected_result = res
                    break

            if not selected_test:
                selected_test = tests[0]
                is_abs = True
            else:
                is_abs = False

            # Check retest criteria
            retest_suggested = is_abs or (selected_result and selected_result.percentage is not None and selected_result.percentage < 50)
            retest_given = False
            retest_marks = None

            if retest_suggested:
                retest_result = TestResult.objects.filter(
                    test=selected_test,
                    student=student,
                    test_type='retest'
                ).first()

                if retest_result:
                    retest_given = True
                    retest_marks = retest_result.total_marks_obtained

            # Only include tests that need retest
            if retest_suggested:
                test_data.append({
                    'test': selected_test,
                    'result': selected_result,
                    'is_absent': is_abs,
                    'retest_suggested': retest_suggested,
                    'retest_given': retest_given,
                    'retest_marks': retest_marks
                })

        batches_by_class_subject[key]['tests'] = test_data

    return batches_by_class_subject

def compare_student_performance_by_week(batch, start_date, end_date):
    """
    For a given batch and week_number (1=current, 2=previous), returns:
    - tests in that week
    - for each student: their percentage in each test, and their average percentage for the week
    - also returns the average percentage for each test across all students
    - for each student: their attendance percentage for the week in this batch
    - for each student: their homework completion percentage (only 'Completed' status) for the week in this batch
    - for each student: test-wise remarks (from StudentTestRemark)
    Considers student's join date (doj): if test is before join date, test value is blank.
    """
    tests = Test.objects.filter(batch=batch, date__range=(start_date, end_date)).order_by('date')
    students = Student.objects.filter(
        enrollments__batch_links__batch=batch,
        enrollments__session__is_active=True,
        enrollments__active=True,
        active=True,
    ).distinct()
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

    # Pre-fetch StudentTestRemark for all students and tests in this batch and week
    remarks_qs = StudentTestRemark.objects.filter(
        student__in=students,
        test__in=tests
    )
    remarks_lookup = {}
    for r in remarks_qs:
        remarks_lookup[(r.student_id, r.test_id)] = r.remark

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
        # Get the latest active recommendation for the student, if any
        recommendation = Recommendation.objects.filter(
            student=stu,
            active=True
        ).order_by('-date').first()

        if recommendation:
            recommendation = recommendation.action
        
        remark = MentorRemark.objects.filter( 
            student=stu, start_date=start_date, end_date=end_date
        ).order_by('-created_at').first()

        if remark and remark.recommendation:
            recommendation_label = dict(Recommendation.ACTION_CHOICES).get(remark.recommendation.action, '') if remark.recommendation else ''
        else:
            recommendation_label = ''

        # Collect test-wise remarks for this student
        test_remarks = {}
        for test in tests:
            test_remarks[test] = remarks_lookup.get((stu.id, test.id), None)

        stu_obj['student'] = {
            'stu': stu,
            'percentage': round((total_marks_obtained / (total_max_marks or 1)) * 100, 1),
            'attendance_percentage': attendance_perc,
            'attendance_present': present_att,
            'attendance_total': total_att,
            'homework_percentage': homework_perc,
            'homework_completed': completed_hw,
            'homework_total': total_hw,
            'recommendation': recommendation,
            'recommendation_label': recommendation_label,
            'remark': remark,
            'test_remarks': test_remarks
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


def get_batch_performance_over_time(batch, start_date, end_date):
    """
    For a given batch and date range, returns monthly average test percentages
    for all students in the batch. it should create a list of batches with their average percentage, attendance, homework completion etc.
    """
    monthly_performance = []

    current = date(start_date.year, start_date.month, 1)
    last_date = date(end_date.year, end_date.month, calendar.monthrange(end_date.year, end_date.month)[1])

    while current <= last_date:
        tests_in_month = Test.objects.filter(
            batch=batch,
            date__range=(current, last_date)
        )

        students = Student.objects.filter(
            enrollments__batch_links__batch=batch,
            enrollments__session__is_active=True,
            enrollments__active=True,
            active=True,
        ).distinct()
        total_percentage = 0
        student_count = 0

        for stu in students:
            total_marks_obtained = 0
            total_max_marks = 0
            doj = getattr(stu, 'doj', None)

            for test in tests_in_month:
                if doj and test.date < doj:
                    continue

                result = TestResult.objects.filter(test=test, student=stu).first()
                if result:
                    total_marks_obtained += result.total_marks_obtained
                    total_max_marks += result.total_max_marks

            if total_max_marks > 0:
                student_percentage = (total_marks_obtained / total_max_marks) * 100
                total_percentage += student_percentage
                student_count += 1

        average_percentage = round((total_percentage / student_count), 2) if student_count > 0 else 0.0

        monthly_performance.append({
            'average_percentage': average_percentage,
            'student_count': student_count,
        })

    return monthly_performance