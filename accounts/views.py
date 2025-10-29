from collections import defaultdict
from datetime import date, timedelta
import calendar
from django.shortcuts import render, redirect
from django.utils import timezone
from registration.models import Installment
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from .utility import generate_whatsapp_link

@login_required(login_url='login')
def installments(request):
    if not request.user.is_superuser:
        messages.error(request, "You do not have permission to view this page.")
        return redirect('staff_dashboard')
    
    today = timezone.now().date()
    year = int(request.GET.get('year', today.year))
    month = int(request.GET.get('month', today.month))

    # First and last date of selected month
    start_date = date(year, month, 1)
    last_day = calendar.monthrange(year, month)[1]
    end_date = date(year, month, last_day)

    # Generate all days of the selected month
    dates = [start_date + timedelta(days=i) for i in range((end_date - start_date).days + 1)]

    # Query installments
    installments = Installment.objects.select_related('student', 'fee_details__student') \
        .filter(due_date__range=(start_date, end_date), student__active=True) \
        .order_by('due_date')

    status_type = request.GET.get('status_type', 'all')  # default is 'all'


    # Group installments by due date
    installments_by_date = defaultdict(list)
    for inst in installments:
        if status_type == 'pending' and inst.paid:
            continue
        if status_type == 'done' and not inst.paid:
            continue

        if not inst.paid:
            amount_str = f"₹{inst.amount:,.0f}"
            due_date_str = inst.due_date.strftime('%d %B %Y')
            stu_name = inst.student.user.first_name + " " + inst.student.user.last_name
            
            try:
                if inst.student.parent_details and inst.student.parent_details.mother_contact:
                    phone = str(inst.student.parent_details.mother_contact)
                else:
                    raise AttributeError
            except Exception:
                messages.warning(request, f"No parent details for student {inst.student.user.first_name} {inst.student.user.last_name}.")
                phone = str(inst.student.user.phone)
            
            if inst.due_date > today:
                inst.reminder_type = 'upcoming'
                inst.reminder_link = generate_whatsapp_link(
                    f"Dear Parent,\n"
                    f"This is a gentle reminder that {stu_name}'s next installment of {amount_str} is due on {due_date_str}.\n"
                    "We kindly request you to plan the payment accordingly to ensure uninterrupted academic support.\n\n"
                    "Thank you for your continued trust in BASU Classes.\n"
                    "— BASU Classes",
                    '91' + phone
                )
            elif inst.due_date == today:
                inst.reminder_type = 'today'
                inst.reminder_link = generate_whatsapp_link(
                    f"Dear Parent,\n"
                    f"A kind reminder that {stu_name}'s installment of {amount_str} is due today ({due_date_str}).\n"
                    "We request you to complete the payment at your earliest convenience to avoid any disruption in academic services.\n\n"
                    "Your timely support is sincerely appreciated.\n"
                    "— BASU Classes",
                    '91' + phone
                )
            elif inst.due_date < today:
                inst.reminder_type = 'late'
                inst.reminder_link = generate_whatsapp_link(
                    f"Dear Parent,\n"
                    f"We noticed that the installment of {amount_str}, due on {due_date_str}, is still pending.\n"
                    f"We kindly request you to clear the payment at the earliest to maintain smooth academic progress for {stu_name}.\n\n"
                    "Your timely support is sincerely appreciated.\n"
                    "— BASU Classes",
                    '91' + phone
                )
        else:
            inst.reminder_type = None
            inst.reminder_link = None

        installments_by_date[inst.due_date].append(inst)

    # Create final merged data for the template
    merged_data = {date: installments_by_date.get(date, []) for date in dates}

    # Calculate total collection and pending amount for the current month
    monthly_collection = sum(inst.amount for inst in installments if inst.paid)
    monthly_pending = sum(inst.amount for inst in installments if not inst.paid and inst.due_date <= today)
    total = sum(inst.amount for inst in installments)

    # For previous/next month navigation
    prev_month = (start_date - timedelta(days=1)).replace(day=1)
    next_month = (end_date + timedelta(days=1)).replace(day=1)

    type_monthly_collection = None
    payment_types = Installment.PAYMENT_CHOICES

    if 'type_of_payment' in request.GET:
        type_of_payment = request.GET.get('type_of_payment')

        # First filter by status
        filtered_installments = []
        for inst in installments:
            if status_type == 'pending' and not inst.paid:
                filtered_installments.append(inst)
            elif status_type == 'done' and inst.paid:
                filtered_installments.append(inst)
            elif status_type == 'all':
                filtered_installments.append(inst)

        # Then filter by payment type
        if type_of_payment == 'any':
            type_monthly_collection = sum(inst.amount for inst in filtered_installments if inst.paid)
        else:
            type_monthly_collection = sum(
                inst.amount for inst in filtered_installments 
                if inst.payment_type == type_of_payment
            )


    return render(request, 'accounts/installments.html', {
        'dates': merged_data,
        'current_month': start_date,
        'today': today,
        'prev_month': {'year': prev_month.year, 'month': prev_month.month},
        'next_month': {'year': next_month.year, 'month': next_month.month},
        'monthly_collected': monthly_collection,
        'monthly_pending': monthly_pending,
        'total' : total,
        'type_monthly_collection': type_monthly_collection,
        'payment_types': payment_types,
        'selected_type': request.GET.get('type_of_payment', None),
        'status_type': status_type,
    })
