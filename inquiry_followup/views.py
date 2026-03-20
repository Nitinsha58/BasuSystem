from django.shortcuts import render, redirect
from django.urls import reverse
from django.utils.html import format_html
from .models import Inquiry, ClassName, Subject, FollowUp, FollowUpStatus, AdmissionCounselor, StationaryPartner, ReferralSource
from datetime import datetime, timedelta
from collections import defaultdict
from django.db.models import Max, Q
from django.contrib import messages
from django.utils.timezone import localtime, now
from registration.models import AcademicSession
from marketing.models import Campaign
from .session_selection import select_session_for_date

from django.http import JsonResponse


from django.utils import timezone
from calendar import monthrange

def inquiries(request):
    today = timezone.now().date()
    year = int(request.GET.get('year', today.year))
    month = int(request.GET.get('month', today.month))
    campaign_id = request.GET.get('campaign')

    if not year or not month:
        year = today.year
        month = today.month

    # Get the first and last day of the selected month
    first_day = datetime(year, month, 1).date()
    last_day = datetime(year, month, monthrange(year, month)[1]).date()

    # Generate all dates for the month
    dates = [first_day + timedelta(days=i) for i in range((last_day - first_day).days + 1)]

    latest_followups = FollowUp.objects.select_related('inquiry', 'inquiry__campaign').order_by('inquiry', '-created_at').distinct('inquiry')
    if campaign_id:
        latest_followups = latest_followups.filter(inquiry__campaign_id=campaign_id)

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

    def _campaign_sort_key(fu):
        c = fu.inquiry.campaign
        if c is None:
            return (1, None)
        return (0, -c.created_at.timestamp())

    merged_dict = {date: sorted(inquiry_followup_dict[date], key=_campaign_sort_key) for date in dates}

    total_inquiries = Inquiry.objects.count()
    if campaign_id:
        total_inquiries = Inquiry.objects.filter(campaign_id=campaign_id).count()

    return render(request, 'inquiry_followup/inquiries.html', {
        'dates': merged_dict,
        'followup_status': FollowUpStatus.objects.all(),
        'status_counts': dict(status_counts),
        'current_month': first_day,
        'prev_month': (first_day - timedelta(days=1)),
        'next_month': (last_day + timedelta(days=1)),
        'total_inquiries': total_inquiries,
        'campaigns': Campaign.objects.filter(is_active=True).order_by('-created_at'),
        'selected_campaign_id': campaign_id,
    })

def inquiry(request, inquiry_id):
    classes = ClassName.objects.all()
    subjects = Subject.objects.all()
    referral_sources = ReferralSource.objects.filter(is_active=True).order_by('category', 'name')
    campaigns = Campaign.objects.filter(is_active=True).order_by('-created_at')
    lead_types = Inquiry.LEAD_TYPE_CHOICES
    lead_quality_choices = Inquiry.LEAD_QUALITY_CHOICES
    academic_sessions = AcademicSession.objects.all().order_by('-start_date')
    inquiry_obj = Inquiry.objects.filter(id=inquiry_id).first()
    if not inquiry_obj:
        messages.error(request, 'Invalid Inquiry')
        return redirect('inquiries')
    
    followups = FollowUp.objects.filter(inquiry_id=inquiry_id).select_related('status').order_by('-created_at')
    latest_followup = followups.first()

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
        lead_quality = request.POST.get("lead_quality") or None
        parent_name = request.POST.get("parent_name", "").strip()
        parent_phone = request.POST.get("parent_phone", "").strip()
        referral_source_id = request.POST.get("referral_source") or None
        referrer_name = request.POST.get("referrer_name", "").strip()
        referrer_phone = request.POST.get("referrer_phone", "").strip()
        campaign_id = request.POST.get("campaign") or None
        session_id = request.POST.get("session_id")

        inquiry_created_date = localtime(inquiry_obj.created_at).date()

        selected_session = None
        if session_id:
            selected_session = AcademicSession.objects.filter(id=session_id).first()

        # update inquiry accordingly
        inquiry_obj.student_name = student_name
        inquiry_obj.school = school_name
        inquiry_obj.address = address
        inquiry_obj.lead_type = lead_type
        inquiry_obj.lead_quality = lead_quality
        inquiry_obj.parent_name = parent_name
        inquiry_obj.parent_phone = parent_phone
        inquiry_obj.referral_source_id = referral_source_id
        inquiry_obj.referrer_name = referrer_name
        inquiry_obj.referrer_phone = referrer_phone
        inquiry_obj.campaign_id = campaign_id

        # Enforce: only associate a session if inquiry year matches session start year.
        # Never leave session NULL if any sessions exist (fallbacks handled by helper).
        if selected_session and selected_session.start_date and selected_session.start_date.year == inquiry_created_date.year:
            inquiry_obj.session = selected_session
        else:
            if session_id:
                messages.warning(
                    request,
                    "Selected session year doesn't match inquiry year; assigning best matching session instead.",
                )
            inquiry_obj.session = select_session_for_date(inquiry_created_date)

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
        'classes': classes,
        'subjects': subjects,
        'referral_sources': referral_sources,
        'campaigns': campaigns,
        'lead_types': lead_types,
        'lead_quality_choices': lead_quality_choices,
        'latest_followup': latest_followup,
        'academic_sessions': academic_sessions,
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
    referral_sources = ReferralSource.objects.filter(is_active=True).order_by('category', 'name')

    is_counsellor = (
        request.user
        and request.user.is_authenticated
        and AdmissionCounselor.objects.filter(user=request.user).exists()
    )

    is_superuser = bool(
        request.user
        and request.user.is_authenticated
        and request.user.is_superuser
    )

    if request.method == "POST":
        student_name = request.POST.get("student-name")
        selected_classes = request.POST.getlist("classes")
        selected_subjects = request.POST.getlist("subjects")
        school_name = request.POST.get("school-name")
        address = request.POST.get("address")
        phone = (request.POST.get("phone") or "").strip()
        referral_source_id = request.POST.get("referral_source") or None
        referrer_name = request.POST.get("referrer_name", "").strip()
        referrer_phone = request.POST.get("referrer_phone", "").strip()
        parent_name = request.POST.get("parent_name", "").strip()
        parent_phone = request.POST.get("parent_phone", "").strip()
        existing_member = request.POST.get("existing_member") == "Yes"

        existing_inquiry = Inquiry.objects.filter(phone=phone).first() if phone else None

        if existing_inquiry:
            if is_counsellor:
                if is_superuser:
                    inquiry_url = reverse('inquiry', kwargs={'inquiry_id': existing_inquiry.id})
                    messages.info(
                        request,
                        format_html(
                            (
                                'Inquiry already exists for phone <b>{}</b>. '
                                '<a href="{}" class="underline">Open existing inquiry</a>.'
                            ),
                            phone,
                            inquiry_url,
                        ),
                    )
                    return redirect('create_inquiry')

                messages.success(request, "Inquiry Already Exists.")
                return redirect('inquiries')

            today = localtime(now()).date()
            old_session_id = existing_inquiry.session_id
            current_session = select_session_for_date(today)

            existing_inquiry.student_name = student_name
            existing_inquiry.school = school_name
            existing_inquiry.address = address
            existing_inquiry.referral_source_id = referral_source_id
            existing_inquiry.referrer_name = referrer_name
            existing_inquiry.referrer_phone = referrer_phone
            existing_inquiry.parent_name = parent_name
            existing_inquiry.parent_phone = parent_phone
            existing_inquiry.existing_member = existing_member
            existing_inquiry.lead_type = 'Verified'
            if current_session:
                existing_inquiry.session = current_session
            existing_inquiry.save()

            existing_inquiry.classes.set(selected_classes)
            existing_inquiry.subjects.set(selected_subjects)

            session_note = "new session" if (current_session and current_session.id != old_session_id) else "same session"
            default_status = FollowUpStatus.objects.order_by('order').first()
            FollowUp.objects.create(
                inquiry=existing_inquiry,
                status=default_status,
                admission_counsellor=None,
                description=f"Parent re-submitted inquiry ({session_note}) on {today.strftime('%d-%b-%Y')}.",
                followup_date=today,
            )

            return render(request, 'success-page.html', {
                'headline': "Thank you, we already have your details.",
                'message': "We’ve recorded your follow-up for the current session.",
            })

        inquiry = Inquiry.objects.create(
            student_name=student_name,
            school=school_name,
            address=address,
            phone=phone,
            referral_source_id=referral_source_id,
            referrer_name=referrer_name,
            referrer_phone=referrer_phone,
            parent_name=parent_name,
            parent_phone=parent_phone,
            existing_member=existing_member,
            lead_type='Verified',
            session=select_session_for_date(localtime(now()).date()),
        )

        inquiry.classes.set(selected_classes)
        inquiry.subjects.set(selected_subjects)
        inquiry.save()

        if is_counsellor:
            messages.success(request, "Inquiry Created.")
            return redirect('inquiries')

        return render(request, 'success-page.html', {
            'headline': "Thank you for submitting your details.",
            'message': "You have taken the first step towards your child's Second Home.",
        })

    return render(request, 'inquiry.html', {
        'classes': classes,
        'subjects': subjects,
        'referral_sources': referral_sources,
        'is_counsellor': is_counsellor,
        'check_inquiry_phone_url': reverse('check_inquiry_phone'),
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
            existing_member=existing_member,
            session=select_session_for_date(localtime(now()).date()),
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
    if not (
        request.user
        and request.user.is_authenticated
        and (
            request.user.is_superuser
            or AdmissionCounselor.objects.filter(user=request.user).exists()
        )
    ):
        return render(request, 'inquiry_followup/inquiries_results.html', {'inquiries': []})

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


def check_inquiry_phone(request):
    if not (
        request.user
        and request.user.is_authenticated
        and request.user.is_superuser
    ):
        return JsonResponse({'exists': False})

    phone = (request.GET.get('phone') or '').strip()
    if phone and not phone.isdigit():
        phone = ''.join(ch for ch in phone if ch.isdigit())

    if len(phone) != 10:
        return JsonResponse({'exists': False})

    inquiry_obj = Inquiry.objects.filter(phone=phone).first()
    if not inquiry_obj:
        return JsonResponse({'exists': False})

    return JsonResponse({
        'exists': True,
        'id': inquiry_obj.id,
        'name': inquiry_obj.student_name,
        'phone': inquiry_obj.phone,
        'url': reverse('inquiry', kwargs={'inquiry_id': inquiry_obj.id}),
    })

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
