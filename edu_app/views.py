
from django.contrib.auth.models import User
from .models import UserProfile, Attendance
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from .models import Course, StudentProfile, Enrollment, CourseTopic, Announcement
from .models import (QuizQuestion, QuizAttempt, QuizAnswer, ParentStudent, StudentTopicProgress)
from django.db.models import Sum, Count
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import date
import os
from google import genai
from django.db import IntegrityError


# Homepage
def home(request):
    return render(request, 'edu_app/index.html')



# Registration
def register_view(request):

    if request.method == 'POST':

        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip().lower()
        role = request.POST.get('role', '').strip()
        password = request.POST.get('password', '')
        confirm_password = request.POST.get('confirm_password', '')

        # Check required fields
        if not name or not email or not role or not password:
            messages.error(request, 'Please fill in all required fields.')
            return redirect('register')

        # Check password
        if password != confirm_password:
            messages.error(request, 'Passwords do not match.')
            return redirect('register')

        # Check valid role
        if role not in ['student', 'teacher', 'parent']:
            messages.error(request, 'Please select a valid role.')
            return redirect('register')

        # Check duplicate email in username and email fields
        if (
            User.objects.filter(username__iexact=email).exists()
            or User.objects.filter(email__iexact=email).exists()
        ):
            messages.error(request, 'This email is already registered.')
            return redirect('register')

        try:
            # Create user
            user = User.objects.create_user(
                username=email,
                email=email,
                password=password
            )

            # Create user profile
            UserProfile.objects.create(
                user=user,
                full_name=name,
                role=role
            )

        except IntegrityError:
            messages.error(request, 'This email is already registered.')
            return redirect('register')

        # Log out any previous user session
        logout(request)

        messages.success(
            request,
            'Registration successful! Please login.'
        )

        return redirect('login')

    return render(request, 'edu_app/register.html')



# Login
def login_view(request):

    if request.user.is_authenticated:

        try:
            role = request.user.userprofile.role
        except UserProfile.DoesNotExist:
            logout(request)
            return redirect('login')

        if role == 'teacher':
            return redirect('teacher_dashboard')

        elif role == 'parent':
            return redirect('parent_dashboard')

        else:
            return redirect('student_dashboard')

    if request.method == 'POST':

        # Accept either username or email field from login form
        username = (
            request.POST.get('username', '')
            or request.POST.get('email', '')
        ).strip().lower()

        password = request.POST.get('password', '')

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is not None:

            try:
                role = user.userprofile.role
            except UserProfile.DoesNotExist:
                messages.error(
                    request,
                    'Your profile is missing. Please contact the administrator.'
                )
                return redirect('login')

            login(request, user)

            # Remember Me
            if request.POST.get('remember'):
                request.session.set_expiry(1209600)
            else:
                request.session.set_expiry(0)

            if role == 'teacher':
                return redirect('teacher_dashboard')

            elif role == 'parent':
                return redirect('parent_dashboard')

            else:
                return redirect('student_dashboard')

        messages.error(request, 'Invalid email or password.')

    return render(request, 'edu_app/login.html')


# Student Dashboard


def student_dashboard(request):
    if not request.user.is_authenticated:
        return redirect('login')
    try:
        profile = request.user.userprofile
        role = profile.role
    except UserProfile.DoesNotExist:
        return redirect('login')

    if role == 'teacher':
        return redirect('teacher_dashboard')

    elif role == 'parent':
        return redirect('parent_dashboard')

    student_name = profile.full_name

    # Get all available courses from the database
    courses = Course.objects.all()

    return render(
        request,
        'edu_app/student_dashboard.html',
        {
            'student_name': student_name,
            'courses': courses,
        }
    )


# My Courses
# My Courses
def courses_view(request):

    if not request.user.is_authenticated:
        return redirect('login')

    # Get or create the student's profile
    student, created = StudentProfile.objects.get_or_create(
        user=request.user,
        defaults={'semester': 1}
    )

    # Default course subjects
    subjects = [
        "Python Programming",
        "Java Programming",
        "Web Technology",
        "Database Management",
        "Computer Networks",
        "Software Engineering",
    ]

    # Add courses if they do not already exist
    for subject in subjects:
        Course.objects.get_or_create(
            course_name=subject,
            semester=1,
            defaults={
                "description": f"Learn {subject}"
            }
        )

    # Show all available courses to every student
    courses = Course.objects.filter(course_name__in=subjects)

    return render(
        request,
        'edu_app/courses.html',
        {
            'courses': courses,
            'student_name': request.user.userprofile.full_name
        }
    )
def course_detail_view(request, course_id):

    if not request.user.is_authenticated:
        return redirect('login')

    # Get the selected course directly
    course = get_object_or_404(Course, id=course_id)

    # Get topics for this course
    topics = course.topics.all().order_by(
        'topic_order',
        'id'
    )

    return render(
        request,
        'edu_app/course_detail.html',
        {
            'course': course,
            'topics': topics,
            'student_name': request.user.userprofile.full_name
        }
    )



@login_required
def topic_detail_view(request, topic_id):

    try:
        profile = request.user.userprofile
    except UserProfile.DoesNotExist:
        return redirect('login')

    if profile.role != 'student':
        return redirect('student_dashboard')

    student, created = StudentProfile.objects.get_or_create(
        user=request.user,
        defaults={
            'college_name': '',
            'course_name': '',
            'semester': 1
        }
    )

    topic = get_object_or_404(
        CourseTopic.objects.select_related('course'),
        id=topic_id
    )
    # Create progress record if it does not exist
    progress_record, created = StudentTopicProgress.objects.get_or_create(
        student=student,
        topic=topic,
        defaults={
            'is_completed': False
        }
    )

    # Mark topic as completed
    if request.method == 'POST' and request.POST.get('mark_completed') == 'yes':

        if not progress_record.is_completed:
            progress_record.is_completed = True
            progress_record.completed_at = timezone.now()
            progress_record.save()

        messages.success(request, 'Topic marked as completed!')

        return redirect(request.path)

    topics = topic.course.topics.all().order_by(
        'topic_order',
        'id'
    )

    return render(
        request,
        'edu_app/course_detail.html',
        {
            'course': topic.course,
            'topics': topics,
            'topic': topic,
            'progress_record': progress_record,
            'student_name': profile.full_name
        }
    )

# Revision and Practice
def revision_practice_view(request):

    if not request.user.is_authenticated:
        return redirect('login')

    try:
        profile = request.user.userprofile
    except UserProfile.DoesNotExist:
        return redirect('login')

    if profile.role != 'student':
        return redirect('student_dashboard')

    student, created = StudentProfile.objects.get_or_create(
        user=request.user,
        defaults={
            'college_name': '',
            'course_name': '',
            'semester': 1
        }
    )

    topics = CourseTopic.objects.select_related(
        'course'
    ).order_by(
        'course__course_name',
        'topic_order'
    )

    # Selected topic from Start Practice button
    topic_id = request.GET.get('topic')

    # Also get topic ID when quiz is submitted
    if request.method == 'POST':
        topic_id = request.POST.get('topic_id')

    selected_topic = None
    questions = QuizQuestion.objects.none()

    score = None
    total_questions = 0
    quiz_submitted = False

    if topic_id:

        selected_topic = get_object_or_404(
            topics.select_related('course'),
            id=topic_id
        )

        questions = QuizQuestion.objects.filter(
            topic=selected_topic
        ).order_by('id')

        if request.method == 'POST' and questions.exists():

            score = 0
            answer_records = []

            for question in questions:

                selected_option = request.POST.get(
                    f'question_{question.id}', ''
                )

                is_correct = (
                    selected_option == question.correct_option
                )

                if is_correct:
                    score += 1

                answer_records.append({
                    'question': question,
                    'selected_option': selected_option,
                    'is_correct': is_correct
                })

            total_questions = questions.count()

            attempt = QuizAttempt.objects.create(
                student=student,
                topic=selected_topic,
                score=score,
                total_questions=total_questions
            )

            for answer in answer_records:

                if answer['selected_option'] in ['A', 'B', 'C', 'D']:

                    QuizAnswer.objects.create(
                        attempt=attempt,
                        question=answer['question'],
                        selected_option=answer['selected_option'],
                        is_correct=answer['is_correct']
                    )

            quiz_submitted = True

    return render(
        request,
        'edu_app/revision_practice.html',
        {
            'topics': topics,
            'student_name': profile.full_name,
            'selected_topic': selected_topic,
            'questions': questions,
            'score': score,
            'total_questions': total_questions,
            'quiz_submitted': quiz_submitted
        }
    )

# =========================
# STUDENT QUIZ
# =========================

def quiz_view(request, topic_id):

    if not request.user.is_authenticated:
        return redirect('login')

    try:
        profile = request.user.userprofile
    except UserProfile.DoesNotExist:
        return redirect('login')

    if profile.role != 'student':
        return redirect('student_dashboard')

    student, created = StudentProfile.objects.get_or_create(
        user=request.user,
        defaults={
            'college_name': '',
            'course_name': '',
            'semester': 1
        }
    )

    topic = get_object_or_404(
        CourseTopic.objects.select_related('course'),
        id=topic_id
    )

    enrolled = Enrollment.objects.filter(
        student=student,
        course=topic.course
    ).exists()

    if not enrolled:
        return redirect('student_courses')

    questions = QuizQuestion.objects.filter(
        topic=topic
    ).order_by('id')

    if not questions.exists():
        messages.warning(
            request,
            'No quiz questions are available for this topic yet.'
        )

        return render(
            request,
            'edu_app/quiz.html',
            {
                'topic': topic,
                'questions': questions,
                'student_name': profile.full_name
            }
        )
    
    if request.method == 'POST':

        score = 0
        answer_records = []

        for question in questions:

            selected_option = request.POST.get(
                f'question_{question.id}', ''
            )

            is_correct = (
                selected_option == question.correct_option
            )

            if is_correct:
                score += 1

            if selected_option in ['A', 'B', 'C', 'D']:
                answer_records.append({
                    'question': question,
                    'selected_option': selected_option,
                    'is_correct': is_correct
                })

        attempt = QuizAttempt.objects.create(
            student=student,
            topic=topic,
            score=score,
            total_questions=questions.count()
        )

        for answer in answer_records:
            QuizAnswer.objects.create(
                attempt=attempt,
                question=answer['question'],
                selected_option=answer['selected_option'],
                is_correct=answer['is_correct']
            )

        # Save topic completion in student progress
        progress, created = StudentTopicProgress.objects.get_or_create(
            student=student,
            topic=topic,
            defaults={
                'is_completed': True,
                'completed_at': timezone.now()
            }
        )

        # If progress already exists, update it
        if not progress.is_completed:
            progress.is_completed = True
            progress.completed_at = timezone.now()
            progress.save()

        return redirect('quiz_result', attempt_id=attempt.id)
    return render(
        request,
        'edu_app/quiz.html',
        {
            'topic': topic,
            'questions': questions,
            'student_name': profile.full_name
        }
    )


# =========================
# QUIZ RESULT
# =========================

def quiz_result_view(request, attempt_id):

    if not request.user.is_authenticated:
        return redirect('login')

    try:
        profile = request.user.userprofile
    except UserProfile.DoesNotExist:
        return redirect('login')

    if profile.role != 'student':
        return redirect('student_dashboard')

    student = get_object_or_404(
        StudentProfile,
        user=request.user
    )

    attempt = get_object_or_404(
        QuizAttempt.objects.select_related(
            'topic', 'topic__course'
        ),
        id=attempt_id,
        student=student
    )

    answers = attempt.answers.select_related(
        'question'
    ).all()

    return render(
        request,
        'edu_app/quiz_result.html',
        {
            'attempt': attempt,
            'answers': answers,
            'student_name': profile.full_name
        }
    )


# Learning Progress

@login_required
def learning_progress_view(request):

    # Get the logged-in student's profile
    student_profile = StudentProfile.objects.get(user=request.user)

    # Get actual quiz attempts of this student
    quiz_attempts = QuizAttempt.objects.filter(
        student=student_profile
    ).select_related("topic", "topic__course")

    # Calculate summary using actual database records
    summary = quiz_attempts.aggregate(
        total_attempts=Count("id"),
        total_questions=Sum("total_questions"),
        total_correct=Sum("score")
    )

    total_attempts = summary["total_attempts"] or 0
    total_questions = summary["total_questions"] or 0
    total_correct = summary["total_correct"] or 0

    # Calculate overall percentage
    if total_questions > 0:
        overall_percentage = round(
            (total_correct / total_questions) * 100
        )
    else:
        overall_percentage = 0

    # Calculate progress separately for each topic
    topic_summary = quiz_attempts.values(
        "topic"
    ).annotate(
        attempts=Count("id"),
        total_score=Sum("score"),
        total_questions=Sum("total_questions")
    ).order_by("topic")

    topic_progress = []

    for item in topic_summary:

        topic = CourseTopic.objects.get(
            id=item["topic"]
        )

        total_score = item["total_score"] or 0
        topic_questions = item["total_questions"] or 0

        if topic_questions > 0:
            percentage = round(
                (total_score / topic_questions) * 100
            )
        else:
            percentage = 0

        topic_progress.append({
            "topic": topic,
            "total_score": total_score,
            "total_questions": topic_questions,
            "attempts": item["attempts"],
            "percentage": percentage
        })
    # Get completed topics
    # A topic is completed when the student submits its quiz
    completed_topic_ids = quiz_attempts.values_list(
        "topic_id",
        flat=True
    ).distinct()
    completed_topics = CourseTopic.objects.filter(
        id__in=completed_topic_ids
    ).select_related("course")

    # Show the latest quiz attempts
    attempts = quiz_attempts.order_by(
        "-attempted_at"
    )[:10]
    student_name = student_profile.user.userprofile.full_name
    # Prepare context
    context = {
        "student_name": student_name,
        "total_attempts": total_attempts,
        "total_questions": total_questions,
        "total_correct": total_correct,
        "overall_percentage": overall_percentage,
        "topic_progress": topic_progress,
        "attempts": attempts,
        "completed_topics": completed_topics,
    }
    return render(
        request,
        "edu_app/learning_progress.html",
        context
    )   



# Student AI Study Assistance
@login_required
def student_ai_assistance_view(request):

    try:
        profile = request.user.userprofile
    except UserProfile.DoesNotExist:
        return redirect('login')

    if profile.role != 'student':
        return redirect('login')

    # Get chat history from session
    chat_history = request.session.get('ai_study_chat', [])

    # Clear Chat
    if request.method == 'POST' and request.POST.get('clear_chat'):
        request.session['ai_study_chat'] = []
        request.session.modified = True

        return redirect('student_ai_assistance')

    if request.method == 'POST':
        student_message = request.POST.get('message', '').strip()

        if student_message:

            # Add student's message
            chat_history.append({
                'role': 'user',
                'message': student_message,
            })

            try:
                # Connect to Gemini using your API key
                client = genai.Client(
                    api_key=os.getenv('GEMINI_API_KEY')
                )

                # Prepare recent chat history for Gemini
                conversation = []

                for item in chat_history[-12:]:
                    if item['role'] == 'user':
                        conversation.append({
                            'role': 'user',
                            'parts': [
                                {'text': item['message']}
                            ]
                        })

                    elif item['role'] == 'assistant':
                        conversation.append({
                            'role': 'model',
                            'parts': [
                                {'text': item['message']}
                            ]
                        })

                # Generate answer
                response = client.models.generate_content(
                    model='gemini-3.5-flash-lite',
                    contents=conversation,
                    config={
                        'system_instruction': (
                            "You are EduGenius Study Assistant, "
                            "an AI tutor for college students. "
                            "Answer the student's exact question "
                            "using simple and clear language. "
                            "Follow the requested format and "
                            "number of points exactly. If the "
                            "student asks for 5 advantages, "
                            "give exactly 5. If they ask for "
                            "short notes, keep the answer short. "
                            "If they ask for code, provide "
                            "correct code and explain it when "
                            "helpful. Do not add unrelated "
                            "information. Use previous messages "
                            "to understand follow-up questions."
                        )
                    }
                )

                assistant_reply = response.text

                if not assistant_reply:
                    assistant_reply = (
                        "I couldn't generate an answer. "
                        "Please try asking again."
                    )

            except Exception as e:
                print("Gemini Error:", e)

                assistant_reply = (
                    "Sorry, I couldn't connect to Gemini. "
                    "Please check your API key and try again."
                )

            # Add AI answer
            chat_history.append({
                'role': 'assistant',
                'message': assistant_reply,
            })

            # Save chat history
            request.session['ai_study_chat'] = chat_history
            request.session.modified = True

    context = {
        'student_name': profile.full_name,
        'chat_history': chat_history,
    }

    return render(
        request,
        'edu_app/ai_study_assistance.html',
        context
    )


# Student Weak Topic Detector
@login_required
def student_weak_topics_view(request):

    try:
        profile = request.user.userprofile
    except UserProfile.DoesNotExist:
        return redirect('login')

    if profile.role != 'student':
        return redirect('login')

    # Get the student's profile
    student = get_object_or_404(
        StudentProfile,
        user=request.user
    )

    # Get all quiz attempts of this student
    attempts = QuizAttempt.objects.filter(
        student=student
    ).select_related('topic')

    # Group quiz scores by topic
    topic_scores = {}

    for attempt in attempts:

        topic_id = attempt.topic.id

        if topic_id not in topic_scores:
            topic_scores[topic_id] = {
                'topic_title': attempt.topic.topic_title,
                'total_percentage': 0,
                'attempt_count': 0,
            }

        topic_scores[topic_id]['total_percentage'] += (
            attempt.percentage
        )

        topic_scores[topic_id]['attempt_count'] += 1

    # Calculate average percentage
    weak_topics = []
    needs_practice = []
    strong_topics = []

    for topic_id, data in topic_scores.items():

        average_score = round(
            data['total_percentage'] /
            data['attempt_count']
        )

        topic_data = {
            'topic_id': topic_id,
            'topic_title': data['topic_title'],
            'average_score': average_score,
            'attempt_count': data['attempt_count'],
        }

        if average_score < 50:
            topic_data['status'] = 'Weak Topic'
            weak_topics.append(topic_data)

        elif average_score < 75:
            topic_data['status'] = 'Needs Practice'
            needs_practice.append(topic_data)

        else:
            topic_data['status'] = 'Strong Topic'
            strong_topics.append(topic_data)

    context = {
        'student_name': profile.full_name,
        'weak_topics': weak_topics,
        'needs_practice': needs_practice,
        'strong_topics': strong_topics,
    }

    return render(
        request,
        'edu_app/student_weak_topics.html',
        context
    )

@login_required
def student_announcements_view(request):

    profile = UserProfile.objects.get(user=request.user)

    # Only students can access this page
    if profile.role != "student":
        return redirect("login")

    # Get announcements using the existing announcement feature
    announcements = Announcement.objects.all().order_by("-created_at")

    context = {
        "profile": profile,
        "announcements": announcements,
    }

    return render(
        request,
        "edu_app/student_announcements.html",
        context
    )


@login_required
def student_attendance_view(request):

    profile = get_object_or_404(
        UserProfile,
        user=request.user
    )

    if profile.role != "student":
        return redirect("login")

    # Get the student's StudentProfile
    student = get_object_or_404(
        StudentProfile,
        user=request.user
    )

    # Get attendance records
    attendance_records = Attendance.objects.filter(
        student=student
    ).select_related("course").order_by("-date")

    # Calculate attendance summary
    total_classes = attendance_records.count()

    present_classes = attendance_records.filter(
        status="Present"
    ).count()

    absent_classes = attendance_records.filter(
        status="Absent"
    ).count()

    # Calculate attendance percentage
    if total_classes > 0:
        attendance_percentage = round(
            (present_classes / total_classes) * 100,
            2
        )
    else:
        attendance_percentage = 0

    return render(
        request,
        "edu_app/student_attendance.html",
        {
            "profile": profile,
            "student_name": profile.full_name,

            "total_classes": total_classes,
            "present_classes": present_classes,
            "absent_classes": absent_classes,
            "attendance_percentage": attendance_percentage,

            "attendance_records": attendance_records,
        }
    )

# Teacher Dashboard
def teacher_dashboard(request):

    if not request.user.is_authenticated:
        return redirect('login')

    try:
        profile = request.user.userprofile
    except UserProfile.DoesNotExist:
        return redirect('login')

    if profile.role != 'teacher':
        return redirect('student_dashboard')

    return render(
        request,
        'edu_app/teacher_dashboard.html',
        {
            'student_name': profile.full_name,
        }
    )


def teacher_my_students(request):
    if not request.user.is_authenticated:
        return redirect('login')

    try:
        profile = request.user.userprofile
    except UserProfile.DoesNotExist:
        return redirect('login')

    if profile.role != 'teacher':
        return redirect('student_dashboard')

    students = StudentProfile.objects.select_related('user').all()

    return render(
        request,
        'edu_app/teacher_my_students.html',
        {
            'student_name': profile.full_name,
            'students': students,
        }
    )

def teacher_create_quiz(request):
    if not request.user.is_authenticated:
        return redirect('login')

    try:
        profile = request.user.userprofile
    except UserProfile.DoesNotExist:
        return redirect('login')

    if profile.role != 'teacher':
        return redirect('student_dashboard')

    courses = Course.objects.all()
    topics = CourseTopic.objects.select_related('course').all()

    if request.method == 'POST':
        topic_id = request.POST.get('topic')
        question_text = request.POST.get('question_text', '').strip()

        option_a = request.POST.get('option_a', '').strip()
        option_b = request.POST.get('option_b', '').strip()
        option_c = request.POST.get('option_c', '').strip()
        option_d = request.POST.get('option_d', '').strip()

        correct_option = request.POST.get('correct_option')
        explanation = request.POST.get('explanation', '').strip()

        if not all([
            topic_id,
            question_text,
            option_a,
            option_b,
            option_c,
            option_d,
            correct_option
        ]):
            messages.error(request, 'Please fill in all required fields.')

        elif correct_option not in ['A', 'B', 'C', 'D']:
            messages.error(request, 'Please select a valid correct answer.')

        else:
            try:
                topic = CourseTopic.objects.get(id=topic_id)

                QuizQuestion.objects.create(
                    topic=topic,
                    created_by=request.user,
                    question_text=question_text,
                    option_a=option_a,
                    option_b=option_b,
                    option_c=option_c,
                    option_d=option_d,
                    correct_option=correct_option,
                    explanation=explanation,
                )

                messages.success(request, 'Quiz question saved successfully.')

                return redirect('teacher_create_quiz')

            except CourseTopic.DoesNotExist:
                messages.error(request, 'Please select a valid topic.')

    return render(
        request,
        'edu_app/teacher_create_quiz.html',
        {
            'student_name': profile.full_name,
            'courses': courses,
            'topics': topics,
        }
    )


def teacher_quiz_history(request):
    if not request.user.is_authenticated:
        return redirect('login')

    try:
        profile = request.user.userprofile
    except UserProfile.DoesNotExist:
        return redirect('login')

    if profile.role != 'teacher':
        return redirect('student_dashboard')

    quiz_questions = QuizQuestion.objects.filter(
        created_by=request.user
    ).select_related('topic', 'topic__course').order_by('-created_at')

    return render(
        request,
        'edu_app/teacher_quiz_history.html',
        {
            'student_name': profile.full_name,
            'quiz_questions': quiz_questions,
        }
    )

@login_required
def teacher_announcements(request):

    try:
        profile = request.user.userprofile
    except UserProfile.DoesNotExist:
        return redirect('login')

    if profile.role != 'teacher':
        return redirect('student_dashboard')

    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        message = request.POST.get('message', '').strip()

        if title and message:
            Announcement.objects.create(
                title=title,
                message=message,
                created_by=request.user
            )

            messages.success(
                request,
                'Announcement published successfully!'
            )

            return redirect('teacher_announcements')

        messages.error(
            request,
            'Please enter both title and message.'
        )

    announcements = Announcement.objects.filter(
        created_by=request.user,
        is_active=True
    ).order_by('-created_at')

    return render(
        request,
        'edu_app/teacher_announcements.html',
        {
            'student_name': profile.full_name,
            'announcements': announcements
        }
    )

@login_required
def teacher_student_progress(request):

    try:
        profile = request.user.userprofile
    except UserProfile.DoesNotExist:
        return redirect('login')

    if profile.role != 'teacher':
        return redirect('student_dashboard')

    students = StudentProfile.objects.select_related('user').all()

    progress_data = []

    for student in students:

        total_topics = StudentTopicProgress.objects.filter(
            student=student
        ).count()

        completed_topics = StudentTopicProgress.objects.filter(
            student=student,
            is_completed=True
        ).count()

        if total_topics > 0:
            progress_percentage = round(
                (completed_topics / total_topics) * 100
            )
        else:
            progress_percentage = 0

        user_profile = getattr(
            student.user,
            'userprofile',
            None
        )
        student_name = (
            user_profile.full_name
            if user_profile and user_profile.full_name
            else student.user.username
        )

        progress_data.append({
            'student': student,
            'student_name': student_name,
            'total_topics': total_topics,
            'completed_topics': completed_topics,
            'progress_percentage': progress_percentage
        })

    return render(
        request,
        'edu_app/teacher_student_progress.html',
        {
            'student_name': profile.full_name,
            'progress_data': progress_data
        }
    )

def teacher_attendance(request):

    courses = Course.objects.all()

    selected_course = None
    students = []
    attendance_date = request.GET.get("date", str(date.today()))

    course_id = request.GET.get("course")

    if course_id:
        selected_course = Course.objects.filter(id=course_id).first()

    if selected_course:
        students = StudentProfile.objects.filter(
            courses=selected_course
        ).select_related("user")

    # Save attendance
    if request.method == "POST":

        course_id = request.POST.get("course_id")
        attendance_date = request.POST.get("date")

        selected_course = Course.objects.filter(
            id=course_id
        ).first()

        if selected_course:

            students = StudentProfile.objects.filter(
                courses=selected_course
            )

            for student in students:

                status = request.POST.get(
                    f"status_{student.id}"
                )

                if status in ["Present", "Absent"]:

                    Attendance.objects.update_or_create(
                        student=student,
                        course=selected_course,
                        date=attendance_date,
                        defaults={
                            "status": status
                        }
                    )

            messages.success(
                request,
                "Attendance saved successfully!"
            )

            return redirect(
                f"{request.path}?course={course_id}&date={attendance_date}"
            )

    # Get attendance already saved for selected date
    attendance_records = {}
    if selected_course:
        records = Attendance.objects.filter(
            course=selected_course,
            date=attendance_date
        )

        attendance_records = {
            record.student_id: record.status
            for record in records
        }

        for student in students:
            student.attendance_status = attendance_records.get(
                student.id,
                ""
            )

    context = {
        "courses": courses,
        "selected_course": selected_course,
        "students": students,
        "attendance_date": attendance_date,
        "attendance_records": attendance_records,
    }

    return render(
        request,
        "edu_app/teacher_attendance.html",
        context
    )

# Parent Dashboard
def parent_dashboard(request):

    if not request.user.is_authenticated:
        return redirect('login')

    try:
        profile = request.user.userprofile
    except UserProfile.DoesNotExist:
        return redirect('login')

    if profile.role != 'parent':
        return redirect('student_dashboard')

    return render(
        request,
        'edu_app/parent_dashboard.html',
        {
            'student_name': profile.full_name,
        }
    )

# Parent Student Performance
@login_required
def parent_student_performance_view(request):

    try:
        profile = request.user.userprofile
    except UserProfile.DoesNotExist:
        return redirect('login')

    if profile.role != 'parent':
        return redirect('student_dashboard')

    # Get students connected to this parent
    student_ids = ParentStudent.objects.filter(
        parent=request.user
    ).values_list('student_id', flat=True)

    # Get actual quiz attempts for linked students
    attempts = QuizAttempt.objects.filter(
        student_id__in=student_ids
    ).select_related(
        'student__user',
        'topic',
        'topic__course'
    ).order_by('-attempted_at')

    return render(
        request,
        'edu_app/parent_student_performance.html',
        {
            'attempts': attempts,
            'parent_name': profile.full_name,
        }
    )


@login_required
def parent_student_progress_view(request):

    try:
        profile = request.user.userprofile
    except UserProfile.DoesNotExist:
        return redirect('login')

    if profile.role != 'parent':
        return redirect('student_dashboard')

    # Get students linked to this parent
    student_ids = ParentStudent.objects.filter(
        parent=request.user
    ).values_list('student_id', flat=True)

    # Get enrolled courses of linked students
    enrollments = Enrollment.objects.filter(
        student_id__in=student_ids
    ).select_related(
        'student__user',
        'course'
    )

    # Get topic progress records
    progress_records = StudentTopicProgress.objects.filter(
        student_id__in=student_ids
    ).select_related(
        'student__user',
        'topic__course'
    )

    # Total topics in enrolled courses
    total_topics = CourseTopic.objects.filter(
        course__enrollment__student_id__in=student_ids
    ).distinct().count()

    # Completed topics
    completed_topics = progress_records.filter(
        is_completed=True
    ).values('topic_id', 'student_id').distinct().count()

    # Remaining topics
    remaining_topics = max(
        total_topics - completed_topics,
        0
    )

    # Overall progress percentage
    if total_topics > 0:
        progress_percentage = round(
            (completed_topics / total_topics) * 100
        )
    else:
        progress_percentage = 0

    context = {
        'parent_name': profile.full_name,
        'enrollments': enrollments,
        'progress_records': progress_records,
        'total_topics': total_topics,
        'completed_topics': completed_topics,
        'remaining_topics': remaining_topics,
        'progress_percentage': progress_percentage,
    }

    return render(
        request,
        'edu_app/parent_student_progress.html',
        context
    )

@login_required
def parent_study_activity_view(request):

    # Check parent role
    try:
        profile = request.user.userprofile
    except UserProfile.DoesNotExist:
        return redirect('login')

    if profile.role != 'parent':
        return redirect('parent_dashboard')

    # Get students linked to this parent
    parent_students = ParentStudent.objects.filter(
        parent=request.user
    ).select_related(
        'student__user'
    )

    student_ids = parent_students.values_list(
        'student_id',
        flat=True
    )

    activities = []

    # Get topic completion activity
    topic_progress = StudentTopicProgress.objects.filter(
        student_id__in=student_ids,
        is_completed=True
    ).select_related(
        'student__user',
        'topic__course'
    )

    for record in topic_progress:

        student_profile = getattr(
            record.student.user,
            'userprofile',
            None
        )

        student_name = (
            student_profile.full_name
            if student_profile
            else record.student.user.username
        )

        activities.append({
            'student_name': student_name,
            'activity': 'Topic Completed',
            'details': record.topic.topic_title,
            'course': record.topic.course.course_name,
            'status': 'Completed',
            'date': record.completed_at,
        })

    # Get quiz activity
    quiz_attempts = QuizAttempt.objects.filter(
        student_id__in=student_ids
    ).select_related(
        'student__user',
        'topic__course'
    )

    for attempt in quiz_attempts:

        student_profile = getattr(
            attempt.student.user,
            'userprofile',
            None
        )

        student_name = (
            student_profile.full_name
            if student_profile
            else attempt.student.user.username
        )

        activities.append({
            'student_name': student_name,
            'activity': 'Quiz Attempted',
            'details': attempt.topic.topic_title,
            'course': attempt.topic.course.course_name,
            'status': f'{attempt.score}/{attempt.total_questions}',
            'date': attempt.attempted_at,
        })

    # Show latest activity first
    activities.sort(
        key=lambda item: (
            item['date'].timestamp()
            if item['date']
            else 0
        ),
        reverse=True
    )

    return render(
        request,
        'edu_app/study_activity.html',
        {
            'parent_name': profile.full_name,
            'activities': activities,
        }
    )

# Parent Announcements View
@login_required
def parent_announcements_view(request):

    try:
        profile = request.user.userprofile
    except UserProfile.DoesNotExist:
        return redirect('login')

    if profile.role != 'parent':
        return redirect('parent_dashboard')

    announcements = Announcement.objects.filter(
        is_active=True
    ).order_by('-created_at')

    context = {
        'parent_name': profile.full_name,
        'announcements': announcements,
    }

    return render(
        request,
        'edu_app/parent_announcements.html',
        context
    )

@login_required
def parent_attendance(request):
    return render(
        request,
        "edu_app/parent_attendance.html"
    )

@login_required
def profile_view(request):

    user_profile = get_object_or_404(
        UserProfile,
        user=request.user
    )

    student_profile = None

    if user_profile.role == "student":
        student_profile = StudentProfile.objects.filter(
            user=request.user
        ).first()

    success_message = ""

    if request.method == "POST":

        full_name = request.POST.get(
            "full_name", ""
        ).strip()

        if full_name:
            user_profile.full_name = full_name
            user_profile.save()

            if student_profile:
                student_profile.college_name = request.POST.get(
                    "college_name", ""
                ).strip()

                student_profile.course_name = request.POST.get(
                    "course_name", ""
                ).strip()

                student_profile.semester = request.POST.get(
                    "semester", ""
                ).strip()

                student_profile.save()

            success_message = "Profile updated successfully!"

    context = {
        "profile": user_profile,
        "student_profile": student_profile,
        "success_message": success_message,
    }

    return render(
        request,
        "edu_app/profile.html",
        context
    )
# Logout
def logout_view(request):
    logout(request)
    return redirect('home')
