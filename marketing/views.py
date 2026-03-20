import json

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.timezone import localtime, now
from django.views.decorators.http import require_POST

from center.models import ClassName, Subject
from inquiry_followup.models import (
    AdmissionCounselor,
    FollowUp,
    FollowUpStatus,
    Inquiry,
    ReferralSource,
)
from inquiry_followup.session_selection import select_session_for_date
from registration.models import AcademicSession

from .forms import CampaignForm
from .models import Campaign


@login_required(login_url='login')
def campaign_create(request):
    form = CampaignForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Campaign created successfully.')
        return redirect('marketing:campaign_list')
    return render(request, 'marketing/campaign_form.html', {'form': form, 'title': 'New Campaign'})


@login_required(login_url='login')
def campaign_edit(request, campaign_id):
    campaign = get_object_or_404(Campaign, pk=campaign_id)
    form = CampaignForm(request.POST or None, instance=campaign)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Campaign updated.')
        return redirect('marketing:campaign_detail', campaign_id=campaign.id)
    return render(request, 'marketing/campaign_form.html', {'form': form, 'campaign': campaign, 'title': 'Edit Campaign'})


@login_required(login_url='login')
def campaign_list(request):
    campaigns = Campaign.objects.annotate(inquiry_count=Count('inquiries')).order_by('-created_at')
    return render(request, 'marketing/campaigns.html', {
        'campaigns': campaigns,
    })


@login_required(login_url='login')
def campaign_detail(request, campaign_id):
    campaign = get_object_or_404(Campaign, pk=campaign_id)

    page = max(1, int(request.GET.get('page', 1)))
    per_page = 50
    offset = (page - 1) * per_page

    inquiry_qs = (
        Inquiry.objects
        .filter(campaign=campaign)
        .prefetch_related('classes', 'subjects')
        .order_by('-created_at')
    )
    total = inquiry_qs.count()
    inquiries = inquiry_qs[offset: offset + per_page]

    # Annotate each inquiry with its latest follow-up status for display
    latest_followups = (
        FollowUp.objects
        .filter(inquiry__campaign=campaign)
        .order_by('inquiry', '-created_at')
        .distinct('inquiry')
        .select_related('status', 'inquiry')
    )
    followup_map = {fu.inquiry_id: fu for fu in latest_followups}
    for inq in inquiries:
        inq.latest_fu = followup_map.get(inq.id)

    classes = ClassName.objects.all()
    subjects = Subject.objects.all()

    return render(request, 'marketing/campaign_detail.html', {
        'campaign': campaign,
        'inquiries': inquiries,
        'total': total,
        'page': page,
        'has_prev': page > 1,
        'has_next': (offset + per_page) < total,
        'prev_page': page - 1,
        'next_page': page + 1,
        'classes': classes,
        'subjects': subjects,
    })


@login_required(login_url='login')
@require_POST
def bulk_create_inquiries(request, campaign_id):
    campaign = get_object_or_404(Campaign, pk=campaign_id)

    try:
        payload = json.loads(request.body)
        rows = payload.get('rows', [])
    except (ValueError, KeyError):
        return JsonResponse({'error': 'Invalid payload'}, status=400)

    today = localtime(now()).date()
    session = select_session_for_date(today)
    default_status = FollowUpStatus.objects.order_by('order').first()

    created_count = 0
    skipped = []

    for row in rows:
        name = (row.get('name') or '').strip()
        phone = (row.get('phone') or '').strip()

        # Skip blank rows
        if not name and not phone:
            continue

        if not phone:
            skipped.append({'name': name, 'phone': '', 'reason': 'Missing phone'})
            continue

        if not name:
            skipped.append({'name': '', 'phone': phone, 'reason': 'Missing name'})
            continue

        # Duplicate phone check
        if Inquiry.objects.filter(phone=phone).exists():
            skipped.append({'name': name, 'phone': phone, 'reason': 'Phone already exists'})
            continue

        school = (row.get('school') or '').strip()
        address = (row.get('address') or '').strip()
        parent_name = (row.get('parent_name') or '').strip()
        parent_phone = (row.get('parent_phone') or '').strip()
        class_ids = [c for c in (row.get('classes') or []) if c]
        subject_ids = [s for s in (row.get('subjects') or []) if s]

        inquiry = Inquiry.objects.create(
            student_name=name,
            phone=phone,
            school=school,
            address=address,
            parent_name=parent_name,
            parent_phone=parent_phone,
            lead_type='Verified',
            campaign=campaign,
            session=session,
        )
        if class_ids:
            inquiry.classes.set(class_ids)
        if subject_ids:
            # The m2m_changed signal on Inquiry.subjects will create the initial FollowUp
            inquiry.subjects.set(subject_ids)
        else:
            # No subjects selected — signal won't fire; create FollowUp manually
            if default_status:
                FollowUp.objects.create(
                    inquiry=inquiry,
                    status=default_status,
                    description=f"Campaign lead: {name}",
                )

        created_count += 1

    return JsonResponse({'created': created_count, 'skipped': skipped})
