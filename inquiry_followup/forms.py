from user.models import BaseUser
from .models import AdmissionCounselor, FollowUpStatus, StationaryPartner, Referral, Inquiry, FollowUp
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


class StationaryPartnerForm(forms.ModelForm):
    user = forms.ModelChoiceField(queryset=BaseUser.objects.all(), required=False)  # Optional user field
    first_name = forms.CharField(max_length=255, required=False)
    last_name = forms.CharField(max_length=255, required=False)
    phone = forms.CharField(max_length=15, required=False)
    password = forms.CharField(widget=forms.PasswordInput, required=False)
    monthly_incentive = forms.DecimalField(max_digits=10, decimal_places=2, required=False)
    lead_incentive = forms.DecimalField(max_digits=10, decimal_places=2, required=False)
    is_active = forms.BooleanField(required=False)

    class Meta:
        model = StationaryPartner
        fields = ['user', 'first_name', 'last_name', 'phone', 'name', 'address', 'center', 'monthly_incentive', 'lead_incentive', 'is_active']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # If updating an existing instance, populate fields
        if self.instance and self.instance.pk:
            self.fields['user'].initial = self.instance.user
            self.fields['first_name'].initial = self.instance.user.first_name
            self.fields['last_name'].initial = self.instance.user.last_name
            self.fields['phone'].initial = self.instance.user.phone
            self.fields['name'].initial = self.instance.name
            self.fields['address'].initial = self.instance.address
            self.fields['monthly_incentive'].initial = self.instance.monthly_incentive
            self.fields['lead_incentive'].initial = self.instance.lead_incentive
            self.fields['is_active'].initial = self.instance.is_active

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
            stationary_partner = super().save(commit=False)
            stationary_partner.user = user
        else:
            # Create a new BaseUser if user is not provided
            base_user = BaseUser.objects.create_user(
                first_name=cleaned_data['first_name'],
                last_name=cleaned_data['last_name'],
                phone=cleaned_data['phone'],
                password='basu@123'
            )
            stationary_partner = super().save(commit=False)
            stationary_partner.user = base_user

        if commit:
            stationary_partner.save()
        return stationary_partner