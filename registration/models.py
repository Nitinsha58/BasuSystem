from django.db import models
import uuid
from django.db.models import Max
from colorfield.fields import ColorField
from .manager import AttendanceManager


from center.models import ClassName, Subject, Section
from user.models import BaseUser


class AcademicSession(models.Model):
    name = models.CharField( max_length=20, unique=True, help_text="Eg: 2025-26")

    start_date = models.DateField()
    end_date = models.DateField()

    is_active = models.BooleanField( default=False, help_text="Only one session should be active at a time")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-start_date"]

    def __str__(self):
        return self.name

    @classmethod
    def get_active(cls):
        return cls.objects.filter(is_active=True).first()

    def activate(self):
        AcademicSession.objects.filter(is_active=True).update(is_active=False)
        self.is_active = True
        self.save()


class ReportPeriod(models.Model):
    name = models.CharField(max_length=50, unique=True)
    start_date = models.DateField()
    end_date = models.DateField()

    def __str__(self):
        return f"({self.start_date} - {self.end_date})"

class Day(models.Model):
    name = models.CharField(max_length=20, unique=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Days"

class Batch(models.Model):
    BATCH_TIME_CHOICES = [
        ('12:00 AM', '12:00 AM'), ('12:15 AM', '12:15 AM'), ('12:30 AM', '12:30 AM'), ('12:45 AM', '12:45 AM'), ('01:00 AM', '01:00 AM'), ('01:15 AM', '01:15 AM'), ('01:30 AM', '01:30 AM'), ('01:45 AM', '01:45 AM'), ('02:00 AM', '02:00 AM'), ('02:15 AM', '02:15 AM'), ('02:30 AM', '02:30 AM'), ('02:45 AM', '02:45 AM'), ('03:00 AM', '03:00 AM'), ('03:15 AM', '03:15 AM'), ('03:30 AM', '03:30 AM'), ('03:45 AM', '03:45 AM'), ('04:00 AM', '04:00 AM'), ('04:15 AM', '04:15 AM'), ('04:30 AM', '04:30 AM'), ('04:45 AM', '04:45 AM'), ('05:00 AM', '05:00 AM'), ('05:15 AM', '05:15 AM'), ('05:30 AM', '05:30 AM'), ('05:45 AM', '05:45 AM'), ('06:00 AM', '06:00 AM'), ('06:15 AM', '06:15 AM'), ('06:30 AM', '06:30 AM'), ('06:45 AM', '06:45 AM'), ('07:00 AM', '07:00 AM'), ('07:15 AM', '07:15 AM'), ('07:30 AM', '07:30 AM'), ('07:45 AM', '07:45 AM'), ('08:00 AM', '08:00 AM'), ('08:15 AM', '08:15 AM'), ('08:30 AM', '08:30 AM'), ('08:45 AM', '08:45 AM'), ('09:00 AM', '09:00 AM'), ('09:15 AM', '09:15 AM'), ('09:30 AM', '09:30 AM'), ('09:45 AM', '09:45 AM'), ('10:00 AM', '10:00 AM'), ('10:15 AM', '10:15 AM'), ('10:30 AM', '10:30 AM'), ('10:45 AM', '10:45 AM'), ('11:00 AM', '11:00 AM'), ('11:15 AM', '11:15 AM'), ('11:30 AM', '11:30 AM'), ('11:45 AM', '11:45 AM'), ('12:00 PM', '12:00 PM'), ('12:15 PM', '12:15 PM'), ('12:30 PM', '12:30 PM'), ('12:45 PM', '12:45 PM'), ('01:00 PM', '01:00 PM'), ('01:15 PM', '01:15 PM'), ('01:30 PM', '01:30 PM'), ('01:45 PM', '01:45 PM'), ('02:00 PM', '02:00 PM'), ('02:15 PM', '02:15 PM'), ('02:30 PM', '02:30 PM'), ('02:45 PM', '02:45 PM'), ('03:00 PM', '03:00 PM'), ('03:15 PM', '03:15 PM'), ('03:30 PM', '03:30 PM'), ('03:45 PM', '03:45 PM'), ('04:00 PM', '04:00 PM'), ('04:15 PM', '04:15 PM'), ('04:30 PM', '04:30 PM'), ('04:45 PM', '04:45 PM'), ('05:00 PM', '05:00 PM'), ('05:15 PM', '05:15 PM'), ('05:30 PM', '05:30 PM'), ('05:45 PM', '05:45 PM'), ('06:00 PM', '06:00 PM'), ('06:15 PM', '06:15 PM'), ('06:30 PM', '06:30 PM'), ('06:45 PM', '06:45 PM'), ('07:00 PM', '07:00 PM'), ('07:15 PM', '07:15 PM'), ('07:30 PM', '07:30 PM'), ('07:45 PM', '07:45 PM'), ('08:00 PM', '08:00 PM'), ('08:15 PM', '08:15 PM'), ('08:30 PM', '08:30 PM'), ('08:45 PM', '08:45 PM'), ('09:00 PM', '09:00 PM'), ('09:15 PM', '09:15 PM'), ('09:30 PM', '09:30 PM'), ('09:45 PM', '09:45 PM'), ('10:00 PM', '10:00 PM'), ('10:15 PM', '10:15 PM'), ('10:30 PM', '10:30 PM'), ('10:45 PM', '10:45 PM'), ('11:00 PM', '11:00 PM'), ('11:15 PM', '11:15 PM'), ('11:30 PM', '11:30 PM'), ('11:45 PM', '11:45 PM')]

    class_name = models.ForeignKey(ClassName, on_delete=models.CASCADE, related_name="batches")
    section = models.ForeignKey(Section, on_delete=models.CASCADE, related_name="batches")
    subject  = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name="batches")
    days = models.ManyToManyField('Day', related_name="batches", blank=True)
    start_time = models.CharField(max_length=10, choices=BATCH_TIME_CHOICES, blank=True, null=True)
    end_time = models.CharField(max_length=10, choices=BATCH_TIME_CHOICES, blank=True, null=True)
    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)

    session = models.ForeignKey(AcademicSession, on_delete=models.CASCADE, related_name="batches", null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("class_name", "section", "subject", "session")

    def __str__(self):
        return f"{self.class_name.name} - {self.section.name} - {self.subject.name} - {self.session.name if self.session else 'No Session'}"
    
    def last_attendance_date(self):
        last_attendance = self.attendance.aggregate(last_date=Max('date'))['last_date']
        return last_attendance

    def last_homework_date(self):
        last_homework = self.homework.aggregate(last_date=Max('date'))['last_date']
        return last_homework

    
class Teacher(models.Model):
    user = models.OneToOneField(BaseUser, on_delete=models.CASCADE, related_name="teachers")
    batches = models.ManyToManyField('Batch', related_name='teachers')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        full_name = f"{self.user.first_name} {self.user.last_name}".strip()
        return f"{full_name  or self.user.phone}"

    def active_batches(self):
        return self.batches.filter(session__is_active=True).distinct()
    
    def get_classes(self):
        classes = set()
        for batch in self.active_batches():
            classes.add(batch.class_name)
        return classes

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
    
    # course = models.CharField(max_length=65, choices=COURSE_CHOICE, blank=True, null=True)
    # batches = models.ManyToManyField('Batch', related_name='students', blank=True)

    # program_duration = models.CharField(max_length=10, choices=DURATION_CHOICE, blank=True, default='1 Year')
    email = models.EmailField(unique=True, blank=True, null=True)
    dob = models.DateField()
    doj = models.DateField(blank=True, null=True)
    school_name = models.CharField(max_length=100)
    # class_enrolled = models.ForeignKey(ClassName, on_delete=models.CASCADE, related_name="students")
    # subjects = models.ManyToManyField(Subject, blank=True, related_name='students')
    # marksheet_submitted = models.BooleanField(default=False)
    # sat_score = models.PositiveIntegerField(blank=True, null=True)
    remarks = models.TextField(blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    # last_year_marks_details = models.TextField(blank=True, null=True)
    aadhar_card_number = models.CharField(max_length=20, blank=True, null=True)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICE, blank=True, null=True)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def needs_mentor(self):
        last = self.mentorships.order_by('-updated_at').first()
        return last is None or not last.active
    
    def active_mentorship(self):
        return self.mentorships.filter(active=True).order_by('-updated_at').first()

    def has_active_mentorship(self):
        return self.active_mentorship() is not None

    def __str__(self):
        return self.user.first_name + " " + self.user.last_name
    
    def all_batches(self):
        """return string of all batches the student is enrolled in
        """
        return self.class_enrolled.name + "," + ", ".join([batch.section.name for batch in self.batches.all()])

    def has_latest_report(self):
        latest_report_period = ReportPeriod.objects.order_by('-end_date').first()
        if not latest_report_period:
            return False
        
        start_date = latest_report_period.start_date
        end_date = latest_report_period.end_date
        # Check if the student has any reports in the latest report period
        return self.mentor_remarks.filter(start_date=start_date, end_date=end_date).exists()
    
    def active_enrollment(self):
        return self.enrollments.filter(
        active=True,
            session__is_active=True
        ).first()
    
    def current_batches(self):
        enrollment = self.active_enrollment()
        if not enrollment:
            return []
        return [link.batch for link in enrollment.batch_links.all()]


class StudentEnrollment(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="enrollments")
    session = models.ForeignKey(AcademicSession, on_delete=models.CASCADE, related_name="enrollments")
    class_name = models.ForeignKey( ClassName, on_delete=models.CASCADE, related_name="enrollments")
    course = models.CharField(max_length=65, choices=Student.COURSE_CHOICE, blank=True, null=True)

    program_duration = models.CharField(max_length=10, choices=Student.DURATION_CHOICE, default="1 Year" )
    subjects = models.ManyToManyField(Subject, blank=True, related_name="enrollments" )
    remarks = models.TextField(blank=True, null=True)
    active = models.BooleanField(default=True,help_text="Active enrollment for this session" )

    promoted_from = models.ForeignKey("self", null=True, blank=True, on_delete=models.SET_NULL, related_name="promoted_to")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("student", "session")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.student} | {self.session}"
    
    @property
    def is_current(self):
        return self.session.is_active and self.active

    def deactivate(self):
        self.active = False
        self.save(update_fields=["active"])

    @classmethod
    def get_current_for_student(cls, student):
        return cls.objects.filter(
            student=student,
            session__is_active=True,
            active=True
        ).first()


class EnrollmentBatch(models.Model):
    enrollment = models.ForeignKey("StudentEnrollment", on_delete=models.CASCADE, related_name="batch_links")
    batch = models.ForeignKey("registration.Batch", on_delete=models.CASCADE, related_name="enrollment_links")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("enrollment", "batch")



class StudentBatchLink(models.Model):
    student = models.ForeignKey('Student', on_delete=models.CASCADE, related_name='batch_links')
    enrollment = models.ForeignKey('StudentEnrollment', on_delete=models.CASCADE, null=True, blank=True, related_name='student_batch_links')
    batch = models.ForeignKey('Batch', on_delete=models.CASCADE, related_name='student_links')
    active = models.BooleanField(default=True)
    joined_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('student', 'batch', 'enrollment')
    
    def __str__(self):
        return f"{self.student.user.first_name} - {self.batch}"

class ParentDetails(models.Model):
    parent_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    student = models.OneToOneField(Student, on_delete=models.CASCADE, related_name='parent_details')
    enrollment = models.OneToOneField( StudentEnrollment, on_delete=models.CASCADE, null=True, blank=True, related_name="parent_details")

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

    enrollment = models.OneToOneField("StudentEnrollment", on_delete=models.CASCADE, null=True, blank=True, related_name="fees")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Fee details for {self.student.user.first_name}"

class Installment(models.Model):
    PAYMENT_CHOICES = [
        ('Cash', 'Cash'),
        ('UPI', 'UPI'),
        ('Net Banking', 'Net Banking'),
        ('Credit Card', 'Credit Card'),
        ('Debit Card', 'Debit Card'),
        ('Auto Debit', 'Auto Debit'),
        ('Cheque', 'Cheque'),
        ('UPI + Cash', 'UPI + Cash'),
    ]
    
    installment_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='installments')
    enrollment = models.ForeignKey("StudentEnrollment", on_delete=models.CASCADE, null=True, blank=True, related_name="installments")

    label = models.CharField(max_length=255, blank=True, null=True)
    payment_type = models.CharField(max_length=255, choices=PAYMENT_CHOICES, blank=True, null=True) 
    remark = models.TextField(blank=True, null=True)

    fee_details = models.ForeignKey(FeeDetails, on_delete=models.CASCADE, related_name='installments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    due_date = models.DateField()
    paid = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['due_date'] 

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.fee_details.save()

    def __str__(self):
        return f"Installment for {self.fee_details.student.user.first_name} - {self.amount}"


class TransportPerson(models.Model):
    person_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    name = models.CharField(max_length=255)
    capacity = models.PositiveIntegerField(default=0, blank=True, null=True)
    user = models.ForeignKey(BaseUser, on_delete=models.CASCADE, related_name='transport_person', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class TransportMode(models.Model):
    mode_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class TransportDetails(models.Model):
    transport_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    transport_person = models.ForeignKey(TransportPerson, on_delete=models.CASCADE, related_name='transport', null=True, blank=True)
    transport_mode = models.ForeignKey(TransportMode, on_delete=models.CASCADE, related_name='transport', null=True, blank=True)
    student = models.OneToOneField(Student, on_delete=models.CASCADE, related_name='transport')
    enrollment = models.OneToOneField( StudentEnrollment, on_delete=models.CASCADE, null=True, blank=True, related_name="transport_details")

    address = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Transport details for {self.student.user.first_name}"

class Attendance(models.Model):
    ATTENDANCE_TYPE = [
        ('Regular', 'Regular'),
        ('Remedial', 'Remedial'),
        ('Retest', 'Retest'),
        ('Test', 'Test'),
        ('Extra Class', 'Extra Class'),
        ('Personal Class', 'Personal Class'),
        ('Practice Session', 'Practice Session'),
    ]

    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="attendance")
    enrollment = models.ForeignKey( StudentEnrollment, on_delete=models.CASCADE, null=True, blank=True,related_name="homeworks")
    type = models.CharField(max_length=20, choices=ATTENDANCE_TYPE, default='Regular')
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE, related_name="attendance")
    is_present = models.BooleanField()
    date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = AttendanceManager()


    class Meta:
        unique_together = ('student', 'batch', 'date', 'type')

    def __str__(self):
        return f"{self.student} - {self.created_at}: {'Present' if self.is_present else 'Absent'}"


class Homework(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Partial Done', 'Partial Done'),
        ('Completed', 'Completed')
    ]

    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="homework")
    enrollment = models.ForeignKey( StudentEnrollment, on_delete=models.CASCADE, null=True, blank=True,related_name="attendances")
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE, related_name="homework")
    date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # class Meta:
    #     unique_together = ('student', 'batch', 'date')

    def __str__(self):
        return f"Homework for {self.student} - {self.status}"


class Test(models.Model):
    name = models.CharField(max_length=255)
    date = models.DateField()
    total_max_marks = models.FloatField(default=0)
    no_of_questions = models.IntegerField(default=0)
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE, related_name="test_paper")
    
    objective = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} -  {self.batch.__str__()}"
    
    def calculate_completion(self):
        # Get all students for this batch via EnrollmentBatch (session-aware)
        enrollments_qs = StudentEnrollment.objects.filter(batch_links__batch=self.batch)
        if self.batch.session_id:
            enrollments_qs = enrollments_qs.filter(session_id=self.batch.session_id)
            # For the active session, only count currently-active enrollments
            if getattr(self.batch.session, 'is_active', False):
                enrollments_qs = enrollments_qs.filter(active=True)

        current_batch_students = set(enrollments_qs.values_list('student_id', flat=True).distinct())
        
        # Get all students who have results for this test
        students_with_results = set(self.results.values_list('student_id', flat=True))
        
        # Combine both sets to get total unique students
        all_relevant_students = current_batch_students.union(students_with_results)
        
        if len(all_relevant_students) == 0:
            return 0
                
        # Students who have completed the test
        completed = len(students_with_results)
        
        return (completed / len(all_relevant_students)) * 100

    def calculate_total_max_marks(self):
        # Calculate the total marks for all related TestQuestions
        self.total_max_marks = self.questions.filter(is_main=True).aggregate(
            total=models.Sum('max_marks')
        )['total'] or 0
        self.save()
    
    def is_data_complete_for_graph(self):
        enrollments_qs = StudentEnrollment.objects.filter(batch_links__batch=self.batch)
        if self.batch.session_id:
            enrollments_qs = enrollments_qs.filter(session_id=self.batch.session_id)
            if getattr(self.batch.session, 'is_active', False):
                enrollments_qs = enrollments_qs.filter(active=True)

        student_ids_in_batch = set(enrollments_qs.values_list('student_id', flat=True).distinct())
        student_ids_with_results = set(self.results.values_list('student_id', flat=True))
        student_ids_with_responses = set(self.responses.values_list('student_id', flat=True))

        students_with_data = student_ids_with_results.union(student_ids_with_responses)
        missing_students = student_ids_in_batch - students_with_data

        return len(students_with_data) > 0


class Chapter(models.Model):
    class_name = models.ForeignKey(ClassName, on_delete=models.CASCADE, related_name='chapters')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='chapters')
    chapter_no = models.IntegerField()
    chapter_name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.chapter_no} - {self.chapter_name} - {self.subject.name} - {self.class_name.name}"

class TestQuestion(models.Model):
    test = models.ForeignKey(Test, on_delete=models.CASCADE, related_name='questions')
    question_number = models.IntegerField()
    is_main = models.BooleanField(default=True)
    optional_question = models.OneToOneField('self', on_delete=models.CASCADE, null=True, blank=True, default=None, related_name='optional')
    chapter_no = models.IntegerField(null=True, blank=True)
    chapter_name = models.CharField(max_length=255, null=True, blank=True)
    chapter = models.ForeignKey(Chapter, on_delete=models.CASCADE, related_name='questions', null=True, blank=True)
    max_marks = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Q{self.question_number} - {self.chapter_name}"

class Remark(models.Model):
    name = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class TestResult(models.Model):
    TEST_TYPE_CHOICES = [
        ('Regular', 'Regular'),
        ('Retest', 'Retest'),
    ]
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="results")
    enrollment = models.ForeignKey( StudentEnrollment, on_delete=models.CASCADE, null=True, blank=True, related_name="results")

    test = models.ForeignKey(Test, on_delete=models.CASCADE, related_name="results")
    no_of_questions_attempted = models.IntegerField(default=0)
    total_marks_obtained = models.FloatField(default=0)
    total_max_marks = models.FloatField(default=0)
    percentage = models.FloatField(default=0)
    test_type = models.CharField(max_length=20, choices=TEST_TYPE_CHOICES, default='Regular')
    previous_marks = models.FloatField(default=0, blank=True, null=True)  # For retest comparison
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def mandatory_retest(self):
        if self.no_of_questions_attempted == 0:
            return True
        
        # Calculate the percentage of marks obtained
        if self.total_max_marks > 0:
            self.percentage = (self.total_marks_obtained / self.test.total_max_marks) * 100
        else:
            self.percentage = 0
        
        return self.percentage <= 50

    def optional_retest(self):
        # Calculate the percentage of marks obtained
        if self.total_max_marks > 0:
            self.percentage = (self.total_marks_obtained / self.test.total_max_marks) * 100
        else:
            self.percentage = 0
        
        return self.percentage <= 75 and self.percentage > 50
    class Meta:
        unique_together = ('student', 'test')  # Ensure one result per student per test

    def __str__(self):
        return f"{self.student.user.first_name} - {self.test}: {self.percentage:.2f}%"

class QuestionResponse(models.Model):
    question = models.ForeignKey(TestQuestion, on_delete=models.CASCADE, related_name='responses')
    student = models.ForeignKey('Student', on_delete=models.CASCADE, related_name='responses')
    enrollment = models.ForeignKey( StudentEnrollment, on_delete=models.CASCADE, null=True, blank=True, related_name="responses")

    test = models.ForeignKey(Test, on_delete=models.CASCADE, related_name='responses')
    marks_obtained = models.FloatField()
    remark = models.ForeignKey(Remark, null=True, blank=True, on_delete=models.SET_NULL, related_name='responses')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('question', 'student')  # Ensures a student can only respond once per question

    def __str__(self):
        test_name = getattr(self.test, 'name', 'Unknown Test')
        return f"{self.student} for {self.question} in {test_name}".title()

class RemarkCount(models.Model):
    test = models.ForeignKey(Test, on_delete=models.CASCADE, related_name="remark_count")
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="remark_count")
    enrollment = models.ForeignKey( StudentEnrollment, on_delete=models.CASCADE, null=True, blank=True, related_name="remark_count")

    remark = models.ForeignKey(Remark, on_delete=models.CASCADE, related_name="remark_count")
    count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('student', 'test', 'remark')  # Ensure one count per student per remark

    def __str__(self):
        return f"{self.remark.name}: {self.count}"


class Mentor(models.Model):
    user = models.OneToOneField(BaseUser, on_delete=models.CASCADE, related_name="mentor_profile")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def get_active_students(self):
        return Student.objects.filter(
            mentorship__mentor=self,
            mentorship__active=True
        )
        
    def total_active_mentorships(self):
        return Mentorship.objects.filter(mentor=self, active=True).count()

    def __str__(self):
        full_name = f"{self.user.first_name} {self.user.last_name}".strip()
        return f"{full_name or self.user.phone}"

class Mentorship(models.Model):
    mentor = models.ForeignKey(Mentor, on_delete=models.CASCADE, related_name="mentorships")
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="mentorships")
    enrollment = models.ForeignKey( StudentEnrollment, on_delete=models.CASCADE, null=True, blank=True, related_name="mentorships")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    active = models.BooleanField(default=True)


    def __str__(self):
        return f"{self.mentor.user.first_name} - {self.student.user.first_name} ({'Active' if self.active else 'Inactive'})"


class Recommendation(models.Model):
    ACTION_CHOICES = [
        ('PTM', 'PTM'),
        ('MENTOR', 'Mentor Session'),
    ]
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='recommendations')
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    date = models.DateField()
    active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.student} - {self.action} on {self.date} ({'Active' if self.active else 'Inactive'})"

class MentorRemark(models.Model):
    mentor = models.ForeignKey(Mentor, on_delete=models.CASCADE, related_name="remarks")
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="mentor_remarks")
    mentor_remark = models.TextField(blank=True, null=True)
    mentor_negative = models.ManyToManyField('ReportNegative', related_name="mentor_remarks", blank=True)
    mentor_positive = models.ManyToManyField('ReportPositive', related_name="mentor_remarks", blank=True)
    
    parent_remark = models.TextField(blank=True, null=True)
    parent_negative = models.ManyToManyField('ReportNegative', related_name="parent_remarks", blank=True)
    parent_positive = models.ManyToManyField('ReportPositive', related_name="parent_remarks", blank=True)

    recommendation = models.OneToOneField(Recommendation, on_delete=models.SET_NULL, null=True, blank=True)

    start_date = models.DateField()
    end_date = models.DateField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.mentor.user.first_name} - {self.student.user.first_name} ({self.start_date})"
    
    class Meta:
        unique_together = ('mentor', 'student', 'start_date', 'end_date')

class StudentRemark(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="student_remarks")
    enrollment = models.ForeignKey(StudentEnrollment, on_delete=models.CASCADE, null=True, blank=True, related_name="student_remarks")

    remark = models.TextField(blank=True, null=True)
    added_by = models.ForeignKey(BaseUser, on_delete=models.CASCADE, related_name="added_student_remarks")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.student.user.first_name} - Remark by {self.added_by.first_name}"

class StudentTestRemark(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="test_remarks")
    enrollment = models.ForeignKey(StudentEnrollment, on_delete=models.CASCADE, null=True, blank=True, related_name="test_remarks")

    test = models.ForeignKey(Test, on_delete=models.CASCADE, related_name="test_remarks")
    remark = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.student.user.first_name} - {self.test.name}"
    
    class Meta:
        unique_together = ('student', 'test')

class ReportNegative(models.Model):
    name = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class ReportPositive(models.Model):
    name = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
    
class Action(models.Model):
    name = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    color = ColorField(null=True, blank=True, verbose_name='Color')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Actions"

class ActionSuggested(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="action_suggestions")
    action = models.ManyToManyField(Action, related_name="action_suggestions")
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE, related_name="action_suggestions")
    mentor_remark = models.ForeignKey(MentorRemark, on_delete=models.CASCADE, related_name="action_suggestions", null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        actions = ", ".join([a.name for a in self.action.all()])
        return f"{self.student.user.first_name} - {actions} ({self.batch})"

    class Meta:
        # unique_together cannot include ManyToMany fields like 'action'
        unique_together = ('student', 'batch', 'mentor_remark')

class TransportAttendance(models.Model):
    ATTENDANCE_CHOICES = [
        ('Pickup', 'Pickup'),
        ('Drop', 'Drop'),
        ('None', 'None'),
    ]
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="transport_attendance")
    enrollment = models.ForeignKey( StudentEnrollment, on_delete=models.CASCADE, null=True, blank=True,related_name="transport_attendances")

    is_present = models.BooleanField()
    driver = models.ForeignKey(TransportPerson, on_delete=models.CASCADE, related_name="transport_attendance", null=True, blank=True)
    date = models.DateField()
    time = models.CharField(max_length=10, choices=Batch.BATCH_TIME_CHOICES)
    action = models.CharField(max_length=10, choices=ATTENDANCE_CHOICES, default='None')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.student.user.first_name} - {self.date}: {'Present' if self.is_present else 'Absent'}"
    
