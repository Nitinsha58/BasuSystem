import secrets
import string
from django.db import models
from center.models import ClassName
from inquiry_followup.models import Inquiry
from marketing.models import Campaign


def _make_token(length):
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


class TestPaper(models.Model):
    title = models.CharField(max_length=255)
    class_name = models.ForeignKey(
        ClassName, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='sat_papers'
    )
    time_limit = models.PositiveIntegerField(default=60, help_text="Minutes")
    marks_per_correct = models.PositiveIntegerField(default=1, help_text="Marks awarded per correct answer")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    @property
    def max_marks(self):
        return self.questions.count() * self.marks_per_correct


class Question(models.Model):
    DIFFICULTY_CHOICES = [('L1', 'L1 – Easy'), ('L2', 'L2 – Moderate'), ('L3', 'L3 – Hard')]
    SUBJECT_CHOICES = [
        ('Math', 'Mathematics'),
        ('Physics', 'Physics'),
        ('Chemistry', 'Chemistry'),
        ('Science', 'General Science'),
        ('Biology', 'Biology'),
        ('English', 'English'),
        ('Reasoning', 'Logical Reasoning'),
        ('Other', 'Other'),
    ]
    QUESTION_TYPE_CHOICES = [
        ('Conceptual', 'Conceptual'),
        ('Application', 'Application Based'),
        ('Numerical', 'Numerical Type'),
        ('Analytical', 'Logical / Analytical Thinking'),
        ('Factual', 'Factual / Memory Based'),
        ('Other', 'Other'),
    ]
    ANSWER_CHOICES = [('A', 'A'), ('B', 'B'), ('C', 'C'), ('D', 'D'), ('E', 'E')]

    paper = models.ForeignKey(TestPaper, on_delete=models.CASCADE, related_name='questions')
    order = models.PositiveIntegerField(default=1)
    text = models.TextField(help_text="Supports Markdown: **bold**, *italic*, `code`")
    option_a = models.CharField(max_length=500)
    option_b = models.CharField(max_length=500)
    option_c = models.CharField(max_length=500)
    option_d = models.CharField(max_length=500)
    option_e = models.CharField(max_length=500, blank=True, default='')
    correct_answer = models.CharField(max_length=1, choices=ANSWER_CHOICES)
    difficulty = models.CharField(max_length=2, choices=DIFFICULTY_CHOICES, default='L2')
    subject_tag = models.CharField(max_length=20, choices=SUBJECT_CHOICES, default='Other')
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPE_CHOICES, default='Conceptual')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"Q{self.order} – {self.paper.title}"


class SchoolTestSession(models.Model):
    paper = models.ForeignKey(
        TestPaper, on_delete=models.SET_NULL, null=True, blank=True, related_name='school_sessions',
        help_text="Leave blank to auto-select the paper based on each student's chosen class."
    )
    campaign = models.ForeignKey(
        Campaign, on_delete=models.SET_NULL, null=True, blank=True, related_name='school_test_sessions'
    )
    school_name = models.CharField(max_length=255)
    date = models.DateField()
    session_code = models.CharField(max_length=10, unique=True, editable=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.session_code:
            self.session_code = _make_token(10)
        super().save(*args, **kwargs)

    def __str__(self):
        paper_label = self.paper.title if self.paper_id else 'Auto by class'
        return f"{self.school_name} – {paper_label} ({self.date})"


class TestAssignment(models.Model):
    inquiry = models.ForeignKey(Inquiry, on_delete=models.CASCADE, related_name='sat_assignments')
    paper = models.ForeignKey(TestPaper, on_delete=models.CASCADE, related_name='assignments')
    school_session = models.ForeignKey(
        SchoolTestSession, on_delete=models.SET_NULL, null=True, blank=True, related_name='assignments'
    )
    token = models.CharField(max_length=16, unique=True, editable=False)
    deadline = models.DateTimeField(null=True, blank=True)
    auto_release = models.BooleanField(
        default=False,
        help_text="If enabled, the report is immediately visible to the parent once the test is submitted."
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.token:
            self.token = _make_token(12)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.inquiry.student_name} – {self.paper.title}"

    @property
    def status(self):
        try:
            attempt = self.attempt
        except TestAttempt.DoesNotExist:
            return 'pending'
        if attempt.submitted_at:
            return 'completed'
        return 'started'


class TestAttempt(models.Model):
    assignment = models.OneToOneField(TestAssignment, on_delete=models.CASCADE, related_name='attempt')
    started_at = models.DateTimeField(auto_now_add=True)
    submitted_at = models.DateTimeField(null=True, blank=True)

    # Anti-cheat fields
    question_order = models.JSONField(
        default=list,
        help_text="Shuffled list of Question IDs assigned at attempt creation."
    )
    tab_switch_count = models.PositiveSmallIntegerField(default=0)
    fullscreen_exit_count = models.PositiveSmallIntegerField(default=0)
    auto_submitted = models.BooleanField(
        default=False,
        help_text="True when the client timer triggered submission (not student action)."
    )
    late_by_seconds = models.IntegerField(
        null=True, blank=True,
        help_text="Seconds past the time limit at submission. Negative means early."
    )

    def __str__(self):
        return f"Attempt – {self.assignment}"


class QuestionResponse(models.Model):
    OPTION_CHOICES = [('A', 'A'), ('B', 'B'), ('C', 'C'), ('D', 'D'), ('E', 'E')]

    attempt = models.ForeignKey(TestAttempt, on_delete=models.CASCADE, related_name='responses')
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='responses')
    selected_option = models.CharField(max_length=1, choices=OPTION_CHOICES, null=True, blank=True)
    is_correct = models.BooleanField(null=True, blank=True)
    marks_obtained = models.PositiveSmallIntegerField(default=0)

    class Meta:
        unique_together = ('attempt', 'question')

    def __str__(self):
        return f"{self.attempt} – Q{self.question.order}"


class TestResult(models.Model):
    VISIBILITY_CHOICES = [('hold', 'Hold – Admin only'), ('shared', 'Shared – Visible via link')]

    attempt = models.OneToOneField(TestAttempt, on_delete=models.CASCADE, related_name='result')
    total_marks = models.PositiveIntegerField(default=0)
    max_marks = models.PositiveIntegerField(default=0)
    subject_scores = models.JSONField(
        default=dict,
        help_text='{"Math": {"obtained": 5, "max": 10, "correct": 5, "attempted": 8}}'
    )
    difficulty_scores = models.JSONField(
        default=dict,
        help_text='{"L1": {"obtained": 3, "max": 5, "correct": 3, "attempted": 4}}'
    )
    type_scores = models.JSONField(
        default=dict,
        help_text='{"Conceptual": {"obtained": 5, "max": 10, "correct": 5, "attempted": 8}}'
    )
    visibility = models.CharField(max_length=10, choices=VISIBILITY_CHOICES, default='hold')
    report_token = models.CharField(max_length=20, unique=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.report_token:
            self.report_token = _make_token(16)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Result – {self.attempt.assignment}"

    @property
    def percentage(self):
        if self.max_marks == 0:
            return 0
        return round(self.total_marks / self.max_marks * 100, 1)

    @property
    def scholarship_tier(self):
        pct = self.percentage
        if pct >= 90:
            return {'label': 'Gold · Merit I',   'waiver': '50–75%', 'color': 'gold',   'eligible': True}
        elif pct >= 75:
            return {'label': 'Silver · Merit II',  'waiver': '25–50%', 'color': 'silver', 'eligible': True}
        elif pct >= 50:
            return {'label': 'Bronze · Merit III', 'waiver': '10–25%', 'color': 'amber',  'eligible': True}
        else:
            return {'label': 'Red · Merit IV', 'waiver': '0–10%',  'color': 'red',    'eligible': True}

    @property
    def grade_band(self):
        pct = self.percentage
        if pct >= 90:
            return 'Outstanding'
        elif pct >= 75:
            return 'Excellent'
        elif pct >= 60:
            return 'Good'
        else:
            return 'Average'
