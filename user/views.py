from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError


def login_user(request):
    if request.user.is_authenticated:
        return redirect('staff_dashboard')
    if request.method == "POST":
        username = request.POST.get("username")  
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect("staff_dashboard")
        else:
            messages.error(request, "Invalid credentials")
    return render(request, "user/login.html")

@login_required(login_url='login')
def logout_user(request):
    logout(request)  # Log the user out
    messages.success(request, "You have been logged out successfully.")  # Optional message
    return redirect('logout')

def change_password(request):
    if request.method == "POST":
        current_password = request.POST.get("current_password")
        new_password = request.POST.get("new_password")
        confirm_password = request.POST.get("confirm_password")

        if new_password != confirm_password:
            messages.error(request, "New password and confirm password do not match.")
            return redirect('change_password')

        try:
            validate_password(new_password, user=request.user)
        except ValidationError as e:
            for error in e.messages:
                messages.error(request, error)
            return redirect('change_password')

        user = authenticate(request, username=request.user.phone, password=current_password)
        if user is not None:
            user.set_password(new_password)
            user.change_password = False
            user.save()
            messages.success(request, "Password changed successfully.")
            return redirect('login')
        else:
            messages.error(request, "Current password is incorrect.")
    return render(request, "user/change_password.html")