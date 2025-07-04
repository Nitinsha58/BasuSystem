from django.shortcuts import render, redirect
from .models import Inquiry, ClassName, Subject, Referral, FollowUp, FollowUpStatus, AdmissionCounselor, StationaryPartner
from datetime import datetime, timedelta
from collections import defaultdict
from django.db.models import Max, Q
from django.contrib import messages
from django.utils.timezone import localtime, now


from django.utils import timezone
from calendar import monthrange

def inquiries(request):
    today = timezone.now().date()
    year = int(request.GET.get('year', today.year))
    month = int(request.GET.get('month', today.month))

    if not year or not month:
        year = today.year
        month = today.month

    # Get the first and last day of the selected month
    first_day = datetime(year, month, 1).date()
    last_day = datetime(year, month, monthrange(year, month)[1]).date()

    # Generate all dates for the month
    dates = [first_day + timedelta(days=i) for i in range((last_day - first_day).days + 1)]

    latest_followups = FollowUp.objects.select_related('inquiry').order_by('inquiry', '-created_at').distinct('inquiry')

    inquiry_followup_dict = defaultdict(list)

    status_counts = defaultdict(int)

    for followup in latest_followups:
        if followup.status:
            status_counts[followup.status] += 1

    for followup in latest_followups:
        # created_date = followup.inquiry.created_at.date()
        created_date = followup.created_at.date()
        followup_date = followup.followup_date
        if followup_date:
            inquiry_followup_dict[followup_date].append(followup)
        else:
            inquiry_followup_dict[created_date].append(followup)

    merged_dict = {date: inquiry_followup_dict[date] for date in dates}

    return render(request, 'inquiry_followup/inquiries.html', {
        'dates': merged_dict,
        'followup_status': FollowUpStatus.objects.all(),
        'status_counts': dict(status_counts),
        'current_month': first_day,
        'prev_month': (first_day - timedelta(days=1)),
        'next_month': (last_day + timedelta(days=1)),
        'total_inquiries': Inquiry.objects.count(),
    })

def inquiry(request, inquiry_id):
    classes = ClassName.objects.all()
    subjects = Subject.objects.all()
    referrals = Referral.objects.all()
    lead_types = Inquiry.LEAD_TYPE_CHOICES
    inquiry_obj = Inquiry.objects.filter(id=inquiry_id).first()
    if not inquiry_obj:
        messages.error(request, 'Invalid Inquiry')
        return redirect('inquiries')
    
    followups = FollowUp.objects.filter(inquiry_id=inquiry_id).select_related('status')

    # Fetch all statuses in order
    statuses = FollowUpStatus.objects.all().order_by('order')  # Change 'id' if there's a custom ordering field

    # Initialize dictionary with statuses in order
    followup_status_dict = {status: [] for status in statuses}

    # Fill dictionary with follow-ups
    for followup in followups:
        status = followup.status if followup.status else "No Status"
        followup_status_dict.setdefault(status, []).append(followup)

    if request.method == 'POST':
        student_name = request.POST.get("student_name")
        selected_classes = request.POST.getlist("classes")  # getlist() for multiple selection
        selected_subjects = request.POST.getlist("subjects")
        school_name = request.POST.get("school")
        address = request.POST.get("address")
        lead_type = request.POST.get("lead_type")

        # update inquiry accordingly 
        inquiry_obj.student_name = student_name
        inquiry_obj.school = school_name
        inquiry_obj.address = address
        inquiry_obj.lead_type = lead_type

        # Update many-to-many relationships
        inquiry_obj.classes.set(selected_classes)
        inquiry_obj.subjects.set(selected_subjects)
        inquiry_obj.save()

        messages.success(request, "Inquiry Updated.")
        return redirect('inquiry', inquiry_id=inquiry_id)
    

    return render(request, 'inquiry_followup/inquiry.html', {
        'inquiry': inquiry_obj,
        'followups': dict(followup_status_dict),
        'followup_status': FollowUpStatus.objects.all(),
        'classes':classes,
        'subjects':subjects,
        'referrals': referrals,
        'lead_types': lead_types
    })

def create_followup(request, inquiry_id):
    inquiry_obj = Inquiry.objects.filter(id=inquiry_id).first()

    if not inquiry_obj:
        messages.error(request, "Invalid inquiry")
        return redirect('inquiries')
    
    if request.method == 'POST':
        status_id = request.POST.get('status')
        desc = request.POST.get('description')
        followup_days_gap = request.POST.get('followup_days_gap')
        followup_date = timezone.now() + timedelta(days=int(followup_days_gap))

        counsellor = AdmissionCounselor.objects.filter(user=request.user).first()

        if not counsellor:
            messages.error(request, "Invalid Counsellor.")
            return redirect("inquiries")


        followup = FollowUp.objects.create(
            inquiry = inquiry_obj,
            status = FollowUpStatus.objects.get(id=status_id),
            description = desc,
            admission_counsellor = counsellor,
            followup_date = followup_date if followup_days_gap.isdigit() and int(followup_days_gap) != 0 else None
        )
        followup.save()

    return redirect('inquiry', inquiry_id=inquiry_id)


def delete_inquiry(request, inquiry_id):
    inquiry_obj = Inquiry.objects.filter(id=inquiry_id).first()

    if not inquiry_obj:
        messages.error(request, "Invalid inquiry")
        return redirect('inquiries')
    
    inquiry_obj.delete()
    messages.success(request, "Deleted Inquiry.")
    return redirect('inquiries')


def delete_followup(request, inquiry_id, followup_id):
    followup = FollowUp.objects.filter(id=followup_id).first()
    inquiry_obj = Inquiry.objects.filter(id=inquiry_id).first()

    if not followup and not inquiry_obj:
        messages.error(request, "Invalid Followup or inquiry")
        return redirect('inquiries')
    
    followup.delete()
    messages.success(request, "Deleted Followup")
    
    return redirect('inquiry', inquiry_id=inquiry_id)

def update_followup(request, inquiry_id, followup_id):
    followup = FollowUp.objects.filter(id=followup_id).first()
    inquiry_obj = Inquiry.objects.filter(id=inquiry_id).first()

    if not followup and not inquiry_obj:
        messages.error(request, "Invalid Followup or inquiry")
        return redirect('inquiries')
    
    if request.method == 'POST':
        status_id = request.POST.get('status')
        desc = request.POST.get('description')

        followup.status = FollowUpStatus.objects.get(id=status_id)
        followup.description = desc

        followup.save()

        return redirect('inquiry', inquiry_id=inquiry_id)


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
        existing_member = request.POST.get("existing_member") == "Yes"

        existing_inquiries = Inquiry.objects.filter(phone=phone)
        
        if existing_inquiries:
            if request.user and request.user.is_authenticated and AdmissionCounselor.objects.filter(user=request.user).first():
                
                messages.success(request, "Inquiry Already Exists.")
                return redirect('inquiries')
            
            return render(request, 'success-page.html', {
                'headline': "Thank you, Your Inquiry has already been submitted.",
                'message': "You have taken the first step towards your child's Second Home.",
            })

        inquiry = Inquiry.objects.create(
            student_name=student_name,
            school=school_name,
            address=address,
            phone=phone,
            referral_id=referral_source,
            existing_member=existing_member,
            lead_type='Verified'
        )

        # Add many-to-many relationships (if applicable)
        inquiry.classes.set(selected_classes)
        inquiry.subjects.set(selected_subjects)
        inquiry.save()

        if request.user and request.user.is_authenticated and AdmissionCounselor.objects.filter(user=request.user).first():
            messages.success(request, "Inquiry Created.")
            return redirect('inquiries')
        
        return render(request, 'success-page.html', {
            'headline': "Thank you for submitting your details.",
            'message': "You have taken the first step towards your child's Second Home.",
        })

    return render(request, 'inquiry.html', {
        'classes':classes,
        'subjects':subjects,
        'referrals': referrals
        })

def create_referral_inquiry(request):
    classes = ClassName.objects.all()
    subjects = Subject.objects.all()
    partners = StationaryPartner.objects.all()

    if request.method == "POST":
        student_name = request.POST.get("student-name")
        selected_classes = request.POST.getlist("classes")  # getlist() for multiple selection
        selected_subjects = request.POST.getlist("subjects")
        phone = request.POST.get("phone")
        partner_refrral = request.POST.get("partner")
        existing_member = request.POST.get("existing_member") == "Yes"

        existing_inquiries = Inquiry.objects.filter(phone=phone)
        
        if existing_inquiries:
            if request.user and request.user.is_authenticated and AdmissionCounselor.objects.filter(user=request.user).first():
                
                messages.success(request, "Inquiry Already Exists.")
                return redirect('inquiries')
            
            return render(request, 'success-page.html', {
                'headline': "Thank you, Your Inquiry has already been submitted.",
                'message': "You have taken the first step towards your child's Second Home.",
            })
        
        if not partner_refrral:
            messages.error(request, "Invalid Partner")
            return redirect('create_referral_inquiry')
        else:
            partner = StationaryPartner.objects.filter(id=partner_refrral).first()
            if not partner:
                messages.error(request, "Invalid Partner")
                return redirect('create_referral_inquiry')
            
        inquiry = Inquiry.objects.create(
            student_name=student_name,
            # school=school_name,
            address=partner.address,
            phone=phone,
            stationary_partner=partner,
            existing_member=existing_member
        )

        # Add many-to-many relationships (if applicable)
        inquiry.classes.set(selected_classes)
        inquiry.subjects.set(selected_subjects)
        inquiry.save()

        if request.user and request.user.is_authenticated and AdmissionCounselor.objects.filter(user=request.user).first():
            messages.success(request, "Inquiry Created.")
            return redirect('inquiries')
        
        return render(request, 'success-page.html', {
            'headline': "Thank you for submitting your details.",
            'message': "You have taken the first step towards your child's Second Home.",
        })

    return render(request, 'referral_inquiry.html', {
        'classes':classes,
        'subjects':subjects,
        'partners': partners
        })


def search_inquiries(request):
    search_term = request.GET.get('search', '').strip()
    if search_term:
        inquiries = Inquiry.objects.filter(
            Q(student_name__icontains=search_term) |
            Q(school__icontains=search_term) |
            Q(phone__icontains=search_term)
        )[:10]
        inquiry_list = [
            {   "id": inquiry.id,
                "name": f"{inquiry.student_name}",
                "phone": inquiry.phone,
                "classes": ", ".join(cls.name for cls in inquiry.classes.all()),
                "subjects": ", ".join(subject.name for subject in inquiry.subjects.all()),
                "address": inquiry.address,
            }
            for inquiry in inquiries
        ]
    else:
        inquiry_list = []
    return render(request, 'inquiry_followup/inquiries_results.html', {'inquiries': inquiry_list})

def stationary_partner_inquiries(request, partner_id):
    partner = StationaryPartner.objects.filter(id=partner_id).first()
    if not partner:
        messages.error(request, "Invalid Partner")
        return redirect('inquiries')
    
    
    inquiries = Inquiry.objects.filter(stationary_partner=partner)
    return render(request, 'inquiry_followup/partner_inquiries.html', {
        'inquiries': inquiries,
        'partner': partner
    })
