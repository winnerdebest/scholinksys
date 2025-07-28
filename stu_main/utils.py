import json
from pathlib import Path
from datetime import datetime


PAYMENT_FILE = Path("temp_payments.json")

def store_payment(data):
    # Create file if it doesn't exist
    if PAYMENT_FILE.exists():
        with open(PAYMENT_FILE, 'r') as f:
            payments = json.load(f)
    else:
        payments = []

    payments.append(data)

    with open(PAYMENT_FILE, 'w') as f:
        json.dump(payments, f, indent=2)


def get_all_payments():
    if PAYMENT_FILE.exists():
        with open(PAYMENT_FILE, 'r') as f:
            return json.load(f)
    return []
