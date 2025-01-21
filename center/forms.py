from django.db import transaction
from django import forms
from user.models import BaseUser
from .models import Student, Batch, Center, Teacher

class TeacherRegistrationForm(forms.ModelForm):
    first_name = forms.CharField(max_length=255, required=True)
    last_name = forms.CharField(max_length=255, required=False)
    phone = forms.CharField(max_length=15, required=True)
    password = forms.CharField(widget=forms.PasswordInput, required=True)

    batches = forms.ModelMultipleChoiceField(queryset=Batch.objects.all(), required=True)
    center = forms.ModelChoiceField(queryset=Center.objects.all(), required=True)

    class Meta:
        model = Teacher
        fields = ['first_name', 'last_name', 'phone', 'batches', 'center', 'password']

    def clean(self):
        cleaned_data = super().clean()
        
        phone = cleaned_data.get('phone')
        batches = cleaned_data.get('batches')

        if not phone:
            self.add_error('phone', "Phone is required.")
        else:
            if len(phone) != 10:
                self.add_error('phone', "Phone must be exactly 10 digits.")

            elif not phone.isdigit():
                self.add_error('phone', "Phone must contain only digits.")

            elif BaseUser.objects.filter(phone=phone).exists():
                self.add_error('phone', "Phone is already taken.")

        if not batches:
            self.add_error('batches', "At least one batch must be assigned.")
        
        return cleaned_data

    def save(self, commit=True):
        with transaction.atomic():
            user = BaseUser.objects.create_user(
                first_name=self.cleaned_data['first_name'],
                last_name=self.cleaned_data['last_name'],
                phone=self.cleaned_data['phone'],
                password=self.cleaned_data['password']
            )

            teacher = super().save(commit=False)
            teacher.user = user
            if commit:
                teacher.save()
                teacher.batches.set(self.cleaned_data['batches'])

            return teacher

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
            self.add_error('phone', "Phone is required.")
        else:
            if len(phone) != 10:
                self.add_error('phone', "Phone must be exactly 10 digits.")

            elif not phone.isdigit():
                self.add_error('phone', "Phone must contain only digits.")

            elif BaseUser.objects.filter(phone=phone).exists():
                self.add_error('phone', "Phone is already taken.")

        if not batches:
            self.add_error('batches', "At least one batch must be assigned.")
        
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


class StudentUpdateForm(forms.ModelForm):
    first_name = forms.CharField(max_length=255, required=True)
    last_name = forms.CharField(max_length=255, required=False)
    phone = forms.CharField(max_length=15, required=True)
    batches = forms.ModelMultipleChoiceField(queryset=Batch.objects.all(), required=True)

    class Meta:
        model = Student
        fields = ['first_name', 'last_name', 'phone', 'batches']

    def __init__(self, *args, **kwargs):
        student_instance = kwargs.get('instance')
        if student_instance:
            kwargs.update(initial={
                'first_name': student_instance.user.first_name,
                'last_name': student_instance.user.last_name,
                'phone': student_instance.user.phone,
            })
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        
        phone = cleaned_data.get('phone')
        batches = cleaned_data.get('batches')

        if not phone:
            self.add_error('phone', "Phone is required.")
        else:
            if len(phone) != 10:
                self.add_error('phone', "Phone must be exactly 10 digits.")
            elif not phone.isdigit():
                self.add_error('phone', "Phone must contain only digits.")
            elif BaseUser.objects.filter(phone=phone).exclude(id=self.instance.user.id).exists():
                self.add_error('phone', "Phone is already taken.")

        if not batches:
            self.add_error('batches', "At least one batch must be assigned.")
        
        return cleaned_data

    def save(self, commit=True):
        student = super().save(commit=False)
        if commit:
            student.user.first_name = self.cleaned_data['first_name']
            student.user.last_name = self.cleaned_data['last_name']
            student.user.phone = self.cleaned_data['phone']
            student.user.save()
            student.batches.set(self.cleaned_data['batches'])
            student.save()
        return student
class TeacherUpdateForm(forms.ModelForm):
    first_name = forms.CharField(max_length=255, required=True)
    last_name = forms.CharField(max_length=255, required=False)
    phone = forms.CharField(max_length=15, required=True)
    batches = forms.ModelMultipleChoiceField(queryset=Batch.objects.all(), required=True)

    class Meta:
        model = Teacher
        fields = ['first_name', 'last_name', 'phone', 'batches']

    def __init__(self, *args, **kwargs):
        teacher_instance = kwargs.get('instance')
        if teacher_instance:
            kwargs.update(initial={
                'first_name': teacher_instance.user.first_name,
                'last_name': teacher_instance.user.last_name,
                'phone': teacher_instance.user.phone,
            })
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        
        phone = cleaned_data.get('phone')
        batches = cleaned_data.get('batches')

        if not phone:
            self.add_error('phone', "Phone is required.")
        else:
            if len(phone) != 10:
                self.add_error('phone', "Phone must be exactly 10 digits.")
            elif not phone.isdigit():
                self.add_error('phone', "Phone must contain only digits.")
            elif BaseUser.objects.filter(phone=phone).exclude(id=self.instance.user.id).exists():
                self.add_error('phone', "Phone is already taken.")

        if not batches:
            self.add_error('batches', "At least one batch must be assigned.")
        
        return cleaned_data

    def save(self, commit=True):
        teacher = super().save(commit=False)
        if commit:
            teacher.user.first_name = self.cleaned_data['first_name']
            teacher.user.last_name = self.cleaned_data['last_name']
            teacher.user.phone = self.cleaned_data['phone']
            teacher.user.save()
            teacher.batches.set(self.cleaned_data['batches'])
            teacher.save()
        return teacher

