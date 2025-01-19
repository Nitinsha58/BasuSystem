from django.shortcuts import render, redirect
from datetime import datetime, timedelta
from .models import TestStatus, Test
from django.contrib import messages

def index(request):
    today = datetime.today()
    start_date = today - timedelta(days=10)

    dates = [start_date + timedelta(days=i) for i in range(31)]

    tests = Test.objects.all().order_by('-created_at')
    test_status = TestStatus.objects.all()

    if request.method == "POST":
        test = request.POST.get('test')
        status_id = request.POST.get('status')
        date_str = request.POST.get('date')
        date = datetime.strptime(date_str, "%Y-%m-%d")

        if not test or not status_id or not date_str:
            messages.error(request, "Invalid Details.")
            return redirect('test_progress')
        status = TestStatus.objects.filter(id=status_id).first()
        if not status:
            return redirect('test_progress')

        obj = Test.objects.create(name=test, status=status, date=date)
        obj.save()
        return redirect('test_progress')

    return render(request, "testprogress/progress.html", {
        'dates': dates,
        'tests': tests,
        'test_status': test_status,
    })


def update_test_progress(request, test_id):

    test = Test.objects.filter(id=test_id).first()

    if not test:
        messages.error(request, "Invalid Test.")
        return redirect('test_progress')
    
    if request.method == "POST":
        test_name = request.POST.get('test')
        status_id = request.POST.get('status')
        date_str = request.POST.get('date')

        # Validate the input
        if not test_name or not status_id or not date_str:
            messages.error(request, "All fields are required.")
            return redirect('test_progress')

        try:
            test_date = datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            messages.error(request, "Invalid date format.")
            return redirect('test_progress')

        # Fetch the status
        status = TestStatus.objects.filter(id=status_id).first()
        if not status:
            messages.error(request, "Invalid status selected.")
            return redirect('test_progress')

        # Update the test object
        test.name = test_name
        test.status = status
        test.date = test_date
        test.save()

        messages.success(request, "Updated Successful!")
    
    return redirect('test_progress')

def delete_test_progress(request, test_id):

    test = Test.objects.filter(id=test_id).first()

    if not test:
        messages.error(request, "Invalid Test.")
        return redirect('test_progress')
    
    test.delete()
    messages.info(request, "Test Deleted.")
    return redirect('test_progress')


