from django.shortcuts import render, redirect
import calendar
from datetime import date, timedelta
from django.contrib.auth.decorators import login_required
from registration.models import ClassName, Student, Batch, Attendance, Homework
from django.contrib import messages

# Create your views here.

@login_required(login_url='login')  
def student_report(request, stu_id):

    student = Student.objects.filter(stu_id=stu_id).first()
    if stu_id and not student:
        messages.error(request, "Invalid Student")
        return redirect('batchwise_students')

    today = date.today()
    year = today.year
    month = today.month

    # Get first weekday and number of days
    first_weekday, total_days = calendar.monthrange(year, month)

    # 1. Combined Total Attendance of student in all batches
    total_present = Attendance.objects.filter(student=student, is_present=True).count()
    total_absent = Attendance.objects.filter(student=student, is_present=False).count()
    total_attendance = total_present + total_absent
    present_percentage = (total_present / total_attendance * 100) if total_attendance > 0 else 0
    absent_percentage = (total_absent / total_attendance * 100) if total_attendance > 0 else 0

    combined_attendance = {
        'present_count': total_present,
        'absent_count': total_absent,
        'present_percentage': round(present_percentage, 1),
        'absent_percentage': round(absent_percentage, 1),
    }

    # 2. Batchwise total attendance of student
    batchwise_attendance = {}
    for batch in student.batches.all():
        batch_present = Attendance.objects.filter(student=student, batch=batch, is_present=True).count()
        batch_absent = Attendance.objects.filter(student=student, batch=batch, is_present=False).count()
        batch_total = batch_present + batch_absent
        batch_present_percentage = (batch_present / batch_total * 100) if batch_total > 0 else 0
        batch_absent_percentage = (batch_absent / batch_total * 100) if batch_total > 0 else 0

        batchwise_attendance[batch] = {
            'present_count': batch_present,
            'absent_count': batch_absent,
            'present_percentage': round(batch_present_percentage, 1),
            'absent_percentage': round(batch_absent_percentage, 1),
        }

    # 3. Combined Total Homework of student in all batches
    total_homework = Homework.objects.filter(student=student).count()
    completed_homework = Homework.objects.filter(student=student, status='Completed').count()
    partial_done_homework = Homework.objects.filter(student=student, status='Partial Done').count()
    pending_homework = Homework.objects.filter(student=student, status='Pending').count()

    combined_homework = {
        'completed_percentage': round((completed_homework / total_homework * 100) if total_homework > 0 else 0 , 1),
        'partial_done_percentage': round((partial_done_homework / total_homework * 100) if total_homework > 0 else 0, 1),
        'pending_percentage': round((pending_homework / total_homework * 100) if total_homework > 0 else 0, 1),
    }

    # 4. Batchwise total homework of student
    batchwise_homework = {}
    for batch in student.batches.all():
        batch_total_homework = Homework.objects.filter(student=student, batch=batch).count()
        batch_completed_homework = Homework.objects.filter(student=student, batch=batch, status='Completed').count()
        batch_partial_done_homework = Homework.objects.filter(student=student, batch=batch, status='Partial Done').count()
        batch_pending_homework = Homework.objects.filter(student=student, batch=batch, status='Pending').count()

        batchwise_homework[batch] = {
            'completed_percentage': round((batch_completed_homework / batch_total_homework * 100) if batch_total_homework > 0 else 0, 1),
            'partial_done_percentage': round((batch_partial_done_homework / batch_total_homework * 100) if batch_total_homework > 0 else 0, 1),
            'pending_percentage': round((batch_pending_homework / batch_total_homework * 100) if batch_total_homework > 0 else 0, 1),
        }


    current_month = []
    week = []
    present_count = 0
    absent_count = 0

    for _ in range(first_weekday):
        week.append(None)

    for day in range(1, total_days + 1):
        current_date = date(year, month, day)
        attendance_records = Attendance.objects.filter(student=student, date__year=year, date__month=month)
        dates_records = attendance_records.values_list('date', flat=True)
        attendance_status = None
        if current_date in dates_records:
            attendance_record = attendance_records.filter(date=current_date).first()
            attendance_status = 'Present' if attendance_record.is_present else 'Absent'
            if attendance_record.is_present:
                present_count += 1
            else:   
                absent_count += 1

        homework_status = None
        homework_record = Homework.objects.filter(student=student, date=current_date).first()
        if homework_record:
            homework_status = homework_record.status

        week.append({
            'date': current_date,
            'attendance': attendance_status,
            'homework': homework_status,
        })

        if len(week) == 7:
            current_month.append(week)
            week = []

    if week:
        while len(week) < 7:
            week.append(None)
        current_month.append(week)

    batchwise_calendar = {}
    for batch in student.batches.all():
        batch_calendar = []
        week = []
        present_count = 0
        absent_count = 0

        for _ in range(first_weekday):
            week.append(None)

        for day in range(1, total_days + 1):
            current_date = date(year, month, day)
            attendance_records = Attendance.objects.filter(student=student, batch=batch, date__year=year, date__month=month)
            dates_records = attendance_records.values_list('date', flat=True)
            attendance_status = None
            if current_date in dates_records:
                attendance_record = attendance_records.filter(date=current_date).first()
                attendance_status = 'Present' if attendance_record.is_present else 'Absent'
            
                if attendance_record.is_present:
                    present_count += 1
                else:   
                    absent_count += 1

            homework_status = None
            homework_record = Homework.objects.filter(student=student, batch=batch, date=current_date).first()
            if homework_record:
                homework_status = homework_record.status

            week.append({
                'date': current_date,
                'attendance': attendance_status,
                'homework': homework_status,
            })

            if len(week) == 7:
                batch_calendar.append(week)
                week = []

        if week:
            while len(week) < 7:
                week.append(None)
            batch_calendar.append(week)

        batchwise_calendar[batch] = {
                "cal": batch_calendar,
                "present_count": present_count,
                "total_count": present_count + absent_count,
                "percentage": round((present_count / (present_count + absent_count) * 100) if (present_count + absent_count) > 0 else 0, 1),
            }

    return render(request, 'reports/student_report.html', {
        'current_month': current_month,
        'current_month_name': calendar.month_name[month],
        'current_month_present_count': present_count,
        'current_month_total_count': present_count + absent_count,
        'current_month_percentage': round((present_count / (present_count + absent_count) * 100) if (present_count + absent_count) > 0 else 0, 1),
        'batchwise_calendar': batchwise_calendar,
        'student': student,
        'combined_attendance': combined_attendance,
        'batchwise_attendance': batchwise_attendance,
        'combined_homework': combined_homework,
        'batchwise_homework': batchwise_homework,
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
