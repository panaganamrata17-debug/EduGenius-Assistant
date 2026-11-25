from django.db import models

# Create your models here.

from django.contrib.auth.models import User


# Student Profile
class StudentProfile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE
    )
    college_name = models.CharField(max_length=200)
    course_name = models.CharField(max_length=100)
    semester = models.IntegerField()

    courses = models.ManyToManyField(
        "Course",
        related_name="students",
        blank=True
    )
    parents = models.ManyToManyField(
        "UserProfile",
        related_name="children",
        blank=True
    )
    def __str__(self):
        return self.user.username


# Courses
class Course(models.Model):
    course_name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    semester = models.IntegerField()

    def __str__(self):
        return self.course_name


# Student Course Enrollment
class Enrollment(models.Model):
    student = models.ForeignKey(
        StudentProfile,
        on_delete=models.CASCADE
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE
    )
    enrolled_date = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"{self.student} - {self.course}"


class CourseTopic(models.Model):
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='topics'
    )

    topic_title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    content = models.TextField(blank=True)
    topic_order = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.course.course_name} - {self.topic_title}"


# User Profile for Student, Teacher and Parent
class UserProfile(models.Model):

    ROLE_CHOICES = [
        ('student', 'Student'),
        ('teacher', 'Teacher'),
        ('parent', 'Parent'),
    ]

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE
    )

    full_name = models.CharField(max_length=150)

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES
    )


#  QUIZ QUESTIONS #

class QuizQuestion(models.Model):

    OPTION_CHOICES = [
        ('A', 'Option A'),
        ('B', 'Option B'),
        ('C', 'Option C'),
        ('D', 'Option D'),
    ]

    topic = models.ForeignKey(
        CourseTopic,
        on_delete=models.CASCADE,
        related_name='quiz_questions'
    )

    question_text = models.TextField()

    option_a = models.CharField(max_length=300)
    option_b = models.CharField(max_length=300)
    option_c = models.CharField(max_length=300)
    option_d = models.CharField(max_length=300)

    correct_option = models.CharField(
        max_length=1,
        choices=OPTION_CHOICES
    )

    explanation = models.TextField(blank=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_quiz_questions'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return self.question_text


# QUIZ ATTEMPTS #

class QuizAttempt(models.Model):

    student = models.ForeignKey(
        StudentProfile,
        on_delete=models.CASCADE,
        related_name='quiz_attempts'
    )

    topic = models.ForeignKey(
        CourseTopic,
        on_delete=models.CASCADE
    )

    score = models.PositiveIntegerField(default=0)

    total_questions = models.PositiveIntegerField(default=0)

    attempted_at = models.DateTimeField(auto_now_add=True)

    @property
    def percentage(self):
        if self.total_questions == 0:
            return 0

        return round(
            (self.score / self.total_questions) * 100
        )

    def __str__(self):
        return f"{self.student} - {self.topic.topic_title}"


# =========================
# STUDENT QUIZ ANSWERS
# =========================

class QuizAnswer(models.Model):

    OPTION_CHOICES = [
        ('A', 'Option A'),
        ('B', 'Option B'),
        ('C', 'Option C'),
        ('D', 'Option D'),
    ]

    attempt = models.ForeignKey(
        QuizAttempt,
        on_delete=models.CASCADE,
        related_name='answers'
    )

    question = models.ForeignKey(
        QuizQuestion,
        on_delete=models.CASCADE
    )

    selected_option = models.CharField(
        max_length=1,
        choices=OPTION_CHOICES
    )

    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.question} - {self.selected_option}"

# Parent and Student Connection
class ParentStudent(models.Model):

    parent = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='linked_students'
    )

    student = models.ForeignKey(
        StudentProfile,
        on_delete=models.CASCADE,
        related_name='linked_parents'
    )

    def __str__(self):
        return f"{self.parent.username} - {self.student.user.username}"


# Student Topic Progress
class StudentTopicProgress(models.Model):

    student = models.ForeignKey(
        StudentProfile,
        on_delete=models.CASCADE,
        related_name='topic_progress'
    )

    topic = models.ForeignKey(
        CourseTopic,
        on_delete=models.CASCADE,
        related_name='student_progress'
    )

    is_completed = models.BooleanField(default=False)

    completed_at = models.DateTimeField(
        null=True,
        blank=True
    )

    def __str__(self):
        return f"{self.student} - {self.topic.topic_title}"

# Announcement model
class Announcement(models.Model):
    title = models.CharField(max_length=200)
    message = models.TextField()

    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.title

class Attendance(models.Model):

    student = models.ForeignKey(
        StudentProfile,
        on_delete=models.CASCADE,
        related_name="attendance_records"
    )

    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE
    )

    date = models.DateField()

    status = models.CharField(
        max_length=10,
        choices=[
            ("Present", "Present"),
            ("Absent", "Absent"),
        ]
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("student", "course", "date")

    def __str__(self):
        return f"{self.student} - {self.course} - {self.date} - {self.status}"
    