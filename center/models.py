from django.db import models
from user.models import BaseUser
from django.utils.timezone import now


class Center(models.Model):
    name = models.CharField(max_length=255)
    location = models.TextField()
    contact_number = models.CharField(max_length=15)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class ClassName(models.Model):
    name = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class Section(models.Model):
    name = models.CharField(max_length=50, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    def __str__(self):
        return self.name


class Subject(models.Model):
    name = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class Batch(models.Model):
    class_name = models.ForeignKey(ClassName, on_delete=models.CASCADE, related_name="batch")
    section = models.ForeignKey(Section, on_delete=models.CASCADE, related_name="batch")
    subject  = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name="batch")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("class_name", "section", "subject")

    def __str__(self):
        class_name = getattr(self.class_name, 'name', 'N/A')
        section = getattr(self.section, 'name', 'N/A')
        subject = getattr(self.subject, 'name', 'N/A')
        return f"{class_name} {subject} {section}"



class Student(models.Model):
    user = models.OneToOneField(BaseUser, on_delete=models.CASCADE, related_name="student")
    batches = models.ManyToManyField('Batch', related_name='student')
    center = models.ForeignKey(Center, on_delete=models.CASCADE, related_name="student")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        full_name = f"{self.user.first_name} {self.user.last_name}".strip()
        return f"{full_name  or self.user.phone} - {self.center.name}"


class Test(models.Model):
    name = models.CharField(max_length=255)
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE, related_name="test")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} -  {self.batch.__str__()}"


class TestQuestion(models.Model):
    test = models.ForeignKey(Test, on_delete=models.CASCADE, related_name='question')
    question_number = models.IntegerField()
    is_main = models.BooleanField(default=True)
    optional_question = models.OneToOneField('self', on_delete=models.CASCADE, null=True, blank=True, default=None, related_name='optional')
    chapter_no = models.IntegerField()
    chapter_name = models.CharField(max_length=255)
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

class QuestionResponse(models.Model):
    question = models.ForeignKey(TestQuestion, on_delete=models.CASCADE, related_name='response')
    student = models.ForeignKey('Student', on_delete=models.CASCADE, related_name='question_response')
    test = models.ForeignKey(Test, on_delete=models.CASCADE, related_name='response')
    marks_obtained = models.FloatField()
    remark = models.ManyToManyField('Remark', related_name='remark')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('question', 'student')  # Ensures a student can only respond once per question

    def __str__(self):
        test_name = getattr(self.test, 'name', 'Unknown Test')
        return f"{self.student} for {self.question} in {test_name}".title()


class Attendance(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="attendance")
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE, related_name="attendance")
    is_present = models.BooleanField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # class Meta:
    #     unique_together = ('student', 'batch', 'created_at')

    def __str__(self):
        return f"{self.student} - {self.date}: {'Present' if self.is_present else 'Absent'}"


class Homework(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Completed', 'Completed')
    ]

    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="homework")
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE, related_name="homework")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Homework for {self.student} - {self.status}"
