from django.shortcuts import render, redirect
from .models import Student, ParentDetails, FeeDetails, Installment, TransportDetails, Batch, Teacher, Attendance, Homework
from .forms import StudentRegistrationForm, StudentUpdateForm, ParentDetailsForm, TransportDetailsForm
from center.models import Subject, ClassName
from django.contrib import messages
from django.db import transaction
from datetime import datetime, timedelta
from collections import defaultdict
from user.models import BaseUser
from django.contrib.auth.decorators import login_required

from django.db.models import Q

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
    
    count = Student.objects.all().distinct().count()
    

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

@login_required('login')
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
    if stu_id and not Student.objects.filter(stu_id=stu_id):
        messages.error(request, "Invalid Student")
        return redirect('student_registration')
    
    student = Student.objects.filter(stu_id=stu_id).first()
    form_data = {}

    if request.method == "POST":
        form_data = {
            "address": request.POST.get("address"),
        }
        form = TransportDetailsForm(form_data)

        if form.is_valid():
            form.save(student)
            messages.success(request, "Location Saved.")
            return redirect("student_transport_details", stu_id=student.stu_id)
        
        for field, error_list in form.errors.items():
            for error in error_list:
                messages.error(request, f"{field}: {error}")
    
    return render(request, "registration/student_transport_details.html", {
        'student': Student.objects.filter(stu_id=stu_id).first()
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
def mark_attendance(request, batch_id=None):
    if batch_id and not Batch.objects.filter(id=batch_id):
        messages.error(request, "Invalid Batch")
        return redirect('students_list')
    
    if not Teacher.objects.filter(user=request.user).exists() and not request.user.is_superuser:
        messages.error(request, "You are not authorized to mark attendance.")
        return redirect('students_list')


    if batch_id and request.method == 'POST':
        date = request.POST.get('date')
        attendance_data = request.POST.getlist('attendance[]')

        batch = Batch.objects.filter(id=batch_id).first()
        if not batch:
            messages.error(request, "Invalid Batch")
            return redirect('mark_attendance', batch_id=batch_id)

        # Check if attendance already exists for the given date
        existing_attendance = Attendance.objects.filter(batch=batch, date=date)
        if existing_attendance.exists():
            messages.error(request, "Attendance for this date already exists.")
            return redirect('mark_attendance', batch_id=batch_id)
        
        batch = Batch.objects.filter(id=batch_id).first()
        students = Student.objects.filter(batches=batch)

        marked_students = set()
        for data in attendance_data:
            stu_id, status = data.split(':')
            student = Student.objects.filter(stu_id=stu_id).first()
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
        return redirect('attendance')

    if batch_id:
        batch = Batch.objects.filter(id=batch_id).first()
        students = Student.objects.filter(batches=batch)

        return render(request, 'registration/mark_attendance.html', {
            'students': students,
            'batch': batch,
            'batches': Batch.objects.all(),
            'date': datetime.now().date(),
        })

    
    classes = ClassName.objects.all()
    batches = Batch.objects.all()

    return render(request, 'registration/attendance.html', {'classes': classes, 'batches': batches})

@login_required(login_url='login')
def mark_homework(request, batch_id):
    if batch_id and not Batch.objects.filter(id=batch_id):
        messages.error(request, "Invalid Batch")
        return redirect('students_list')

    if not Teacher.objects.filter(user=request.user).exists() and not request.user.is_superuser:
        messages.error(request, "You are not authorized to update homework.")
        return redirect('students_list')
    
    batch = Batch.objects.filter(id=batch_id).first()
    students = Student.objects.filter(batches=batch)

    if batch_id and request.method == 'POST':
        date = request.POST.get('date')
        homework_data = request.POST.getlist('homework[]')

        # Check if homework already marked for the given date
        existing_homework = Homework.objects.filter(batch=batch, date=date)
        if existing_homework.exists():
            messages.error(request, "Homework for this date already marked.")
            return redirect('mark_homework', batch_id=batch_id)

        # Process the homework data
        students = Student.objects.filter(batches=batch)

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
    start_date = today - timedelta(days=15)
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
