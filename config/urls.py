from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings
import os

urlpatterns = [
    path('admin/', admin.site.urls),
    path("", include("center.urls")),
    path("user/", include("user.urls")),
    path("mock-progress/", include("testprogress.urls")),
    path("", include("inquiry_followup.urls")),
    path("student/", include("registration.urls")),
    path("accounts/", include("accounts.urls")),
    path("reports/", include("reports.urls")),
    path("lesson/", include("lesson.urls")),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Load Debug Toolbar ONLY when running local settings
dj_settings = os.environ.get("DJANGO_SETTINGS_MODULE", "")

if dj_settings == "config.django.local":
    try:
        import debug_toolbar
        urlpatterns += [
            path("__debug__/", include(debug_toolbar.urls)),
        ]
    except Exception:
        # Fail silently if toolbar not installed in production
        pass
