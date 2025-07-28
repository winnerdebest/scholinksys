from django.db import models
from django.conf import settings



class School(models.Model):
    principal = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    logo = models.ImageField(upload_to='school_logos/')
    address = models.TextField()
    email = models.EmailField()

    def __str__(self):
        return self.name


class PaymentProvider(models.TextChoices):
    FLUTTERWAVE = 'flutterwave', 'Flutterwave'
    BANK_TRANSFER = 'bank_transfer', 'Bank Transfer'


class SchoolPaymentInfo(models.Model):
    school = models.ForeignKey('School', on_delete=models.CASCADE, related_name='payment_methods')
    
    provider = models.CharField(max_length=20, choices=PaymentProvider.choices)
    
    # Required for bank-based payments and subaccount setup
    account_name = models.CharField(max_length=255, blank=True, null=True)
    account_number = models.CharField(max_length=50, blank=True, null=True)
    bank_name = models.CharField(max_length=255, blank=True, null=True)
    bank_code = models.CharField(max_length=20, blank=True, null=True) 

    # Flutterwave-specific
    flutterwave_subaccount_id = models.CharField(max_length=255, blank=True, null=True) 
    split_percentage = models.PositiveIntegerField(default=98)  # ✅ School gets this percentage

    # Secret API credentials (can be left blank if you're using only your own account)
    provider_account_id = models.CharField(max_length=255, blank=True, null=True)
    provider_secret_key = models.CharField(max_length=255, blank=True, null=True)

    metadata = models.JSONField(blank=True, null=True)

    is_active = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.school.name} - {self.get_provider_display()}"




class Term(models.Model):
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='terms')
    name = models.CharField(max_length=50)  

    def __str__(self):
        return self.name




class ActiveTerm(models.Model):
    school = models.OneToOneField(School, on_delete=models.CASCADE, related_name='active_term')
    term = models.OneToOneField(Term, on_delete=models.CASCADE)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Active Term: {self.term.name}"

    @classmethod
    def get_active_term(cls):
        return cls.objects.first().term
    




