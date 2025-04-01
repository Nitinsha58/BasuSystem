from django.contrib import admin
from .models import Student, ParentDetails, FeeDetails, Installment, TransportDetails, Batch

admin.site.register(Student)
admin.site.register(ParentDetails)
admin.site.register(FeeDetails)
admin.site.register(Installment)
admin.site.register(TransportDetails)
admin.site.register(Batch)