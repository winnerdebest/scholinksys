from django import template
from decimal import Decimal

register = template.Library()

@register.filter
def sum_fees(fees):
    total = Decimal('0.00')
    for fee in fees:
        if fee.amount:  # In case it's None
            total += fee.amount
    return total

@register.filter
def sum_class_fees(classes):
    total = Decimal('0.00')
    for class_obj in classes:
        for fee in class_obj.class_fees.all():
            if fee.amount:
                total += fee.amount
    return total
