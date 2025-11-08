# bot_receipt_fun.py
# نیازمندی‌ها:
# pip install python-telegram-bot==20.3 Pillow

import json
import time
from pathlib import Path
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont

from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardRemove
)
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    ContextTypes, ConversationHandler, MessageHandler, filters
)

# ---------- تنظیمات ----------
BOT_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"
SUPPORT_USER = "YourSupportUsername"  # بدون @
ADMIN_IDS = [123456789]  # آیدی عددی ادمین‌ها
DATA_FILE = Path("users_data.json")

RECEIPT_TYPES = [
    "رسید آپ", "رسید همراه کارت", "رسید ایوا", "رسید تاپ",
    "رسید بلو", "رسید همراه بانک ملت", "رسید همراه بانک تجارت",
    "رسید همراه بانک رفاه", "رسید همراه بانک ملی بام", "رسید 724",
    "پیامک بانکی", "خرید حساب ویژه", "سکه روزانه"
]

# conversation states
CHOOSING_TYPE, ASK_CARD_FROM, ASK_CARD_TO, ASK_AMOUNT, ASK_NAME = range(5)

# ---------- ذخیره و بارگذاری ----------
def load_data():
    if DATA_FILE.exists():
        return json.loads(DATA_FILE.read_text(encoding="utf-8"))
    return {}

def save_data(data):
    DATA_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

users = load_data()

def ensure_user(uid, username=None, first_name=None, last_name=None):
    s = users.setdefault(str(uid), {
        "username": username,
        "first_name": first_name,
        "last_name": last_name,
        "coins": 0,
        "is_premium": False,
        "last_daily": 0
    })
    # به‌روز کردن اطلاعات له‌صورت سبک
    s["username"] = username
    s["first_name"] = first_name
    s["last_name"] = last_name
    return s

# ---------- تولید تصویر نمونه رسید (با واترمارک و متن واضح "نمونه") ----------
def make_sample_receipt(receipt_type, card_from, card_to, amount, owner_name):
    # تصویر پایه ساده بساز
    W, H = 800, 500
    img = Image.new("RGB", (W, H), color=(255,255,255))
    draw = ImageDraw.Draw(img)

    # فونت (سعی کن فونت فارسی مناسب در سیستم باشه، در غیر این صورت از فونت پیش‌فرض استفاده می‌شود)
    try:
        font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
        font_bold = ImageFont.truetype(font_path, 22)
        font_large = ImageFont.truetype(font_path, 32)
        font_small = ImageFont.truetype(font_path, 18)
    except:
        font_bold = ImageFont.load_default()
        font_large = ImageFont.load_default()
        font_small = ImageFont.load_default()

    # هدر
    draw.text((20,20), f"نمونه رسید — {receipt_type}", font=font_large, fill=(0,0,0))
    draw.text((20,70), "توجه: این تصویر صرفاً نمونه و برای شوخی/آموزش است. قابل استفاده برای جعل نیست.", font=font_small, fill=(120,0,0))

    # مشخصات
    start_y = 120
    gap = 45
    draw.text((40, start_y + 0*gap), f"کارت مبدا: {card_from}", font=font_bold, fill=(0,0,0))
    draw.text((40, start_y + 1*gap), f"کارت مقصد: {card_to}", font=font_bold, fill=(0,0,0))
    draw.text((40, start_y + 2*gap), f"مبلغ: {amount}", font=font_bold, fill=(0,0,0))
    draw.text((40, start_y + 3*gap), f"نام صاحب کارت: {owner_name}", font=font_bold, fill=(0,0,0))

    # واترمارک بزرگ مخفی‌ناپذیر
    wm_text = "نمونه / FOR FUN / AmiriYT"
    w, h = draw.textsize(wm_text, font=font_large)
    # چرخش واترمارک
    watermark = Image.new("RGBA", (w+20, h+10), (255,255,255,0))
    dw = ImageDraw.Draw(watermark)
    dw.text((10,5), wm_text, font=font_large, fill=(200,200,200,80))
    watermark = watermark.rotate(30, expand=1)
    img.paste(watermark, (220,260), watermark)

    # استمپ بزرگ "نمونه" نیمه‌شفاف
    try:
        stamp_font = ImageFont.truetype(font_path, 80)
    except:
        stamp_font = ImageFont.load_default()
    stamp = Image.new("RGBA", (W, H), (255,255,255,0))
    ds = ImageDraw.Draw(stamp)
    text = "نمونه"
    tw, th = ds.textsize(text, font=stamp_font)
    ds.text(((W-tw)//2, (H-th)//2), text, font=stamp_font, fill=(255,0,0,80))
    img.paste(stamp, (0,0), stamp)

    # خروجی بایت
    bio = BytesIO()
    bio.name = "receipt_sample.png"
    img.save(bio, "PNG")
    bio.seek(0)
    return bio

# ---------- هندلرها ----------
async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    ensure_user(user.id, user.username, user.first_name, user.last_name)
    keyboard = [
        [InlineKeyboardButton(t, callback_data=f"receipt:{t}") for t in RECEIPT_TYPES[:3]],
        [InlineKeyboardButton(t, callback_data=f"receipt:{t}") for t in RECEIPT_TYPES[3:6]],
        [InlineKeyboardButton(t, callback_data=f"receipt:{t}") for t in RECEIPT_TYPES[6:9]],
        [InlineKeyboardButton(t, callback_data=f"receipt:{t}") for t in RECEIPT_TYPES[9:12]],
        [InlineKeyboardButton("خرید حساب ویژه", callback_data="buy_premium"), InlineKeyboardButton("سکه روزانه", callback_data="daily_coin")]
    ]
    kb = InlineKeyboardMarkup(keyboard)
    text = (
        f"سلام {user.first_name or ''} {user.last_name or ''} (@{user.username or '—'})\n"
        f"آیدی عددی: {user.id}\n\n"
        "به ربات رسید ساز خوش اومدی!\n"
        "چه نوع رسیدی میخوای درست کنی؟"
    )
    await update.message.reply_text(text, reply_markup=kb)

async def callback_query_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    data = q.data

    user = update.effective_user
    u = ensure_user(user.id, user.username, user.first_name, user.last_name)

    if data == "buy_premium":
        await q.message.reply_text(
            f"برای خرید حساب ویژه لطفاً به پشتیبانی مراجعه کن: @{SUPPORT_USER}\n\n(اینجا فقط ارجاع به پی‌وی انجام می‌شود.)"
        )
        return

    if data == "daily_coin":
        now = int(time.time())
        if now - u.get("last_daily", 0) >= 24*3600:
            # در صورت تمایل چک عضویت کانال در اینجا اضافه شود
            u["coins"] = u.get("coins",0) + 1
            u["last_daily"] = now
            save_data(users)
            await q.message.reply_text("سکه روزانه به شما تعلق گرفت! 🎉\nامتیاز فعلی: {}".format(u["coins"]))
        else:
            await q.message.reply_text("شما در ۲۴ ساعت گذشته از سکه استفاده کرده‌اید. دوباره بعداً مراجعه کنید.")
        return

    if data.startswith("receipt:"):
        rtype = data.split(":",1)[1]
        # ذخیره نوع انتخاب شده در context و شروع پرسش‌ها
        context.user_data['selected_type'] = rtype
        await q.message.reply_text("شماره کارت مبدا را وارد کن:", reply_markup=ReplyKeyboardRemove())
        return ASK_CARD_FROM

async def ask_card_from(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['card_from'] = update.message.text.strip()
    await update.message.reply_text("شماره کارت مقصد را وارد کن:")
    return ASK_CARD_TO

async def ask_card_to(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['card_to'] = update.message.text.strip()
    await update.message.reply_text("مبلغ را وارد کن (مثلاً ۵۰۰۰۰۰):")
    return ASK_AMOUNT

async def ask_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['amount'] = update.message.text.strip()
    await update.message.reply_text("نام صاحب کارت را وارد کن:")
    return ASK_NAME

async def ask_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.message.text.strip()
    context.user_data['owner_name'] = name

    # تولید تصویر نمونه
    rtype = context.user_data.get('selected_type', 'رسید نمونه')
    bio = make_sample_receipt(
        receipt_type=rtype,
        card_from=context.user_data.get('card_from','-'),
        card_to=context.user_data.get('card_to','-'),
        amount=context.user_data.get('amount','-'),
        owner_name=name
    )

    await update.message.reply_photo(photo=bio, caption=(
        "رسید شما با موفقیت ساخته شد.\n"
        "توجه: این تصویر صرفاً نمونه/شوخی است. در صورت استفاده برای کلاهبرداری مسئولیت قانونی دارد."
    ))

    # پاک کردن user_data موقتی
    context.user_data.clear()
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("عملیات کنسل شد.", reply_markup=ReplyKeyboardRemove())
    context.user_data.clear()
    return ConversationHandler.END

# ادمین: ویژه کردن کاربر
async def admin_add_premium(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id not in ADMIN_IDS:
        await update.message.reply_text("فقط ادمین مجاز است.")
        return
    parts = context.args
    if len(parts) != 1:
        await update.message.reply_text("استفاده: /addpremium <user_id>")
        return
    target = parts[0]
    if target not in users:
        await update.message.reply_text("کاربر پیدا نشد.")
        return
    users[target]["is_premium"] = True
    save_data(users)
    await update.message.reply_text("کاربر ویژه شد.")

# وضعیت حساب
async def me_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    u = ensure_user(user.id, user.username, user.first_name, user.last_name)
    txt = f"آیدی: {user.id}\nیوزرنیم: @{user.username or '—'}\nامتیاز: {u.get('coins',0)}\nحساب ویژه: {'بله' if u.get('is_premium') else 'خیر'}"
    await update.message.reply_text(txt)

# ---------- برنامه اصلی ----------
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(callback_query_handler, pattern=r"^receipt:")],
        states={
            ASK_CARD_FROM: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_card_from)],
            ASK_CARD_TO: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_card_to)],
            ASK_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_amount)],
            ASK_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_name)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
        allow_reentry=True
    )

    # هندلرها
    app.add_handler(CommandHandler("start", start_handler))
    app.add_handler(CallbackQueryHandler(callback_query_handler, pattern=r"^(buy_premium|daily_coin)$"))
    app.add_handler(conv)
    app.add_handler(CommandHandler("me", me_handler))
    app.add_handler(CommandHandler("addpremium", admin_add_premium))  # admin only

    print("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
