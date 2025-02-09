from django.shortcuts import render, redirect
from .models import Student, ParentDetails, FeeDetails, Installment, TransportDetails
from .forms import StudentRegistrationForm, StudentUpdateForm, ParentDetailsForm
from center.models import Subject, ClassName
from django.contrib import messages

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

    return render(request, "registration/student_registration.html", {
        'classes': classes, 
        'subjects': subjects,
        'form': form_data
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

    if stu_id and not Student.objects.filter(stu_id=stu_id):
        messages.error(request, "Invalid Student")
        return redirect('student_registration')
    
    return render(request, "registration/student_fees_details.html", {
        'student': Student.objects.filter(stu_id=stu_id).first()
    })

def student_transport_details(request, stu_id):
    if stu_id and not Student.objects.filter(stu_id=stu_id):
        messages.error(request, "Invalid Student")
        return redirect('student_registration')
    
    return render(request, "registration/student_transport_details.html", {
        'student': Student.objects.filter(stu_id=stu_id).first()
    })
    