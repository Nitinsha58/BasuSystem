from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect
from django.contrib import messages

# Create your views here.
def staff_login(request):
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


