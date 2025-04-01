from django.contrib import admin
from .models import Student, ParentDetails, FeeDetails, Installment, TransportDetails, Batch, Teacher
from .forms import TeacherForm
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db import IntegrityError

class TeacherAdmin(admin.ModelAdmin):
    form = TeacherForm
    list_display = ['user', 'created_at', 'updated_at']

    def save_model(self, request, obj, form, change):
        teacher = form.save(commit=False)  # Call form.save()

        if teacher is None:  # Means an error was added in form.save()
            messages.error(request, "A user with this phone number already exists.")
            return  # Stop saving

        try:
            super().save_model(request, obj, form, change)
            messages.success(request, "Teacher saved successfully!")
        except IntegrityError:
            messages.error(request, "A teacher with this user already exists.")

admin.site.register(Student)
admin.site.register(ParentDetails)
admin.site.register(FeeDetails)
admin.site.register(Installment)
admin.site.register(TransportDetails)
admin.site.register(Batch)
admin.site.register(Teacher)