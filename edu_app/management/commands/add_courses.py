from django.core.management.base import BaseCommand
from edu_app.models import Course


class Command(BaseCommand):
    help = "Add default EduGenius courses"

    def handle(self, *args, **kwargs):
        subjects = [
            "Python Programming",
            "Java Programming",
            "Web Technology",
        ]

        for subject in subjects:
            Course.objects.get_or_create(
                course_name=subject,
                defaults={
                    "description": f"Learn {subject}"
                }
            )

        self.stdout.write(
            self.style.SUCCESS("All 3 courses added successfully!")
        )