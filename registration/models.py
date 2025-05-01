from django.db import models
import uuid
from django.db.models import Max


from center.models import ClassName, Subject, Section
from user.models import BaseUser

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
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("class_name", "section", "subject")

    def __str__(self):
        class_name = getattr(self.class_name, 'name', 'N/A')
        section = getattr(self.section, 'name', 'N/A')
        subject = getattr(self.subject, 'name', 'N/A')
        return f"{class_name} {subject} {section}"
    
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
    
    course = models.CharField(max_length=65, choices=COURSE_CHOICE, blank=True, null=True)
    batches = models.ManyToManyField('Batch', related_name='students', blank=True)

    program_duration = models.CharField(max_length=10, choices=DURATION_CHOICE, blank=True, default='1 Year')
    email = models.EmailField(unique=True, blank=True, null=True)
    dob = models.DateField()
    doj = models.DateField(blank=True, null=True)
    school_name = models.CharField(max_length=100)
    class_enrolled = models.ForeignKey(ClassName, on_delete=models.CASCADE, related_name="students")
    subjects = models.ManyToManyField(Subject, blank=True, related_name='students')
    marksheet_submitted = models.BooleanField(default=False)
    sat_score = models.PositiveIntegerField(blank=True, null=True)
    remarks = models.TextField(blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    last_year_marks_details = models.TextField(blank=True, null=True)
    aadhar_card_number = models.CharField(max_length=20, blank=True, null=True)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICE, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.user.first_name + " " + self.user.last_name

class ParentDetails(models.Model):
    parent_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    student = models.OneToOneField(Student, on_delete=models.CASCADE, related_name='parent_details')
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
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Fees for {self.student.user.first_name}"

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
    label = models.CharField(max_length=255, blank=True, null=True)
    payment_type = models.CharField(max_length=255, choices=PAYMENT_CHOICES, blank=True, null=True)

    fee_details = models.ForeignKey(FeeDetails, on_delete=models.CASCADE, related_name='installments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    due_date = models.DateField()
    paid = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.fee_details.save()

    def __str__(self):
        return f"Installment for {self.fee_details.student.user.first_name} - {self.amount}"

class TransportDetails(models.Model):
    transport_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    student = models.OneToOneField(Student, on_delete=models.CASCADE, related_name='transport')
    address = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Transport details for {self.student.user.first_name}"

class Attendance(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="attendance")
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE, related_name="attendance")
    is_present = models.BooleanField()
    date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # class Meta:
    #     unique_together = ('student', 'batch', 'created_at')

    def __str__(self):
        return f"{self.student} - {self.created_at}: {'Present' if self.is_present else 'Absent'}"


class Homework(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Partial Done', 'Partial Done'),
        ('Completed', 'Completed')
    ]

    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="homework")
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE, related_name="homework")
    date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Homework for {self.student} - {self.status}"


class Test(models.Model):
    name = models.CharField(max_length=255)
    date = models.DateField()
    total_max_marks = models.FloatField(default=0)
    no_of_questions = models.IntegerField(default=0)
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE, related_name="test_paper")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} -  {self.batch.__str__()}"

    def calculate_total_max_marks(self):
        # Calculate the total marks for all related TestQuestions
        self.total_max_marks = self.questions.filter(is_main=True).aggregate(
            total=models.Sum('max_marks')
        )['total'] or 0
        self.save()

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
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="results")
    test = models.ForeignKey(Test, on_delete=models.CASCADE, related_name="results")
    no_of_questions_attempted = models.IntegerField(default=0)
    total_marks_obtained = models.FloatField(default=0)
    total_max_marks = models.FloatField(default=0)
    percentage = models.FloatField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('student', 'test')  # Ensure one result per student per test

    def __str__(self):
        return f"{self.student.user.first_name} - {self.test}: {self.percentage:.2f}%"

class QuestionResponse(models.Model):
    question = models.ForeignKey(TestQuestion, on_delete=models.CASCADE, related_name='responses')
    student = models.ForeignKey('Student', on_delete=models.CASCADE, related_name='responses')
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
    remark = models.ForeignKey(Remark, on_delete=models.CASCADE, related_name="remark_count")
    count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('student', 'test', 'remark')  # Ensure one count per student per remark

    def __str__(self):
        return f"{self.remark.name}: {self.count}"

# class Mentor(models.Model):
#     user = models.OneToOneField(BaseUser, on_delete=models.CASCADE, related_name="mentor_profile")
#     students = models.ManyToManyField('Student', related_name="mentors", blank=True)
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)

#     def __str__(self):
#         full_name = f"{self.user.first_name} {self.user.last_name}".strip()
#         return full_name or self.user.phone
#     def get_students(self):
#         return self.students.all()

# class MentorReview(models.Model):
#     student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="mentor_reviews")
#     mentor = models.ForeignKey(Mentor, on_delete=models.CASCADE, related_name="reviews")
#     mentor_review = models.TextField()
#     parent_remark = models.TextField(blank=True, null=True)

#     rating = models.PositiveIntegerField(default=0)
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)

#     def __str__(self):
#         return f"Review by {self.student.user.first_name} for {self.mentor.user.first_name}"
