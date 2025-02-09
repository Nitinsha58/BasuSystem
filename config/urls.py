from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings
import debug_toolbar

urlpatterns = [
    path('__debug__/', include(debug_toolbar.urls)),
    path('admin/', admin.site.urls),
    path("", include("center.urls")),
    path("user/", include("user.urls")),
    path("mock-progress/", include("testprogress.urls")),
    path("", include("inquiry_followup.urls")),
    path("student/", include("registration.urls")),

] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
