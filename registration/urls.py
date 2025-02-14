from django.urls import path
from .views import (
    student_registration, 
    student_fees_details, 
    student_parent_details, 
    student_transport_details,
    student_update,
    students_list,
    student_reg_doc
    )


urlpatterns = [
    path('', students_list, name='students_list'),
    path('registration', student_registration, name='student_registration'),
    path('<uuid:stu_id>', student_update, name='student_update'),
    path('<uuid:stu_id>/parent', student_parent_details, name='student_parent_details'),
    path('<uuid:stu_id>/fees', student_fees_details, name='student_fees_details'),
    path('<uuid:stu_id>/transport', student_transport_details, name='student_transport_details'),
    path('<uuid:stu_id>/registration_document', student_reg_doc, name='student_reg_doc'),
]