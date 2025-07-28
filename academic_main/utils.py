import requests
import random
from django.conf import settings





FLUTTERWAVE_BASE_URL = "https://api.flutterwave.com/v3"
FLUTTERWAVE_SECRET_KEY = settings.FLUTTERWAVE_SECRET_KEY


def create_flutterwave_subaccount(account_name, account_number, bank_code, split_percentage,school):
    url = f"{FLUTTERWAVE_BASE_URL}/subaccounts"

    default_phone = f"080{random.randint(10000000, 99999999)}"


    headers = {
        "Authorization": f"Bearer {FLUTTERWAVE_SECRET_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "account_bank": bank_code,
        "account_number": account_number,
        "business_name": account_name,
        "split_type": "percentage",
        "split_value": split_percentage / 100,
        "business_email": school.email or "winnerbrown9@gmail.com",
        "business_mobile": default_phone,
        "business_contact": account_name,
        "business_contact_mobile": default_phone,
    }
    print("Sending payload:", data)  # 🔍 Debug
    response = requests.post(url, headers=headers, json=data)

    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        print("Response text:", response.text)  # 🔍 Debug
        raise e

    return response.json()["data"]

def get_flutterwave_banks(country="NG"):
    url = f"{FLUTTERWAVE_BASE_URL}/banks/{country}"
    headers = {"Authorization": f"Bearer {FLUTTERWAVE_SECRET_KEY}"}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()["data"]
