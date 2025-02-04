from django.shortcuts import render, redirect
from .models import Inquiry, ClassName, Subject, Referral


def index(request):
    return render(request, 'inquiry.html')


def create_inquiry(request):
    classes = ClassName.objects.all()
    subjects = Subject.objects.all()
    referrals = Referral.objects.all()

    if request.method == "POST":
        student_name = request.POST.get("student-name")
        selected_classes = request.POST.getlist("classes")  # getlist() for multiple selection
        selected_subjects = request.POST.getlist("subjects")
        school_name = request.POST.get("school-name")
        address = request.POST.get("address")
        phone = request.POST.get("phone")
        referral_source = request.POST.get("referral")
        inquiry = Inquiry.objects.create(
            student_name=student_name,
            school=school_name,
            address=address,
            phone=phone,
            referral_id=referral_source 
        )

        # Add many-to-many relationships (if applicable)
        inquiry.classes.set(selected_classes)
        inquiry.subjects.set(selected_subjects)
        inquiry.save()

        return render(request, 'success-page.html')

    return render(request, 'inquiry.html', {
        'classes':classes,
        'subjects':subjects,
        'referrals': referrals
        })