from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.db import transaction

from .models import BaseUser
from registration.models import Teacher, Mentor, TransportPerson, Batch, AcademicSession
from inquiry_followup.models import AdmissionCounselor, StationaryPartner, SalesPerson
from center.models import Center


# ---------------------------------------------------------------------------
# Profile role detection helper
# ---------------------------------------------------------------------------

_ROLE_LABELS = {
    'teacher':     'Teacher',
    'student':     'Student',
    'mentor':      'Mentor',
    'counsellor':  'Counsellor',
    'transport':   'Transport',
    'partner':     'Partner',
    'salesperson': 'Sales Person',
    'staff':       'Staff Only',
}


def _detect_role(user):
    """Return (role_type, role_obj) for a BaseUser, checking all role models."""
    try:
        return 'teacher', user.teachers
    except Exception:
        pass
    try:
        return 'mentor', user.mentor_profile
    except Exception:
        pass
    try:
        return 'counsellor', user.admission_counsellor
    except Exception:
        pass
    try:
        return 'partner', user.stationary_partner
    except Exception:
        pass
    tp = user.transport_person.first()
    if tp:
        return 'transport', tp
    sp = user.sales_person.first()
    if sp:
        return 'salesperson', sp
    try:
        return 'student', user.registered_student
    except Exception:
        pass
    return 'staff', None


def login_user(request):
    if request.user.is_authenticated:
        return redirect('staff_dashboard')
    if request.method == "POST":
        username = request.POST.get("username")  
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect("staff_dashboard")
        else:
            messages.error(request, "Invalid credentials")
    return render(request, "user/login.html")

@login_required(login_url='login')
def logout_user(request):
    logout(request)  # Log the user out
    messages.success(request, "You have been logged out successfully.")  # Optional message
    return redirect('logout')

def change_password(request):
    if request.method == "POST":
        current_password = request.POST.get("current_password")
        new_password = request.POST.get("new_password")
        confirm_password = request.POST.get("confirm_password")

        if new_password != confirm_password:
            messages.error(request, "New password and confirm password do not match.")
            return redirect('change_password')

        try:
            validate_password(new_password, user=request.user)
        except ValidationError as e:
            for error in e.messages:
                messages.error(request, error)
            return redirect('change_password')

        user = authenticate(request, username=request.user.phone, password=current_password)
        if user is not None:
            user.set_password(new_password)
            user.change_password = False
            user.save()
            messages.success(request, "Password changed successfully.")
            return redirect('login')
        else:
            messages.error(request, "Current password is incorrect.")
    return render(request, "user/change_password.html")


# ---------------------------------------------------------------------------
# Profile Management (superuser only)
# ---------------------------------------------------------------------------

@login_required(login_url='login')
def profile_list(request):
    if not request.user.is_superuser:
        messages.error(request, "You do not have permission to view this page.")
        return redirect('staff_dashboard')

    # Build efficient role lookup sets (one query per model)
    teacher_ids      = set(Teacher.objects.values_list('user_id', flat=True))
    student_ids      = set(BaseUser.objects.filter(registered_student__isnull=False).values_list('id', flat=True))
    mentor_ids       = set(Mentor.objects.values_list('user_id', flat=True))
    transport_ids    = set(TransportPerson.objects.exclude(user=None).values_list('user_id', flat=True))
    counsellor_ids   = set(AdmissionCounselor.objects.values_list('user_id', flat=True))
    partner_ids      = set(StationaryPartner.objects.values_list('user_id', flat=True))
    salesperson_ids  = set(SalesPerson.objects.exclude(user=None).values_list('user_id', flat=True))

    def _role(uid):
        if uid in teacher_ids:     return 'teacher'
        if uid in mentor_ids:      return 'mentor'
        if uid in counsellor_ids:  return 'counsellor'
        if uid in partner_ids:     return 'partner'
        if uid in transport_ids:   return 'transport'
        if uid in salesperson_ids: return 'salesperson'
        if uid in student_ids:     return 'student'
        return 'staff'

    role_filter = request.GET.get('role', '').lower()

    users = list(BaseUser.objects.all().order_by('first_name', 'last_name', 'phone'))
    for u in users:
        u.detected_role = _role(u.id)

    if role_filter and role_filter in _ROLE_LABELS:
        users = [u for u in users if u.detected_role == role_filter]

    orphaned_drivers = TransportPerson.objects.filter(user__isnull=True).order_by('name')

    return render(request, 'user/profile_list.html', {
        'users': users,
        'role_filter': role_filter,
        'role_labels': _ROLE_LABELS,
        'orphaned_drivers': orphaned_drivers,
    })


@login_required(login_url='login')
def profile_create(request):
    if not request.user.is_superuser:
        messages.error(request, "You do not have permission to view this page.")
        return redirect('staff_dashboard')

    active_session = AcademicSession.get_active()
    batches  = Batch.objects.filter(session=active_session).select_related('class_name', 'subject', 'section').order_by('class_name__name', 'subject__name') if active_session else []
    centers  = Center.objects.all().order_by('name')

    if request.method == 'POST':
        first_name = request.POST.get('first_name', '').strip()
        last_name  = request.POST.get('last_name', '').strip()
        phone      = request.POST.get('phone', '').strip()
        is_staff   = request.POST.get('is_staff') == 'on'
        role_type  = request.POST.get('role_type', 'staff').strip()

        errors = []
        if not first_name:
            errors.append("First name is required.")
        if not phone:
            errors.append("Phone is required.")
        elif not phone.isdigit():
            errors.append("Phone must contain only digits.")
        elif len(phone) < 10:
            errors.append("Phone must be at least 10 digits.")
        elif BaseUser.objects.filter(phone=phone).exists():
            errors.append("A user with this phone number already exists.")

        if role_type == 'counsellor' and not request.POST.get('counsellor_center'):
            errors.append("Center is required for Admission Counsellor.")
        if role_type == 'transport' and not request.POST.get('transport_name', '').strip():
            errors.append("Name is required for Transport Person.")
        if role_type == 'partner':
            if not request.POST.get('partner_center'):
                errors.append("Center is required for Stationary Partner.")
            if not request.POST.get('partner_name', '').strip():
                errors.append("Name is required for Stationary Partner.")
            if not request.POST.get('partner_address', '').strip():
                errors.append("Address is required for Stationary Partner.")
        if role_type == 'salesperson':
            if not request.POST.get('salesperson_name', '').strip():
                errors.append("Name is required for Sales Person.")
            utm = request.POST.get('utm_slug', '').strip()
            if not utm:
                errors.append("UTM slug is required for Sales Person.")
            elif SalesPerson.objects.filter(utm_slug=utm).exists():
                errors.append("A sales person with this UTM slug already exists.")

        if errors:
            for e in errors:
                messages.error(request, e)
        else:
            try:
                with transaction.atomic():
                    user = BaseUser.objects.create(
                        first_name=first_name,
                        last_name=last_name,
                        phone=phone,
                        is_staff=is_staff,
                        change_password=True,
                    )
                    user.set_password('basu@123')
                    user.save()

                    if role_type == 'teacher':
                        teacher = Teacher.objects.create(user=user)
                        batch_ids = request.POST.getlist('batches')
                        if batch_ids:
                            teacher.batches.set(Batch.objects.filter(id__in=batch_ids))
                    elif role_type == 'mentor':
                        Mentor.objects.create(user=user)
                    elif role_type == 'counsellor':
                        center = get_object_or_404(Center, id=request.POST.get('counsellor_center'))
                        AdmissionCounselor.objects.create(user=user, center=center)
                    elif role_type == 'transport':
                        transport_name = request.POST.get('transport_name', '').strip()
                        capacity_raw   = request.POST.get('capacity', '0').strip()
                        capacity       = int(capacity_raw) if capacity_raw.isdigit() else 0
                        TransportPerson.objects.create(user=user, name=transport_name, capacity=capacity)
                    elif role_type == 'partner':
                        center = get_object_or_404(Center, id=request.POST.get('partner_center'))
                        StationaryPartner.objects.create(
                            user=user,
                            center=center,
                            name=request.POST.get('partner_name', '').strip(),
                            address=request.POST.get('partner_address', '').strip(),
                        )
                    elif role_type == 'salesperson':
                        SalesPerson.objects.create(
                            user=user,
                            name=request.POST.get('salesperson_name', '').strip(),
                            phone=phone,
                            utm_slug=request.POST.get('utm_slug', '').strip(),
                        )

                full_name = f"{first_name} {last_name}".strip()
                messages.success(request, f"Profile for {full_name} created. Default password: basu@123")
                return redirect('profile_list')
            except Exception as e:
                messages.error(request, f"Error creating profile: {e}")

    return render(request, 'user/profile_form.html', {
        'mode': 'create',
        'batches': batches,
        'centers': centers,
        'active_session': active_session,
        'role_labels': _ROLE_LABELS,
    })


@login_required(login_url='login')
def profile_update(request, user_id):
    if not request.user.is_superuser:
        messages.error(request, "You do not have permission to view this page.")
        return redirect('staff_dashboard')

    target_user  = get_object_or_404(BaseUser, id=user_id)
    active_session = AcademicSession.get_active()
    batches  = Batch.objects.filter(session=active_session).select_related('class_name', 'subject', 'section').order_by('class_name__name', 'subject__name') if active_session else []
    centers  = Center.objects.all().order_by('name')

    current_role, role_obj = _detect_role(target_user)

    if request.method == 'POST':
        first_name = request.POST.get('first_name', '').strip()
        last_name  = request.POST.get('last_name', '').strip()
        phone      = request.POST.get('phone', '').strip()
        is_staff   = request.POST.get('is_staff') == 'on'
        role_type  = request.POST.get('role_type', 'staff').strip() if current_role != 'student' else 'student'

        errors = []
        if not first_name:
            errors.append("First name is required.")
        if not phone:
            errors.append("Phone is required.")
        elif not phone.isdigit():
            errors.append("Phone must contain only digits.")
        elif len(phone) < 10:
            errors.append("Phone must be at least 10 digits.")
        elif BaseUser.objects.exclude(id=target_user.id).filter(phone=phone).exists():
            errors.append("A user with this phone number already exists.")

        if role_type == 'counsellor' and not request.POST.get('counsellor_center'):
            errors.append("Center is required for Admission Counsellor.")
        if role_type == 'transport' and not request.POST.get('transport_name', '').strip():
            errors.append("Name is required for Transport Person.")
        if role_type == 'partner':
            if not request.POST.get('partner_center'):
                errors.append("Center is required for Stationary Partner.")
            if not request.POST.get('partner_name', '').strip():
                errors.append("Name is required for Stationary Partner.")
            if not request.POST.get('partner_address', '').strip():
                errors.append("Address is required for Stationary Partner.")
        if role_type == 'salesperson':
            if not request.POST.get('salesperson_name', '').strip():
                errors.append("Name is required for Sales Person.")
            utm = request.POST.get('utm_slug', '').strip()
            if not utm:
                errors.append("UTM slug is required for Sales Person.")
            elif SalesPerson.objects.exclude(user=target_user).filter(utm_slug=utm).exists():
                errors.append("A sales person with this UTM slug already exists.")

        if errors:
            for e in errors:
                messages.error(request, e)
        else:
            try:
                with transaction.atomic():
                    target_user.first_name = first_name
                    target_user.last_name  = last_name
                    target_user.phone      = phone
                    target_user.is_staff   = is_staff
                    target_user.save()

                    if current_role != 'student' and role_type != current_role:
                        # Remove old role record
                        if current_role == 'teacher':
                            try: target_user.teachers.delete()
                            except Exception: pass
                        elif current_role == 'mentor':
                            try: target_user.mentor_profile.delete()
                            except Exception: pass
                        elif current_role == 'counsellor':
                            try: target_user.admission_counsellor.delete()
                            except Exception: pass
                        elif current_role == 'partner':
                            try: target_user.stationary_partner.delete()
                            except Exception: pass
                        elif current_role == 'transport':
                            target_user.transport_person.all().delete()
                        elif current_role == 'salesperson':
                            # Nullify FK only — preserves inquiry attribution history
                            target_user.sales_person.all().update(user=None)

                    if current_role != 'student':
                        if role_type == 'teacher':
                            teacher, _ = Teacher.objects.get_or_create(user=target_user)
                            batch_ids  = request.POST.getlist('batches')
                            teacher.batches.set(Batch.objects.filter(id__in=batch_ids))
                        elif role_type == 'mentor':
                            Mentor.objects.get_or_create(user=target_user)
                        elif role_type == 'counsellor':
                            center = get_object_or_404(Center, id=request.POST.get('counsellor_center'))
                            counsellor, _ = AdmissionCounselor.objects.get_or_create(user=target_user)
                            counsellor.center = center
                            counsellor.save()
                        elif role_type == 'transport':
                            transport_name = request.POST.get('transport_name', '').strip()
                            capacity_raw   = request.POST.get('capacity', '0').strip()
                            capacity       = int(capacity_raw) if capacity_raw.isdigit() else 0
                            tp = target_user.transport_person.first()
                            if tp:
                                tp.name     = transport_name
                                tp.capacity = capacity
                                tp.save()
                            else:
                                TransportPerson.objects.create(user=target_user, name=transport_name, capacity=capacity)
                        elif role_type == 'partner':
                            center  = get_object_or_404(Center, id=request.POST.get('partner_center'))
                            partner, _ = StationaryPartner.objects.get_or_create(user=target_user)
                            partner.center  = center
                            partner.name    = request.POST.get('partner_name', '').strip()
                            partner.address = request.POST.get('partner_address', '').strip()
                            partner.save()
                        elif role_type == 'salesperson':
                            utm = request.POST.get('utm_slug', '').strip()
                            sp_name = request.POST.get('salesperson_name', '').strip()
                            sp = target_user.sales_person.first()
                            if sp:
                                sp.name     = sp_name
                                sp.utm_slug = utm
                                sp.save()
                            else:
                                SalesPerson.objects.create(
                                    user=target_user,
                                    name=sp_name,
                                    phone=target_user.phone,
                                    utm_slug=utm,
                                )

                full_name = f"{first_name} {last_name}".strip()
                messages.success(request, f"Profile for {full_name} updated successfully.")
                return redirect('profile_list')
            except Exception as e:
                messages.error(request, f"Error updating profile: {e}")

    context = {
        'mode': 'update',
        'target_user': target_user,
        'current_role': current_role,
        'role_obj': role_obj,
        'batches': batches,
        'centers': centers,
        'active_session': active_session,
        'role_labels': _ROLE_LABELS,
    }
    if current_role == 'teacher' and role_obj:
        context['current_batches'] = list(role_obj.batches.values_list('id', flat=True))

    return render(request, 'user/profile_form.html', context)


@login_required(login_url='login')
def profile_toggle_active(request, user_id):
    if not request.user.is_superuser:
        messages.error(request, "You do not have permission to perform this action.")
        return redirect('staff_dashboard')
    if request.method != 'POST':
        return redirect('profile_list')

    target_user = get_object_or_404(BaseUser, id=user_id)
    if target_user.id == request.user.id:
        messages.error(request, "You cannot deactivate your own account.")
        return redirect('profile_list')

    target_user.is_active = not target_user.is_active
    target_user.save()
    status = "activated" if target_user.is_active else "deactivated"
    full_name = f"{target_user.first_name} {target_user.last_name}".strip() or target_user.phone
    messages.success(request, f"{full_name} has been {status}.")
    return redirect('profile_list')


@login_required(login_url='login')
def profile_reset_password(request, user_id):
    if not request.user.is_superuser:
        messages.error(request, "You do not have permission to perform this action.")
        return redirect('staff_dashboard')
    if request.method != 'POST':
        return redirect('profile_list')

    target_user = get_object_or_404(BaseUser, id=user_id)
    target_user.set_password('basu@123')
    target_user.change_password = True
    target_user.save()
    full_name = f"{target_user.first_name} {target_user.last_name}".strip() or target_user.phone
    messages.success(request, f"Password reset to basu@123 for {full_name}. They will be prompted to change it on next login.")
    return redirect('profile_list')


@login_required(login_url='login')
def profile_driver_create_login(request, driver_id):
    """Create a login account for an orphaned TransportPerson (no BaseUser yet)."""
    if not request.user.is_superuser:
        messages.error(request, "You do not have permission to perform this action.")
        return redirect('staff_dashboard')

    driver = get_object_or_404(TransportPerson, id=driver_id, user__isnull=True)

    if request.method == 'POST':
        phone = request.POST.get('phone', '').strip()
        first_name = request.POST.get('first_name', driver.name).strip()
        last_name  = request.POST.get('last_name', '').strip()

        errors = []
        if not phone:
            errors.append("Phone is required.")
        elif not phone.isdigit():
            errors.append("Phone must contain only digits.")
        elif len(phone) < 10:
            errors.append("Phone must be at least 10 digits.")
        elif BaseUser.objects.filter(phone=phone).exists():
            errors.append("A user with this phone number already exists.")

        if errors:
            for e in errors:
                messages.error(request, e)
        else:
            try:
                with transaction.atomic():
                    user = BaseUser.objects.create(
                        first_name=first_name,
                        last_name=last_name,
                        phone=phone,
                        is_staff=True,
                        change_password=True,
                    )
                    user.set_password('basu@123')
                    user.save()
                    driver.user = user
                    driver.save()
                messages.success(request, f"Login created for driver {driver.name}. Default password: basu@123")
                return redirect('profile_update', user_id=user.id)
            except Exception as e:
                messages.error(request, f"Error creating login: {e}")

    return render(request, 'user/driver_create_login.html', {'driver': driver})