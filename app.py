import os
import telebot
from flask import Flask, request

# توکن مستقیم (برای تست)
TOKEN = "8357876689:AAHtsXA7aByoK4g6U0Rh6mPsX3nPL_jsBfw"
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

@app.route("/", methods=["GET"])
def index():
    return "✅ ربات تلگرام در حال اجراست!"

@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    try:
        json_data = request.get_data().decode("utf-8")
        update = telebot.types.Update.de_json(json_data)
        bot.process_new_updates([update])
    except Exception as e:
        print("❌ خطا در پردازش پیام:", e)
    return "OK", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)