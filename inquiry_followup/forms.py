from user.models import BaseUser
from .models import AdmissionCounselor, FollowUpStatus
from django import forms

class AdmissionCounselorForm(forms.ModelForm):
    user = forms.ModelChoiceField(queryset=BaseUser.objects.all(), required=False)  # Optional user field
    first_name = forms.CharField(max_length=255, required=False)
    last_name = forms.CharField(max_length=255, required=False)
    phone = forms.CharField(max_length=15, required=False)

    class Meta:
        model = AdmissionCounselor
        fields = ['user', 'first_name', 'last_name', 'phone', 'center']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # If updating an existing instance, populate fields
        if self.instance and self.instance.pk:
            self.fields['user'].initial = self.instance.user
            self.fields['first_name'].initial = self.instance.user.first_name
            self.fields['last_name'].initial = self.instance.user.last_name
            self.fields['phone'].initial = self.instance.user.phone

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
            # If a user is provided, use it directly
            admission_counselor = super().save(commit=False)
            admission_counselor.user = user
        else:
            # Create a new BaseUser if user is not provided
            base_user = BaseUser.objects.create(
                first_name=cleaned_data['first_name'],
                last_name=cleaned_data['last_name'],
                phone=cleaned_data['phone'],
            )
            admission_counselor = super().save(commit=False)
            admission_counselor.user = base_user

        if commit:
            admission_counselor.save()
        return admission_counselor
