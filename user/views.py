from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required


def staff_login(request):
    if request.user.is_authenticated:
        return redirect('staff_dashboard')
    if request.method == "POST":
        username = request.POST.get("username")  
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)
        print("Post Request")
        if user is not None:
            login(request, user)
            return redirect("staff_dashboard")
        else:
            messages.error(request, "Invalid credentials")
    return render(request, "user/staff_login.html")

@login_required(login_url='staff_login')
def staff_logout(request):
    logout(request)  # Log the user out
    messages.success(request, "You have been logged out successfully.")  # Optional message
    return redirect('staff_login')
