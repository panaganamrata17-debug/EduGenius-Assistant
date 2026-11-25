from django.contrib import admin

# Register your models here.
from .models import StudentProfile, Course, Enrollment, UserProfile, CourseTopic, QuizQuestion

admin.site.register(StudentProfile)
admin.site.register(Course)
admin.site.register(Enrollment)
admin.site.register(UserProfile)
admin.site.register(CourseTopic)
admin.site.register(QuizQuestion)


