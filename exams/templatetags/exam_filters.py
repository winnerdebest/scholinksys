from django import template

register = template.Library()

@register.filter
def get_option_text(question, option):
    return getattr(question, f"option_{option.lower()}_text", "")

@register.filter
def get_option_image(question, option):
    return getattr(question, f"option_{option.lower()}_image", None)
