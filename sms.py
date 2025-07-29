def generate_sms(bank, amount):
    return f"[{bank}] مبلغ {amount:,} ریال با موفقیت واریز شد."

def get_balance(card_number):
    fake_balance = {
        "6037991234567890": 15000000,
        "6104339876543210": 7200000,
        "6273531122334455": 5000000
    }
    return fake_balance.get(card_number, "❌ کارت یافت نشد")