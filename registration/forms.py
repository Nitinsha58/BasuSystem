from django import forms
from django.contrib.auth.hashers import make_password
from django.db import transaction
from .models import Student, BaseUser, ParentDetails, FeeDetails, Installment, TransportDetails, Batch, Teacher
from center.models import Subject
from django.core.exceptions import ValidationError
from django.contrib import messages
from django.db import IntegrityError


class StudentRegistrationForm(forms.ModelForm):
    first_name = forms.CharField(max_length=255)
    last_name = forms.CharField(max_length=255, required=False)
    phone = forms.CharField(max_length=15)
    subjects = forms.ModelMultipleChoiceField(queryset=Subject.objects.all(), required=False)
    
    class Meta:
        model = Student
        fields = [
            "dob", 
            "doj", 
            "email", 
            "school_name", 
            "class_enrolled", 
            "marksheet_submitted", 
            "sat_score", 
            "remarks", 
            "address", 
            "last_year_marks_details", 
            "aadhar_card_number", 
            "gender", 
            "subjects",
            "course",
            "program_duration"
        ]
    
    def clean_phone(self):
        phone = self.cleaned_data.get("phone")
        if not phone.isdigit():
            self.add_error("phone", "Phone number must contaon only digits.")
        if len(phone) < 10:
            self.add_error("phone", "Phone number must be at least 10 digits long.")

        if phone and BaseUser.objects.filter(phone=phone).exists() and Student.objects.filter(user__phone=phone).exists():
            self.add_error("phone", "Already taken")
        return phone

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if email and Student.objects.exclude(pk=self.instance.pk).filter(email=email).exists():
            self.add_error("email", "A student with this email already exists.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        dob = cleaned_data.get("dob")
        doj = cleaned_data.get("doj")

        if dob and doj and doj < dob:
            self.add_error("doj", "Date of joining cannot be earlier than date of birth.")

        return cleaned_data

    def save(self, commit=True):
        with transaction.atomic():
            # Create User

            user = BaseUser.objects.filter(phone=self.cleaned_data['phone']).first()
            if not user:
                user = BaseUser.objects.create(
                    first_name=self.cleaned_data['first_name'],
                    last_name=self.cleaned_data['last_name'],
                    phone=self.cleaned_data['phone'],
                    password=make_password("basu@123")  # Default password
                )

            # Create Student
            student = super().save(commit=False)
            student.user = user  
            if commit:
                student.save()
                self.cleaned_data['subjects'] and student.subjects.set(self.cleaned_data['subjects'])  

        return student


class StudentUpdateForm(forms.ModelForm):
    first_name = forms.CharField(max_length=255)
    last_name = forms.CharField(max_length=255, required=False)
    phone = forms.CharField(max_length=15)
    email = forms.EmailField(required=False)
    subjects = forms.ModelMultipleChoiceField(queryset=Subject.objects.all())
    batches = forms.ModelMultipleChoiceField(queryset=Batch.objects.all(), required=False)

    class Meta:
        model = Student
        fields = [
            "dob", 
            "doj",
            "email",
            "school_name", 
            "class_enrolled", 
            "marksheet_submitted", 
            "sat_score", 
            "remarks", 
            "subjects",
            "address", 
            "last_year_marks_details", 
            "aadhar_card_number", 
            "gender",
            "course",
            "program_duration",
            "batches",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.user:
            self.fields['first_name'].initial = self.instance.user.first_name
            self.fields['last_name'].initial = self.instance.user.last_name
            self.fields['phone'].initial = self.instance.user.phone

    def clean_phone(self):
        phone = self.cleaned_data.get("phone")
        if not phone.isdigit():
            self.add_error("phone", "Phone number must contaon only digits.")
        if len(phone) < 10:
            self.add_error("phone", "Phone number must be at least 10 digits long.")

        if phone and BaseUser.objects.exclude(pk=self.instance.user.pk).filter(phone=phone).exists():
            self.add_error("phone", "Already taken")
        return phone

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if email and Student.objects.exclude(pk=self.instance.pk).filter(email=email).exists():
            self.add_error("email", "A student with this email already exists.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        dob = cleaned_data.get("dob")
        doj = cleaned_data.get("doj")

        if dob and doj and doj < dob:
            self.add_error("doj", "Date of joining cannot be earlier than date of birth.")

        return cleaned_data

    def save(self, commit=True):
        with transaction.atomic():
            student = super().save(commit=False)
            user = student.user
            user.first_name = self.cleaned_data['first_name']
            user.last_name = self.cleaned_data['last_name']
            user.phone = self.cleaned_data['phone']

            if commit:
                user.save()
                student.save()
                self.cleaned_data['subjects'] and student.subjects.set(self.cleaned_data['subjects'])
                self.cleaned_data['batches'] and student.batches.add(*self.cleaned_data['batches'])

        return student

class ParentDetailsForm(forms.ModelForm):
    father_name = forms.CharField(max_length=255, required=False)
    mother_name = forms.CharField(max_length=255, required=False)
    father_contact = forms.CharField(max_length=10, required=False)
    mother_contact = forms.CharField(max_length=10, required=False)

    class Meta:
        model = ParentDetails
        fields = ["father_name", "mother_name", "father_contact", "mother_contact"]

    def clean_father_contact(self):
        father_contact = self.cleaned_data.get("father_contact")
        if father_contact and (not father_contact.isdigit() or len(father_contact) != 10):
            self.add_error("father_contact", "Father's contact must be a 10-digit number.")
        return father_contact

    def clean_mother_contact(self):
        mother_contact = self.cleaned_data.get("mother_contact")
        if mother_contact and (not mother_contact.isdigit() or len(mother_contact) != 10):
            self.add_error("mother_contact", "Mother's contact must be a 10-digit number.")
        return mother_contact

    def save(self, student, commit=True):
        with transaction.atomic():
            parent_details, created = ParentDetails.objects.get_or_create(student=student)
            parent_details.father_name = self.cleaned_data["father_name"]
            parent_details.mother_name = self.cleaned_data["mother_name"]
            parent_details.father_contact = self.cleaned_data["father_contact"]
            parent_details.mother_contact = self.cleaned_data["mother_contact"]
            if commit:
                parent_details.save()
        return parent_details

class TransportDetailsForm(forms.ModelForm):
    address = forms.CharField(max_length=255, required=True)
    class Meta:
        model = TransportDetails
        fields = ["address"]

    def save(self, student, commit=True):
        with transaction.atomic():
            transport_details, created = TransportDetails.objects.get_or_create(student=student)
            transport_details.address = self.cleaned_data["address"]
            if commit:
                transport_details.save()
        return transport_details
    
class TeacherForm(forms.ModelForm):
    user = forms.ModelChoiceField(queryset=BaseUser.objects.all(), required=False)  # Optional user field
    first_name = forms.CharField(max_length=255, required=False)
    last_name = forms.CharField(max_length=255, required=False)
    phone = forms.CharField(max_length=15, required=False)
    batches = forms.ModelMultipleChoiceField(queryset=Batch.objects.all(), required=False)

    class Meta:
        model = Teacher
        fields = ['user', 'first_name', 'last_name', 'phone', 'batches']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # If updating an existing instance, populate fields
        if self.instance and self.instance.pk:
            self.fields['user'].initial = self.instance.user
            self.fields['first_name'].initial = self.instance.user.first_name
            self.fields['last_name'].initial = self.instance.user.last_name
            self.fields['phone'].initial = self.instance.user.phone
            self.fields['batches'].initial = self.instance.batches.all()
    
    def clean(self):
        cleaned_data = super().clean()
        user = cleaned_data.get('user')
        first_name = cleaned_data.get('first_name')
        last_name = cleaned_data.get('last_name')
        phone = cleaned_data.get('phone')

        # If no user is provided, first_name, last_name, and phone are required
        if not user:
            if not first_name:
                self.add_error('first_name', "This field is required when no user is selected.")
            if not last_name:
                self.add_error('last_name', "This field is required when no user is selected.")
            if not phone:
                self.add_error('phone', "This field is required when no user is selected.")

        return cleaned_data

    def save(self, commit=True):
        cleaned_data = self.cleaned_data
        user = cleaned_data.get('user')

        if user:
            teacher = super().save(commit=False)
            teacher.user = user
        else:
            # Check if a user with the same phone already exists
            existing_user = BaseUser.objects.filter(phone=cleaned_data['phone']).first()

            if existing_user:
                self.add_error("phone", "A user with this phone number already exists.")
                return None  # Prevent saving

            # Create a new BaseUser
            base_user = BaseUser.objects.create(
                first_name=cleaned_data['first_name'],
                last_name=cleaned_data['last_name'],
                phone=cleaned_data['phone'],
            )
            teacher = super().save(commit=False)
            teacher.user = base_user

        if commit:
            teacher.save()
            if 'batches' in cleaned_data:
                teacher.batches.set(cleaned_data['batches'])

        return teacher