from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import School, Term, ActiveTerm

@receiver(post_save, sender=School)
def create_default_terms_and_active_term(sender, instance, created, **kwargs):
    if created:
        # Create the three terms
        first_term = Term.objects.create(school=instance, name="1st Term")
        Term.objects.create(school=instance, name="2nd Term")
        Term.objects.create(school=instance, name="3rd Term")

        # Set "1st Term" as active
        ActiveTerm.objects.create(school=instance, term=first_term)
