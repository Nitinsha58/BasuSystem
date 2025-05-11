from django.shortcuts import render, redirect
from .models import (
    Student, 
    ParentDetails,
    FeeDetails, 
    Installment, 
    TransportDetails, 
    Batch, 
    Teacher, 
    Attendance, 
    Homework, 
    Test, 
    TestQuestion, 
    Chapter, 
    Remark, 
    RemarkCount, 
    QuestionResponse, 
    TestResult, 
    Day, 
    Mentor,
    Mentorship,
    TransportPerson,
    TransportMode
    )
from .forms import StudentRegistrationForm, StudentUpdateForm, ParentDetailsForm, TransportDetailsForm
from center.models import Subject, ClassName
from django.contrib import messages
from django.db import transaction
from datetime import datetime, timedelta
from collections import defaultdict
from user.models import BaseUser
from django.contrib.auth.decorators import login_required

from django.db.models import Q
from django.urls import reverse

@login_required(login_url='login')
def student_registration(request):
    form_data = {}
    if request.method == "POST":
        form_data = {
            "first_name": request.POST.get("first_name"),
            "last_name": request.POST.get("last_name"),
            "phone": request.POST.get("phone"),
            "email": request.POST.get("email"),
            "dob": request.POST.get("dob"),
            "doj": request.POST.get("doj"),
            "school_name": request.POST.get("school_name"),
            "class_enrolled": ClassName.objects.filter(id=request.POST.get("class_enrolled")).first() if request.POST.get("class_enrolled") else '',
            "subjects": request.POST.getlist("subjects"),  # ManyToMany field
            "marksheet_submitted": request.POST.get("marksheet_submitted") == "yes",
            "sat_score": request.POST.get("sat_score"),
            "remarks": request.POST.get("remarks"),
            "address": request.POST.get("address"),
            "last_year_marks_details": request.POST.get("last_year_marks_details"),
            "aadhar_card_number": request.POST.get("aadhar_card_number"),
            "gender": request.POST.get("gender"),
            "course": request.POST.get("course"),
            "program_duration": request.POST.get("program_duration"),
        }
        form = StudentRegistrationForm(form_data)

        if form.is_valid():
            student = form.save()
            messages.success(request, "Student Created.")
            return redirect("student_update", stu_id = student.stu_id)
        
        for field, error_list in form.errors.items():
            for error in error_list:
                messages.error(request, f"{field}: {error}")

    classes = ClassName.objects.all().order_by('-name')
    subjects = Subject.objects.all().order_by('name')
    courses = Student.COURSE_CHOICE
    durations = Student.DURATION_CHOICE

    return render(request, "registration/student_registration.html", {
        'classes': classes, 
        'subjects': subjects,
        'form': form_data,
        'courses': courses,
        'durations': durations
    })

@login_required(login_url='login')
def student_update(request, stu_id):
    student = Student.objects.filter(stu_id=stu_id).first()

    if not student:
        messages.error(request, 'Invalid Student Id.')
        return redirect('student_registration')
    
    if request.method == 'POST':
        form_data = {
            "first_name": request.POST.get("first_name"),
            "last_name": request.POST.get("last_name"),
            "phone": request.POST.get("phone"),
            "email": request.POST.get("email"),
            "dob": request.POST.get("dob"),
            "doj": request.POST.get("doj"),
            "school_name": request.POST.get("school_name"),
            "class_enrolled": ClassName.objects.filter(id=request.POST.get("class_enrolled")).first() if request.POST.get("class_enrolled") else '',
            "subjects": request.POST.getlist("subjects"),  # ManyToMany field
            "batches": request.POST.getlist("batches"),  # ManyToMany field
            "marksheet_submitted": request.POST.get("marksheet_submitted") == "yes",
            "sat_score": request.POST.get("sat_score"),
            "remarks": request.POST.get("remarks"),
            "address": request.POST.get("address"),
            "last_year_marks_details": request.POST.get("last_year_marks_details"),
            "aadhar_card_number": request.POST.get("aadhar_card_number"),
            "gender": request.POST.get("gender"),
            "course": request.POST.get("course"),
            "program_duration": request.POST.get("program_duration"),
            "active": request.POST.get("active") == "Active",
        }
        form = StudentUpdateForm(form_data, instance=student)
        if form.is_valid():
            form.save()
            messages.success(request, 'Student Updated.')
            return redirect("student_update", stu_id=student.stu_id)
        
        for field, error_list in form.errors.items():
            for error in error_list:
                messages.error(request, f"{field}: {error}")

        return redirect("student_update", stu_id=student.stu_id)
    
    classes = ClassName.objects.all().order_by('-name')
    subjects = Subject.objects.all().order_by('name')
    selected_class = ClassName.objects.filter(id=student.class_enrolled.id).first() if student.class_enrolled else None
    batches = Batch.objects.filter(class_name=selected_class)

    return render(request, "registration/student_update.html", {
        'student': student,
        'classes': classes, 
        'subjects': subjects,
        'batches': batches,
    })

@login_required(login_url='login')
def students_list(request):
    classes = ClassName.objects.all().order_by('-created_at')
    class_students = [
        {'class': cls.name, 'students': Student.objects.filter(class_enrolled=cls).order_by('-created_at', 'user__first_name', 'user__last_name').distinct()} for cls in classes ]
    
    count = Student.objects.filter(active=True).distinct().count()
    

    return render(request, "registration/students.html", {
        'class_students' : class_students,
        'count': count,
    })

@login_required(login_url='login')
def student_parent_details(request, stu_id):

    if stu_id and not Student.objects.filter(stu_id=stu_id):
        messages.error(request, "Invalid Student")
        return redirect('student_registration')
    student = Student.objects.filter(stu_id=stu_id).first()
    form_data = {}

    if request.method == "POST":
        form_data = {
            "father_name": request.POST.get("father_name"),
            "mother_name": request.POST.get("mother_name"),
            "father_contact": request.POST.get("father_contact"),
            "mother_contact": request.POST.get("mother_contact"),
        }
        form = ParentDetailsForm(form_data)

        if form.is_valid():
            form.save(student)
            messages.success(request, "Parent details saved successfully.")
            return redirect("student_parent_details", stu_id=student.stu_id)
        
        for field, error_list in form.errors.items():
            for error in error_list:
                messages.error(request, f"{field}: {error}")

    parent_details = ParentDetails.objects.filter(student=student).first()
    return render(request, "registration/student_parent_details.html", {
        "student": student,
        "form": form_data,
        "parent_details": parent_details
    })

@login_required(login_url = 'login')
def student_fees_details(request, stu_id):
    student = Student.objects.filter(stu_id=stu_id).first()
    if not student:
        messages.error(request, "Invalid Student")
        return redirect('student_registration')

    fees_details = FeeDetails.objects.filter(student__stu_id=stu_id).first()

    if request.method == 'POST':
        form_data = {
            "registration_fee": request.POST.get("registration_fee") or 0,
            "uniform_fees": request.POST.get("uniform_fees") or 0,
            "cab_fees": request.POST.get("cab_fees") or 0,
            "tuition_fees": request.POST.get("tuition_fees") or 0,
            "num_installments": request.POST.get("num_installments") or 1,
            "discount": request.POST.get("discount") or 0,
            "total_fees": request.POST.get("total_fees") or 0,
            "book_fees": request.POST.get("book_fees") or 0,
            "installments": []
        }

        try:
            with transaction.atomic():
                fees_details, created = FeeDetails.objects.get_or_create(student=student)

                fees_details.total_fees = request.POST.get("total_fees") or 0
                fees_details.registration_fee = request.POST.get("registration_fee") or 0
                fees_details.cab_fees = request.POST.get("cab_fees") or 0
                fees_details.tuition_fees = request.POST.get("tuition_fees") or 0
                fees_details.discount = request.POST.get("discount") or 0
                fees_details.book_fees = request.POST.get("book_fees") or 0
                fees_details.book_discount = (request.POST.get("book_discount") == 'on')
                fees_details.registration_discount = (request.POST.get("registration_discount") == 'on')

                fees_details.save()

                # Delete existing installments
                Installment.objects.filter(fee_details=fees_details).delete()

                for ins in range(1, int(request.POST.get("num_installments") or 1) + 1):
                    installment = Installment(
                        fee_details=fees_details,
                        student=student,
                        amount=request.POST.get(f'installment_amount_{ins}'),
                        due_date=request.POST.get(f'installment_due_date_{ins}'),
                        paid=(request.POST.get(f'paid_{ins}') == 'on') ,
                        label = request.POST.get(f'installment_label_{ins}'),
                        payment_type = request.POST.get(f'payment_type_{ins}')
                    )
                    installment.save()
        except Exception as e:
            messages.error(request, "Invalid Data or form.")
            return redirect('student_fees_details', stu_id=stu_id)

    payment_options = Installment.PAYMENT_CHOICES

    return render(request, "registration/student_fees_details.html", {
        'student': student,
        'fees_details': fees_details,
        'payment_options': payment_options,
    })

@login_required(login_url='login')
def student_transport_details(request, stu_id):
    student = Student.objects.filter(stu_id=stu_id).first()
    if not student:
        messages.error(request, "Invalid Student")
        return redirect('student_registration')

    instance = getattr(student, 'transport', None)

    if request.method == "POST":
        form = TransportDetailsForm(request.POST, instance=instance)
        if form.is_valid():
            transport = form.save(commit=False)
            transport.student = student
            transport.save()
            messages.success(request, "Transport details saved.")
            return redirect("student_transport_details", stu_id=student.stu_id)
        else:
            for field, error_list in form.errors.items():
                for error in error_list:
                    messages.error(request, f"{field}: {error}")
    else:
        form = TransportDetailsForm(instance=instance)

    return render(request, "registration/student_transport_details.html", {
        'form': form,
        'student': student,
    })

    
@login_required(login_url='login')
def delete_installment(request, stu_id, ins_id):
    if stu_id and not Student.objects.filter(stu_id=stu_id):
        messages.error(request, "Invalid Student")
        return redirect('student_registration')
    
    student = Student.objects.filter(stu_id=stu_id).first()
    
    Installment.objects.filter(id=ins_id).delete()
    messages.success(request, "Installment Deleted.")
    return redirect('student_fees_details', stu_id=student.stu_id)

@login_required(login_url='login')
def student_reg_doc(request, stu_id):
    if stu_id and not Student.objects.filter(stu_id=stu_id):
        messages.error(request, "Invalid Student")
        return redirect('student_registration')

    student = Student.objects.filter(stu_id=stu_id).first()
    total_discount = 0
    total_fees = 0
    if student:
        fee_details = FeeDetails.objects.filter(student=student).first()
        total_discount = fee_details.discount + (fee_details.book_fees if fee_details.book_discount else 0) + (fee_details.registration_fee if fee_details.registration_discount else 0)

        total_fees = fee_details.total_fees + fee_details.discount
        if fee_details.book_discount:
            total_fees += fee_details.book_fees
        if fee_details.registration_discount:
            total_fees += fee_details.registration_fee

    return render(request, "registration/student_reg_doc.html", {
        'student': Student.objects.filter(stu_id=stu_id).first(),
        'total_discount': total_discount,
        'total_fees': total_fees
    })

@login_required(login_url='login')
def print_receipt(request, stu_id):
    if stu_id and not Student.objects.filter(stu_id=stu_id):
        messages.error(request, "Invalid Student")
        return redirect('student_registration')
    
    return render(request, "registration/receipt.html", {
        'student': Student.objects.filter(stu_id=stu_id).first(),
        'today': datetime.now()
    })

@login_required(login_url='login')
def search_students(request):
    search_term = request.GET.get('search', '').strip()
    if search_term:
        students = Student.objects.filter(
            Q(user__first_name__icontains=search_term) |
            Q(user__last_name__icontains=search_term) |
            Q(user__phone__icontains=search_term) |
            Q(user__registered_student__school_name__icontains = search_term) |
            Q(user__registered_student__class_enrolled__name__icontains = search_term) |
            Q(user__registered_student__subjects__name__icontains = search_term)
        ).select_related('user')[:10]
        student_list = [
            {   "stu_id": student.stu_id,
                "name": f"{student.user.first_name} {student.user.last_name}",
                "phone": student.user.phone,
                "class": student.class_enrolled if student.class_enrolled else "N/A",
                "subjects": ", ".join(subject.name for subject in student.subjects.all()),
                "school_name": student.school_name,
                "batches": bool(student.batches.all()),
            }
            for student in set(students)
        ]
    else:
        student_list = []
    return render(request, 'registration/students_results.html', {'students': student_list})
    
@login_required(login_url='login')
def mark_attendance(request, class_id = None, batch_id=None):
    classes = None
    batches = None
    cls = None
    batch = None

    if class_id and not ClassName.objects.filter(id=class_id):
        messages.error(request, "Invalid Class")
        return redirect('attendance')

    if batch_id and not Batch.objects.filter(id=batch_id):
        messages.error(request, "Invalid Batch")
        return redirect('attendance_class', class_id=class_id)
    
    if class_id:
        cls = ClassName.objects.filter(id=class_id).first()
        batches = Batch.objects.filter(class_name=cls).order_by('created_at')

    if batch_id:
        batch = Batch.objects.filter(id=batch_id).first()
    
    if batch_id and not batch:
        messages.error(request, "Invalid Batch")
        return redirect('attendance_class', class_id=class_id)

    date_str = request.GET.get("date")
    move = request.GET.get("move")

    if not date_str or date_str == "None":
        date = datetime.now().date()
    else:
        try:
            date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            messages.error(request, "Invalid date format.")
            return redirect(f"{reverse('attendance_batch', args=[class_id, batch_id])}?date={datetime.now().date()}")

    if move == "next":
        date += timedelta(days=1)
    elif move == "prev":
        date -= timedelta(days=1)

    if not Teacher.objects.filter(user=request.user).exists() and not request.user.is_superuser:
        messages.error(request, "You are not authorized to mark attendance.")
        return redirect('students_list')

    classes = ClassName.objects.all().order_by('created_at')

    students = Student.objects.filter(batches=batch, active=True)
    marked_students = students.filter(attendance__date=date, attendance__batch=batch).order_by('created_at')
    marked_attendance = Attendance.objects.filter(batch=batch, date=date, student__active=True).order_by('student__created_at')
    un_marked_students = students.exclude(id__in=marked_students.values_list('id', flat=True))
    
    print("Students", students)
    print("Marked Students", marked_students)
    print("Marked Attendance", marked_attendance)
    print("Unmarked Students", un_marked_students)


    if batch_id and request.method == 'POST':
        attendance_data = request.POST.getlist('attendance[]')

        batch = Batch.objects.filter(id=batch_id).first()
        if not batch:
            messages.error(request, "Invalid Batch")
            return redirect('mark_attendance', batch_id=batch_id)
        
        students = Student.objects.filter(active=True, batches=batch)
        marked_attendance = students.filter(attendance__batch=batch, active=True, attendance__date=date)

        marked_students = set()
        for data in attendance_data:
            stu_id, status = data.split(':')
            student = Student.objects.filter(stu_id=stu_id, batches=batch, active=True).first()
            if student:
                Attendance.objects.create(
                    student=student,
                    batch=batch,
                    is_present=(status == 'present'),
                    date=date
                )
            marked_students.add(student.stu_id)

        # Mark absent for students not in attendance_data
        for student in students:
            if student.stu_id not in marked_students:
                Attendance.objects.create(
                    student=student,
                    batch=batch,
                    is_present=False,
                    date = date
                )

        messages.success(request, "Attendance marked successfully.")
        return redirect(f"{reverse('attendance_batch', args=[class_id, batch_id])}?date={date}")

    return render(request, 'registration/attendance.html', {
        'classes': classes,
        'batches': batches,
        'cls': cls,
        'batch': batch,
        'marked_students': marked_students,
        'marked_attendance': marked_attendance,
        'un_marked_students': un_marked_students,
        'date': date,
    })


@login_required(login_url='login')
def mark_present(request, class_id, batch_id, attendance_id):
    day = request.GET.get('date')
    obj = Attendance.objects.filter(id=attendance_id).first()
    obj.is_present = True 
    obj.save()
    return redirect(f"{reverse('attendance_batch', args=[class_id, batch_id])}?date={day}")

@login_required(login_url='login')
def mark_absent(request, class_id, batch_id, attendance_id):
    day = request.GET.get('date')
    obj = Attendance.objects.filter(id=attendance_id).first()
    obj.is_present = False 
    obj.save()
    return redirect(f"{reverse('attendance_batch', args=[class_id, batch_id])}?date={day}")

@login_required(login_url='login')
def mark_homework(request, batch_id):
    if batch_id and not Batch.objects.filter(id=batch_id):
        messages.error(request, "Invalid Batch")
        return redirect('students_list')

    if not Teacher.objects.filter(user=request.user).exists() and not request.user.is_superuser:
        messages.error(request, "You are not authorized to update homework.")
        return redirect('students_list')
    
    batch = Batch.objects.filter(id=batch_id).first()
    students = Student.objects.filter(batches=batch, active=True)

    if batch_id and request.method == 'POST':
        date = request.POST.get('date')
        homework_data = request.POST.getlist('homework[]')

        # Check if homework already marked for the given date
        existing_homework = Homework.objects.filter(batch=batch, date=date)
        if existing_homework.exists():
            messages.error(request, "Homework for this date already marked.")
            return redirect('mark_homework', batch_id=batch_id)

        # Process the homework data
        students = Student.objects.filter(batches=batch, active=True)

        for data in homework_data:
            stu_id, status = data.split(':')
            student = Student.objects.filter(stu_id=stu_id).first()
            if student:
                Homework.objects.create(
                    student=student,
                    batch=batch,
                    status=status,
                    date = date
                )

        messages.success(request, "Homework updated successfully.")
        return redirect('mark_homework', batch_id=batch_id)
    
    homework_status = Homework.STATUS_CHOICES

  

    return render(request, 'registration/mark_homework.html', {
        'students': students,
        'batch': batch,
        'batches': Batch.objects.all(),
        'date': datetime.now().date(),
        'homework_status': homework_status,
    })

@login_required(login_url='login')
def get_attendance(request, batch_id):
    if batch_id and not Batch.objects.filter(id=batch_id):
        messages.error(request, "Invalid Batch")
        return redirect('students_list')

    if not Teacher.objects.filter(user=request.user).exists():
        messages.error(request, "You are not authorized to view attendance.")
        return redirect('students_list')

    batch = Batch.objects.filter(id=batch_id).first()
    students = Student.objects.filter(batches=batch).order_by('stu_id')

    # Get attendance records for the batch
    attendance_records = Attendance.objects.filter(batch=batch).order_by('date', 'student__stu_id')

    # Organize attendance records by date and student
    attendance_by_date = defaultdict(dict)
    for record in attendance_records:
        date = record.date
        attendance_by_date[date][record.student.stu_id] = record.is_present

    # Generate a timeline of dates for the past 30 days
    today = datetime.now().date()
    start_date = today - timedelta(days=30)
    dates = [start_date + timedelta(days=i) for i in range(31)]

    # Merge attendance data with the timeline and ensure all students are included
    attendance_timeline = []
    for date in dates:
        daily_attendance = []
        if date in attendance_by_date:    
            for student in students:
                daily_attendance.append({
                    'student': student,
                    'is_present': attendance_by_date.get(date, {}).get(student.stu_id, None)  # None means not marked
                })
        attendance_timeline.append({'date': date, 'attendance': daily_attendance})

    return render(request, 'registration/get_attendance.html', {
        'batch': batch,
        'attendance_timeline': attendance_timeline,
        'students': students,
        'dates': dates,
    })

@login_required(login_url='login')
def get_homework(request, batch_id):
    if batch_id and not Batch.objects.filter(id=batch_id):
        messages.error(request, "Invalid Batch")
        return redirect('students_list')

    if not Teacher.objects.filter(user=request.user).exists():
        messages.error(request, "You are not authorized to view homework.")
        return redirect('students_list')

    batch = Batch.objects.filter(id=batch_id).first()
    students = Student.objects.filter(batches=batch).order_by('stu_id')

    # Get homework records for the batch
    homework_records = Homework.objects.filter(batch=batch).order_by('date', 'student__stu_id')

    # Organize homework records by date and student
    homework_by_date = defaultdict(dict)
    for record in homework_records:
        date = record.date
        homework_by_date[date][record.student.stu_id] = record.status

    # Generate a timeline of dates for the past 30 days
    today = datetime.now().date()
    start_date = today - timedelta(days=15)
    dates = [start_date + timedelta(days=i) for i in range(31)]

    # Merge homework data with the timeline and ensure all students are included
    homework_timeline = []
    for date in dates:
        daily_homework = []
        if date in homework_by_date:
            for student in students:
                daily_homework.append({
                    'student': student,
                    'status': homework_by_date.get(date, {}).get(student.stu_id, None)  # None means not marked
                })
        homework_timeline.append({'date': date, 'homework': daily_homework})

    return render(request, 'registration/get_homework.html', {
        'batch': batch,
        'homework_timeline': homework_timeline,
        'students': students,
        'dates': dates,
    })

@login_required(login_url='login')
def add_teacher(request):
    if request.method == "POST":
        form_data = {
            "first_name": request.POST.get("first_name"),
            "last_name": request.POST.get("last_name"),
            "phone": request.POST.get("phone"),
            "password": "basu@123",
            "batches": request.POST.getlist("batches"),
        }

        # Check if user already exists
        user = BaseUser.objects.filter(phone=form_data["phone"]).first()

        if Teacher.objects.filter(user=user):
            messages.error(request, "Teacher already exists")
            return redirect("add_teacher")
        if user:
            messages.info(request, "User already exists. Linking the existing user to the teacher.")
        else:
            # Create a new user
            user = BaseUser.objects.create_user(
                phone=form_data["phone"],
                password=form_data["password"],
                first_name=form_data["first_name"],
                last_name=form_data["last_name"],
            )
            messages.success(request, "User created successfully.")

        # Create or update the teacher
        teacher, created = Teacher.objects.get_or_create(user=user)
        if not created:
            messages.info(request, "Teacher already exists. Updating the teacher details.")
        teacher.batches.set(form_data["batches"])
        teacher.save()

        messages.success(request, "Teacher registered successfully.")
        return redirect("add_teacher")

    classes = ClassName.objects.all()
    class_teachers = [{'class': cls.name, 'teachers': Teacher.objects.filter(batches__class_name=cls).distinct()} for cls in classes ]
    batches = Batch.objects.all()
    return render(request, "registration/add_teacher.html", {'batches': batches, "class_teachers": class_teachers})

@login_required(login_url='login')
def update_teacher(request, teacher_id):
    teacher = Teacher.objects.filter(id = teacher_id).first()
    if not teacher:
        messages.error(request, "Invalid Teacher Id")
        return redirect("add_teacher")

    if request.method == "POST":
        form_data = {
            "first_name": request.POST.get("first_name"),
            "last_name": request.POST.get("last_name"),
            "batches": request.POST.getlist("batches"),
        }

        # Update teacher's user details
        teacher.user.first_name = form_data["first_name"]
        teacher.user.last_name = form_data["last_name"]
        teacher.user.save()

        # Update assigned batches
        teacher.batches.set(form_data["batches"])
        teacher.save()

        messages.success(request, "Teacher details updated successfully.")
        return redirect("update_teacher", teacher_id=teacher.id)

    # Fetch existing details
    classes = ClassName.objects.all()
    class_teachers = [{'class': cls.name, 'teachers': Teacher.objects.filter(batches__class_name=cls).distinct()} for cls in classes ]
    batches = Batch.objects.all()

    return render(
        request, 
        "registration/update_teacher.html", 
        {'batches': batches, "class_teachers": class_teachers, "teacher": teacher}
    )


# Test Paper
@login_required(login_url='login')
def test_templates(request, batch_id=None):
    if not request.user.is_superuser:
        messages.error(request, "You are not authorized to view this page.")
        return redirect('staff_dashboard')
    
    if batch_id and request.method == "POST":
        if Batch.objects.filter(id=batch_id).first() == None:
            messages.error("Invalid Batch")
            return redirect('test_templates')
        
        batch = Batch.objects.filter(id=batch_id).first()
        test = Test.objects.create(batch=batch, date=datetime.now())
        test.name = 'Demo Test Paper '
        test.save()

        return redirect("create_testpaper", batch_id=batch_id, test_id=test.id )

    classes = ClassName.objects.all().order_by('name')
    class_batches = {
            cls.name : Batch.objects.filter(class_name=cls).order_by('class_name__name', 'section')
            for cls in classes
        }

    return render(request, "registration/test_templates.html", {
        'class_batches': class_batches,
    })

@login_required(login_url='login')
def create_testpaper(request, batch_id, test_id):
    if not request.user.is_superuser:
        return redirect('staff_dashboard')
    batch = Batch.objects.filter(id=batch_id).first()
    test = Test.objects.filter(id=test_id).first()
    if not batch or not test:
        messages.error(request, "Invalid Batch or Test")
        return redirect("test_templates")
    
    if request.method == 'POST':
        test_name = request.POST.get('test_name')
        total_marks = request.POST.get('total_marks')
        test_date = request.POST.get('date')
        test.date = test_date
        test.name = test_name
        if total_marks:
            test.total_max_marks = float(total_marks)

        test.save()

        return redirect('test_templates')
    
    questions = TestQuestion.objects.filter(test = test, is_main=True).order_by('question_number')
    chapters = Chapter.objects.filter(subject=batch.subject, class_name=batch.class_name).order_by('chapter_no')
    
    return render(request,"registration/create_testpaper.html", {
        "batch":batch, 
        "test":test, 
        "questions": questions,
        "chapters": chapters,
    })

@login_required(login_url='login')
def delete_testpaper(request, test_id):
    if not request.user.is_superuser:
        return redirect('staff_dashboard')
    
    test = Test.objects.filter(id=test_id).first()
    if not test:
        messages.error(request, "Invalid Test")
        return redirect("test_templates")
    
    test.delete()
    messages.success(request, "Test deleted successfully.")
    return redirect("test_templates")

@login_required(login_url='login')
def create_test_question(request, batch_id, test_id):
    if not request.user.is_superuser:
        return redirect('staff_dashboard')
    batch = Batch.objects.filter(id=batch_id).first()
    test = Test.objects.filter(id=test_id).first()
    if not batch or not test:
        messages.error(request, "Invalid Batch or Test")
        return redirect("test_templates")

    if request.method == 'POST':
        chapter_id = request.POST.get('chapter')
        max_marks = request.POST.get('max_marks')
        chapter = Chapter.objects.filter(id=chapter_id).first()

        is_optional = request.POST.get('is_option')
        opt_chapter_id = request.POST.get('opt_chapter')
        opt_chapter = Chapter.objects.filter(id=opt_chapter_id).first()
        opt_max_marks = request.POST.get('opt_max_marks')

        if not chapter:
            messages.error(request, "Invalid Chapter")
            return redirect("create_testpaper", batch_id=batch_id, test_id=test_id)


        if not opt_chapter and is_optional:
            messages.error(request, "Invalid Optional Chapter")
            return redirect("create_testpaper", batch_id=batch_id, test_id=test_id)


        try:
            with transaction.atomic():
                question = TestQuestion.objects.create(
                    test = test,
                    question_number = TestQuestion.objects.filter(test=test, is_main=True).count() + 1,
                    max_marks=float(max_marks),  # Convert to float here
                    chapter_no = int(chapter.chapter_no),
                    chapter_name=chapter.chapter_name,
                    chapter = chapter,
                )
                question.save()

                if is_optional:
                    opt_question = TestQuestion.objects.create(
                        test = test,
                        is_main = False,
                        question_number = question.question_number,
                        chapter = opt_chapter,
                        chapter_no = int(opt_chapter.chapter_no),
                        chapter_name= opt_chapter.chapter_name,
                        max_marks=float(opt_max_marks),  # Convert to float here
                    )
                    opt_question.save()

                    question.optional_question = opt_question
                    question.save()

        except Exception as e:
            messages.error(request, "Invalid Input.")

        return redirect("create_testpaper", batch_id=batch_id, test_id=test_id )
    return redirect("create_testpaper", batch_id=batch_id, test_id=test_id )

@login_required(login_url='login')
def update_test_question(request, batch_id, test_id, question_id):
    if not request.user.is_superuser:
        return redirect('staff_dashboard')
    batch = Batch.objects.filter(id=batch_id).first()
    test = Test.objects.filter(id=test_id).first()
    question = TestQuestion.objects.filter(id=question_id).first()
    if not batch or not test or not question:
        messages.error(request, "Invalid Question")
        return redirect("create_test_template")

    if request.method == 'POST':
        chapter_id = request.POST.get('chapter')
        max_marks = request.POST.get('max_marks')

        chapter = Chapter.objects.filter(id=chapter_id).first()
        if not chapter:
            messages.error(request, "Invalid Chapter")
            return redirect("create_testpaper", batch_id=batch_id, test_id=test_id)


        question.max_marks = float(max_marks)
        question.chapter = chapter
        question.chapter_no = int(chapter.chapter_no)
        question.chapter_name = chapter.chapter_name

        question.save()

        if question.optional_question:
            opt_question = question.optional_question
            # opt_chapter_name = request.POST.get('opt_chapter_name')
            # opt_chapter_no = request.POST.get('opt_chapter_no')
            opt_chapter_id = request.POST.get('opt_chapter')
            opt_chapter = Chapter.objects.filter(id=opt_chapter_id).first()
            if not opt_chapter:
                messages.error(request, "Invalid Optional Chapter")
                return redirect("create_testpaper", batch_id=batch_id, test_id=test_id)
            opt_chapter_no = chapter.chapter_no
            opt_chapter_name = chapter.chapter_name
            opt_max_marks = request.POST.get('opt_max_marks')

            opt_question.chapter_no = opt_chapter_no
            opt_question.max_marks = float(opt_max_marks)
            opt_question.chapter_name= opt_chapter_name
            opt_question.chapter = opt_chapter
            opt_question.save()

        return redirect("create_testpaper", batch_id=batch_id, test_id=test_id )
    return redirect("create_testpaper", batch_id=batch_id, test_id=test_id )


@login_required(login_url='login')
def calculate_marks(request, batch_id, test_id):
    if not request.user.is_superuser:
        return redirect('staff_dashboard')
    batch = Batch.objects.filter(id=batch_id).first()
    test = Test.objects.filter(id=test_id).first()
    if not batch or not test:
        messages.error(request, "Invalid Batch or Test")
        return redirect("create_test_template")
    test.calculate_total_max_marks()
    return redirect("create_testpaper", batch_id=batch_id, test_id=test_id )

# Test Response
@login_required(login_url='login')
def result_templates(request):
    if not request.user.is_superuser:
        return redirect('staff_dashboard')
    
    classes = ClassName.objects.all().order_by('name')
    class_batches = {
        cls.name : Batch.objects.filter(class_name=cls).order_by('class_name__name', 'section')
        for cls in classes
    }

    return render(request, "registration/result_templates.html", {
        'class_batches': class_batches,
    })

@login_required(login_url='login')
def add_result(request, batch_id, test_id, student_id=None, question_id = None):
    if not request.user.is_superuser:
        return redirect('staff_dashboard')
    batch = Batch.objects.filter(id=batch_id).first()
    test = Test.objects.filter(id=test_id).first()
    student = None
    question_response = None
    result = None
    
    if not batch or not test:
        messages.error(request, "Invalid Batch or Test")
        return redirect("result_templates")

    questions = TestQuestion.objects.filter(test=test).order_by('question_number')
    remarks = Remark.objects.all()

    if student_id and Student.objects.filter(id=student_id).first():
        student = Student.objects.filter(id=student_id).first()
        question = TestQuestion.objects.filter(id=question_id).first()

        result = TestResult.objects.filter(test=test, student=student).first()

        if request.method == 'POST' and question:
            marks_obtained = request.POST.get("marks_obtained")
            remark_id = request.POST.get("remark")
            remark = Remark.objects.filter(id=remark_id).first()

            response = QuestionResponse.objects.create(
                question = question,
                student=student,
                test=test,
                marks_obtained = float(question.max_marks) - float(marks_obtained),
                remark = remark
            )
            response.save()
            return redirect("add_student_result", batch_id=batch_id, test_id=test_id, student_id=student_id)
        
        responses = QuestionResponse.objects.filter(student=student, test=test).select_related("question")

        # Create a dictionary to map questions to their responses
        response_map = {response.question.id: response for response in responses}
        question_nums = [response.question.question_number for response in responses]

        question_response = []

        for question in questions:
            if question.id in response_map:
                question_response.append({"response": response_map.get(question.id)})
            elif question.is_main and question.question_number not in question_nums:
                question_response.append({"question": question})
    
    students = Student.objects.filter(batches=batch)
    students_map = {student : TestResult.objects.filter(test=test, student=student).first() or 0 for student in students}

    return render(request, "registration/add_results.html", {
        "batch":batch, 
        "test":test,
        "students": students_map,
        "questions": questions,
        "student":student,
        "remarks":remarks,
        "question_response": question_response,
        "result":result,
    })


@login_required(login_url='login')
def update_result(request, batch_id, test_id, student_id, response_id):
    if not request.user.is_superuser:
        return redirect('staff_dashboard')
    batch = Batch.objects.filter(id=batch_id).first()
    test = Test.objects.filter(id=test_id).first()
    student = Student.objects.filter(id=student_id).first()
    response = QuestionResponse.objects.filter(id = response_id).first()

    if ( not batch or not test or not student or not response ) :
        messages.error("Invalid Details.")
        return redirect("add_student_question_response", batch_id=batch_id, test_id=test_id, student_id=student_id)

    if request.method == 'POST':
        marks_obtained = request.POST.get("marks_obtained")
        remark_id = request.POST.get("remark")

        response.marks_obtained = float(response.question.max_marks) - abs(float(marks_obtained))
        if remark_id:
            remark = Remark.objects.get(id=remark_id)
            response.remark = remark
        response.save()

    return redirect("add_student_result", batch_id=batch_id, test_id=test_id, student_id=student_id)

@login_required(login_url='login')
def delete_result(request, batch_id, test_id, student_id, response_id):
    if not request.user.is_superuser:
        return redirect('staff_dashboard')
    try:
        if not Batch.objects.filter(id=batch_id).exists():
            messages.error(request, "Invalid batch ID.")
            return redirect("add_student_result", batch_id=batch_id, test_id=test_id, student_id=student_id)

        if not Test.objects.filter(id=test_id).exists():
            messages.error(request, "Invalid test ID.")
            return redirect("add_student_result", batch_id=batch_id, test_id=test_id, student_id=student_id)

        if not Student.objects.filter(id=student_id).exists():
            messages.error(request, "Invalid student ID.")
            return redirect("add_student_result", batch_id=batch_id, test_id=test_id, student_id=student_id)

        response = QuestionResponse.objects.get(id=response_id)

        response.delete()
        messages.success(request, "Response deleted.")

    except QuestionResponse.DoesNotExist:

        messages.error(request, "Response not found. Unable to delete.")
    except Exception as e:
        messages.error(request, f"An error occurred: {str(e)}")

    return redirect("add_student_result", batch_id=batch_id, test_id=test_id, student_id=student_id)

@login_required(login_url='login')
def all_pending_response(request, batch_id, test_id, student_id):
    if not request.user.is_superuser:
        return redirect('staff_dashboard')
    test = Test.objects.filter(id=test_id).first()
    student = Student.objects.filter(id=student_id).first()

    if not student or not test:
        messages.error(request, "Invalid Student or Test")
        return redirect("add_student_result", batch_id=batch_id, test_id=test_id, student_id=student_id)

    unanswered_questions = TestQuestion.objects.filter(
        test=test
    ).exclude(
        responses__student=student
    )

    for question in unanswered_questions:
        if question.optional_question or question.is_main==False:
            messages.error(request, "Set Optional Questions Manually.")
            continue
        obj = QuestionResponse.objects.create(
            question=question,
            student=student,
            test=test,
            marks_obtained=question.max_marks,  # Default marks
        )
        obj.save()

    return redirect("add_student_result", batch_id=batch_id, test_id=test_id, student_id=student_id)
    

@login_required(login_url='login')
def transport_list(request):
    if not request.user.is_superuser:
        return redirect('staff_dashboard')

    weekdays = list(Day.objects.order_by("id"))  # or "name" if alphabetically sorted
    total = len(weekdays)

    index = int(request.GET.get("day", 0))

    move = request.GET.get("move")
    if move == "next" and index < total - 1:
        index += 1
    elif move == "prev" and index > 0:
        index -= 1
    

    # request.session["day"] = index
    current_day = weekdays[index]

    # # get all the batches with their days as current_day
    # batches = Batch.objects.filter(days__name=current_day).order_by('start_time', 'class_name__name', 'section')
    # grouped_batches = defaultdict(lambda: defaultdict(list))
    # for batch in batches:
    #     transport_students = Student.objects.filter(batches=batch, fees__cab_fees__gt=0).order_by('stu_id')
    #     # if transport_students.exists():
    #     #     grouped_batches[batch.start_time][batch] = transport_students
    
    batches = Batch.objects.filter(days__name=current_day).order_by('start_time', 'class_name__name', 'section')

    # Group batches by start_time, and filter students with cab_fees > 0
    grouped_batches = {}
    for batch in batches:
        transport_students = Student.objects.filter(
            batches=batch,
            fees__cab_fees__gt=0
        ).order_by('stu_id')

        if transport_students.exists():
            if batch.start_time not in grouped_batches:
                grouped_batches[batch.start_time] = {}
            grouped_batches[batch.start_time][batch] = list(transport_students)
    

    return render(request, "registration/students_timing.html", {
        "current_day": current_day,
        "day": index,
        "grouped_batches": dict(grouped_batches),
    })

@login_required(login_url='login')
def assign_mentor(request):
    
    if request.method == 'POST':
        mentor = request.POST.get('mentor')
        students = request.POST.getlist('students[]')

        if not mentor or not students:
            messages.error(request, "Please select a mentor and at least one student.")
            return redirect('assign_mentor')
        mentor_obj = Mentor.objects.filter(id=mentor).first()
        if not mentor_obj:
            messages.error(request, "Invalid Mentor")
            return redirect('assign_mentor')
        for student_id in students:
            student = Student.objects.filter(stu_id=student_id).first()
            if student:
                mentorship, created = Mentorship.objects.get_or_create(
                    mentor=mentor_obj,
                    student=student,
                    defaults={'active': True}
                )
                if not created:
                    mentorship.active = True
                    mentorship.save()
        messages.success(request, "Mentor assigned successfully.")
        return redirect('assign_mentor')

    classes = ClassName.objects.all().order_by('-created_at')
    class_students = [
        {
            'class': cls.name, 
            'students': Student.objects.filter(class_enrolled=cls, active=True).order_by('-created_at', 'user__first_name', 'user__last_name').distinct()
        } for cls in classes ]

    mentors = Mentor.objects.all().order_by('-created_at')


    return render(request, "registration/assign_mentor.html", {
        'class_students' : class_students,
        'mentors' : mentors,
    })

@login_required(login_url='login')
def unassign_mentor(request, stu_id):
    if not request.user.is_superuser:
        return redirect('staff_dashboard')
    
    student = Student.objects.filter(stu_id=stu_id).first()
    if not student:
        messages.error(request, "Invalid Student")
        return redirect('assign_mentor')

    mentorships = Mentorship.objects.filter(student=student)
    if not mentorships.exists():
        messages.error(request, "No mentorship found for this student.")
        return redirect('assign_mentor')
    
    for mentorship in mentorships:
        mentorship.active = False
        mentorship.save()
    messages.success(request, "Mentorship unassigned successfully.")

    return redirect('assign_mentor')