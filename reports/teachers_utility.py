from registration.models import (
    Student,
    ClassName, 
    Batch, 
    Attendance, 
    Homework,
    QuestionResponse,
    Test,
    TestResult,
    )
from django.db.models import Q, Count

from django.db import models 
from django.contrib import messages
from django.shortcuts import render, redirect

def exclude_special_batches(batches):
    return batches.exclude(
        Q(class_name__name__in=['CLASS 9', 'CLASS 10']) &
        Q(section__name='CBSE') &
        Q(subject__name__in=['MATH', 'SCIENCE'])
    )

def percentage(part, total):
    return round((part / total * 100), 1) if total > 0 else 0


def get_teacher_attendance_performance(teacher, start_date, end_date):
    batches = exclude_special_batches(teacher.batches.all())
    students = Student.objects.filter(batches__in=batches, active=True).distinct()

    attendance_qs = Attendance.objects.filter(
        student__in=students,
        batch__in=batches,
        date__range=(start_date, end_date)
    )

    total_present = attendance_qs.filter(is_present=True).count()
    total_absent = attendance_qs.filter(is_present=False).count()
    total_attendance = total_present + total_absent

    return {
        'present_count': total_present,
        'absent_count': total_absent,
        'present_percentage': percentage(total_present, total_attendance),
        'absent_percentage': percentage(total_absent, total_attendance),
    }

def get_teacher_batchwise_attendance_performance(teacher, start_date, end_date):
    result = {}
    batches = exclude_special_batches(teacher.batches.all())

    for batch in batches:
        students = Student.objects.filter(batches=batch, active=True).distinct()
        attendance_qs = Attendance.objects.filter(
            student__in=students,
            batch=batch,
            date__range=(start_date, end_date)
        )

        stats = attendance_qs.aggregate(
            present=Count('id', filter=Q(is_present=True)),
            absent=Count('id', filter=Q(is_present=False)),
        )

        total = stats['present'] + stats['absent']
        result[batch] = {
            'present_count': stats['present'],
            'absent_count': stats['absent'],
            'present_percentage': percentage(stats['present'], total),
            'absent_percentage': percentage(stats['absent'], total),
        }

    return result

def get_teacher_combined_homework_performance(teacher, start_date, end_date):
    batches = exclude_special_batches(teacher.batches.all())
    students = Student.objects.filter(batches__in=batches, active=True).distinct()

    homework_qs = Homework.objects.filter(
        student__in=students,
        batch__in=batches,
        date__range=(start_date, end_date)
    )

    total = homework_qs.count()
    completed = homework_qs.filter(status='Completed').count()
    partial = homework_qs.filter(status='Partial Done').count()
    pending = homework_qs.filter(status='Pending').count()

    return {
        'completed_percentage': percentage(completed, total),
        'partial_done_percentage': percentage(partial, total),
        'pending_percentage': percentage(pending, total),
        'completed_count': completed,
        'partial_done_count': partial,
        'pending_count': pending,
        'total_count': total,
    }

def get_teacher_batchwise_homework_performance(teacher, start_date, end_date):
    result = {}
    batches = exclude_special_batches(teacher.batches.all())

    for batch in batches:
        students = Student.objects.filter(batches=batch, active=True).distinct()
        homework_qs = Homework.objects.filter(
            student__in=students,
            batch=batch,
            date__range=(start_date, end_date)
        )

        stats = homework_qs.aggregate(
            completed=Count('id', filter=Q(status='Completed')),
            partial=Count('id', filter=Q(status='Partial Done')),
            pending=Count('id', filter=Q(status='Pending'))
        )

        total = stats['completed'] + stats['partial'] + stats['pending']
        result[batch] = {
            'completed_percentage': percentage(stats['completed'], total),
            'partial_done_percentage': percentage(stats['partial'], total),
            'pending_percentage': percentage(stats['pending'], total),
            'completed_count': stats['completed'],
            'partial_done_count': stats['partial'],
            'pending_count': stats['pending'],
            'total_count': total,
        }

    return result

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

def get_teacher_marks_percentage(teacher, start_date, end_date):
    included_batches = exclude_special_batches(teacher.batches.all())

    tests = Test.objects.filter(
        batch__in=included_batches,
        date__range=(start_date, end_date)
    ).distinct()

    students = Student.objects.filter(batches__in=included_batches, active=True).distinct()
    student_ids = list(students.values_list('id', flat=True))
    test_ids = list(tests.values_list('id', flat=True))

    test_results = TestResult.objects.filter(test_id__in=test_ids, student_id__in=student_ids)
    test_result_map = {(tr.test_id, tr.student_id): tr for tr in test_results}

    total_max_marks = 0
    total_obtained_marks = 0
    present = 0
    absent = 0

    for test in tests:
        for student_id in student_ids:
            if is_absent(test, Student(id=student_id)):
                absent += 1
                continue

            present += 1
            key = (test.id, student_id)
            if key in test_result_map:
                total_max_marks += test.total_max_marks
                total_obtained_marks += test_result_map[key].total_marks_obtained

    percentage_scored = round((total_obtained_marks / total_max_marks) * 100, 2) if total_max_marks > 0 else 0.0
    percentage_deducted = round(100 - percentage_scored, 2) if total_max_marks > 0 else 0.0
    present_percentage = percentage(present, present + absent)
    absent_percentage = percentage(absent, present + absent)

    return {
        'scored': percentage_scored,
        'deducted': percentage_deducted,
        'present': present_percentage,
        'absent': absent_percentage,
    }

def get_teacher_batchwise_marks_performance(teacher, start_date, end_date):
    result = {}
    batches = exclude_special_batches(teacher.batches.all())

    for batch in batches:
        students = Student.objects.filter(batches=batch, active=True).distinct()
        tests = Test.objects.filter(batch=batch, date__range=(start_date, end_date)).distinct()

        student_ids = list(students.values_list('id', flat=True))
        test_ids = list(tests.values_list('id', flat=True))

        test_results = TestResult.objects.filter(test_id__in=test_ids, student_id__in=student_ids)
        test_result_map = {(tr.test_id, tr.student_id): tr for tr in test_results}

        total_max_marks = 0
        total_obtained_marks = 0
        present = 0
        absent = 0

        for test in tests:
            for student_id in student_ids:
                if is_absent(test, Student(id=student_id)):
                    absent += 1
                    continue

                present += 1
                key = (test.id, student_id)
                if key in test_result_map:
                    total_max_marks += test.total_max_marks
                    total_obtained_marks += test_result_map[key].total_marks_obtained

        scored = round((total_obtained_marks / total_max_marks) * 100, 2) if total_max_marks > 0 else 0.0
        deducted = round(100 - scored, 2) if total_max_marks > 0 else 0.0
        present = percentage(present, present + absent)
        absent = percentage(absent, present + absent)
        result[batch] = {
            'scored': scored,
            'deducted': deducted,
            'present': present,
            'absent': absent,
        }

    return result
