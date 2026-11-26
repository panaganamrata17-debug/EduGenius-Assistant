
from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),

    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),

    path(
        'student/dashboard/',
        views.student_dashboard,
        name='student_dashboard'
    ),

    path('student/courses/', views.courses_view, name='student_courses'),
    path(
        'student/course/<int:course_id>/',
        views.course_detail_view,
        name='course_detail'
    ),

    path(
        'student/topic/<int:topic_id>/',
        views.topic_detail_view,
        name='topic_detail'
    ),

        # Student Quiz
    path(
        'student/quiz/<int:topic_id>/',
        views.quiz_view,
        name='student_quiz'
    ),

    path(
        'student/revision-practice/',
        views.revision_practice_view,
        name='revision_practice'
    ),

    path(
        'student/learning-progress/',
        views.learning_progress_view,
        name='learning_progress'
    ),

    path(
        'student/ai-study-assistance/',
        views.student_ai_assistance_view,
        name='student_ai_assistance'
    ),

    path(
        'student/weak-topics/',
        views.student_weak_topics_view,
        name='student_weak_topics'
    ),

    path(
        "student/attendance/",
        views.student_attendance_view,
        name="student_attendance"
    ),

    path(
        "student/announcements/",
        views.student_announcements_view,
        name="student_announcements"
    ),

    path(
        'teacher/dashboard/',
        views.teacher_dashboard,
        name='teacher_dashboard'
    ),

    path(
        'teacher/my-students/',
        views.teacher_my_students,
        name='teacher_my_students'
    ),

    path(
        'teacher/create-quiz/',
        views.teacher_create_quiz,
        name='teacher_create_quiz'
    ),
    path(
        'teacher/quiz-history/',
        views.teacher_quiz_history,
        name='teacher_quiz_history'
    ),
    path(
        'teacher/announcements/',
        views.teacher_announcements,
        name='teacher_announcements'
    ),
    path(
        'teacher/student-progress/',
        views.teacher_student_progress,
        name='teacher_student_progress'
    ),
    path(
        "teacher/attendance/",
        views.teacher_attendance,
        name="teacher_attendance"
    ),
    path(
        'parent/dashboard/',
        views.parent_dashboard,
        name='parent_dashboard'
    ),
    path(
        'parent/link-student/',
        views.link_student_view,
        name='link_student'
    ),
    path(
        'parent/student-performance/',
        views.parent_student_performance_view,
        name='parent_student_performance'
    ),
    path(
        'parent/student-progress/',
        views.parent_student_progress_view,
        name='parent_student_progress'
    ),
    path(
        'parent/study-activity/',
        views.parent_study_activity_view,
        name='parent_study_activity'
    ),

    path(
        'parent/announcements/',
        views.parent_announcements_view,
        name='parent_announcements'
    ),
    path(
        "parent/attendance/",
        views.parent_attendance,
        name="parent_attendance"
    ),
    path(
        "profile/",
        views.profile_view,
        name="profile"
    ),
    path('logout/', views.logout_view, name='logout'),
]
