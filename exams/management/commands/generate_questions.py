import random
from random import choice
from django.contrib.auth import get_user_model
from exams.models import Question, Exam  
from django.core.management.base import BaseCommand

User = get_user_model()

SAMPLE_QUESTIONS = [
    "What is the capital of Nigeria?",
    "Which gas do plants use for photosynthesis?",
    "Who discovered gravity?",
    "Which planet is closest to the sun?",
    "How many legs does a spider have?",
    "What is the largest ocean on Earth?",
    "Who wrote 'Things Fall Apart'?",
    "Which continent is Egypt located in?",
    "What is 7 × 8?",
    "What part of the plant absorbs water?"
]

SAMPLE_OPTIONS = {
    "A": ["Abuja", "Oxygen", "Newton", "Mercury", "6", "Pacific", "Achebe", "Africa", "56", "Root"],
    "B": ["Lagos", "Carbon Dioxide", "Einstein", "Venus", "8", "Atlantic", "Soyinka", "Asia", "49", "Stem"],
    "C": ["Kano", "Nitrogen", "Galileo", "Earth", "10", "Indian", "Okri", "Europe", "63", "Leaf"],
    "D": ["Port Harcourt", "Hydrogen", "Tesla", "Mars", "12", "Arctic", "Ekwensi", "South America", "72", "Flower"]
}

class Command(BaseCommand):
    help = "Generate 50 dummy exam questions, randomly assigning each to an existing exam"

    def handle(self, *args, **kwargs):
        exams = list(Exam.objects.all())
        teachers = list(User.objects.filter(user_type='teacher'))

        if not exams:
            self.stdout.write(self.style.ERROR("❌ No exams found in the database."))
            return

        if not teachers:
            self.stdout.write(self.style.ERROR("❌ No teachers found in the database."))
            return

        for i in range(50):
            base_q = random.choice(SAMPLE_QUESTIONS)
            question = Question.objects.create(
                exam=None,
                assignment=None,
                text=f"{i+1}. {base_q}",
                option_a_text=SAMPLE_OPTIONS["A"][i % len(SAMPLE_OPTIONS["A"])],
                option_b_text=SAMPLE_OPTIONS["B"][i % len(SAMPLE_OPTIONS["B"])],
                option_c_text=SAMPLE_OPTIONS["C"][i % len(SAMPLE_OPTIONS["C"])],
                option_d_text=SAMPLE_OPTIONS["D"][i % len(SAMPLE_OPTIONS["D"])],
                correct_answer=random.choice(['A', 'B', 'C', 'D']),
                created_by=random.choice(teachers)
            )
            self.stdout.write(f"✅ Created Question {i+1}: {question.text[:40]}...")

        self.stdout.write(self.style.SUCCESS("🎉 Successfully created 50 randomized exam questions."))
