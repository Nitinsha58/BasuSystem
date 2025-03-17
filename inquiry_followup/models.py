from django.db import models
from center.models import ClassName, Subject, Center
from user.models import BaseUser
from colorfield.fields import ColorField


class AdmissionCounselor(models.Model):
    user = models.OneToOneField(BaseUser, on_delete=models.CASCADE, related_name="admission_counsellor")
    center = models.ForeignKey(Center, on_delete=models.CASCADE, related_name="admission_counsellor")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        full_name = f"{self.user.first_name} {self.user.last_name}".strip()
        return f"{full_name  or self.user.phone} - {self.center.name}"

class StationaryPartner(models.Model):
    user = models.OneToOneField(BaseUser, on_delete=models.CASCADE, related_name="stationary_partner")
    center = models.ForeignKey(Center, on_delete=models.CASCADE, related_name="stationary_partner")
    name = models.CharField(max_length=255)
    address = models.TextField()

    earned_commission = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    pending_commission = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_commission = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    monthly_incentive = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    lead_incentive = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        full_name = f"{self.user.first_name} {self.user.last_name}".strip()
        return f"{full_name  or self.user.phone} - {self.address}"

class PartnerPayments(models.Model):
    TYPE_OF_PAYMENT_CHOICES = [
        ('Monthly Payment', 'Monthly Payment'),
        ('Incentive', 'Incentive'),
    ]

    PAYMENT_CHOICES = [
        ('Cash', 'Cash'),
        ('UPI', 'UPI'),
        ('Net Banking', 'Net Banking'),
        ('Credit Card', 'Credit Card'),
        ('Debit Card', 'Debit Card'),
        ('Auto Debit', 'Auto Debit'),
    ]
    payment_mode = models.CharField(max_length=255, choices=PAYMENT_CHOICES, blank=True, null=True)

    stationary_partner = models.ForeignKey(StationaryPartner, on_delete=models.CASCADE, related_name='payments')
    payment_amount = models.DecimalField(max_digits=10, decimal_places=2)
    remark = models.TextField()
    date = models.DateField()
    paid_by = models.CharField(max_length=255)
    type_of_payment = models.CharField(max_length=20, choices=TYPE_OF_PAYMENT_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.stationary_partner.name} - {self.amount} on {self.created_at}"

class FollowUpStatus(models.Model):
    name = models.CharField(max_length=255)
    order = models.IntegerField(unique=True)
    color = ColorField(null=True, blank=True, verbose_name='Color')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class Referral(models.Model):
    name = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class Inquiry(models.Model):
    LEAD_TYPE_CHOICES = [
        ('Unverified', 'Unverified'),
        ('Verified', 'Verified'),
        ('Fake', 'Fake'),
    ]
    student_name = models.CharField(max_length=255)
    classes = models.ManyToManyField(ClassName, blank=True)
    subjects = models.ManyToManyField(Subject, blank=True)
    school = models.CharField(max_length=255)
    address = models.TextField()
    phone = models.CharField(max_length=15, unique=True)
    referral = models.ForeignKey(Referral, on_delete=models.SET_NULL, null=True, blank=True, related_name='inquiry')
    stationary_partner = models.ForeignKey(StationaryPartner, on_delete=models.SET_NULL, null=True, blank=True, related_name='inquiries')
    lead_type = models.CharField(max_length=20, choices=LEAD_TYPE_CHOICES, default='Unverified')
    existing_member = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.student_name}"

class FollowUp(models.Model):
    inquiry = models.ForeignKey(Inquiry, on_delete=models.CASCADE, related_name='followup')
    status = models.ForeignKey(FollowUpStatus, on_delete=models.SET_NULL, null=True, blank=True, related_name='followup')
    admission_counsellor = models.ForeignKey(AdmissionCounselor, on_delete=models.SET_NULL, null=True, blank=True)
    description = models.TextField()
    followup_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.inquiry.student_name}-{self.status.name}"