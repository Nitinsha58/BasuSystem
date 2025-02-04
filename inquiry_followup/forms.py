from user.models import BaseUser
from .models import AdmissionCounselor, FollowUpStatus
from django import forms


class AdmissionCounselorForm(forms.ModelForm):
    # Adding fields from BaseUser into the AdmissionCounselor form
    first_name = forms.CharField(max_length=255)
    last_name = forms.CharField(max_length=255)
    phone = forms.CharField(max_length=15)

    class Meta:
        model = AdmissionCounselor
        fields = ['first_name', 'last_name', 'phone', 'center']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Prepopulate fields if updating an existing instance
        if self.instance and self.instance.pk:
            self.fields['first_name'].initial = self.instance.user.first_name
            self.fields['last_name'].initial = self.instance.user.last_name
            self.fields['phone'].initial = self.instance.user.phone

    def save(self, commit=True):
        # If editing an existing AdmissionCounselor, update the associated BaseUser
        if self.instance and self.instance.pk:
            base_user = self.instance.user
            base_user.first_name = self.cleaned_data['first_name']
            base_user.last_name = self.cleaned_data['last_name']
            base_user.phone = self.cleaned_data['phone']
            base_user.save()
        else:
            # If creating a new AdmissionCounselor, create a new BaseUser first
            base_user = BaseUser.objects.create(
                first_name=self.cleaned_data['first_name'],
                last_name=self.cleaned_data['last_name'],
                phone=self.cleaned_data['phone'],
            )

        # Save the AdmissionCounselor instance and associate it with the BaseUser
        admission_counselor = super().save(commit=False)
        admission_counselor.user = base_user
        if commit:
            admission_counselor.save()
        return admission_counselor
