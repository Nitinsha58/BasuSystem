from django.shortcuts import render, redirect
from .models import Student, ParentDetails, FeeDetails, Installment, TransportDetails
from .forms import StudentRegistrationForm, StudentUpdateForm, ParentDetailsForm, TransportDetailsForm
from center.models import Subject, ClassName
from django.contrib import messages
from django.db import transaction
from datetime import datetime

from django.db.models import Q

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

    return render(request, "registration/student_update.html", {
        'student': student,
        'classes': classes, 
        'subjects': subjects
    })

def students_list(request):
    classes = ClassName.objects.all().order_by('-name')
    class_students = [
        {'class': cls.name, 'students': Student.objects.filter(class_enrolled=cls).distinct()} for cls in classes ]
    return render(request, "registration/students.html", {
        'class_students' : class_students
    })

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
    

def delete_installment(request, stu_id, ins_id):
    if stu_id and not Student.objects.filter(stu_id=stu_id):
        messages.error(request, "Invalid Student")
        return redirect('student_registration')
    
    student = Student.objects.filter(stu_id=stu_id).first()
    
    Installment.objects.filter(id=ins_id).delete()
    messages.success(request, "Installment Deleted.")
    return redirect('student_fees_details', stu_id=student.stu_id)

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
    
def print_receipt(request, stu_id):
    if stu_id and not Student.objects.filter(stu_id=stu_id):
        messages.error(request, "Invalid Student")
        return redirect('student_registration')
    
    return render(request, "registration/receipt.html", {
        'student': Student.objects.filter(stu_id=stu_id).first(),
        'today': datetime.now()
    })


def search_students(request):
    search_term = request.GET.get('search', '').strip()
    if search_term:
        students = Student.objects.filter(
            Q(user__first_name__icontains=search_term) |
            Q(user__last_name__icontains=search_term) |
            Q(user__phone__icontains=search_term)
        ).select_related('user')[:10]
        student_list = [
            {   "stu_id": student.stu_id,
                "name": f"{student.user.first_name} {student.user.last_name}",
                "phone": student.user.phone,
                "class": student.class_enrolled if student.class_enrolled else "N/A",
                "subjects": ", ".join(subject.name for subject in student.subjects.all())
            }
            for student in students
        ]
    else:
        student_list = []
    return render(request, 'registration/students_results.html', {'students': student_list})
    
    