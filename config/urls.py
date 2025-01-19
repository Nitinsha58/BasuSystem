from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings
urlpatterns = [
    path('admin/', admin.site.urls),
    path("", include("center.urls")),
    path("staff/", include("user.urls")),
    path("mock-progress/", include("testprogress.urls")),

] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
