from django.contrib import admin
from .models import Student, ParentDetails, FeeDetails, Installment, TransportDetails

admin.site.register(Student)
admin.site.register(ParentDetails)
admin.site.register(FeeDetails)
admin.site.register(Installment)
admin.site.register(TransportDetails)