from django.db import models
import uuid

from center.models import ClassName, Subject, Section
from user.models import BaseUser

class Batch(models.Model):
    class_name = models.ForeignKey(ClassName, on_delete=models.CASCADE, related_name="batches")
    section = models.ForeignKey(Section, on_delete=models.CASCADE, related_name="batches")
    subject  = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name="batches")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("class_name", "section", "subject")

    def __str__(self):
        class_name = getattr(self.class_name, 'name', 'N/A')
        section = getattr(self.section, 'name', 'N/A')
        subject = getattr(self.subject, 'name', 'N/A')
        return f"{class_name} {subject} {section}"
    
class Teacher(models.Model):
    user = models.OneToOneField(BaseUser, on_delete=models.CASCADE, related_name="teachers")
    batches = models.ManyToManyField('Batch', related_name='teachers')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        full_name = f"{self.user.first_name} {self.user.last_name}".strip()
        return f"{full_name  or self.user.phone}"

class Student(models.Model):
    GENDER_CHOICE = [('Male', 'Male'), ('Female', 'Female'), ('Other', 'Other')]
    COURSE_CHOICE = [
        ('CBSE', 'CBSE'), 
        ('NEET', 'NEET'), 
        ('JEE', 'JEE'),
        ('Apex Course', 'Apex Course'),
        ('Momentum Course', 'Momentum Course'),
        ('Foundation Course', 'Foundation Course'),
        ]
    
    DURATION_CHOICE = [
        ('1 Year', '1 Year'), 
        ('2 Year', '2 Year'), 
        ('3 Year', '3 Year')
    ]
    
    stu_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    user = models.OneToOneField(BaseUser, on_delete=models.CASCADE, related_name="registered_student")
    
    course = models.CharField(max_length=65, choices=COURSE_CHOICE, blank=True, null=True)
    batches = models.ManyToManyField('Batch', related_name='students', blank=True)

    program_duration = models.CharField(max_length=10, choices=DURATION_CHOICE, blank=True, default='1 Year')
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
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, null=True, blank=True)
    registration_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, null=True, blank=True)
    cab_fees = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, null=True, blank=True)
    tuition_fees = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_fees = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    book_fees = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, null=True, blank=True)
    book_discount = models.BooleanField(default=False)
    registration_discount = models.BooleanField(default=False)
    paid_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    remaining_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Fees for {self.student.user.first_name}"

class Installment(models.Model):
    PAYMENT_CHOICES = [
        ('Cash', 'Cash'),
        ('UPI', 'UPI'),
        ('Net Banking', 'Net Banking'),
        ('Credit Card', 'Credit Card'),
        ('Debit Card', 'Debit Card'),
        ('Auto Debit', 'Auto Debit'),
        ('Cheque', 'Cheque'),
    ]
    
    installment_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='installments')
    label = models.CharField(max_length=255, blank=True, null=True)
    payment_type = models.CharField(max_length=255, choices=PAYMENT_CHOICES, blank=True, null=True)

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

class Attendance(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="attendance")
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE, related_name="attendance")
    is_present = models.BooleanField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # class Meta:
    #     unique_together = ('student', 'batch', 'created_at')

    def __str__(self):
        return f"{self.student} - {self.created_at}: {'Present' if self.is_present else 'Absent'}"


class Homework(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Completed', 'Completed')
    ]

    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="homework")
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE, related_name="homework")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Homework for {self.student} - {self.status}"