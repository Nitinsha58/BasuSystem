from django.db import transaction
from django import forms
from user.models import BaseUser
from .models import Student, Batch, Center

class StudentRegistrationForm(forms.ModelForm):
    # Fields for the BaseUser model
    first_name = forms.CharField(max_length=255, required=True)
    last_name = forms.CharField(max_length=255, required=False)
    phone = forms.CharField(max_length=15, required=True)
    password = forms.CharField(widget=forms.PasswordInput, required=True)

    # Fields for the Student model
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
            raise forms.ValidationError("Either phone must be provided.")
        
        if not batches:
            raise forms.ValidationError("At least one batch must be assigned.")

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
