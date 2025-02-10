from django.db import models
import uuid

from center.models import ClassName, Subject
from user.models import BaseUser

class Student(models.Model):
    GENDER_CHOICE = [('Male', 'Male'), ('Female', 'Female'), ('Other', 'Other')]
    
    stu_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    user = models.OneToOneField(BaseUser, on_delete=models.CASCADE, related_name="registered_student")
    
    email = models.EmailField(unique=True, blank=True, null=True)
    dob = models.DateField()
    doj = models.DateField(blank=True, null=True)
    school_name = models.CharField(max_length=100)
    class_enrolled = models.ForeignKey(ClassName, on_delete=models.CASCADE, related_name="students")
    subjects = models.ManyToManyField(Subject, blank=True, related_name='students')
    marksheet_submitted = models.BooleanField(default=False)
    sat_score = models.PositiveIntegerField(blank=True, null=True)
    remarks = models.TextField(blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    last_year_marks_details = models.TextField(blank=True, null=True)
    aadhar_card_number = models.CharField(max_length=20, blank=True, null=True)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICE, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.user.first_name + " " + self.user.last_name

class ParentDetails(models.Model):
    parent_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    student = models.OneToOneField(Student, on_delete=models.CASCADE, related_name='parent_details')
    father_name = models.CharField(max_length=255, blank=True, null=True)
    mother_name = models.CharField(max_length=255, blank=True, null=True)
    father_contact = models.CharField(max_length=15, blank=True, null=True)
    mother_contact = models.CharField(max_length=15, blank=True, null=True) 
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Parent of {self.student.user.first_name}"

class FeeDetails(models.Model):
    fee_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    student = models.OneToOneField(Student, on_delete=models.CASCADE, related_name='fees')
    book_fees = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, null=True, blank=True)
    uniform_fees = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, null=True, blank=True)
    cab_fees = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, null=True, blank=True)
    tuition_fees = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_fees = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    paid_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    remaining_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Fees for {self.student.user.first_name}"

class Installment(models.Model):
    installment_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='installments')
    fee_details = models.ForeignKey(FeeDetails, on_delete=models.CASCADE, related_name='installments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    due_date = models.DateField()
    paid = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.fee_details.save()

    def __str__(self):
        return f"Installment for {self.fee_details.student.user.first_name} - {self.amount}"

class TransportDetails(models.Model):
    transport_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    student = models.OneToOneField(Student, on_delete=models.CASCADE, related_name='transport')
    address = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Transport details for {self.student.user.first_name}"
