from django.db import transaction
from django import forms
from user.models import BaseUser
from .models import Student, Batch, Center

class StudentRegistrationForm(forms.ModelForm):
    first_name = forms.CharField(max_length=255, required=True)
    last_name = forms.CharField(max_length=255, required=False)
    phone = forms.CharField(max_length=15, required=True)
    password = forms.CharField(widget=forms.PasswordInput, required=True)

    batches = forms.ModelMultipleChoiceField(queryset=Batch.objects.all(), required=True)
    center = forms.ModelChoiceField(queryset=Center.objects.all(), required=True)

    class Meta:
        model = Student
        fields = ['first_name', 'last_name', 'phone', 'batches', 'center', 'password']

    def clean(self):
        cleaned_data = super().clean()
        
        phone = cleaned_data.get('phone')
        batches = cleaned_data.get('batches')

        if not phone:
            self.add_error('phone', "Phone number is required.")

        if not batches:
            self.add_error('batches', "At least one batch must be assigned.")
        
        if phone and BaseUser.objects.filter(phone=phone).exists():
            self.add_error('phone', "Phone number is already taken.")
        
        return cleaned_data

    def save(self, commit=True):
        with transaction.atomic():
            user = BaseUser.objects.create_user(
                first_name=self.cleaned_data['first_name'],
                last_name=self.cleaned_data['last_name'],
                phone=self.cleaned_data['phone'],
                password=self.cleaned_data['password']
            )

            student = super().save(commit=False)
            student.user = user
            if commit:
                student.save()
                student.batches.set(self.cleaned_data['batches'])

            return student
