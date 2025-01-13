from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models

class CustomUserManager(BaseUserManager):
    def create_user(self, email, phone, password=None, **extra_fields):
        if not email and not phone:
            raise ValueError("The Email or Phone must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, phone=phone, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, phone, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self.create_user(email, phone, password, **extra_fields)

class BaseUser(AbstractBaseUser, PermissionsMixin):
    first_name = models.CharField(max_length=255, default="")
    last_name = models.CharField(max_length=255, default="")
    email = models.EmailField(unique=True, null=True, blank=True)
    phone = models.CharField(max_length=15, unique=True, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)

    USERNAME_FIELD = 'email'  # Change this to 'phone' if preferred
    REQUIRED_FIELDS = ['phone']  # Adjust as necessary

    objects = CustomUserManager()

    def __str__(self):
        return f" {self.first_name} {self.last_name} {self.email or self.phone}" 



from django.contrib.auth.backends import BaseBackend

class EmailOrPhoneBackend(BaseBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            user = BaseUser.objects.get(models.Q(email=username) | models.Q(phone=username))
        except BaseUser.DoesNotExist:
            return None
        if user.check_password(password):
            return user
        return None

    def get_user(self, user_id):
        try:
            return BaseUser.objects.get(pk=user_id)
        except BaseUser.DoesNotExist:
            return None
