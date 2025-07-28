import random
from django.core.management.base import BaseCommand
from exams.models import *
from academic_main.models import *
from stu_main.models import *

class Command(BaseCommand):
    help = "Generate random exams for class subjects"

    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=50,
            help='Number of exams to generate (default: 50)'
        )

    def handle(self, *args, **options):
        count = options['count']

        class_subjects = list(ClassSubject.objects.all())
        terms = list(Term.objects.all())
        durations = [30, 45, 60, 90]  # You can add more if needed

        if not class_subjects:
            self.stdout.write(self.style.ERROR("❌ No ClassSubject entries found."))
            return

        if not terms:
            self.stdout.write(self.style.ERROR("❌ No Term entries found."))
            return

        for i in range(count):
            class_subject = random.choice(class_subjects)
            term = random.choice(terms)
            duration = random.choice(durations)

            exam = Exam.objects.create(
                class_subject=class_subject,
                term=term,
                duration_minutes=duration,
                is_active=True
            )

            self.stdout.write(f"✅ Created Exam {i+1}: {exam}")

        self.stdout.write(self.style.SUCCESS(f"\n🎉 Successfully created {count} exams."))
