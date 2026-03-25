from django.urls import path
from .views import (
    login_user,
    logout_user,
    change_password,
    profile_list,
    profile_create,
    profile_update,
    profile_toggle_active,
    profile_reset_password,
    profile_driver_create_login,
)


urlpatterns = [
    path('login/', login_user, name="login"),
    path('logout/', logout_user, name="logout"),
    path('change_password/', change_password, name="change_password"),
    path('profiles/', profile_list, name="profile_list"),
    path('profiles/create/', profile_create, name="profile_create"),
    path('profiles/<int:user_id>/edit/', profile_update, name="profile_update"),
    path('profiles/<int:user_id>/toggle-active/', profile_toggle_active, name="profile_toggle_active"),
    path('profiles/<int:user_id>/reset-password/', profile_reset_password, name="profile_reset_password"),
    path('profiles/driver/<int:driver_id>/create-login/', profile_driver_create_login, name="profile_driver_create_login"),
]