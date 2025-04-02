from django.urls import path
from .views import (
    student_registration, 
    student_fees_details, 
    student_parent_details, 
    student_transport_details,
    student_update,
    students_list,
    student_reg_doc,
    delete_installment,
    search_students,
    print_receipt,
    mark_attendance,
    get_attendance,
    add_teacher,
    update_teacher
    )


urlpatterns = [
    path('', students_list, name='students_list'),
    path('search-students/', search_students, name='search_students'),
    path('registration', student_registration, name='student_registration'),
    path('<uuid:stu_id>', student_update, name='student_update'),
    path('<uuid:stu_id>/parent', student_parent_details, name='student_parent_details'),
    path('<uuid:stu_id>/fees', student_fees_details, name='student_fees_details'),
    path('<uuid:stu_id>/transport', student_transport_details, name='student_transport_details'),
    path('<uuid:stu_id>/registration_document', student_reg_doc, name='student_reg_doc'),
    path('<uuid:stu_id>/receipt', print_receipt, name='receipt'),
    path('delete_installment/<uuid:stu_id>/<int:ins_id>', delete_installment, name='delete_installment'),
    path('mark_attendance/', mark_attendance, name='attendance'),
    path('mark_attendance/<int:batch_id>', mark_attendance, name='mark_attendance'),
    path('get_attendance/<int:batch_id>', get_attendance, name='get_attendance'),

    path('add_teacher/', add_teacher, name='add_teacher'),
    path('update_teacher/<int:teacher_id>', update_teacher, name='update_teacher'),
]