
from django.core.management.base import BaseCommand
from edu_app.models import Course, CourseTopic


class Command(BaseCommand):
    help = "Add 4 topics to Python, Java and Web Technology"

    def handle(self, *args, **kwargs):

        course_topics = {
            "Python Programming": [
                "Introduction to Python",
                "Python Variables and Data Types",
                "Python Operators",
                "Python Conditional Statements",
            ],

            "Java Programming": [
                "Introduction to Java",
                "Java Variables and Data Types",
                "Java Operators",
                "Java Conditional Statements",
            ],

            "Web Technology": [
                "Introduction to HTML",
                "HTML Forms and Tables",
                "CSS Basics",
                "JavaScript Fundamentals",
            ],
        }

        for course_name, topics in course_topics.items():

            course, created = Course.objects.get_or_create(
                course_name=course_name,
                semester=1,
                defaults={
                    "description": f"Learn {course_name}"
                }
            )

            for order, topic_title in enumerate(topics, start=1):

                CourseTopic.objects.get_or_create(
                    course=course,
                    topic_title=topic_title,
                    defaults={
                        "description": f"Learn about {topic_title}",
                        "content": f"Study the concepts of {topic_title}.",
                        "topic_order": order,
                    }
                )

        self.stdout.write(
            self.style.SUCCESS("Topics added successfully!")
        )
