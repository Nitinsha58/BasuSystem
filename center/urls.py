from django.urls import path
from .views import ( 
    staff_student_registration,
    staff_dashboard,
    create_test_template,
    create_test_response,
    create_response,
    create_template,
    delete_template,
    create_question,
    update_question,
    update_response    
)

urlpatterns = [
    path('', staff_dashboard, name="staff_dashboard"),
    path('student-registration/', staff_student_registration, name="staff_student_registration"),
    path('create-test-template/', create_test_template, name="create_test_template"),
    path('create-test-response/', create_test_response, name="create_test_response"),
    path('create-test-response/<int:batch_id>/<int:test_id>/', create_response, name="create_response"),
    path('create-test-response/<int:batch_id>/<int:test_id>/<int:student_id>/', create_response, name="create_student_response"),
    path('create-test-response/<int:batch_id>/<int:test_id>/<int:student_id>/<int:question_id>', create_response, name="add_response"),
    path('update-test-response/<int:batch_id>/<int:test_id>/<int:student_id>/<int:response_id>', update_response, name="update_response"),

    path('create-test-template/<int:batch_id>/', create_test_template, name="create_test_template"),
    path('create-template/<int:batch_id>/<int:test_id>/', create_template, name="create_template"),
    path('delete-template/<int:batch_id>/<int:test_id>/', delete_template, name="delete_template"),
    path('create-question/<int:batch_id>/<int:test_id>/', create_question, name="create_question"),
    path('update-question/<int:batch_id>/<int:test_id>/<int:question_id>', update_question, name="update_question"),
]