import random

ADJECTIVES = ["Swift", "Bright", "Bold", "Clever", "Lucky", "Brave", "Happy", "Witty", "Sharp", "Rapid"]
ANIMALS = ["Tiger", "Eagle", "Lion", "Panther", "Wolf", "Falcon", "Shark", "Hawk", "Leopard", "Fox"]

def generate_username(first_name, last_name):
    random_number = random.randint(100, 999)
    return f"{first_name.lower()}.{last_name.lower()}{random_number}"

def generate_readable_password():
    adjective = random.choice(ADJECTIVES)
    animal = random.choice(ANIMALS)
    number = random.randint(10, 99)
    return f"{adjective}{animal}{number}"
