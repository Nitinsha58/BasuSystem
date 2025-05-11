# middleware.py
from django.shortcuts import redirect
from django.urls import reverse

class ForcePasswordChangeMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            if request.user.change_password:
                if request.path not in [reverse('change_password'), reverse('logout')]:
                    return redirect('change_password')
        return self.get_response(request)
