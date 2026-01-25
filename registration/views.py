from django.shortcuts import render, redirect, get_object_or_404
from .models import (
    Student, ParentDetails,FeeDetails, 
    Installment, TransportDetails, Batch, 
    Teacher, Attendance, Homework, 
    Test, TestQuestion, Chapter, 
    Remark, RemarkCount,QuestionResponse, 
    TestResult, Day, Mentor,
    Mentorship, TransportPerson, TransportMode, TransportAttendance,
    AcademicSession, StudentEnrollment, EnrollmentBatch,
    )
from lesson.models import Lecture

from .forms import (
    StudentRegistrationForm, StudentUpdateForm, ParentDetailsForm, TransportDetailsForm,
    )

from lesson.models import ChapterSequence, Lesson, Holiday
from django.utils.timezone import now

from center.models import Subject, ClassName
from django.contrib import messages
from django.db import transaction
from datetime import datetime, timedelta
from collections import defaultdict, OrderedDict
from user.models import BaseUser
from django.contrib.auth.decorators import login_required

from django.db.models import Q
from django.urls import reverse
import time as clock_time

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
            "batches": request.POST.getlist("batches[]"),  # ManyToMany field
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
    # WhatsApp group links mapping by class and type
    WHATSAPP_GROUP_LINKS = {
        "7": {
            "student": "https://chat.whatsapp.com/CODPG4w7eFX43VQpOi6BnD",
            "parent": "https://chat.whatsapp.com/Hi0U7fSFFwbGNlfinyCZII",
        },
        "8": {
            "student": "https://chat.whatsapp.com/H2xTY2qpUOb5EXut75iNwV",
            "parent": "https://chat.whatsapp.com/CGsBhqddvtI5BNKwzXm2wC",
        },
        "9": {
            "student": "https://chat.whatsapp.com/BasrRWXoC3x88lyXrvctEU",
            "parent": "https://chat.whatsapp.com/IOj2m12EWZI3fp9rEjF01x",
        },
        "10": {
            "student": "https://chat.whatsapp.com/L0zF6dVCBDNEF1eGEBR1Wg",
            "parent": "https://chat.whatsapp.com/Lb7Q1Xq1YBz9J2ZfcbK5dC",
        },
        "11_PCM": {
            "student": "https://chat.whatsapp.com/JdbjvZ55nwKDREkmsw2GMD",
            "parent": "https://chat.whatsapp.com/IbQTtuqBQIALABUPcE688G",
        },
        "11_COMMERCE": {
            "student": "https://chat.whatsapp.com/GruyEBmP0dZ0WOADZlEeic",
            "parent": "https://chat.whatsapp.com/I6bm2asTs9T4KJEJvKgMCL",
        },
        "12_PCM": {
            "student": "https://chat.whatsapp.com/IsveJm0QuCT9IM9Y93vZ6s",
            "parent": "https://chat.whatsapp.com/B7wsZHE4oDHDmpvC0UB1YH",
        },
        "12_COMMERCE": {
            "student": "https://chat.whatsapp.com/Esgz3orRZuLEkyQB9iJ3Va",
            "parent": "https://chat.whatsapp.com/ByZk2Dnu0el5WGanR4SZcB",
        },
        "transport_erikshaw": "https://chat.whatsapp.com/Hea0v2pn5NzDdZdzCeE4mL",
        "transport_cab": "https://chat.whatsapp.com/IvSYxCyANmFL7QjzuHljGF",
    }

    def get_class_group_key(student):
        cls = student.class_enrolled.name.upper() if student.class_enrolled else ""
        if "11" in cls:
            if "COMMERCE" in cls:
                return "11_COMMERCE"
            return "11_PCM"
        if "12" in cls:
            if "COMMERCE" in cls:
                return "12_COMMERCE"
            return "12_PCM"
        for num in ["7", "8", "9", "10"]:
            if num in cls:
                return num
        return None

    def get_whatsapp_group_links(student):
        group_key = get_class_group_key(student)
        student_link = parent_link = None
        if group_key and group_key in WHATSAPP_GROUP_LINKS:
            student_link = WHATSAPP_GROUP_LINKS[group_key].get("student")
            parent_link = WHATSAPP_GROUP_LINKS[group_key].get("parent")
        return student_link, parent_link

    def get_transport_group_links(student):
        links = []
        if getattr(student, "transport", None):
            mode = getattr(student.transport, "mode", None)
            if mode and hasattr(mode, "name"):
                mode_name = mode.name.lower()
                if "rikshaw" in mode_name:
                    links.append(WHATSAPP_GROUP_LINKS.get("transport_erikshaw"))
                if "cab" in mode_name:
                    links.append(WHATSAPP_GROUP_LINKS.get("transport_cab"))
        return [l for l in links if l]

    def generate_wa_me_link(phone, message):
        import urllib.parse
        return f"https://wa.me/{phone}?text={urllib.parse.quote(message)}"

    # Compose the join message for WhatsApp with both group links (both links are always included)
    def get_join_message(student, student_link, parent_link):
        class_name = student.class_enrolled.name if student.class_enrolled else ""
        message = (
            "Dear Parent,\n\n"
            "We're excited to begin the 2025-26 session!\n\n"
            "Thank you for your continued support. This year, we've made key improvements and new strategies to boost student results.\n\n"
            f"👇 Join the official WhatsApp groups for updates:\n\n"
        )
        # Always include both links, even if one is missing (show as N/A if not found)
        message += f"{class_name} Students Group\n{student_link or 'N/A'}\n\n"
        message += f"{class_name} Parents Group\n{parent_link or 'N/A'}\n\n"
        message += (
            "Feel free to reach out for any queries. We're here to help!\n\n"
            "- BASU Classes"
        )
        return message

    # Prepare WhatsApp join links for student, mother, and father (same message for all)
    student_link, parent_link = get_whatsapp_group_links(student)
    transport_links = get_transport_group_links(student)

    wa_links = {}

    join_message = get_join_message(student, student_link, parent_link)

    # Student WhatsApp link
    wa_links['student'] = generate_wa_me_link(
        '91' + str(student.user.phone),
        join_message
    )

    # Mother WhatsApp link
    mother_phone = getattr(getattr(student, "parent_details", None), "mother_contact", None)
    if mother_phone:
        wa_links['mother'] = generate_wa_me_link(
            '91' + str(mother_phone),
            join_message
        )

    # Father WhatsApp link
    father_phone = getattr(getattr(student, "parent_details", None), "father_contact", None)
    if father_phone:
        wa_links['father'] = generate_wa_me_link(
            '91' + str(father_phone),
            join_message
        )

    # Optionally add transport group links for student (separate message for transport)
    wa_links['transport'] = []
    for link in transport_links:
        wa_links['transport'].append(
            generate_wa_me_link(
                '91' + str(student.user.phone),
                f"Dear Parent,\n\nJoin the official transport WhatsApp group for updates:\n{link}\n\n- BASU Classes"
            )
        )


    return render(request, "registration/student_update.html", {
        'student': student,
        'classes': classes, 
        'subjects': subjects,
        'batches': batches,
        'wa_links': wa_links,
    })

@login_required(login_url='login')
def student_enrollment_update(request, stu_id):
    student = Student.objects.filter(stu_id=stu_id).first()

    if not student:
        messages.error(request, 'Invalid Student Id.')
        return redirect('student_registration')

    sessions = AcademicSession.objects.all().order_by('-start_date')
    active_session = AcademicSession.get_active()

    selected_session_id = (
        request.GET.get('session')
        or request.GET.get('academic-session')
        or request.POST.get('session')
        or request.POST.get('academic-session')
    )
    selected_session = None

    if selected_session_id:
        selected_session = AcademicSession.objects.filter(id=selected_session_id).first()
    if not selected_session:
        selected_session = active_session

    if not selected_session:
        messages.error(request, 'No academic session selected and no active session found.')
        return redirect('students_enrollment_list')

    enrollment = (
        StudentEnrollment.objects.filter(student=student, session=selected_session)
        .prefetch_related('subjects')
        .first()
    )

    batches = (
        Batch.objects.filter(session=selected_session)
        .select_related('class_name', 'subject', 'section')
        .order_by('class_name__name', 'subject__name', 'section__name')
    )

    selected_batch_ids = []
    if enrollment:
        selected_batch_ids = list(
            EnrollmentBatch.objects.filter(enrollment=enrollment).values_list('batch_id', flat=True)
        )
    
    if request.method == 'POST':
        class_id = request.POST.get('class_name')
        class_name = ClassName.objects.filter(id=class_id).first() if class_id else None

        if not class_name:
            messages.error(request, 'Please select a class.')
            return redirect(f"{reverse('student_enrollment_update', args=[student.stu_id])}?session={selected_session.id}")

        if enrollment is None:
            enrollment = StudentEnrollment(student=student, session=selected_session)

        enrollment.class_name = class_name
        enrollment.course = request.POST.get('course') or None
        enrollment.program_duration = request.POST.get('program_duration') or enrollment.program_duration
        enrollment.active = request.POST.get('active') == 'Active'
        enrollment.save()

        subject_ids_raw = request.POST.getlist('subjects[]') or request.POST.getlist('subjects')
        subject_ids = [int(s) for s in subject_ids_raw if str(s).isdigit()]
        enrollment.subjects.set(subject_ids)

        eligible_batch_ids = set(
            Batch.objects.filter(
                class_name=class_name,
                subject_id__in=subject_ids,
                session=selected_session,
            ).values_list('id', flat=True)
        )

        # Save enrollment->batch links
        batch_ids = [int(b) for b in request.POST.getlist('batches[]') if str(b).isdigit() and int(b) in eligible_batch_ids]
        with transaction.atomic():
            EnrollmentBatch.objects.filter(enrollment=enrollment).exclude(batch_id__in=batch_ids).delete()
            existing_ids = set(
                EnrollmentBatch.objects.filter(enrollment=enrollment, batch_id__in=batch_ids).values_list('batch_id', flat=True)
            )
            to_create = [
                EnrollmentBatch(enrollment=enrollment, batch_id=batch_id)
                for batch_id in batch_ids
                if batch_id not in existing_ids
            ]
            if to_create:
                EnrollmentBatch.objects.bulk_create(to_create)

        messages.success(request, 'Enrollment updated.')
        return redirect(f"{reverse('student_enrollment_update', args=[student.stu_id])}?session={selected_session.id}")
    
    classes = ClassName.objects.all().order_by('-name')
    subjects = Subject.objects.all().order_by('name')
    if enrollment:
        selected_subject_ids = list(enrollment.subjects.values_list('id', flat=True))
    else:
        selected_subject_ids = list(student.subjects.values_list('id', flat=True))

    return render(request, "registration/enrollment/student_enrollment_update.html", {
        'student': student,
        'enrollment': enrollment,
        'classes': classes,
        'subjects': subjects,
        'selected_subject_ids': selected_subject_ids,
        'batches': batches,
        'selected_batch_ids': selected_batch_ids,
        'academic_sessions': sessions,
        'active_session': active_session,
        'selected_session': selected_session,
    })

@login_required(login_url='login')
def student_enrollment_details_update(request, stu_id):
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
            "batches": request.POST.getlist("batches[]"),  # ManyToMany field
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

    # # WhatsApp group links mapping by class and type
    # WHATSAPP_GROUP_LINKS = {
    #     "7": {
    #         "student": "https://chat.whatsapp.com/CODPG4w7eFX43VQpOi6BnD",
    #         "parent": "https://chat.whatsapp.com/Hi0U7fSFFwbGNlfinyCZII",
    #     },
    #     "8": {
    #         "student": "https://chat.whatsapp.com/H2xTY2qpUOb5EXut75iNwV",
    #         "parent": "https://chat.whatsapp.com/CGsBhqddvtI5BNKwzXm2wC",
    #     },
    #     "9": {
    #         "student": "https://chat.whatsapp.com/BasrRWXoC3x88lyXrvctEU",
    #         "parent": "https://chat.whatsapp.com/IOj2m12EWZI3fp9rEjF01x",
    #     },
    #     "10": {
    #         "student": "https://chat.whatsapp.com/L0zF6dVCBDNEF1eGEBR1Wg",
    #         "parent": "https://chat.whatsapp.com/Lb7Q1Xq1YBz9J2ZfcbK5dC",
    #     },
    #     "11_PCM": {
    #         "student": "https://chat.whatsapp.com/JdbjvZ55nwKDREkmsw2GMD",
    #         "parent": "https://chat.whatsapp.com/IbQTtuqBQIALABUPcE688G",
    #     },
    #     "11_COMMERCE": {
    #         "student": "https://chat.whatsapp.com/GruyEBmP0dZ0WOADZlEeic",
    #         "parent": "https://chat.whatsapp.com/I6bm2asTs9T4KJEJvKgMCL",
    #     },
    #     "12_PCM": {
    #         "student": "https://chat.whatsapp.com/IsveJm0QuCT9IM9Y93vZ6s",
    #         "parent": "https://chat.whatsapp.com/B7wsZHE4oDHDmpvC0UB1YH",
    #     },
    #     "12_COMMERCE": {
    #         "student": "https://chat.whatsapp.com/Esgz3orRZuLEkyQB9iJ3Va",
    #         "parent": "https://chat.whatsapp.com/ByZk2Dnu0el5WGanR4SZcB",
    #     },
    #     "transport_erikshaw": "https://chat.whatsapp.com/Hea0v2pn5NzDdZdzCeE4mL",
    #     "transport_cab": "https://chat.whatsapp.com/IvSYxCyANmFL7QjzuHljGF",
    # }

    # def get_class_group_key(student):
    #     cls = student.class_enrolled.name.upper() if student.class_enrolled else ""
    #     if "11" in cls:
    #         if "COMMERCE" in cls:
    #             return "11_COMMERCE"
    #         return "11_PCM"
    #     if "12" in cls:
    #         if "COMMERCE" in cls:
    #             return "12_COMMERCE"
    #         return "12_PCM"
    #     for num in ["7", "8", "9", "10"]:
    #         if num in cls:
    #             return num
    #     return None

    # def get_whatsapp_group_links(student):
    #     group_key = get_class_group_key(student)
    #     student_link = parent_link = None
    #     if group_key and group_key in WHATSAPP_GROUP_LINKS:
    #         student_link = WHATSAPP_GROUP_LINKS[group_key].get("student")
    #         parent_link = WHATSAPP_GROUP_LINKS[group_key].get("parent")
    #     return student_link, parent_link

    # def get_transport_group_links(student):
    #     links = []
    #     if getattr(student, "transport", None):
    #         mode = getattr(student.transport, "mode", None)
    #         if mode and hasattr(mode, "name"):
    #             mode_name = mode.name.lower()
    #             if "rikshaw" in mode_name:
    #                 links.append(WHATSAPP_GROUP_LINKS.get("transport_erikshaw"))
    #             if "cab" in mode_name:
    #                 links.append(WHATSAPP_GROUP_LINKS.get("transport_cab"))
    #     return [l for l in links if l]

    # def generate_wa_me_link(phone, message):
    #     import urllib.parse
    #     return f"https://wa.me/{phone}?text={urllib.parse.quote(message)}"

    # # Compose the join message for WhatsApp with both group links (both links are always included)
    # def get_join_message(student, student_link, parent_link):
    #     class_name = student.class_enrolled.name if student.class_enrolled else ""
    #     message = (
    #         "Dear Parent,\n\n"
    #         "We're excited to begin the 2025-26 session!\n\n"
    #         "Thank you for your continued support. This year, we've made key improvements and new strategies to boost student results.\n\n"
    #         f"👇 Join the official WhatsApp groups for updates:\n\n"
    #     )
    #     # Always include both links, even if one is missing (show as N/A if not found)
    #     message += f"{class_name} Students Group\n{student_link or 'N/A'}\n\n"
    #     message += f"{class_name} Parents Group\n{parent_link or 'N/A'}\n\n"
    #     message += (
    #         "Feel free to reach out for any queries. We're here to help!\n\n"
    #         "- BASU Classes"
    #     )
    #     return message

    # # Prepare WhatsApp join links for student, mother, and father (same message for all)
    # student_link, parent_link = get_whatsapp_group_links(student)
    # transport_links = get_transport_group_links(student)

    # wa_links = {}

    # join_message = get_join_message(student, student_link, parent_link)

    # # Student WhatsApp link
    # wa_links['student'] = generate_wa_me_link(
    #     '91' + str(student.user.phone),
    #     join_message
    # )

    # # Mother WhatsApp link
    # mother_phone = getattr(getattr(student, "parent_details", None), "mother_contact", None)
    # if mother_phone:
    #     wa_links['mother'] = generate_wa_me_link(
    #         '91' + str(mother_phone),
    #         join_message
    #     )

    # # Father WhatsApp link
    # father_phone = getattr(getattr(student, "parent_details", None), "father_contact", None)
    # if father_phone:
    #     wa_links['father'] = generate_wa_me_link(
    #         '91' + str(father_phone),
    #         join_message
    #     )

    # # Optionally add transport group links for student (separate message for transport)
    # wa_links['transport'] = []
    # for link in transport_links:
    #     wa_links['transport'].append(
    #         generate_wa_me_link(
    #             '91' + str(student.user.phone),
    #             f"Dear Parent,\n\nJoin the official transport WhatsApp group for updates:\n{link}\n\n- BASU Classes"
    #         )
    #     )


    return render(request, "registration/enrollment/student_details_update.html", {
        'student': student,
        'classes': classes, 
        'subjects': subjects,
        'batches': batches,
        # 'wa_links': wa_links,
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
def students_enrollment_list(request):
    sessions = AcademicSession.objects.all().order_by('-start_date')
    active_session = AcademicSession.get_active()

    selected_session_id = request.GET.get('session')
    selected_session = None
    
    if selected_session_id:
        selected_session = AcademicSession.objects.filter(id=selected_session_id).first()
    if not selected_session:
        selected_session = active_session

    classes = ClassName.objects.all().order_by('-created_at')
    class_students = []
    for cls in classes:
        students_qs = StudentEnrollment.objects.filter(
            session=selected_session,
            class_name=cls,
        ).order_by('-created_at', 'student__user__first_name', 'student__user__last_name').distinct()
        class_students.append({'class': cls.name, 'students': students_qs})

    count = StudentEnrollment.objects.filter(active=True, student__active=True, session=selected_session).distinct().count()

    return render(request, "registration/enrollment/students_enrollment_list.html", {
        'class_students': class_students,
        'count': count,
        'academic_sessions': sessions,
        'selected_session': selected_session,
    })

@login_required(login_url='login')
def student_enrollment_parent_details(request, stu_id):

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
    return render(request, "registration/enrollment/student_parent_details.html", {
        "student": student,
        "form": form_data,
        "parent_details": parent_details
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
def student_enrollment_fees_details(request, stu_id):
    student = Student.objects.filter(stu_id=stu_id).first()
    if not student:
        messages.error(request, "Invalid Student")
        return redirect('student_registration')

    sessions = AcademicSession.objects.all().order_by('-start_date')
    active_session = AcademicSession.get_active()

    selected_session_id = (
        request.GET.get('session')
        or request.GET.get('academic-session')
        or request.POST.get('session')
        or request.POST.get('academic-session')
    )
    selected_session = None

    if selected_session_id:
        selected_session = AcademicSession.objects.filter(id=selected_session_id).first()
    if not selected_session:
        selected_session = active_session

    if not selected_session:
        messages.error(request, 'No academic session selected and no active session found.')
        return redirect('students_enrollment_list')

    enrollment = StudentEnrollment.objects.filter(student=student, session=selected_session).first()
    if not enrollment:
        messages.error(request, 'No enrollment found for the selected session. Please create/update enrollment first.')
        return redirect(f"{reverse('student_enrollment_update', args=[student.stu_id])}?session={selected_session.id}")

    fees_details, _ = FeeDetails.objects.get_or_create(student=student)
    if fees_details.enrollment_id != enrollment.id:
        fees_details.enrollment = enrollment
        fees_details.save(update_fields=['enrollment'])

    if request.method == 'POST':

        try:
            with transaction.atomic():
                fees_details, created = FeeDetails.objects.get_or_create(student=student)
                if fees_details.enrollment_id != enrollment.id:
                    fees_details.enrollment = enrollment

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
                Installment.objects.filter(fee_details=fees_details, enrollment=enrollment).delete()

                for ins in range(1, int(request.POST.get("num_installments") or 1) + 1):
                    installment = Installment(
                        fee_details=fees_details,
                        student=student,
                        enrollment=enrollment,
                        amount=request.POST.get(f'installment_amount_{ins}'),
                        due_date=request.POST.get(f'installment_due_date_{ins}'),
                        paid=(request.POST.get(f'paid_{ins}') == 'on') ,
                        label = request.POST.get(f'installment_label_{ins}'),
                        payment_type = request.POST.get(f'payment_type_{ins}'),
                        remark = request.POST.get(f'installment_remark_{ins}'),
                    )
                    installment.save()
        except Exception as e:
            messages.error(request, "Invalid Data or form.")
            return redirect(f"{reverse('student_enrollment_fees_details', args=[student.stu_id])}?session={selected_session.id}")

        messages.success(request, 'Fee details saved.')
        return redirect(f"{reverse('student_enrollment_fees_details', args=[student.stu_id])}?session={selected_session.id}")

    payment_options = Installment.PAYMENT_CHOICES

    installments = Installment.objects.filter(fee_details=fees_details, enrollment=enrollment).order_by('due_date')

    return render(request, "registration/enrollment/student_enrollment_fees_details.html", {
        'student': student,
        'fees_details': fees_details,
        'installments': installments,
        'installments_count': installments.count(),
        'payment_options': payment_options,
        'academic_sessions': sessions,
        'active_session': active_session,
        'selected_session': selected_session,
    })


@login_required(login_url='login')
def student_enrollment_reg_doc(request, stu_id):
    student = Student.objects.filter(stu_id=stu_id).first()
    if not student:
        messages.error(request, "Invalid Student")
        return redirect('student_registration')

    sessions = AcademicSession.objects.all().order_by('-start_date')
    active_session = AcademicSession.get_active()

    selected_session_id = (
        request.GET.get('session')
        or request.GET.get('academic-session')
        or request.POST.get('session')
        or request.POST.get('academic-session')
    )
    selected_session = None

    if selected_session_id:
        selected_session = AcademicSession.objects.filter(id=selected_session_id).first()
    if not selected_session:
        selected_session = active_session

    if not selected_session:
        messages.error(request, 'No academic session selected and no active session found.')
        return redirect('students_enrollment_list')

    enrollment = StudentEnrollment.objects.filter(student=student, session=selected_session).first()
    if not enrollment:
        messages.error(request, 'No enrollment found for the selected session. Please create/update enrollment first.')
        return redirect(f"{reverse('student_enrollment_update', args=[student.stu_id])}?session={selected_session.id}")

    fees_details = FeeDetails.objects.filter(enrollment=enrollment).first()
    installments = Installment.objects.none()
    total_discount = 0
    total_fees = 0

    if fees_details:
        total_discount = (
            (fees_details.discount or 0)
            + ((fees_details.book_fees or 0) if fees_details.book_discount else 0)
            + ((fees_details.registration_fee or 0) if fees_details.registration_discount else 0)
        )

        total_fees = (fees_details.total_fees or 0) + (fees_details.discount or 0)
        if fees_details.book_discount:
            total_fees += (fees_details.book_fees or 0)
        if fees_details.registration_discount:
            total_fees += (fees_details.registration_fee or 0)

        installments = Installment.objects.filter(fee_details=fees_details, enrollment=enrollment).order_by('due_date')

    transport_details = TransportDetails.objects.filter(enrollment=enrollment).first()

    return render(request, "registration/enrollment/student_enrollment_reg_doc.html", {
        'student': student,
        'enrollment': enrollment,
        'fees_details': fees_details,
        'installments': installments,
        'transport_details': transport_details,
        'total_discount': total_discount,
        'total_fees': total_fees,
        'academic_sessions': sessions,
        'active_session': active_session,
        'selected_session': selected_session,
    })

@login_required(login_url = 'login')
def student_fees_details(request, stu_id):
    student = Student.objects.filter(stu_id=stu_id).first()
    if not student:
        messages.error(request, "Invalid Student")
        return redirect('student_registration')

    fees_details = FeeDetails.objects.filter(student__stu_id=stu_id).first()

    if request.method == 'POST':

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
                        payment_type = request.POST.get(f'payment_type_{ins}'),
                        remark = request.POST.get(f'installment_remark_{ins}'),
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
    if not instance:
        return render(request, "registration/student_transport_details.html", {
            'form': form,
            'student': student,
        })
    WEEKDAYS = Day.objects.all()
    batch_timings_by_weekday = {}
    slots = []
    min_slot_time = None
    max_slot_time = None

    for day in WEEKDAYS:
        batches_by_day = student.batches.filter(days=day)
        if not batches_by_day:
            continue
        earliest = min(batches_by_day, key=lambda b: datetime.strptime(b.start_time, "%I:%M %p").time())
        latest = max(batches_by_day, key=lambda b: datetime.strptime(b.end_time, "%I:%M %p").time())
        
        if min_slot_time is None:
            min_slot_time = earliest.start_time
        else:
            min_slot_time = min([min_slot_time, earliest.start_time], key=lambda time: datetime.strptime(time, "%I:%M %p").time())
        if max_slot_time is None:
            max_slot_time = latest.end_time
        else:
            max_slot_time = max([max_slot_time, latest.end_time], key=lambda time: datetime.strptime(time, "%I:%M %p").time())
        

        driver_capacity = None
        assigned_driver = getattr(student.transport, "transport_person", None)
        if assigned_driver and hasattr(assigned_driver, "capacity"):
            driver_capacity = assigned_driver.capacity
            
            students_qs = Student.objects.filter(
                transport__transport_person=assigned_driver,
                active=True,
                fees__cab_fees__gt=0,
                batches__days=day,
            ).distinct()
            # Calculate pickup (earliest) and drop (latest) counts separately
            pickup_count = 0
            drop_count = 0
            pickup_status = "0"
            drop_status = "0"

            if earliest and earliest.start_time:
                pickup_students_qs = []
                for other_student in students_qs:
                    batches_on_day = other_student.batches.filter(days=day)
                    if batches_on_day:
                        first_batch = min(batches_on_day, key=lambda b: datetime.strptime(b.start_time, "%I:%M %p"))
                        if first_batch.start_time == earliest.start_time:
                            pickup_students_qs.append(other_student)

                pickup_count = len(pickup_students_qs)

            if latest and latest.end_time:
                drop_students_qs = students_qs.filter(batches__end_time=latest.end_time).distinct()
                drop_count = drop_students_qs.count()
            
                drop_students_qs = []
                for other_student in students_qs:
                    batches_on_day = other_student.batches.filter(days=day)
                    if batches_on_day:
                        last_batch = max(batches_on_day, key=lambda b: datetime.strptime(b.end_time, "%I:%M %p"))
                        if last_batch.end_time == earliest.end_time:
                            drop_students_qs.append(other_student)
                drop_count = len(drop_students_qs)


            if driver_capacity is not None:
                pickup_diff = driver_capacity - pickup_count
                drop_diff = driver_capacity - drop_count

                pickup_status = {
                    'diff': pickup_diff,  # keep raw number
                    'display': f"{'+' if pickup_diff < 0 else '-'}{abs(pickup_diff)}"
                }
                drop_status = {
                    'diff': drop_diff,
                    'display': f"{'+' if drop_diff < 0 else '-'}{abs(drop_diff)}"
                }

            driver_status = {
                "pickup": pickup_status,
                "pickup_count": pickup_count,
                "drop": drop_status,
                "drop_count": drop_count,
                "capacity": driver_capacity,
            }
        else:
            driver_status = None

        batch_timings_by_weekday[day.name] = {
            'earliest_start': earliest.start_time if earliest else None,
            'latest_end': latest.end_time if latest else None,
            'driver_capacity': driver_capacity,
            'driver_status': driver_status,
        }

    # Generate 15-minute time slots with a 15-minute buffer before and after
    if min_slot_time and max_slot_time:
        start_dt = datetime.combine(datetime.today(), datetime.strptime(min_slot_time, "%I:%M %p").time()) - timedelta(minutes=30)
        end_dt = datetime.combine(datetime.today(), datetime.strptime(max_slot_time, "%I:%M %p").time()) + timedelta(minutes=30)
        slots = []
        current_time = start_dt
        while current_time <= end_dt:
            slots.append(current_time.strftime("%I:%M %p"))
            current_time += timedelta(minutes=30)

    return render(request, "registration/student_transport_details.html", {
        'form': form,
        'student': student,
        'time_slots': slots,
        'batch_timings': batch_timings_by_weekday,
        'weekdays': WEEKDAYS,
    })

@login_required(login_url='login')
def student_enrollment_transport_details(request, stu_id):
    student = Student.objects.filter(stu_id=stu_id).first()
    if not student:
        messages.error(request, "Invalid Student")
        return redirect('student_registration')

    sessions = AcademicSession.objects.all().order_by('-start_date')
    active_session = AcademicSession.get_active()

    selected_session_id = (
        request.GET.get('session')
        or request.GET.get('academic-session')
        or request.POST.get('session')
        or request.POST.get('academic-session')
    )
    selected_session = None

    if selected_session_id:
        selected_session = AcademicSession.objects.filter(id=selected_session_id).first()
    if not selected_session:
        selected_session = active_session

    if not selected_session:
        messages.error(request, 'No academic session selected and no active session found.')
        return redirect('students_enrollment_list')

    enrollment = StudentEnrollment.objects.filter(student=student, session=selected_session).first()

    instance = getattr(student, 'transport', None)

    if request.method == "POST":
        form = TransportDetailsForm(request.POST, instance=instance)
        if form.is_valid():
            transport = form.save(commit=False)
            transport.student = student
            transport.save()
            messages.success(request, "Transport details saved.")
            return redirect(f"{reverse('student_enrollment_transport_details', args=[student.stu_id])}?session={selected_session.id}")
        else:
            for field, error_list in form.errors.items():
                for error in error_list:
                    messages.error(request, f"{field}: {error}")
    else:
        form = TransportDetailsForm(instance=instance)
    if not instance:
        return render(request, "registration/enrollment/student_enrollment_transport_details.html", {
            'form': form,
            'student': student,
            'academic_sessions': sessions,
            'active_session': active_session,
            'selected_session': selected_session,
        })
    WEEKDAYS = Day.objects.all()
    batch_timings_by_weekday = {}
    slots = []
    min_slot_time = None
    max_slot_time = None

    enrollment_batches = Batch.objects.none()
    if enrollment:
        enrollment_batches = Batch.objects.filter(enrollment_links__enrollment=enrollment).distinct()

    for day in WEEKDAYS:
        batches_by_day = enrollment_batches.filter(days=day)
        if not batches_by_day.exists():
            continue

        batches_by_day_with_times = [b for b in batches_by_day if b.start_time and b.end_time]
        if not batches_by_day_with_times:
            continue

        earliest = min(batches_by_day_with_times, key=lambda b: datetime.strptime(b.start_time, "%I:%M %p").time())
        latest = max(batches_by_day_with_times, key=lambda b: datetime.strptime(b.end_time, "%I:%M %p").time())
        
        if min_slot_time is None:
            min_slot_time = earliest.start_time
        else:
            min_slot_time = min([min_slot_time, earliest.start_time], key=lambda time: datetime.strptime(time, "%I:%M %p").time())
        if max_slot_time is None:
            max_slot_time = latest.end_time
        else:
            max_slot_time = max([max_slot_time, latest.end_time], key=lambda time: datetime.strptime(time, "%I:%M %p").time())
        

        driver_capacity = None
        assigned_driver = getattr(student.transport, "transport_person", None)
        if assigned_driver and hasattr(assigned_driver, "capacity"):
            driver_capacity = assigned_driver.capacity

            students_qs = Student.objects.filter(
                transport__transport_person=assigned_driver,
                active=True,
                fees__cab_fees__gt=0,
                enrollments__session=selected_session,
                enrollments__active=True,
                enrollments__batch_links__batch__days=day,
            ).distinct()
            # Calculate pickup (earliest) and drop (latest) counts separately
            pickup_count = 0
            drop_count = 0
            pickup_status = "0"
            drop_status = "0"

            if earliest and earliest.start_time:
                pickup_students_qs = []
                for other_student in students_qs:
                    other_enrollment = StudentEnrollment.objects.filter(
                        student=other_student,
                        session=selected_session,
                        active=True,
                    ).first()
                    if not other_enrollment:
                        continue

                    batches_on_day = Batch.objects.filter(
                        enrollment_links__enrollment=other_enrollment,
                        days=day,
                    ).exclude(start_time__isnull=True).exclude(start_time="")

                    if batches_on_day.exists():
                        first_batch = min(batches_on_day, key=lambda b: datetime.strptime(b.start_time, "%I:%M %p"))
                        if first_batch.start_time == earliest.start_time:
                            pickup_students_qs.append(other_student)

                pickup_count = len(pickup_students_qs)

            if latest and latest.end_time:
                drop_students_qs = []
                for other_student in students_qs:
                    other_enrollment = StudentEnrollment.objects.filter(
                        student=other_student,
                        session=selected_session,
                        active=True,
                    ).first()
                    if not other_enrollment:
                        continue

                    batches_on_day = Batch.objects.filter(
                        enrollment_links__enrollment=other_enrollment,
                        days=day,
                    ).exclude(end_time__isnull=True).exclude(end_time="")

                    if batches_on_day.exists():
                        last_batch = max(batches_on_day, key=lambda b: datetime.strptime(b.end_time, "%I:%M %p"))
                        if last_batch.end_time == latest.end_time:
                            drop_students_qs.append(other_student)
                drop_count = len(drop_students_qs)


            if driver_capacity is not None:
                pickup_diff = driver_capacity - pickup_count
                drop_diff = driver_capacity - drop_count

                pickup_status = {
                    'diff': pickup_diff,  # keep raw number
                    'display': f"{'+' if pickup_diff < 0 else '-'}{abs(pickup_diff)}"
                }
                drop_status = {
                    'diff': drop_diff,
                    'display': f"{'+' if drop_diff < 0 else '-'}{abs(drop_diff)}"
                }

            driver_status = {
                "pickup": pickup_status,
                "pickup_count": pickup_count,
                "drop": drop_status,
                "drop_count": drop_count,
                "capacity": driver_capacity,
            }
        else:
            driver_status = None

        batch_timings_by_weekday[day.name] = {
            'earliest_start': earliest.start_time if earliest else None,
            'latest_end': latest.end_time if latest else None,
            'driver_capacity': driver_capacity,
            'driver_status': driver_status,
        }

    # Generate 15-minute time slots with a 15-minute buffer before and after
    if min_slot_time and max_slot_time:
        start_dt = datetime.combine(datetime.today(), datetime.strptime(min_slot_time, "%I:%M %p").time()) - timedelta(minutes=30)
        end_dt = datetime.combine(datetime.today(), datetime.strptime(max_slot_time, "%I:%M %p").time()) + timedelta(minutes=30)
        slots = []
        current_time = start_dt
        while current_time <= end_dt:
            slots.append(current_time.strftime("%I:%M %p"))
            current_time += timedelta(minutes=30)

    return render(request, "registration/enrollment/student_enrollment_transport_details.html", {
        'form': form,
        'student': student,
        'time_slots': slots,
        'batch_timings': batch_timings_by_weekday,
        'weekdays': WEEKDAYS,
        'academic_sessions': sessions,
        'active_session': active_session,
        'selected_session': selected_session,
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
def print_enrollment_receipt(request, stu_id):
    student = Student.objects.filter(stu_id=stu_id).first()
    if not student:
        messages.error(request, "Invalid Student")
        return redirect('student_registration')

    sessions = AcademicSession.objects.all().order_by('-start_date')
    active_session = AcademicSession.get_active()

    selected_session_id = (
        request.GET.get('session')
        or request.GET.get('academic-session')
        or request.POST.get('session')
        or request.POST.get('academic-session')
    )
    selected_session = None

    if selected_session_id:
        selected_session = AcademicSession.objects.filter(id=selected_session_id).first()
    if not selected_session:
        selected_session = active_session

    if not selected_session:
        messages.error(request, 'No academic session selected and no active session found.')
        return redirect('students_enrollment_list')

    enrollment = StudentEnrollment.objects.filter(student=student, session=selected_session).first()
    if not enrollment:
        messages.error(request, 'No enrollment found for the selected session. Please create/update enrollment first.')
        return redirect(f"{reverse('student_enrollment_update', args=[student.stu_id])}?session={selected_session.id}")

    fees_details = FeeDetails.objects.filter(enrollment=enrollment).first()
    installments = Installment.objects.none()
    if fees_details:
        installments = Installment.objects.filter(
            fee_details=fees_details,
            enrollment=enrollment,
        ).order_by('due_date')

    return render(request, "registration/enrollment/enrollment_receipt.html", {
        'student': student,
        'enrollment': enrollment,
        'fees_details': fees_details,
        'installments': installments,
        'today': datetime.now(),
        'academic_sessions': sessions,
        'active_session': active_session,
        'selected_session': selected_session,
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
        ).select_related('user')
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
def mark_attendance(request, class_id=None, batch_id=None):
    cls = None
    batch = None
    lesson_info = None

    sessions = AcademicSession.objects.all().order_by('-start_date')
    active_session = AcademicSession.get_active()

    selected_session_id = (
        request.GET.get('session')
        or request.GET.get('academic-session')
        or request.POST.get('session')
        or request.POST.get('academic-session')
    )
    selected_session = None

    if selected_session_id:
        selected_session = AcademicSession.objects.filter(id=selected_session_id).first()
    if not selected_session:
        selected_session = active_session

    if class_id and not ClassName.objects.filter(id=class_id).exists():
        messages.error(request, "Invalid Class")
        return redirect('attendance')

    if batch_id and not Batch.objects.filter(id=batch_id).exists():
        messages.error(request, "Invalid Batch")
        return redirect('attendance_class', class_id=class_id)

    if class_id:
        cls = ClassName.objects.filter(id=class_id).first()
        batches_qs = Batch.objects.filter(class_name=cls)
        if selected_session:
            batches_qs = batches_qs.filter(session=selected_session)

        batches = batches_qs.order_by('created_at').exclude(
            Q(class_name__name__in=['CLASS 9', 'CLASS 10']) &
            Q(section__name='CBSE') &
            Q(subject__name__in=['MATH', 'SCIENCE'])
        )
    else:
        batches = None

    if batch_id:
        batch = Batch.objects.filter(id=batch_id).select_related('session').first()
        if batch and getattr(batch, 'session_id', None):
            selected_session = batch.session
    

    if batch_id and not batch:
        messages.error(request, "Invalid Batch")
        return redirect('attendance_class', class_id=class_id)

    # Handle date input
    date_str = request.GET.get("date")
    attendance_type = request.GET.get("type")

    attendance_type_choices = Attendance.ATTENDANCE_TYPE
    selected_type = attendance_type if attendance_type in dict(attendance_type_choices) else 'Regular'

    try:
        date = datetime.strptime(date_str, "%Y-%m-%d").date() if date_str else datetime.now().date()
    except ValueError:
        messages.error(request, "Invalid date format.")
        return redirect(f"{reverse('attendance_batch', args=[class_id, batch_id])}?date={datetime.now().date()}")

    # Compute previous and next dates
    prev_date = date - timedelta(days=1)
    next_date = date + timedelta(days=1)

    if not Teacher.objects.filter(user=request.user).exists() and not request.user.is_superuser:
        messages.error(request, "You are not authorized to mark attendance.")
        return redirect('students_list')

    classes = ClassName.objects.all().order_by('created_at')

    students = Student.objects.none()
    enrollments_by_student_id = {}
    if batch and selected_session:
        enrollments_qs = (
            StudentEnrollment.objects.filter(
                active=True,
                session=selected_session,
                batch_links__batch=batch,
            )
            .select_related('student')
            .only('id', 'student_id')
            .distinct()
        )
        enrollments_by_student_id = {e.student_id: e for e in enrollments_qs if e.student_id}
        if enrollments_by_student_id:
            students = Student.objects.filter(id__in=enrollments_by_student_id.keys()).distinct()

    marked_students = students.filter(
        attendance__date=date,
        attendance__batch=batch,
        attendance__type=selected_type
    ).order_by('created_at')
    marked_attendance = list(
        Attendance.objects.filter(
            batch=batch,
            date=date,
            type=selected_type,
            student__in=students,
        ).order_by('student__created_at')
    )
    un_marked_students = list(students.exclude(id__in=marked_students.values_list('id', flat=True)))
    
    if batch_id:
        all_lectures = Lecture.objects.filter(
            lesson__chapter_sequence__batch=batch
        ).select_related('lesson__chapter_sequence').order_by(
            'date',
            'lesson__chapter_sequence__sequence',
            'lesson__sequence'
        )

        if date == datetime.today().date():
            # Check if lecture already exists for today
            lecture_today = all_lectures.filter(date=date).first()
            previous_lecture = all_lectures.filter(date__lt=date).order_by('-date').first()

            # Get last completed lecture before today
            last_completed = all_lectures.filter(
                status='completed',
                date__lt=date
            ).order_by('-date').first()
            last_lesson = last_completed.lesson if last_completed else None
            next_lesson = last_lesson.next() if last_lesson else None

            if lecture_today:
                lesson_info = {
                    'previous_lecture': previous_lecture,
                    'lecture': lecture_today,
                    'editable': True,
                    'suggested_lesson': None,
                    'next_lesson': lecture_today.lesson.next() if lecture_today.lesson else None,
                }
            else:
                is_delayed = Lecture.objects.filter(lesson=next_lesson, status='pending').first()
                lesson_info = {
                    'previous_lecture': previous_lecture,
                    'lecture': None,
                    'editable': True,
                    'suggested_lesson': next_lesson,
                    'next_lesson': next_lesson.next() if next_lesson else None,
                    'is_delayed': is_delayed if True else False,
                }
        else:
            # For past/future dates (non-editable)
            lecture = all_lectures.filter(date=date).first()

            lesson_info = {
                'lecture': lecture,
                'editable': False,
                'suggested_lesson': None,
            }

    if batch_id and request.method == 'POST':
        attendance_data = request.POST.getlist('attendance[]')
        marked_students_set = set()
    
        status_data = request.POST.get('status', '')

        if status_data:
            parts = status_data.split(':')
            if len(parts) == 3:
                lecture_id, lesson_id, status = parts
            else:
                lecture_id = lesson_id = status = ""
            if status and status.isdigit() and date == datetime.today().date() and (selected_type == 'Regular' or selected_type == 'Extra Class'):
                status = int(status)
                if lecture_id:
                    try:
                        lecture = Lecture.objects.get(id=lecture_id)
                        lecture.status = 'completed' if status == 2 else 'pending'
                        lecture.save()
                    except Lecture.DoesNotExist:
                        messages.error(request, "Lecture doesn't exists.")
                        return redirect(f"{reverse('attendance_batch', args=[class_id, batch_id])}?date={date}")

                if lesson_id and not lecture_id:
                    try:
                        lesson = Lesson.objects.get(id=lesson_id)
                        lecture = Lecture.objects.create(
                            lesson=lesson,
                            date = date,
                            status = 'completed' if status == 2 else 'pending'
                        )
                        lecture.save()

                    except Lesson.DoesNotExist:
                        messages.error(request, "Lesson doesn't exists.")
                        return redirect(f"{reverse('attendance_batch', args=[class_id, batch_id])}?date={date}")

        for data in attendance_data:
            try:
                stu_id, status = data.split(':', 1)
            except ValueError:
                continue

            if status not in ('2', '3'):
                continue

            student = students.filter(stu_id=stu_id).first()
            if not student:
                continue

            enrollment = enrollments_by_student_id.get(student.id)

            Attendance.objects.update_or_create(
                student=student,
                batch=batch,
                date=date,
                type=selected_type,
                defaults={
                    'is_present': (status == '2'),
                    'enrollment': enrollment,
                }
            )
            marked_students_set.add(student.stu_id)

        messages.success(request, "Attendance marked successfully.")
        redirect_url = f"{reverse('attendance_batch', args=[class_id, batch_id])}?date={date}&type={selected_type}"
        if selected_session:
            redirect_url += f"&session={selected_session.id}"
        return redirect(redirect_url)

    return render(request, 'registration/attendance.html', {
        'classes': classes,
        'batches': batches,
        'cls': cls,
        'batch': batch,
        'marked_attendance': marked_attendance,
        'marked_students': marked_students,
        'un_marked_students': un_marked_students,
        'date': date,
        'prev_date': prev_date,
        'next_date': next_date,
        'lesson_info': lesson_info,
        'academic_sessions': sessions,
        'active_session': active_session,
        'selected_session': selected_session,
        'type_choices': attendance_type_choices,
        'selected_type': selected_type,
    })


@login_required(login_url='login')
def mark_homework(request, class_id=None, batch_id=None):
    cls = None
    batch = None

    sessions = AcademicSession.objects.all().order_by('-start_date')
    active_session = AcademicSession.get_active()

    selected_session_id = (
        request.GET.get('session')
        or request.GET.get('academic-session')
        or request.POST.get('session')
        or request.POST.get('academic-session')
    )
    selected_session = None

    if selected_session_id:
        selected_session = AcademicSession.objects.filter(id=selected_session_id).first()
    if not selected_session:
        selected_session = active_session

    if class_id and not ClassName.objects.filter(id=class_id).exists():
        messages.error(request, "Invalid Class")
        return redirect('homework')

    if batch_id and not Batch.objects.filter(id=batch_id).exists():
        messages.error(request, "Invalid Batch")
        return redirect('homework_class', class_id=class_id)

    if class_id:
        cls = ClassName.objects.filter(id=class_id).first()
        batches_qs = Batch.objects.filter(class_name=cls)
        if selected_session:
            batches_qs = batches_qs.filter(session=selected_session)

        batches = batches_qs.order_by('created_at').exclude(
            Q(class_name__name__in=['CLASS 9', 'CLASS 10']) &
            Q(section__name='CBSE') &
            Q(subject__name__in=['MATH', 'SCIENCE'])
        )
    else:
        batches = None


    if batch_id:
        batch = Batch.objects.filter(id=batch_id).select_related('session').first()
        if batch and getattr(batch, 'session_id', None):
            selected_session = batch.session

    if batch_id and not batch:
        messages.error(request, "Invalid Batch")
        return redirect('homework_class', class_id=class_id)

    # Handle date input
    date_str = request.GET.get("date")
    try:
        date = datetime.strptime(date_str, "%Y-%m-%d").date() if date_str else datetime.now().date()
    except ValueError:
        messages.error(request, "Invalid date format.")
        return redirect(f"{reverse('homework_batch', args=[class_id, batch_id])}?date={datetime.now().date()}")

    # Compute previous and next dates
    prev_date = date - timedelta(days=1)
    next_date = date + timedelta(days=1)

    if not Teacher.objects.filter(user=request.user).exists() and not request.user.is_superuser:
        messages.error(request, "You are not authorized to mark homework.")
        return redirect('students_list')

    classes = ClassName.objects.all().order_by('created_at')

    students = Student.objects.none()
    enrollments_by_student_id = {}
    if batch and selected_session:
        enrollments_qs = (
            StudentEnrollment.objects.filter(
                active=True,
                session=selected_session,
                batch_links__batch=batch,
            )
            .select_related('student')
            .only('id', 'student_id')
            .distinct()
        )
        enrollments_by_student_id = {e.student_id: e for e in enrollments_qs if e.student_id}
        if enrollments_by_student_id:
            students = Student.objects.filter(id__in=enrollments_by_student_id.keys()).distinct()

    marked_students = students.filter(homework__date=date, homework__batch=batch).order_by('created_at')
    marked_homework = list(
        Homework.objects.filter(
            batch=batch,
            date=date,
            student__in=students,
        ).order_by('student__created_at')
    )
    un_marked_students = list(students.exclude(id__in=marked_students.values_list('id', flat=True)))

    if batch_id and request.method == 'POST':
        attendance_data = request.POST.getlist('homework[]')
        marked_students_set = set()

        for data in attendance_data:
            try:
                stu_id, status = data.split(':', 1)
            except ValueError:
                continue

            student = students.filter(stu_id=stu_id).first()
            if not student:
                continue

            enrollment = enrollments_by_student_id.get(student.id)

            updated = Homework.objects.filter(
                student=student,
                batch=batch,
                date=date,
            ).update(
                status=status,
                enrollment=enrollment,
            )
            if updated == 0:
                Homework.objects.create(
                    student=student,
                    enrollment=enrollment,
                    batch=batch,
                    status=status,
                    date=date,
                )

            marked_students_set.add(student.stu_id)

        messages.success(request, "Homework marked successfully.")
        redirect_url = f"{reverse('homework_batch', args=[class_id, batch_id])}?date={date}"
        if selected_session:
            redirect_url += f"&session={selected_session.id}"
        return redirect(redirect_url)
    
    homework_status = Homework.STATUS_CHOICES

    return render(request, 'registration/homework.html', {
        'classes': classes,
        'batches': batches,
        'cls': cls,
        'batch': batch,
        'marked_homework': marked_homework,
        'marked_students': marked_students,
        'un_marked_students': un_marked_students,
        'date': date,
        'prev_date': prev_date,
        'next_date': next_date,
        'homework_status': homework_status,
        'academic_sessions': sessions,
        'active_session': active_session,
        'selected_session': selected_session,
    })

@login_required(login_url='login')
def update_homework(request, class_id, batch_id):
    
    if class_id and not ClassName.objects.filter(id=class_id).exists():
        messages.error(request, "Invalid Class")
        return redirect('homework')

    if batch_id and not Batch.objects.filter(id=batch_id).exists():
        messages.error(request, "Invalid Batch")
        return redirect('homework_class', class_id=class_id)

    sessions = AcademicSession.objects.all().order_by('-start_date')
    active_session = AcademicSession.get_active()

    selected_session_id = (
        request.GET.get('session')
        or request.GET.get('academic-session')
        or request.POST.get('session')
        or request.POST.get('academic-session')
    )
    selected_session = None
    if selected_session_id:
        selected_session = AcademicSession.objects.filter(id=selected_session_id).first()
    if not selected_session:
        selected_session = active_session

    if batch_id:
        batch = Batch.objects.filter(id=batch_id).select_related('session').first()
        if batch and getattr(batch, 'session_id', None):
            selected_session = batch.session

    if batch_id and not batch:
        messages.error(request, "Invalid Batch")
        return redirect('homework_class', class_id=class_id)

    if not Teacher.objects.filter(user=request.user).exists() and not request.user.is_superuser:
        messages.error(request, "You are not authorized to mark homework.")
        return redirect('students_list')
    
    date = datetime.now().date()

    if request.method == 'POST':
        homework_data = request.POST.getlist('homework[]')
        # Handle date input
        date_str = request.POST.get("date")
        try:
            date = datetime.strptime(date_str, "%Y-%m-%d").date() if date_str else datetime.now().date()
        except ValueError:
            messages.error(request, "Invalid date format.")
            redirect_url = f"{reverse('homework_batch', args=[class_id, batch_id])}?date={datetime.now().date()}"
            if selected_session:
                redirect_url += f"&session={selected_session.id}"
            return redirect(redirect_url)
        
        for data in homework_data:
            hw_id, status = data.split(':')
            homework_qs = Homework.objects.filter(id=int(hw_id), batch=batch, date=date)
            if selected_session:
                homework_qs = homework_qs.filter(Q(enrollment__session=selected_session) | Q(enrollment__isnull=True))
            homework = homework_qs.first()
            if homework:
                homework.status = status
                homework.save()
        messages.success(request, "Homework updated successfully.")
        redirect_url = f"{reverse('homework_batch', args=[class_id, batch_id])}?date={date}"
        if selected_session:
            redirect_url += f"&session={selected_session.id}"
        return redirect(redirect_url)

    redirect_url = f"{reverse('homework_batch', args=[class_id, batch_id])}?date={date}"
    if selected_session:
        redirect_url += f"&session={selected_session.id}"
    return redirect(redirect_url)


@login_required(login_url='login')
def mark_present(request, class_id, batch_id, attendance_id):
    day = request.GET.get('date')
    selected_type = request.GET.get('type')
    if not selected_type:
        messages.error(request, "Attendance type not specified.")
        return redirect(f"{reverse('attendance_batch', args=[class_id, batch_id])}?date={day}")

    active_session = AcademicSession.get_active()
    selected_session_id = request.GET.get('session') or request.GET.get('academic-session')
    selected_session = AcademicSession.objects.filter(id=selected_session_id).first() if selected_session_id else None

    batch = Batch.objects.filter(id=batch_id).select_related('session').first()
    if batch and getattr(batch, 'session_id', None):
        selected_session = batch.session
    if not selected_session:
        selected_session = active_session

    obj_qs = Attendance.objects.filter(id=attendance_id, batch_id=batch_id, type=selected_type)
    if selected_session:
        obj_qs = obj_qs.filter(Q(enrollment__session=selected_session) | Q(enrollment__isnull=True))
    obj = obj_qs.first()
    if not obj:
        messages.error(request, "Invalid Attendance Id.")
        redirect_url = f"{reverse('attendance_batch', args=[class_id, batch_id])}?type={selected_type}&date={day}"
        if selected_session:
            redirect_url += f"&session={selected_session.id}"
        return redirect(redirect_url)

    obj.is_present = True
    obj.save()
    redirect_url = f"{reverse('attendance_batch', args=[class_id, batch_id])}?type={selected_type}&date={day}"
    if selected_session:
        redirect_url += f"&session={selected_session.id}"
    return redirect(redirect_url)

@login_required(login_url='login')
def mark_absent(request, class_id, batch_id, attendance_id):
    day = request.GET.get('date')
    selected_type = request.GET.get('type')
    if not selected_type:
        messages.error(request, "Attendance type not specified.")
        return redirect(f"{reverse('attendance_batch', args=[class_id, batch_id])}?date={day}")

    active_session = AcademicSession.get_active()
    selected_session_id = request.GET.get('session') or request.GET.get('academic-session')
    selected_session = AcademicSession.objects.filter(id=selected_session_id).first() if selected_session_id else None

    batch = Batch.objects.filter(id=batch_id).select_related('session').first()
    if batch and getattr(batch, 'session_id', None):
        selected_session = batch.session
    if not selected_session:
        selected_session = active_session

    obj_qs = Attendance.objects.filter(id=attendance_id, batch_id=batch_id, type=selected_type)
    if selected_session:
        obj_qs = obj_qs.filter(Q(enrollment__session=selected_session) | Q(enrollment__isnull=True))
    obj = obj_qs.first()
    if not obj:
        messages.error(request, "Invalid Attendance Id.")
        redirect_url = f"{reverse('attendance_batch', args=[class_id, batch_id])}?type={selected_type}&date={day}"
        if selected_session:
            redirect_url += f"&session={selected_session.id}"
        return redirect(redirect_url)

    obj.is_present = False
    obj.save()
    redirect_url = f"{reverse('attendance_batch', args=[class_id, batch_id])}?type={selected_type}&date={day}"
    if selected_session:
        redirect_url += f"&session={selected_session.id}"
    return redirect(redirect_url)

@login_required(login_url='login')
def get_attendance(request, batch_id):
    if batch_id and not Batch.objects.filter(id=batch_id):
        messages.error(request, "Invalid Batch")
        return redirect('students_list')

    if not Teacher.objects.filter(user=request.user).exists():
        messages.error(request, "You are not authorized to view attendance.")
        return redirect('students_list')

    sessions = AcademicSession.objects.all().order_by('-start_date')
    active_session = AcademicSession.get_active()

    selected_session_id = (
        request.GET.get('session')
        or request.GET.get('academic-session')
        or request.POST.get('session')
        or request.POST.get('academic-session')
    )
    selected_session = None
    if selected_session_id:
        selected_session = AcademicSession.objects.filter(id=selected_session_id).first()
    if not selected_session:
        selected_session = active_session

    attendance_type = request.GET.get("type")

    attendance_type_choices = Attendance.ATTENDANCE_TYPE
    selected_type = attendance_type if attendance_type in dict(attendance_type_choices) else 'Regular'

    batch = Batch.objects.filter(id=batch_id).select_related('session').first()
    if batch and getattr(batch, 'session_id', None):
        selected_session = batch.session

    students = Student.objects.none()
    enrollments_by_student_id = {}
    if batch and selected_session:
        enrollments_qs = (
            StudentEnrollment.objects.filter(
                active=True,
                session=selected_session,
                batch_links__batch=batch,
            )
            .select_related('student')
            .only('id', 'student_id')
            .distinct()
        )
        enrollments_by_student_id = {e.student_id: e for e in enrollments_qs if e.student_id}
        if enrollments_by_student_id:
            students = Student.objects.filter(id__in=enrollments_by_student_id.keys()).order_by('stu_id').distinct()

    # Get attendance records for the batch
    attendance_records = Attendance.objects.filter(
        batch=batch,
        type=selected_type,
        enrollment__active=True,
        enrollment__session=selected_session,
        student__in=students,
    ).order_by('date', 'student__stu_id')

    # Organize attendance records by date and student
    attendance_by_date = defaultdict(dict)
    for record in attendance_records:
        date = record.date
        attendance_by_date[date][record.student.stu_id] = record.is_present

    # Generate a timeline of dates for the past 30 days
    today = datetime.now().date()
    start_date = today - timedelta(days=45)
    dates = [start_date + timedelta(days=i) for i in range(90)]

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
        'type_choices': attendance_type_choices,
        'selected_type': selected_type,
        'academic_sessions': sessions,
        'active_session': active_session,
        'selected_session': selected_session,
    })

@login_required(login_url='login')
def get_homework(request, batch_id):
    if batch_id and not Batch.objects.filter(id=batch_id):
        messages.error(request, "Invalid Batch")
        return redirect('students_list')

    if not Teacher.objects.filter(user=request.user).exists():
        messages.error(request, "You are not authorized to view homework.")
        return redirect('students_list')

    sessions = AcademicSession.objects.all().order_by('-start_date')
    active_session = AcademicSession.get_active()

    selected_session_id = (
        request.GET.get('session')
        or request.GET.get('academic-session')
        or request.POST.get('session')
        or request.POST.get('academic-session')
    )
    selected_session = None
    if selected_session_id:
        selected_session = AcademicSession.objects.filter(id=selected_session_id).first()
    if not selected_session:
        selected_session = active_session

    batch = Batch.objects.filter(id=batch_id).select_related('session').first()
    if batch and getattr(batch, 'session_id', None):
        selected_session = batch.session

    students = Student.objects.none()
    enrollments_by_student_id = {}
    if batch and selected_session:
        enrollments_qs = (
            StudentEnrollment.objects.filter(
                active=True,
                session=selected_session,
                batch_links__batch=batch,
            )
            .select_related('student')
            .only('id', 'student_id')
            .distinct()
        )
        enrollments_by_student_id = {e.student_id: e for e in enrollments_qs if e.student_id}
        if enrollments_by_student_id:
            students = Student.objects.filter(id__in=enrollments_by_student_id.keys()).order_by('stu_id').distinct()

    # Get homework records for the batch
    homework_records = Homework.objects.filter(
        batch=batch,
        enrollment__active=True,
        enrollment__session=selected_session,
        student__in=students,
    ).order_by('date', 'student__stu_id')

    # Organize homework records by date and student
    homework_by_date = defaultdict(dict)
    for record in homework_records:
        date = record.date
        homework_by_date[date][record.student.stu_id] = record.status

    # Generate a timeline of dates for the past 30 days
    today = datetime.now().date()
    start_date = today - timedelta(days=45)
    dates = [start_date + timedelta(days=i) for i in range(90)]

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
        'academic_sessions': sessions,
        'active_session': active_session,
        'selected_session': selected_session,
    })


@login_required(login_url='login')
def delete_attendance(request, class_id, batch_id, attendance_id):
    day = request.GET.get('date')
    selected_type = request.GET.get('type')
    if not selected_type:
        messages.error(request, "Attendance type not specified.")
        return redirect(f"{reverse('attendance_batch', args=[class_id, batch_id])}?date={day}")

    active_session = AcademicSession.get_active()
    selected_session_id = request.GET.get('session') or request.GET.get('academic-session')
    selected_session = AcademicSession.objects.filter(id=selected_session_id).first() if selected_session_id else None

    batch = Batch.objects.filter(id=batch_id).select_related('session').first()
    if batch and getattr(batch, 'session_id', None):
        selected_session = batch.session
    if not selected_session:
        selected_session = active_session

    obj_qs = Attendance.objects.filter(id=attendance_id, batch_id=batch_id, type=selected_type)
    if selected_session:
        obj_qs = obj_qs.filter(Q(enrollment__session=selected_session) | Q(enrollment__isnull=True))
    obj = obj_qs.first()
    if obj:
        obj.delete()
        messages.success(request, "Attendance Deleted.")
    else:
        messages.error(request, "Invalid Attendance Id.")
    redirect_url = f"{reverse('attendance_batch', args=[class_id, batch_id])}?type={selected_type}&date={day}"
    if selected_session:
        redirect_url += f"&session={selected_session.id}"
    return redirect(redirect_url)

@login_required(login_url='login')
def delete_homework(request, class_id, batch_id, homework_id):
    day = request.GET.get('date')

    active_session = AcademicSession.get_active()
    selected_session_id = request.GET.get('session') or request.GET.get('academic-session')
    selected_session = AcademicSession.objects.filter(id=selected_session_id).first() if selected_session_id else None

    batch = Batch.objects.filter(id=batch_id).select_related('session').first()
    if batch and getattr(batch, 'session_id', None):
        selected_session = batch.session
    if not selected_session:
        selected_session = active_session

    obj_qs = Homework.objects.filter(id=homework_id, batch_id=batch_id)
    if day:
        try:
            parsed_day = datetime.strptime(day, "%Y-%m-%d").date()
            obj_qs = obj_qs.filter(date=parsed_day)
        except ValueError:
            pass
    if selected_session:
        obj_qs = obj_qs.filter(Q(enrollment__session=selected_session) | Q(enrollment__isnull=True))
    obj = obj_qs.first()
    if obj:
        obj.delete()
        messages.success(request, "Homework Deleted.")
    else:
        messages.error(request, "Invalid Homework Id.")
    redirect_url = f"{reverse('homework_batch', args=[class_id, batch_id])}?date={day}"
    if selected_session:
        redirect_url += f"&session={selected_session.id}"
    return redirect(redirect_url)

@login_required(login_url='login')
def add_teacher(request):
    sessions = AcademicSession.objects.all().order_by('-start_date')
    active_session = AcademicSession.get_active()

    selected_session_id = (
        request.GET.get('session')
        or request.GET.get('academic-session')
        or request.POST.get('session')
        or request.POST.get('academic-session')
    )
    selected_session = None
    if selected_session_id:
        selected_session = AcademicSession.objects.filter(id=selected_session_id).first()
    if not selected_session:
        selected_session = active_session

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
        batches_qs = Batch.objects.filter(id__in=form_data["batches"])
        if selected_session:
            batches_qs = batches_qs.filter(session=selected_session)
        teacher.batches.set(batches_qs)
        teacher.save()

        messages.success(request, "Teacher registered successfully.")
        redirect_url = reverse("add_teacher")
        if selected_session:
            redirect_url += f"?session={selected_session.id}"
        return redirect(redirect_url)

    classes = ClassName.objects.all()
    class_teachers = []
    for cls in classes:
        teachers_qs = Teacher.objects.filter(batches__class_name=cls)
        if selected_session:
            teachers_qs = teachers_qs.filter(batches__session=selected_session)
        class_teachers.append({'class': cls.name, 'teachers': teachers_qs.distinct()})

    batches = Batch.objects.all()
    if selected_session:
        batches = batches.filter(session=selected_session)

    return render(request, "registration/add_teacher.html", {
        'batches': batches,
        "class_teachers": class_teachers,
        'academic_sessions': sessions,
        'active_session': active_session,
        'selected_session': selected_session,
    })

@login_required(login_url='login')
def update_teacher(request, teacher_id):
    teacher = Teacher.objects.filter(id = teacher_id).first()
    if not teacher:
        messages.error(request, "Invalid Teacher Id")
        return redirect("add_teacher")

    sessions = AcademicSession.objects.all().order_by('-start_date')
    active_session = AcademicSession.get_active()

    selected_session_id = (
        request.GET.get('session')
        or request.GET.get('academic-session')
        or request.POST.get('session')
        or request.POST.get('academic-session')
    )
    selected_session = None
    if selected_session_id:
        selected_session = AcademicSession.objects.filter(id=selected_session_id).first()
    if not selected_session:
        selected_session = active_session

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
        batches_qs = Batch.objects.filter(id__in=form_data["batches"])
        if selected_session:
            batches_qs = batches_qs.filter(session=selected_session)
        teacher.batches.set(batches_qs)
        teacher.save()

        messages.success(request, "Teacher details updated successfully.")
        redirect_url = reverse("update_teacher", kwargs={'teacher_id': teacher.id})
        if selected_session:
            redirect_url += f"?session={selected_session.id}"
        return redirect(redirect_url)

    # Fetch existing details
    classes = ClassName.objects.all()
    class_teachers = []
    for cls in classes:
        teachers_qs = Teacher.objects.filter(batches__class_name=cls)
        if selected_session:
            teachers_qs = teachers_qs.filter(batches__session=selected_session)
        class_teachers.append({'class': cls.name, 'teachers': teachers_qs.distinct()})

    batches = Batch.objects.all()
    if selected_session:
        batches = batches.filter(session=selected_session)

    return render(
        request, 
        "registration/update_teacher.html", 
        {
            'batches': batches,
            "class_teachers": class_teachers,
            "teacher": teacher,
            'academic_sessions': sessions,
            'active_session': active_session,
            'selected_session': selected_session,
        }
    )


# Test Paper
@login_required(login_url='login')
def test_templates(request, batch_id=None):
    if not request.user.is_superuser:
        messages.error(request, "You are not authorized to view this page.")
        return redirect('staff_dashboard')
    
    sessions = AcademicSession.objects.all().order_by('-start_date')
    active_session = AcademicSession.get_active()

    selected_session_id = (
        request.GET.get('session')
        or request.GET.get('academic-session')
        or request.POST.get('session')
        or request.POST.get('academic-session')
    )
    selected_session = None
    if selected_session_id:
        selected_session = AcademicSession.objects.filter(id=selected_session_id).first()
    if not selected_session:
        selected_session = active_session

    if batch_id and request.method == "POST":
        if Batch.objects.filter(id=batch_id).first() == None:
            messages.error("Invalid Batch")
            return redirect('test_templates')
        
        batch = Batch.objects.filter(id=batch_id).select_related('session').first()
        if batch and getattr(batch, 'session_id', None):
            selected_session = batch.session
        test = Test.objects.create(batch=batch, date=datetime.now())
        test.name = 'Demo Test Paper '
        test.save()

        redirect_url = reverse("create_testpaper", kwargs={'batch_id': batch_id, 'test_id': test.id})
        if selected_session:
            redirect_url += f"?session={selected_session.id}"
        return redirect(redirect_url)

    classes = ClassName.objects.all().order_by('name')
    class_batches = {
            cls.name : Batch.objects.filter(
                class_name=cls,
                **({'session': selected_session} if selected_session else {})
            ).order_by('class_name__name', 'section')
            for cls in classes
        }

    return render(request, "registration/test_templates.html", {
        'class_batches': class_batches,
        'academic_sessions': sessions,
        'active_session': active_session,
        'selected_session': selected_session,
    })

@login_required(login_url='login')
def create_testpaper(request, batch_id, test_id):
    if not request.user.is_superuser:
        return redirect('staff_dashboard')
    active_session = AcademicSession.get_active()
    selected_session_id = (
        request.GET.get('session')
        or request.GET.get('academic-session')
        or request.POST.get('session')
        or request.POST.get('academic-session')
    )
    selected_session = AcademicSession.objects.filter(id=selected_session_id).first() if selected_session_id else None

    batch = Batch.objects.filter(id=batch_id).select_related('session').first()
    if batch and getattr(batch, 'session_id', None):
        selected_session = batch.session
    if not selected_session:
        selected_session = active_session

    test = Test.objects.filter(id=test_id).first()
    if not batch or not test:
        messages.error(request, "Invalid Batch or Test")
        return redirect("test_templates")
    
    if request.method == 'POST':
        test_name = request.POST.get('test_name')
        total_marks = request.POST.get('total_marks')
        test_date = request.POST.get('date')
        test.objective = request.POST.get('objective') == 'on'
        test.date = test_date
        test.name = test_name
        if total_marks:
            test.total_max_marks = float(total_marks)

        test.save()

        redirect_url = reverse('test_templates')
        if selected_session:
            redirect_url += f"?session={selected_session.id}"
        return redirect(redirect_url)
    
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
    
    test = Test.objects.filter(id=test_id).select_related('batch__session').first()
    if not test:
        messages.error(request, "Invalid Test")
        return redirect("test_templates")

    selected_session = getattr(getattr(test, 'batch', None), 'session', None)
    test.delete()
    messages.success(request, "Test deleted successfully.")
    redirect_url = reverse("test_templates")
    if selected_session:
        redirect_url += f"?session={selected_session.id}"
    return redirect(redirect_url)

@login_required(login_url='login')
def create_test_question(request, batch_id, test_id):
    if not request.user.is_superuser:
        return redirect('staff_dashboard')
    active_session = AcademicSession.get_active()
    selected_session_id = (
        request.GET.get('session')
        or request.GET.get('academic-session')
        or request.POST.get('session')
        or request.POST.get('academic-session')
    )
    selected_session = AcademicSession.objects.filter(id=selected_session_id).first() if selected_session_id else None

    batch = Batch.objects.filter(id=batch_id).select_related('session').first()
    if batch and getattr(batch, 'session_id', None):
        selected_session = batch.session
    if not selected_session:
        selected_session = active_session
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

        redirect_url = reverse("create_testpaper", kwargs={'batch_id': batch_id, 'test_id': test_id})
        if selected_session:
            redirect_url += f"?session={selected_session.id}"
        return redirect(redirect_url)
    redirect_url = reverse("create_testpaper", kwargs={'batch_id': batch_id, 'test_id': test_id})
    if selected_session:
        redirect_url += f"?session={selected_session.id}"
    return redirect(redirect_url)

@login_required(login_url='login')
def update_test_question(request, batch_id, test_id, question_id):
    if not request.user.is_superuser:
        return redirect('staff_dashboard')
    active_session = AcademicSession.get_active()
    selected_session_id = (
        request.GET.get('session')
        or request.GET.get('academic-session')
        or request.POST.get('session')
        or request.POST.get('academic-session')
    )
    selected_session = AcademicSession.objects.filter(id=selected_session_id).first() if selected_session_id else None

    batch = Batch.objects.filter(id=batch_id).select_related('session').first()
    if batch and getattr(batch, 'session_id', None):
        selected_session = batch.session
    if not selected_session:
        selected_session = active_session
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

        redirect_url = reverse("create_testpaper", kwargs={'batch_id': batch_id, 'test_id': test_id})
        if selected_session:
            redirect_url += f"?session={selected_session.id}"
        return redirect(redirect_url)
    redirect_url = reverse("create_testpaper", kwargs={'batch_id': batch_id, 'test_id': test_id})
    if selected_session:
        redirect_url += f"?session={selected_session.id}"
    return redirect(redirect_url)

@login_required(login_url='login')
def calculate_marks(request, batch_id, test_id):
    if not request.user.is_superuser:
        return redirect('staff_dashboard')
    active_session = AcademicSession.get_active()
    selected_session_id = request.GET.get('session') or request.GET.get('academic-session')
    selected_session = AcademicSession.objects.filter(id=selected_session_id).first() if selected_session_id else None

    batch = Batch.objects.filter(id=batch_id).select_related('session').first()
    if batch and getattr(batch, 'session_id', None):
        selected_session = batch.session
    if not selected_session:
        selected_session = active_session
    test = Test.objects.filter(id=test_id).first()
    if not batch or not test:
        messages.error(request, "Invalid Batch or Test")
        return redirect("create_test_template")
    test.calculate_total_max_marks()
    redirect_url = reverse("create_testpaper", kwargs={'batch_id': batch_id, 'test_id': test_id})
    if selected_session:
        redirect_url += f"?session={selected_session.id}"
    return redirect(redirect_url)

# Test Response
@login_required(login_url='login')
def result_templates(request):
    if not request.user.is_superuser:
        return redirect('staff_dashboard')
    
    sessions = AcademicSession.objects.all().order_by('-start_date')
    active_session = AcademicSession.get_active()

    selected_session_id = (
        request.GET.get('session')
        or request.GET.get('academic-session')
        or request.POST.get('session')
        or request.POST.get('academic-session')
    )
    selected_session = None
    if selected_session_id:
        selected_session = AcademicSession.objects.filter(id=selected_session_id).first()
    if not selected_session:
        selected_session = active_session

    classes = ClassName.objects.all().order_by('name')
    class_batches = {
        cls.name : Batch.objects.filter(
            class_name=cls,
            **({'session': selected_session} if selected_session else {})
        ).order_by('class_name__name', 'section')
        for cls in classes
    }

    return render(request, "registration/result_templates.html", {
        'class_batches': class_batches,
        'academic_sessions': sessions,
        'active_session': active_session,
        'selected_session': selected_session,
    })

@login_required(login_url='login')
def add_result(request, batch_id, test_id, student_id=None, question_id = None):
    if not request.user.is_superuser:
        return redirect('staff_dashboard')
    active_session = AcademicSession.get_active()
    selected_session_id = (
        request.GET.get('session')
        or request.GET.get('academic-session')
        or request.POST.get('session')
        or request.POST.get('academic-session')
    )
    selected_session = AcademicSession.objects.filter(id=selected_session_id).first() if selected_session_id else None

    batch = Batch.objects.filter(id=batch_id).select_related('session').first()
    if batch and getattr(batch, 'session_id', None):
        selected_session = batch.session
    if not selected_session:
        selected_session = active_session

    test = Test.objects.filter(id=test_id).first()
    student = None
    question_response = None
    result = None
    
    if not batch or not test:
        messages.error(request, "Invalid Batch or Test")
        return redirect("result_templates")

    questions = TestQuestion.objects.filter(test=test).order_by('question_number')
    remarks = Remark.objects.all()

    enrollments_qs = StudentEnrollment.objects.filter(
        active=True,
        session=selected_session,
        batch_links__batch=batch,
    ).select_related('student').distinct()
    enrollments_by_student_id = {e.student_id: e for e in enrollments_qs if e.student_id}
    students = Student.objects.filter(id__in=enrollments_by_student_id.keys()).order_by('stu_id')

    if student_id:
        student = students.filter(id=student_id).first()
        question = TestQuestion.objects.filter(id=question_id).first()

        enrollment = enrollments_by_student_id.get(getattr(student, 'id', None)) if student else None

        result = TestResult.objects.filter(test=test, student=student).first()

        if request.method == 'POST' and question:
            marks_obtained = request.POST.get("marks_obtained")
            remark_id = request.POST.get("remark")
            remark = Remark.objects.filter(id=remark_id).first()

            response = QuestionResponse.objects.create(
                question = question,
                student=student,
                enrollment=enrollment,
                test=test,
                marks_obtained = float(question.max_marks) - float(marks_obtained),
                remark = remark
            )
            response.save()
            redirect_url = reverse(
                "add_student_result",
                kwargs={'batch_id': batch_id, 'test_id': test_id, 'student_id': student_id}
            )
            if selected_session:
                redirect_url += f"?session={selected_session.id}"
            return redirect(redirect_url)
        
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
    
    students_map = {stu: (TestResult.objects.filter(test=test, student=stu).first() or 0) for stu in students}
    return render(request, "registration/add_results.html", {
        "batch":batch, 
        "test":test,
        "students": students_map,
        "questions": questions,
        "student":student,
        "remarks":remarks,
        "question_response": question_response,
        "result":result,
        "test_types": TestResult.TEST_TYPE_CHOICES,
        'selected_session': selected_session,
    })

@login_required(login_url='login')
def add_test_result_type(request, test_result_id):
    if not request.user.is_superuser:
        return redirect('staff_dashboard')

    active_session = AcademicSession.get_active()
    selected_session_id = (
        request.GET.get('session')
        or request.GET.get('academic-session')
        or request.POST.get('session')
        or request.POST.get('academic-session')
    )
    selected_session = AcademicSession.objects.filter(id=selected_session_id).first() if selected_session_id else None
    
    test_result = TestResult.objects.filter(id=test_result_id).select_related('test__batch__session').first()
    if not test_result:
        messages.error(request, "Invalid Test Result")
        return redirect("result_templates")

    batch_session = getattr(getattr(getattr(test_result, 'test', None), 'batch', None), 'session', None)
    if batch_session:
        selected_session = batch_session
    if not selected_session:
        selected_session = active_session

    if request.method == 'POST':
        test_type = request.POST.get("test_type")
        previous_marks = request.POST.get("previous_marks")

        if previous_marks and test_type == "Retest":
            test_result.previous_marks = float(previous_marks)
            test_result.save()
        
        if test_type:
            test_result.test_type = test_type
            test_result.save()
            messages.success(request, "Result Type Updated Successfully.")
        else:
            messages.error(request, "Invalid Result Type.")

    redirect_url = reverse(
        "add_student_result",
        kwargs={
            'batch_id': test_result.test.batch.id,
            'test_id': test_result.test.id,
            'student_id': test_result.student.id,
        },
    )
    if selected_session:
        redirect_url += f"?session={selected_session.id}"
    return redirect(redirect_url)


@login_required(login_url='login')
def update_result(request, batch_id, test_id, student_id, response_id):
    if not request.user.is_superuser:
        return redirect('staff_dashboard')

    active_session = AcademicSession.get_active()
    selected_session_id = (
        request.GET.get('session')
        or request.GET.get('academic-session')
        or request.POST.get('session')
        or request.POST.get('academic-session')
    )
    selected_session = AcademicSession.objects.filter(id=selected_session_id).first() if selected_session_id else None

    batch = Batch.objects.filter(id=batch_id).select_related('session').first()
    if batch and getattr(batch, 'session_id', None):
        selected_session = batch.session
    if not selected_session:
        selected_session = active_session

    test = Test.objects.filter(id=test_id).first()
    student = Student.objects.filter(id=student_id).first()

    enrollment = None
    if batch and selected_session and student:
        enrollment = StudentEnrollment.objects.filter(
            student=student,
            session=selected_session,
            active=True,
            batch_links__batch=batch,
        ).first()

    response_qs = QuestionResponse.objects.filter(id=response_id, student_id=student_id, test_id=test_id)
    if selected_session:
        response_qs = response_qs.filter(Q(enrollment__session=selected_session) | Q(enrollment__isnull=True))
    response = response_qs.select_related('question').first()

    if ( not batch or not test or not student or not response ) :
        messages.error("Invalid Details.")
        redirect_url = reverse(
            "add_student_result",
            kwargs={'batch_id': batch_id, 'test_id': test_id, 'student_id': student_id},
        )
        if selected_session:
            redirect_url += f"?session={selected_session.id}"
        return redirect(redirect_url)

    if selected_session and enrollment is None:
        messages.error(request, "Student is not enrolled in this batch/session")
        redirect_url = reverse(
            "add_student_result",
            kwargs={'batch_id': batch_id, 'test_id': test_id, 'student_id': student_id},
        )
        if selected_session:
            redirect_url += f"?session={selected_session.id}"
        return redirect(redirect_url)

    if request.method == 'POST':
        marks_obtained = request.POST.get("marks_obtained")
        remark_id = request.POST.get("remark")

        response.marks_obtained = float(response.question.max_marks) - abs(float(marks_obtained))
        if remark_id:
            remark = Remark.objects.get(id=remark_id)
            response.remark = remark

        if enrollment and response.enrollment_id != enrollment.id:
            response.enrollment = enrollment
        response.save()

    redirect_url = reverse(
        "add_student_result",
        kwargs={'batch_id': batch_id, 'test_id': test_id, 'student_id': student_id},
    )
    if selected_session:
        redirect_url += f"?session={selected_session.id}"
    return redirect(redirect_url)

@login_required(login_url='login')
def add_total_marks_obtained(request, batch_id, test_id, student_id):
    if not request.user.is_superuser:
        return redirect('staff_dashboard')

    active_session = AcademicSession.get_active()
    selected_session_id = (
        request.GET.get('session')
        or request.GET.get('academic-session')
        or request.POST.get('session')
        or request.POST.get('academic-session')
    )
    selected_session = AcademicSession.objects.filter(id=selected_session_id).first() if selected_session_id else None

    batch = Batch.objects.filter(id=batch_id).select_related('session').first()
    if batch and getattr(batch, 'session_id', None):
        selected_session = batch.session
    if not selected_session:
        selected_session = active_session

    test = Test.objects.filter(id=test_id).first()
    student = None

    if not batch or not test:
        messages.error(request, "Invalid Batch or Test")
        return redirect("result_templates")

    student = Student.objects.filter(id=student_id).first()
    if not student:
        messages.error(request, "Invalid Student")
        redirect_url = reverse("add_result", kwargs={'batch_id': batch_id, 'test_id': test_id})
        if selected_session:
            redirect_url += f"?session={selected_session.id}"
        return redirect(redirect_url)

    enrollment = None
    if batch and selected_session and student:
        enrollment = StudentEnrollment.objects.filter(
            student=student,
            session=selected_session,
            active=True,
            batch_links__batch=batch,
        ).first()

    if selected_session and enrollment is None:
        messages.error(request, "Student is not enrolled in this batch/session")
        redirect_url = reverse(
            "add_student_result",
            kwargs={'batch_id': batch_id, 'test_id': test_id, 'student_id': student_id},
        )
        if selected_session:
            redirect_url += f"?session={selected_session.id}"
        return redirect(redirect_url)

    if request.method == 'POST':
        total_marks_obtained = request.POST.get('total_marks_obtained')
        result, created = TestResult.objects.get_or_create(student=student,test=test)
        if enrollment and result.enrollment_id != enrollment.id:
            result.enrollment = enrollment
        result.total_marks_obtained = float(total_marks_obtained)
        result.total_max_marks = test.total_max_marks
        result.percentage = (float(total_marks_obtained) / test.total_max_marks or 1) * 100
        result.save()
        redirect_url = reverse(
            "add_student_result",
            kwargs={'batch_id': batch_id, 'test_id': test_id, 'student_id': student_id},
        )
        if selected_session:
            redirect_url += f"?session={selected_session.id}"
        return redirect(redirect_url)

    redirect_url = reverse(
        "add_student_result",
        kwargs={'batch_id': batch_id, 'test_id': test_id, 'student_id': student_id},
    )
    if selected_session:
        redirect_url += f"?session={selected_session.id}"
    return redirect(redirect_url)

@login_required(login_url='login')
def delete_result(request, batch_id, test_id, student_id, response_id):
    if not request.user.is_superuser:
        return redirect('staff_dashboard')

    active_session = AcademicSession.get_active()
    selected_session_id = (
        request.GET.get('session')
        or request.GET.get('academic-session')
        or request.POST.get('session')
        or request.POST.get('academic-session')
    )
    selected_session = AcademicSession.objects.filter(id=selected_session_id).first() if selected_session_id else None

    batch = Batch.objects.filter(id=batch_id).select_related('session').first()
    if batch and getattr(batch, 'session_id', None):
        selected_session = batch.session
    if not selected_session:
        selected_session = active_session

    try:
        if not batch:
            messages.error(request, "Invalid batch ID.")
            redirect_url = reverse(
                "add_student_result",
                kwargs={'batch_id': batch_id, 'test_id': test_id, 'student_id': student_id},
            )
            if selected_session:
                redirect_url += f"?session={selected_session.id}"
            return redirect(redirect_url)

        if not Test.objects.filter(id=test_id).exists():
            messages.error(request, "Invalid test ID.")
            redirect_url = reverse(
                "add_student_result",
                kwargs={'batch_id': batch_id, 'test_id': test_id, 'student_id': student_id},
            )
            if selected_session:
                redirect_url += f"?session={selected_session.id}"
            return redirect(redirect_url)

        if not Student.objects.filter(id=student_id).exists():
            messages.error(request, "Invalid student ID.")
            redirect_url = reverse(
                "add_student_result",
                kwargs={'batch_id': batch_id, 'test_id': test_id, 'student_id': student_id},
            )
            if selected_session:
                redirect_url += f"?session={selected_session.id}"
            return redirect(redirect_url)

        response_qs = QuestionResponse.objects.filter(id=response_id, student_id=student_id, test_id=test_id)
        if selected_session:
            response_qs = response_qs.filter(Q(enrollment__session=selected_session) | Q(enrollment__isnull=True))
        response = response_qs.first()
        if not response:
            raise QuestionResponse.DoesNotExist

        response.delete()
        messages.success(request, "Response deleted.")

    except QuestionResponse.DoesNotExist:

        messages.error(request, "Response not found. Unable to delete.")
    except Exception as e:
        messages.error(request, f"An error occurred: {str(e)}")

    redirect_url = reverse(
        "add_student_result",
        kwargs={'batch_id': batch_id, 'test_id': test_id, 'student_id': student_id},
    )
    if selected_session:
        redirect_url += f"?session={selected_session.id}"
    return redirect(redirect_url)

@login_required(login_url='login')
def all_pending_response(request, batch_id, test_id, student_id):
    if not request.user.is_superuser:
        return redirect('staff_dashboard')

    active_session = AcademicSession.get_active()
    selected_session_id = (
        request.GET.get('session')
        or request.GET.get('academic-session')
        or request.POST.get('session')
        or request.POST.get('academic-session')
    )
    selected_session = AcademicSession.objects.filter(id=selected_session_id).first() if selected_session_id else None

    batch = Batch.objects.filter(id=batch_id).select_related('session').first()
    if batch and getattr(batch, 'session_id', None):
        selected_session = batch.session
    if not selected_session:
        selected_session = active_session

    test = Test.objects.filter(id=test_id).first()
    student = Student.objects.filter(id=student_id).first()

    if not student or not test:
        messages.error(request, "Invalid Student or Test")
        redirect_url = reverse(
            "add_student_result",
            kwargs={'batch_id': batch_id, 'test_id': test_id, 'student_id': student_id},
        )
        if selected_session:
            redirect_url += f"?session={selected_session.id}"
        return redirect(redirect_url)

    enrollment = None
    if batch and selected_session and student:
        enrollment = StudentEnrollment.objects.filter(
            student=student,
            session=selected_session,
            active=True,
            batch_links__batch=batch,
        ).first()

    if selected_session and enrollment is None:
        messages.error(request, "Student is not enrolled in this batch/session")
        redirect_url = reverse(
            "add_student_result",
            kwargs={'batch_id': batch_id, 'test_id': test_id, 'student_id': student_id},
        )
        if selected_session:
            redirect_url += f"?session={selected_session.id}"
        return redirect(redirect_url)

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
            enrollment=enrollment,
            test=test,
            marks_obtained=question.max_marks,  # Default marks
        )
        obj.save()

    redirect_url = reverse(
        "add_student_result",
        kwargs={'batch_id': batch_id, 'test_id': test_id, 'student_id': student_id},
    )
    if selected_session:
        redirect_url += f"?session={selected_session.id}"
    return redirect(redirect_url)
    

@login_required(login_url='login')
def transport_list(request):
    if not request.user.is_superuser:
        return redirect('staff_dashboard')

    sessions = AcademicSession.objects.all().order_by('-start_date')
    active_session = AcademicSession.get_active()
    selected_session_id = (
        request.GET.get('session')
        or request.GET.get('academic-session')
        or request.POST.get('session')
        or request.POST.get('academic-session')
    )
    selected_session = AcademicSession.objects.filter(id=selected_session_id).first() if selected_session_id else None
    if not selected_session:
        selected_session = active_session

    weekdays = list(Day.objects.order_by("id"))  # or "name" if alphabetically sorted
    total = len(weekdays)

    index = int(request.GET.get("day", 0))

    move = request.GET.get("move")
    if move == "next" and index < total - 1:
        index += 1
    elif move == "prev" and index > 0:
        index -= 1
    

    current_day = weekdays[index]
    
    batches = Batch.objects.filter(days__name=current_day).exclude(
        Q(class_name__name__in=['CLASS 9', 'CLASS 10']) &
        Q(section__name='CBSE') &
        Q(subject__name__in=['MATH', 'SCIENCE'])
    ).order_by('start_time', 'class_name__name', 'section')

    if selected_session:
        batches = batches.filter(session=selected_session)

    grouped_batches = {}
    for batch in batches:
        enrollments_qs = StudentEnrollment.objects.filter(
            active=True,
            session=selected_session,
            batch_links__batch=batch,
        ).select_related('student').distinct()
        student_ids = [e.student_id for e in enrollments_qs if e.student_id]
        transport_students = Student.objects.filter(
            id__in=student_ids,
            fees__cab_fees__gt=0,
            transport__isnull=False,
        ).select_related(
            'user',
            'transport',
            'transport__transport_person',
            'transport__transport_mode',
            'fees',
        ).order_by('stu_id')

        if transport_students.exists():
            if batch.start_time not in grouped_batches:
                grouped_batches[batch.start_time] = {}
            grouped_batches[batch.start_time][batch] = list(transport_students)
    

    return render(request, "registration/students_timing.html", {
        "current_day": current_day,
        "day": index,
        "grouped_batches": dict(grouped_batches),
        'academic_sessions': sessions,
        'active_session': active_session,
        'selected_session': selected_session,
    })


@login_required(login_url='login')
def transport_driver_list(request):
    if not request.user.is_superuser:
        return redirect('staff_dashboard')

    sessions = AcademicSession.objects.all().order_by('-start_date')
    active_session = AcademicSession.get_active()
    selected_session_id = (
        request.GET.get('session')
        or request.GET.get('academic-session')
        or request.POST.get('session')
        or request.POST.get('academic-session')
    )
    selected_session = AcademicSession.objects.filter(id=selected_session_id).first() if selected_session_id else None
    if not selected_session:
        selected_session = active_session

    weekdays = list(Day.objects.order_by("id"))
    total = len(weekdays)

    index = int(request.GET.get("day", 0))
    move = request.GET.get("move")

    if move == "next" and index < total - 1:
        index += 1
    elif move == "prev" and index > 0:
        index -= 1

    current_day = weekdays[index]

    batch_links_qs = EnrollmentBatch.objects.filter(
        enrollment__active=True,
        enrollment__session=selected_session,
        batch__days__name=current_day.name,
    ).exclude(
        Q(batch__class_name__name__in=['CLASS 9', 'CLASS 10']) &
        Q(batch__section__name='CBSE') &
        Q(batch__subject__name__in=['MATH', 'SCIENCE'])
    ).select_related(
        'batch',
        'enrollment',
        'enrollment__student',
        'enrollment__student__user',
        'enrollment__student__transport',
        'enrollment__student__transport__transport_person',
        'enrollment__student__transport__transport_mode',
        'enrollment__student__fees',
    ).order_by('batch__start_time')

    grouped_transports = defaultdict(lambda: defaultdict(list))
    seen_students = set()  # to avoid duplicate inclusion

    for link in batch_links_qs:
        student = getattr(getattr(link, 'enrollment', None), 'student', None)
        if not student:
            continue
        if student.id in seen_students:
            continue
        if not getattr(student, 'fees', None) or float(student.fees.cab_fees or 0) <= 0:
            continue
        try:
            if not student.transport or not student.transport.transport_person:
                continue
        except Student.transport.RelatedObjectDoesNotExist:
            continue

        time = link.batch.start_time
        driver = student.transport.transport_person
        grouped_transports[time][driver].append(student)
        seen_students.add(student.id)

    # Sort students and timings
    for time in grouped_transports:
        for driver in grouped_transports[time]:
            grouped_transports[time][driver].sort(key=lambda s: s.stu_id)

    # Ensure timings are in ascending order
    sorted_grouped = OrderedDict(sorted(grouped_transports.items()))

    # Convert defaultdicts to normal nested dicts for template usage
    for time in grouped_transports:
        grouped_transports[time] = dict(grouped_transports[time])
    grouped_transports = dict(grouped_transports)
    sorted_grouped = dict(sorted(grouped_transports.items()))

    return render(request, "registration/students_driver_timing.html", {
        "current_day": current_day,
        "day": index,
        "grouped_transports": sorted_grouped,
        'academic_sessions': sessions,
        'active_session': active_session,
        'selected_session': selected_session,
    })


@login_required(login_url='login')
def grouped_transports(request):
    if not request.user.is_superuser:
        return redirect('staff_dashboard')

    sessions = AcademicSession.objects.all().order_by('-start_date')
    active_session = AcademicSession.get_active()
    selected_session_id = (
        request.GET.get('session')
        or request.GET.get('academic-session')
        or request.POST.get('session')
        or request.POST.get('academic-session')
    )
    selected_session = AcademicSession.objects.filter(id=selected_session_id).first() if selected_session_id else None
    if not selected_session:
        selected_session = active_session

    weekdays = list(Day.objects.order_by("id"))
    total = len(weekdays)
    index = int(request.GET.get("day", 0))
    move = request.GET.get("move")
    if move == "next" and index < total - 1:
        index += 1
    elif move == "prev" and index > 0:
        index -= 1
    current_day = weekdays[index]

    enrolled_student_ids = StudentEnrollment.objects.filter(
        active=True,
        session=selected_session,
        batch_links__batch__days__name=current_day.name,
    ).values_list('student_id', flat=True)

    students = Student.objects.filter(
        id__in=enrolled_student_ids,
        fees__cab_fees__gt=0,
        transport__transport_person__isnull=False,
    ).select_related(
        'user',
        'fees',
        'transport',
        'transport__transport_person',
        'transport__transport_mode',
    ).distinct().order_by('stu_id')

    grouped_by_driver = defaultdict(list)

    for student in students:
        driver = student.transport.transport_person
        grouped_by_driver[driver].append(student)

    # Sort students under each driver by student ID
    for driver in grouped_by_driver:
        grouped_by_driver[driver].sort(key=lambda s: s.stu_id)

    return render(request, "registration/grouped_transports.html", {
        "grouped_transports": dict(grouped_by_driver),
        "current_day": current_day,
        "day": index,
        'academic_sessions': sessions,
        'active_session': active_session,
        'selected_session': selected_session,
    })

@login_required(login_url='login')
def transport_student_list(request):
    if not request.user.is_superuser:
        return redirect('staff_dashboard')

    sessions = AcademicSession.objects.all().order_by('-start_date')
    active_session = AcademicSession.get_active()
    selected_session_id = (
        request.GET.get('session')
        or request.GET.get('academic-session')
        or request.POST.get('session')
        or request.POST.get('academic-session')
    )
    selected_session = AcademicSession.objects.filter(id=selected_session_id).first() if selected_session_id else None
    if not selected_session:
        selected_session = active_session

    weekdays = list(Day.objects.order_by("id"))
    total = len(weekdays)

    index = int(request.GET.get("day", 0))
    move = request.GET.get("move")

    if move == "next" and index < total - 1:
        index += 1
    elif move == "prev" and index > 0:
        index -= 1

    current_day = weekdays[index]

    batch_links_qs = EnrollmentBatch.objects.filter(
        enrollment__active=True,
        enrollment__session=selected_session,
        batch__days__name=current_day.name,
    ).select_related(
        'batch',
        'enrollment',
        'enrollment__student',
        'enrollment__student__user',
        'enrollment__student__transport',
        'enrollment__student__transport__transport_person',
        'enrollment__student__transport__transport_mode',
        'enrollment__student__fees',
    ).order_by('batch__start_time')

    grouped_transports = defaultdict(lambda: defaultdict(list))
    seen_students = set()  # to avoid duplicate inclusion

    for link in batch_links_qs:
        student = getattr(getattr(link, 'enrollment', None), 'student', None)
        if not student:
            continue
        if student.id in seen_students:
            continue
        if not getattr(student, 'fees', None) or float(student.fees.cab_fees or 0) <= 0:
            continue
        try:
            if not student.transport or not student.transport.transport_person:
                continue
        except Student.transport.RelatedObjectDoesNotExist:
            continue

        time = link.batch.start_time
        driver = student.transport.transport_person
        grouped_transports[time][driver].append(student)
        seen_students.add(student.id)

    # Sort students and timings
    for time in grouped_transports:
        for driver in grouped_transports[time]:
            grouped_transports[time][driver].sort(key=lambda s: s.stu_id)

    # Ensure timings are in ascending order
    sorted_grouped = OrderedDict(sorted(grouped_transports.items()))

    # Convert defaultdicts to normal nested dicts for template usage
    for time in grouped_transports:
        grouped_transports[time] = dict(grouped_transports[time])
    grouped_transports = dict(grouped_transports)
    sorted_grouped = dict(sorted(grouped_transports.items()))

    return render(request, "registration/students_driver_timing.html", {
        "current_day": current_day,
        "day": index,
        "grouped_transports": sorted_grouped,
        'academic_sessions': sessions,
        'active_session': active_session,
        'selected_session': selected_session,
    })

@login_required(login_url='login')
def assign_mentor(request):
    if not request.user.is_superuser:
        return redirect('staff_dashboard')

    sessions = AcademicSession.objects.all().order_by('-start_date')
    active_session = AcademicSession.get_active()

    selected_session_id = (
        request.GET.get('session')
        or request.GET.get('academic-session')
        or request.POST.get('session')
        or request.POST.get('academic-session')
    )
    selected_session = AcademicSession.objects.filter(id=selected_session_id).first() if selected_session_id else None
    if not selected_session:
        selected_session = active_session
    
    if request.method == 'POST':
        mentor = request.POST.get('mentor')
        enrollment_ids = request.POST.getlist('enrollments[]')

        if not mentor or not enrollment_ids:
            messages.error(request, "Please select a mentor and at least one student.")
            redirect_url = reverse('assign_mentor')
            if selected_session:
                redirect_url += f"?session={selected_session.id}"
            return redirect(redirect_url)
        mentor_obj = Mentor.objects.filter(id=mentor).first()
        if not mentor_obj:
            messages.error(request, "Invalid Mentor")
            redirect_url = reverse('assign_mentor')
            if selected_session:
                redirect_url += f"?session={selected_session.id}"
            return redirect(redirect_url)

        enrollments = StudentEnrollment.objects.filter(
            id__in=enrollment_ids,
            session=selected_session,
            active=True,
        ).select_related('student')

        for enrollment in enrollments:
            if not enrollment.student:
                continue
            Mentorship.objects.filter(enrollment=enrollment, active=True).update(active=False)
            mentorship, created = Mentorship.objects.get_or_create(
                mentor=mentor_obj,
                student=enrollment.student,
                enrollment=enrollment,
                defaults={'active': True}
            )
            if not created and not mentorship.active:
                mentorship.active = True
                mentorship.save(update_fields=['active'])
        messages.success(request, "Mentor assigned successfully.")
        redirect_url = reverse('assign_mentor')
        if selected_session:
            redirect_url += f"?session={selected_session.id}"
        return redirect(redirect_url)

    classes = ClassName.objects.all().order_by('name')

    enrollments_qs = StudentEnrollment.objects.filter(
        session=selected_session,
        active=True,
    ).select_related(
        'class_name',
        'student',
        'student__user',
    ).order_by('student__user__first_name', 'student__user__last_name', 'student__stu_id')

    enrollments_by_class_id = defaultdict(list)
    enrollment_ids = []
    for e in enrollments_qs:
        if not e.class_name_id or not e.student_id:
            continue
        enrollments_by_class_id[e.class_name_id].append(e)
        enrollment_ids.append(e.id)

    active_mentorships = Mentorship.objects.filter(
        active=True,
        enrollment_id__in=enrollment_ids,
    ).select_related('mentor__user', 'enrollment')
    mentorship_by_enrollment_id = {m.enrollment_id: m for m in active_mentorships if m.enrollment_id}

    class_enrollments = []
    for cls in classes:
        cls_enrollments = enrollments_by_class_id.get(cls.id, [])
        if not cls_enrollments:
            continue

        enrollment_rows = []
        for enrollment in cls_enrollments:
            active_mentorship = mentorship_by_enrollment_id.get(enrollment.id)
            enrollment_rows.append({
                'enrollment': enrollment,
                'student': enrollment.student,
                'active_mentorship': active_mentorship,
                'needs_mentor': active_mentorship is None,
            })
        class_enrollments.append({
            'class': cls.name,
            'enrollments': enrollment_rows,
            'total': len(enrollment_rows),
        })

    mentors = Mentor.objects.all().order_by('-created_at')


    return render(request, "registration/assign_mentor.html", {
        'class_enrollments': class_enrollments,
        'mentors': mentors,
        'academic_sessions': sessions,
        'active_session': active_session,
        'selected_session': selected_session,
    })


@login_required(login_url='login')
def unassign_mentor_enrollment(request, enrollment_id):
    if not request.user.is_superuser:
        return redirect('staff_dashboard')

    active_session = AcademicSession.get_active()
    selected_session_id = (
        request.GET.get('session')
        or request.GET.get('academic-session')
        or request.POST.get('session')
        or request.POST.get('academic-session')
    )
    selected_session = AcademicSession.objects.filter(id=selected_session_id).first() if selected_session_id else None

    enrollment = StudentEnrollment.objects.filter(id=enrollment_id).select_related('session').first()
    if not enrollment:
        messages.error(request, "Invalid Enrollment")
        redirect_url = reverse('assign_mentor')
        if selected_session:
            redirect_url += f"?session={selected_session.id}"
        return redirect(redirect_url)

    if enrollment.session:
        selected_session = enrollment.session
    if not selected_session:
        selected_session = active_session

    Mentorship.objects.filter(enrollment=enrollment, active=True).update(active=False)
    messages.success(request, "Mentorship unassigned successfully.")

    redirect_url = reverse('assign_mentor')
    if selected_session:
        redirect_url += f"?session={selected_session.id}"
    return redirect(redirect_url)

@login_required(login_url='login')
def unassign_mentor(request, stu_id):
    if not request.user.is_superuser:
        return redirect('staff_dashboard')

    active_session = AcademicSession.get_active()
    selected_session_id = (
        request.GET.get('session')
        or request.GET.get('academic-session')
        or request.POST.get('session')
        or request.POST.get('academic-session')
    )
    selected_session = AcademicSession.objects.filter(id=selected_session_id).first() if selected_session_id else None
    
    student = Student.objects.filter(stu_id=stu_id).first()
    if not student:
        messages.error(request, "Invalid Student")
        redirect_url = reverse('assign_mentor')
        if selected_session:
            redirect_url += f"?session={selected_session.id}"
        return redirect(redirect_url)

    # If session is provided (or can be inferred), unassign only for that session's enrollment.
    enrollment = None
    if selected_session:
        enrollment = StudentEnrollment.objects.filter(student=student, session=selected_session).first()
    if not enrollment:
        enrollment = StudentEnrollment.get_current_for_student(student)
        if enrollment and enrollment.session:
            selected_session = enrollment.session
    if not selected_session:
        selected_session = active_session

    if enrollment:
        Mentorship.objects.filter(enrollment=enrollment, active=True).update(active=False)
        messages.success(request, "Mentorship unassigned successfully.")
        redirect_url = reverse('assign_mentor')
        if selected_session:
            redirect_url += f"?session={selected_session.id}"
        return redirect(redirect_url)

    mentorships = Mentorship.objects.filter(student=student)
    if not mentorships.exists():
        messages.error(request, "No mentorship found for this student.")
        redirect_url = reverse('assign_mentor')
        if selected_session:
            redirect_url += f"?session={selected_session.id}"
        return redirect(redirect_url)
    
    for mentorship in mentorships:
        mentorship.active = False
        mentorship.save()
    messages.success(request, "Mentorship unassigned successfully.")

    redirect_url = reverse('assign_mentor')
    if selected_session:
        redirect_url += f"?session={selected_session.id}"
    return redirect(redirect_url)

@login_required(login_url='login')
def add_driver(request):
    if request.method == "POST":
        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name")
        phone = request.POST.get("phone")
        password = "basu@123"
        name = request.POST.get("name")

        # Try to find existing BaseUser
        user = BaseUser.objects.filter(phone=phone).first()

        # Try to find existing TransportPerson
        driver = TransportPerson.objects.filter(name=name).first()

        if driver:
            if driver.user:
                messages.error(request, "Driver already exists and is linked to a user.")
                return redirect("add_driver")
            else:
                if user:
                    driver.user = user
                    messages.success(request, "Linked existing user to the driver.")
                else:
                    # Create new BaseUser and link
                    user = BaseUser.objects.create_user(
                        phone=phone,
                        password=password,
                        first_name=first_name,
                        last_name=last_name,
                    )
                    driver.user = user
                    messages.success(request, "New user created and linked to existing driver.")
                driver.save()
        else:
            if not user:
                user = BaseUser.objects.create_user(
                    phone=phone,
                    password=password,
                    first_name=first_name,
                    last_name=last_name,
                )
                messages.success(request, "New user created.")

            # Create new TransportPerson and link user
            driver = TransportPerson.objects.create(name=name, user=user)
            messages.success(request, "New driver created and linked with user.")

        return redirect("add_driver")

    drivers = TransportPerson.objects.all()
    return render(request, "registration/add_driver.html", {'drivers': drivers})

def students_pick_drop(request):
    try:
        driver = TransportPerson.objects.filter(user=request.user).first()
    except Exception:
        messages.error(request, 'Invalid Driver')
        return redirect('staff_dashboard')

    sessions = AcademicSession.objects.all().order_by('-start_date')
    active_session = AcademicSession.get_active()
    selected_session_id = (
        request.GET.get('session')
        or request.GET.get('academic-session')
        or request.POST.get('session')
        or request.POST.get('academic-session')
    )
    selected_session = AcademicSession.objects.filter(id=selected_session_id).first() if selected_session_id else None
    if not selected_session:
        selected_session = active_session
    
    date_str = request.GET.get("date")
    try:
        date = datetime.strptime(date_str, "%Y-%m-%d").date() if date_str else datetime.now().date()
    except ValueError:
        messages.error(request, "Invalid date format.")
        return redirect(f"?date={datetime.now().date()}")

    prev_date = date - timedelta(days=1)
    next_date = date + timedelta(days=1)

    current_day = Day.objects.filter(name=date.strftime("%A")).first()

    if not current_day:
        return render(request, "registration/students_pick_drop.html", {
            "current_day": None,
            "date": date,
            "prev_date": prev_date,
            "next_date": next_date,
            "driver": driver,
            "grouped_transports": {},
            'academic_sessions': sessions,
            'active_session': active_session,
            'selected_session': selected_session,
        })

    enrollments_qs = StudentEnrollment.objects.filter(
        active=True,
        session=selected_session,
        fees__cab_fees__gt=0,
        transport_details__transport_person=driver,
        batch_links__batch__days__name=current_day.name,
    ).select_related(
        'student',
        'student__user',
        'fees',
        'transport_details',
        'transport_details__transport_person',
        'transport_details__transport_mode',
    ).distinct()

    enrollment_ids = [e.id for e in enrollments_qs]

    batch_links_qs = EnrollmentBatch.objects.filter(
        enrollment_id__in=enrollment_ids,
        batch__days__name=current_day.name,
    ).exclude(
        Q(batch__class_name__name__in=['CLASS 9', 'CLASS 10']) &
        Q(batch__section__name='CBSE') &
        Q(batch__subject__name__in=['MATH', 'SCIENCE'])
    ).select_related('batch', 'enrollment').distinct()

    batches_by_enrollment_id = defaultdict(list)
    for link in batch_links_qs:
        batches_by_enrollment_id[link.enrollment_id].append(link.batch)

    enrollments = [e for e in enrollments_qs if e.id in batches_by_enrollment_id]
    students = [e.student for e in enrollments if e.student_id]

    attendance_qs = TransportAttendance.objects.filter(date=date).filter(
        Q(enrollment__in=enrollments) | (Q(enrollment__isnull=True) & Q(student__in=students))
    )
    # Build a lookup: {(enrollment_id|student_id, time, action): attendance_obj}
    attendance_lookup = {}
    for att in attendance_qs:
        if att.enrollment_id:
            attendance_lookup[(att.enrollment_id, att.time, att.action)] = att
        else:
            attendance_lookup[(att.student_id, att.time, att.action)] = att

    grouped = defaultdict(lambda: {"Pickup": [], "Drop": []})

    def _parse_time(value):
        try:
            return datetime.strptime(value, "%I:%M %p").time()
        except Exception:
            return None

    for enrollment in enrollments:
        student = enrollment.student
        batches_today = batches_by_enrollment_id.get(enrollment.id, [])
        if not batches_today or not student:
            continue

        earliest = min(
            batches_today,
            key=lambda b: (_parse_time(getattr(b, 'start_time', None)) or datetime.max.time()),
        )
        latest = max(
            batches_today,
            key=lambda b: (_parse_time(getattr(b, 'end_time', None)) or datetime.min.time()),
        )

        # For Pickup
        pickup_time_obj = _parse_time(getattr(earliest, 'start_time', None))
        if not pickup_time_obj:
            continue

        pickup_time_str = str(getattr(earliest, 'start_time', ''))
        pickup_attendance = (
            attendance_lookup.get((enrollment.id, pickup_time_str, "Pickup"))
            or attendance_lookup.get((student.id, pickup_time_str, "Pickup"))
        )
        grouped[pickup_time_obj]["Pickup"].append({
            "enrollment": enrollment,
            "attendance": pickup_attendance,
        })

        # For Drop
        drop_time_obj = _parse_time(getattr(latest, 'end_time', None))
        if not drop_time_obj:
            continue

        drop_time_str = str(getattr(latest, 'end_time', ''))
        drop_attendance = (
            attendance_lookup.get((enrollment.id, drop_time_str, "Drop"))
            or attendance_lookup.get((student.id, drop_time_str, "Drop"))
        )
        grouped[drop_time_obj]["Drop"].append({
            "enrollment": enrollment,
            "attendance": drop_attendance,
        })

    sorted_grouped = OrderedDict(sorted(grouped.items()))

    return render(request, "registration/students_pick_drop.html", {
        "current_day": current_day,
        "date": date,
        "prev_date": prev_date,
        "next_date": next_date,
        "driver": driver,
        "grouped_transports": sorted_grouped,
        'academic_sessions': sessions,
        'active_session': active_session,
        'selected_session': selected_session,
    })

@login_required(login_url='login')
def mark_transport_attendance(request):
    if request.method == "POST":
        enrollment_id = request.POST.get("enrollment_id")
        legacy_student_id = request.POST.get("student_id")
        date_str = request.POST.get("date")
        time = request.POST.get("time")
        action = request.POST.get("action")
        is_present = request.POST.get("present") == "true"

        active_session = AcademicSession.get_active()
        selected_session_id = (
            request.GET.get('session')
            or request.GET.get('academic-session')
            or request.POST.get('session')
            or request.POST.get('academic-session')
        )
        selected_session = AcademicSession.objects.filter(id=selected_session_id).first() if selected_session_id else None
        if not selected_session:
            selected_session = active_session

        driver = TransportPerson.objects.filter(user=request.user).first()

        if not driver:
            messages.error(request, 'Invalid Driver')
            return redirect('staff_dashboard')

        enrollment_qs = StudentEnrollment.objects.filter(session=selected_session, active=True).select_related(
            'student',
            'student__user',
            'transport_details',
            'transport_details__transport_person',
            'transport_details__transport_mode',
            'fees',
        )

        enrollment = enrollment_qs.filter(id=enrollment_id).first() if enrollment_id else None
        if not enrollment and legacy_student_id:
            enrollment = enrollment_qs.filter(student_id=legacy_student_id).first()
        if not enrollment or not enrollment.student:
            messages.error(request, "Invalid Enrollment")
            redirect_url = reverse('students_pick_drop')
            if selected_session:
                redirect_url += f"?date={datetime.now().date()}&session={selected_session.id}"
            return redirect(redirect_url)
        student = enrollment.student

        try:
            date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            messages.error(request, "Invalid date format.")
            return redirect('students_pick_drop')

        attendance, created = TransportAttendance.objects.get_or_create(
            enrollment=enrollment,
            date=date_obj,
            time=time,
            action=action,
            driver=driver,
            defaults={'is_present': is_present, 'student': student}
        )
        if not created:
            attendance.is_present = is_present
            if attendance.student_id != student.id:
                attendance.student = student
            if attendance.enrollment_id != enrollment.id:
                attendance.enrollment = enrollment
            attendance.save()

        if is_present:
            messages.success(request, f"{action} marked as Present for {student.user.first_name} on {date_obj}.")
        else:
            messages.success(request, f"{action} marked as Absent for {student.user.first_name} on {date_obj}.")

        redirect_url = f"{reverse('students_pick_drop')}?date={date_obj}"
        if selected_session:
            redirect_url += f"&session={selected_session.id}"
        return redirect(redirect_url)
    else:
        messages.error(request, "Invalid request method.")
        return redirect('students_pick_drop')


@login_required(login_url='login')
def drivers_list(request):
    if not request.user.is_superuser:
        return redirect('staff_dashboard')

    drivers = TransportPerson.objects.all().order_by('name')
    return render(request, "registration/drivers_list.html", {'drivers': drivers})

@login_required(login_url='login')
def transport_attendance(request, driver_id):
    try:
        driver = TransportPerson.objects.get(id=driver_id)
    except Exception:
        messages.error(request, 'Invalid Driver')
        return redirect('staff_dashboard')

    sessions = AcademicSession.objects.all().order_by('-start_date')
    active_session = AcademicSession.get_active()
    selected_session_id = (
        request.GET.get('session')
        or request.GET.get('academic-session')
        or request.POST.get('session')
        or request.POST.get('academic-session')
    )
    selected_session = AcademicSession.objects.filter(id=selected_session_id).first() if selected_session_id else None
    if not selected_session:
        selected_session = active_session
    
    date_str = request.GET.get("date")
    try:
        date = datetime.strptime(date_str, "%Y-%m-%d").date() if date_str else datetime.now().date()
    except ValueError:
        messages.error(request, "Invalid date format.")
        return redirect(f"?date={datetime.now().date()}")

    prev_date = date - timedelta(days=1)
    next_date = date + timedelta(days=1)

    current_day = Day.objects.filter(name=date.strftime("%A")).first()

    if not current_day:
        return render(request, "registration/students_pick_drop.html", {
            "current_day": None,
            "date": date,
            "prev_date": prev_date,
            "next_date": next_date,
            "driver": driver,
            "grouped_transports": {},
            'academic_sessions': sessions,
            'active_session': active_session,
            'selected_session': selected_session,
        })

    enrollments_qs = StudentEnrollment.objects.filter(
        active=True,
        session=selected_session,
        fees__cab_fees__gt=0,
        transport_details__transport_person=driver,
        batch_links__batch__days__name=current_day.name,
    ).select_related(
        'student',
        'student__user',
        'fees',
        'transport_details',
        'transport_details__transport_person',
        'transport_details__transport_mode',
    ).distinct()

    enrollment_ids = [e.id for e in enrollments_qs]

    batch_links_qs = EnrollmentBatch.objects.filter(
        enrollment_id__in=enrollment_ids,
        batch__days__name=current_day.name,
    ).exclude(
        Q(batch__class_name__name__in=['CLASS 9', 'CLASS 10']) &
        Q(batch__section__name='CBSE') &
        Q(batch__subject__name__in=['MATH', 'SCIENCE'])
    ).select_related('batch', 'enrollment').distinct()

    batches_by_enrollment_id = defaultdict(list)
    for link in batch_links_qs:
        batches_by_enrollment_id[link.enrollment_id].append(link.batch)

    enrollments = [e for e in enrollments_qs if e.id in batches_by_enrollment_id]
    students = [e.student for e in enrollments if e.student_id]
    
    attendance_qs = TransportAttendance.objects.filter(date=date).filter(
        Q(enrollment__in=enrollments) | (Q(enrollment__isnull=True) & Q(student__in=students))
    )
    # Build a lookup: {(enrollment_id|student_id, time, action): attendance_obj}
    attendance_lookup = {}
    for att in attendance_qs:
        if att.enrollment_id:
            attendance_lookup[(att.enrollment_id, att.time, att.action)] = att
        else:
            attendance_lookup[(att.student_id, att.time, att.action)] = att

    grouped = defaultdict(lambda: {"Pickup": [], "Drop": []})

    def _parse_time(value):
        try:
            return datetime.strptime(value, "%I:%M %p").time()
        except Exception:
            return None

    for enrollment in enrollments:
        student = enrollment.student
        batches_today = batches_by_enrollment_id.get(enrollment.id, [])
        if not batches_today or not student:
            continue

        earliest = min(
            batches_today,
            key=lambda b: (_parse_time(getattr(b, 'start_time', None)) or datetime.max.time()),
        )
        latest = max(
            batches_today,
            key=lambda b: (_parse_time(getattr(b, 'end_time', None)) or datetime.min.time()),
        )

        # For Pickup
        pickup_time_obj = _parse_time(getattr(earliest, 'start_time', None))
        if not pickup_time_obj:
            continue

        pickup_time_str = str(getattr(earliest, 'start_time', ''))
        pickup_attendance = (
            attendance_lookup.get((enrollment.id, pickup_time_str, "Pickup"))
            or attendance_lookup.get((student.id, pickup_time_str, "Pickup"))
        )
        grouped[pickup_time_obj]["Pickup"].append({
            "enrollment": enrollment,
            "attendance": pickup_attendance,
        })

        # For Drop
        drop_time_obj = _parse_time(getattr(latest, 'end_time', None))
        if not drop_time_obj:
            continue

        drop_time_str = str(getattr(latest, 'end_time', ''))
        drop_attendance = (
            attendance_lookup.get((enrollment.id, drop_time_str, "Drop"))
            or attendance_lookup.get((student.id, drop_time_str, "Drop"))
        )
        grouped[drop_time_obj]["Drop"].append({
            "enrollment": enrollment,
            "attendance": drop_attendance,
        })

    sorted_grouped = OrderedDict(sorted(grouped.items()))

    return render(request, "registration/students_pick_drop.html", {
        "current_day": current_day,
        "date": date,
        "prev_date": prev_date,
        "next_date": next_date,
        "driver": driver,
        "grouped_transports": sorted_grouped,
        'academic_sessions': sessions,
        'active_session': active_session,
        'selected_session': selected_session,
    })


@login_required(login_url='login')
def delete_transport_attendance(request):
    # Allow both superusers and drivers to delete attendance
    if request.method == "POST":
        enrollment_id = request.POST.get("enrollment_id")
        legacy_student_id = request.POST.get("student_id")
        date_str = request.POST.get("date")
        time = request.POST.get("time")
        action = request.POST.get("action")

        active_session = AcademicSession.get_active()
        selected_session_id = (
            request.GET.get('session')
            or request.GET.get('academic-session')
            or request.POST.get('session')
            or request.POST.get('academic-session')
        )
        selected_session = AcademicSession.objects.filter(id=selected_session_id).first() if selected_session_id else None
        if not selected_session:
            selected_session = active_session

        driver = TransportPerson.objects.filter(user=request.user).first()

        if not driver and not request.user.is_superuser:
            messages.error(request, 'Invalid Driver')
            return redirect('staff_dashboard')

        enrollment_qs = StudentEnrollment.objects.filter(session=selected_session).select_related(
            'student',
            'student__user',
            'transport_details',
            'transport_details__transport_person',
        )
        enrollment = enrollment_qs.filter(id=enrollment_id).first() if enrollment_id else None
        if not enrollment and legacy_student_id:
            enrollment = enrollment_qs.filter(student_id=legacy_student_id).first()
        student = enrollment.student if enrollment else None
        if not enrollment or not student:
            messages.error(request, "Invalid Enrollment")
            redirect_url = reverse('students_pick_drop')
            if selected_session:
                redirect_url += f"?date={datetime.now().date()}&session={selected_session.id}"
            return redirect(redirect_url)

        try:
            date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            messages.error(request, "Invalid date format.")
            return redirect('students_pick_drop')

        attendance_filter = {
            'enrollment': enrollment,
            'date': date_obj,
            'time': time,
            'action': action,
        }
        if not request.user.is_superuser:
            attendance_filter['driver'] = driver

        attendance = TransportAttendance.objects.filter(**attendance_filter).first()
        if not attendance:
            # Legacy fallback
            legacy_filter = {
                'student': student,
                'enrollment__isnull': True,
                'date': date_obj,
                'time': time,
                'action': action,
            }
            if not request.user.is_superuser:
                legacy_filter['driver'] = driver
            attendance = TransportAttendance.objects.filter(**legacy_filter).first()

        if attendance:
            attendance.delete()
            messages.success(request, f"{action} attendance deleted for {student.user.first_name} on {date_obj}.")
        else:
            messages.error(request, "Attendance record not found.")

        if request.user and request.user.is_superuser:
            transport_person = None
            try:
                transport_person = enrollment.transport_details.transport_person if enrollment else None
            except Exception:
                transport_person = None
            if transport_person:
                return redirect(f"{reverse('transport_attendance', args=[transport_person.id])}?date={date_obj}")
            return redirect(f"{reverse('drivers_list')}?date={date_obj}")
            
        redirect_url = f"{reverse('students_pick_drop')}?date={date_obj}"
        if selected_session:
            redirect_url += f"&session={selected_session.id}"
        return redirect(redirect_url)
    return redirect('students_pick_drop')