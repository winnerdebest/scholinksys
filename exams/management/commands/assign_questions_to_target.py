from django.core.management.base import BaseCommand
from exams.models import *
from academic_main.models import *
from stu_main.models import *

class Command(BaseCommand):
    help = "Assign unassigned questions to a specific Exam or Assignment"

    def handle(self, *args, **kwargs):
        # Step 1: Choose target type
        target_type = input("Do you want to assign questions to an 'exam' or an 'assignment'? ").strip().lower()
        if target_type not in ['exam', 'assignment']:
            self.stdout.write(self.style.ERROR("❌ Invalid type. Must be 'exam' or 'assignment'."))
            return

        # Step 2: Display options
        if target_type == 'exam':
            items = Exam.objects.all()
        else:
            items = Assignment.objects.all()

        if not items.exists():
            self.stdout.write(self.style.ERROR(f"❌ No {target_type}s found in the database."))
            return

        self.stdout.write(self.style.NOTICE(f"\nAvailable {target_type}s:\n"))
        for i, item in enumerate(items, start=1):
            self.stdout.write(f"{i}. {str(item)}")

        try:
            selected_index = int(input(f"\nEnter the number of the {target_type} you want to assign to: ").strip())
            target = items[selected_index - 1]
        except (ValueError, IndexError):
            self.stdout.write(self.style.ERROR("❌ Invalid selection. Please choose a valid number from the list."))
            return

        # Step 3: Assign all unassigned questions
        unassigned_questions = Question.objects.filter(exam__isnull=True, assignment__isnull=True)
        if not unassigned_questions.exists():
            self.stdout.write(self.style.WARNING("⚠️ No unassigned questions found."))
            return

        for question in unassigned_questions:
            if target_type == 'exam':
                question.exam = target
            else:
                question.assignment = target
            question.save()

        self.stdout.write(self.style.SUCCESS(
            f"✅ Successfully assigned {unassigned_questions.count()} questions to '{target}'."
        ))
