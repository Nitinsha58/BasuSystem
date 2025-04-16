from collections import defaultdict
from datetime import date, timedelta
import calendar
from django.shortcuts import render, redirect
from django.utils import timezone
from registration.models import Installment
from django.contrib.auth.decorators import login_required
from django.contrib import messages

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
        .filter(due_date__range=(start_date, end_date)) \
        .order_by('due_date')

    # Group installments by due date
    installments_by_date = defaultdict(list)
    for inst in installments:
        installments_by_date[inst.due_date].append(inst)

    # Create final merged data for the template
    merged_data = {date: installments_by_date.get(date, []) for date in dates}

    # Calculate total collection and pending amount for the current month
    monthly_collection = sum(inst.amount for inst in installments if inst.paid)
    monthly_pending = sum(inst.amount for inst in installments if not inst.paid)

    # For previous/next month navigation
    prev_month = (start_date - timedelta(days=1)).replace(day=1)
    next_month = (end_date + timedelta(days=1)).replace(day=1)

    return render(request, 'accounts/installments.html', {
        'dates': merged_data,
        'current_month': start_date,
        'today': today,
        'prev_month': {'year': prev_month.year, 'month': prev_month.month},
        'next_month': {'year': next_month.year, 'month': next_month.month},
        'monthly_collection': monthly_collection,
        'monthly_pending': monthly_pending,
    })
