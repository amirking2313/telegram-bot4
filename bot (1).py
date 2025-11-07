import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes, ConversationHandler
from datetime import datetime, timedelta
import json
import os
import re

# تنظیمات لاگینگ
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# تنظیمات ربات - این قسمت را حتماً تغییر دهید
BOT_TOKEN = "8589878762:AAFPJkAuZZfXFEE_02dLL_dZGiap9UNy8GI"
REQUIRED_CHANNEL = "@mmdcoc50"
SUPPORT_ID = "8211979192"

# مراحل مکالمه
CARD_SOURCE, CARD_DEST, VERIFY_CARD, AMOUNT, CARD_NAME, CONFIRM_RECEIPT = range(6)

# فایل ذخیره‌سازی
USER_DATA_FILE = "users_data.json"

# بارگذاری و ذخیره‌سازی داده‌ها
def load_users_data():
    if os.path.exists(USER_DATA_FILE):
        try:
            with open(USER_DATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_users_data(data):
    with open(USER_DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

users_data = load_users_data()

# تابع استعلام شماره کارت (شبیه‌سازی شده)
def query_card_info(card_number):
    """
    این تابع شماره کارت را استعلام می‌کند
    در حالت واقعی باید به API بانک متصل شود
    در اینجا به صورت شبیه‌سازی شده عمل می‌کند
    """
    # حذف فاصله‌ها و کاراکترهای اضافی
    card_clean = re.sub(r'\D', '', card_number)
    
    # بررسی طول شماره کارت
    if len(card_clean) != 16:
        return None
    
    # شبیه‌سازی استعلام - در حالت واقعی این داده‌ها از API بانک می‌آیند
    # شماره‌های معتبر شبیه‌سازی شده
    fake_database = {
        '6037': {'bank': 'ملی ایران', 'names': ['علی رضایی', 'محمد احمدی', 'حسین محمدی']},
        '6219': {'bank': 'سامان', 'names': ['فاطمه کریمی', 'زهرا حسینی', 'مریم اکبری']},
        '6104': {'bank': 'ملت', 'names': ['امیر تقی‌پور', 'رضا صادقی', 'مهدی کاظمی']},
        '6273': {'bank': 'تجارت', 'names': ['سارا یوسفی', 'نرگس رحیمی', 'نازنین جعفری']},
        '6362': {'bank': 'آینده', 'names': ['حمید نوری', 'جواد مرادی', 'بهرام شریفی']},
    }
    
    # گرفتن 4 رقم اول کارت
    card_prefix = card_clean[:4]
    
    if card_prefix in fake_database:
        import random
        bank_info = fake_database[card_prefix]
        return {
            'success': True,
            'bank': bank_info['bank'],
            'card_number': card_number,
            'owner_name': random.choice(bank_info['names'])
        }
    
    # اگر کارت شناخته نشد، یک نام تصادفی برمی‌گرداند
    default_names = ['احمد رحمانی', 'حسن موسوی', 'علیرضا حسینی', 'محمدرضا کریمی']
    import random
    return {
        'success': True,
        'bank': 'نامشخص',
        'card_number': card_number,
        'owner_name': random.choice(default_names)
    }

# فرمت کردن شماره کارت
def format_card_number(card):
    card_clean = re.sub(r'\D', '', card)
    if len(card_clean) == 16:
        return f"{card_clean[:4]}-{card_clean[4:8]}-{card_clean[8:12]}-{card_clean[12:]}"
    return card

# بررسی عضویت در کانال
async def check_channel_membership(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    try:
        member = await context.bot.get_chat_member(REQUIRED_CHANNEL, user_id)
        return member.status in ['member', 'administrator', 'creator']
    except Exception as e:
        logger.error(f"خطا در بررسی عضویت: {e}")
        return False

# دستور شروع
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = str(user.id)
    
    # ایجاد یا بارگذاری اطلاعات کاربر
    if user_id not in users_data:
        users_data[user_id] = {
            'points': 0,
            'is_premium': False,
            'last_daily_claim': None,
            'receipts_created': 0
        }
        save_users_data(users_data)
    
    # پیام خوش‌آمدگویی
    last_name = user.last_name or ''
    username = f"@{user.username}" if user.username else 'ندارد'
    
    welcome_text = f"""
╔═══════════════════════╗
        خوش آمدید
╚═══════════════════════╝

👤 نام: {user.first_name} {last_name}
🆔 یوزرنیم: {username}
🔢 آیدی عددی: {user.id}
💰 امتیاز: {users_data[user_id]['points']}

🎉 به ربات رسید ساز خوش‌آمدی!
"""
    
    await update.message.reply_text(welcome_text)
    await show_main_menu(update, context)

# نمایش منوی اصلی
async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("💳 رسید آپ", callback_data='receipt_up'),
         InlineKeyboardButton("💳 رسید همراه کارت", callback_data='receipt_hamrah_card')],
        [InlineKeyboardButton("💳 رسید ایوا", callback_data='receipt_iva'),
         InlineKeyboardButton("💳 رسید تاپ", callback_data='receipt_top')],
        [InlineKeyboardButton("💳 رسید بلو", callback_data='receipt_blue'),
         InlineKeyboardButton("💳 رسید همراه بانک ملت", callback_data='receipt_mellat')],
        [InlineKeyboardButton("💳 رسید همراه بانک تجارت", callback_data='receipt_tejarat'),
         InlineKeyboardButton("💳 رسید همراه بانک رفاه", callback_data='receipt_refah')],
        [InlineKeyboardButton("💳 رسید همراه بانک ملی بام", callback_data='receipt_melli_bam'),
         InlineKeyboardButton("💳 رسید 724", callback_data='receipt_724')],
        [InlineKeyboardButton("📱 پیامک بانکی", callback_data='bank_sms')],
        [InlineKeyboardButton("⭐️ خرید حساب ویژه", callback_data='buy_premium'),
         InlineKeyboardButton("🎁 سکه روزانه", callback_data='daily_coin')]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    text = "❓ چه نوع رسیدی میخوای درست کنی؟"
    
    if update.callback_query:
        await update.callback_query.message.reply_text(text, reply_markup=reply_markup)
    else:
        await update.message.reply_text(text, reply_markup=reply_markup)

# مدیریت دکمه‌ها
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = str(update.effective_user.id)
    
    # دریافت سکه روزانه
    if query.data == 'daily_coin':
        is_member = await check_channel_membership(update, context)
        
        if not is_member:
            keyboard = [[InlineKeyboardButton("🔗 عضویت در کانال", url=f"https://t.me/{REQUIRED_CHANNEL.replace('@', '')}")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.message.reply_text(
                "⚠️ ابتدا در این کانال عضو شوید:",
                reply_markup=reply_markup
            )
            return ConversationHandler.END
        
        last_claim = users_data[user_id].get('last_daily_claim')
        now = datetime.now()
        
        if last_claim:
            last_claim_date = datetime.fromisoformat(last_claim)
            if now - last_claim_date < timedelta(hours=24):
                remaining = timedelta(hours=24) - (now - last_claim_date)
                hours = remaining.seconds // 3600
                minutes = (remaining.seconds % 3600) // 60
                await query.message.reply_text(
                    f"⏰ شما قبلاً امتیاز روزانه خود را دریافت کرده‌اید.\n"
                    f"⏳ زمان باقی‌مانده: {hours} ساعت و {minutes} دقیقه"
                )
                return ConversationHandler.END
        
        # اضافه کردن امتیاز
        users_data[user_id]['points'] += 10
        users_data[user_id]['last_daily_claim'] = now.isoformat()
        save_users_data(users_data)
        
        await query.message.reply_text(
            f"✅ تبریک! 10 امتیاز دریافت کردید\n"
            f"💰 امتیاز فعلی شما: {users_data[user_id]['points']}"
        )
        return ConversationHandler.END
    
    # خرید حساب ویژه
    elif query.data == 'buy_premium':
        await query.message.reply_text(
            f"⭐️ برای خرید حساب ویژه به پشتیبانی مراجعه کنید:\n"
            f"👤 @{SUPPORT_ID}"
        )
        return ConversationHandler.END
    
    # شروع ساخت رسید
    elif query.data.startswith('receipt_') or query.data == 'bank_sms':
        context.user_data['receipt_type'] = query.data
        await query.message.reply_text("📝 لطفاً شماره کارت مبدا را وارد کنید:\n\n💡 مثال: 6037-9971-1234-5678")
        return CARD_SOURCE
    
    return ConversationHandler.END

# دریافت شماره کارت مبدا
async def get_card_source(update: Update, context: ContextTypes.DEFAULT_TYPE):
    card_source = update.message.text.strip()
    
    # بررسی فرمت شماره کارت
    card_clean = re.sub(r'\D', '', card_source)
    if len(card_clean) != 16:
        await update.message.reply_text("❌ شماره کارت نامعتبر است. لطفاً 16 رقم وارد کنید.")
        return CARD_SOURCE
    
    context.user_data['card_source'] = format_card_number(card_source)
    await update.message.reply_text("📝 لطفاً شماره کارت مقصد را وارد کنید:\n\n💡 مثال: 6219-8611-2345-6789")
    return CARD_DEST

# دریافت شماره کارت مقصد و استعلام
async def get_card_dest(update: Update, context: ContextTypes.DEFAULT_TYPE):
    card_dest = update.message.text.strip()
    
    # بررسی فرمت شماره کارت
    card_clean = re.sub(r'\D', '', card_dest)
    if len(card_clean) != 16:
        await update.message.reply_text("❌ شماره کارت نامعتبر است. لطفاً 16 رقم وارد کنید.")
        return CARD_DEST
    
    # نمایش پیام در حال استعلام
    processing_msg = await update.message.reply_text("🔍 در حال استعلام شماره کارت...")
    
    # استعلام اطلاعات کارت
    card_info = query_card_info(card_dest)
    
    if card_info and card_info['success']:
        context.user_data['card_dest'] = format_card_number(card_dest)
        context.user_data['card_dest_owner'] = card_info['owner_name']
        context.user_data['card_dest_bank'] = card_info.get('bank', 'نامشخص')
        
        # حذف پیام در حال استعلام
        await processing_msg.delete()
        
        # نمایش اطلاعات کارت و درخواست تایید
        keyboard = [
            [InlineKeyboardButton("✅ تایید و ادامه", callback_data='verify_yes')],
            [InlineKeyboardButton("❌ اصلاح شماره کارت", callback_data='verify_no')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        verify_text = f"""
╔═══════════════════════╗
      استعلام شماره کارت
╚═══════════════════════╝

💳 شماره کارت: {context.user_data['card_dest']}
🏦 بانک: {card_info.get('bank', 'نامشخص')}
👤 نام صاحب کارت: {card_info['owner_name']}

❓ آیا اطلاعات صحیح است؟
"""
        
        await update.message.reply_text(verify_text, reply_markup=reply_markup)
        return VERIFY_CARD
    else:
        await processing_msg.delete()
        await update.message.reply_text("❌ خطا در استعلام کارت. لطفاً دوباره وارد کنید:")
        return CARD_DEST

# تایید یا رد استعلام کارت
async def verify_card(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == 'verify_yes':
        await query.message.reply_text("💰 لطفاً مبلغ انتقال را وارد کنید:\n\n💡 مثال: 500000")
        return AMOUNT
    else:
        await query.message.reply_text("📝 لطفاً شماره کارت مقصد را دوباره وارد کنید:")
        return CARD_DEST

# دریافت مبلغ
async def get_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    amount = update.message.text.strip()
    
    # بررسی عدد بودن مبلغ
    if not re.match(r'^\d+$', amount.replace(',', '')):
        await update.message.reply_text("❌ لطفاً مبلغ را به صورت عددی وارد کنید.")
        return AMOUNT
    
    # فرمت کردن مبلغ با کاما
    amount_formatted = "{:,}".format(int(amount.replace(',', '')))
    context.user_data['amount'] = amount_formatted
    
    await update.message.reply_text("👤 لطفاً نام و نام خانوادگی صاحب کارت مبدا را وارد کنید:\n\n💡 مثال: محمد احمدی")
    return CARD_NAME

# دریافت نام و نمایش پیش‌نمایش رسید
async def get_card_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    card_name = update.message.text.strip()
    context.user_data['card_name'] = card_name
    
    # اطلاعات رسید
    receipt_type = context.user_data['receipt_type']
    
    # نام رسید
    receipt_names = {
        'receipt_up': 'آپ',
        'receipt_hamrah_card': 'همراه کارت',
        'receipt_iva': 'ایوا',
        'receipt_top': 'تاپ',
        'receipt_blue': 'بلو',
        'receipt_mellat': 'همراه بانک ملت',
        'receipt_tejarat': 'همراه بانک تجارت',
        'receipt_refah': 'همراه بانک رفاه',
        'receipt_melli_bam': 'همراه بانک ملی بام',
        'receipt_724': '724',
        'bank_sms': 'پیامک بانکی'
    }
    
    receipt_name = receipt_names.get(receipt_type, 'نامشخص')
    
    # پیش‌نمایش رسید
    preview_text = f"""
╔═══════════════════════╗
   پیش‌نمایش رسید {receipt_name}
╚═══════════════════════╝

💳 کارت مبدا: {context.user_data['card_source']}
👤 صاحب کارت مبدا: {card_name}

💳 کارت مقصد: {context.user_data['card_dest']}
👤 صاحب کارت مقصد: {context.user_data.get('card_dest_owner', 'نامشخص')}
🏦 بانک: {context.user_data.get('card_dest_bank', 'نامشخص')}

💰 مبلغ: {context.user_data['amount']} تومان
📅 تاریخ: {datetime.now().strftime('%Y/%m/%d')}
🕐 زمان: {datetime.now().strftime('%H:%M:%S')}

❓ آیا اطلاعات صحیح است؟
"""
    
    keyboard = [
        [InlineKeyboardButton("✅ تایید و ساخت رسید", callback_data='confirm_yes')],
        [InlineKeyboardButton("❌ لغو", callback_data='confirm_no')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(preview_text, reply_markup=reply_markup)
    return CONFIRM_RECEIPT

# تایید نهایی و ساخت رسید
async def confirm_receipt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == 'confirm_no':
        await query.message.reply_text("❌ ساخت رسید لغو شد.")
        await show_main_menu(update, context)
        return ConversationHandler.END
    
    # اطلاعات رسید
    receipt_type = context.user_data['receipt_type']
    
    receipt_names = {
        'receipt_up': 'آپ',
        'receipt_hamrah_card': 'همراه کارت',
        'receipt_iva': 'ایوا',
        'receipt_top': 'تاپ',
        'receipt_blue': 'بلو',
        'receipt_mellat': 'همراه بانک ملت',
        'receipt_tejarat': 'همراه بانک تجارت',
        'receipt_refah': 'همراه بانک رفاه',
        'receipt_melli_bam': 'همراه بانک ملی بام',
        'receipt_724': '724',
        'bank_sms': 'پیامک بانکی'
    }
    
    receipt_name = receipt_names.get(receipt_type, 'نامشخص')
    now = datetime.now()
    
    # ساخت رسید نهایی
    receipt_text = f"""
╔═══════════════════════════╗
        رسید {receipt_name}
╚═══════════════════════════╝

💳 کارت مبدا
   {context.user_data['card_source']}
   👤 {context.user_data['card_name']}

💳 کارت مقصد
   {context.user_data['card_dest']}
   👤 {context.user_data.get('card_dest_owner', 'نامشخص')}
   🏦 بانک {context.user_data.get('card_dest_bank', 'نامشخص')}

💰 مبلغ: {context.user_data['amount']} تومان
📅 تاریخ: {now.strftime('%Y/%m/%d')}
🕐 زمان: {now.strftime('%H:%M:%S')}
🔢 شماره پیگیری: {now.strftime('%Y%m%d%H%M%S')}

━━━━━━━━━━━━━━━━━━━━━
✅ رسید شما با موفقیت ساخته شد.
⚠️ در صورت کلاهبرداری اکانت شما 
    مسدود خواهد شد.
━━━━━━━━━━━━━━━━━━━━━
"""
    
    await query.message.reply_text(receipt_text)
    
    # ثبت آمار
    user_id = str(update.effective_user.id)
    users_data[user_id]['receipts_created'] = users_data[user_id].get('receipts_created', 0) + 1
    save_users_data(users_data)
    
    # بازگشت به منوی اصلی
    await show_main_menu(update, context)
    
    return ConversationHandler.END

# لغو عملیات
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ عملیات لغو شد.")
    await show_main_menu(update, context)
    return ConversationHandler.END

def main():
    # ساخت اپلیکیشن
    application = Application.builder().token(BOT_TOKEN).build()
    
    # هندلر مکالمه برای ساخت رسید
    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(button_handler)],
        states={
            CARD_SOURCE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_card_source)],
            CARD_DEST: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_card_dest)],
            VERIFY_CARD: [CallbackQueryHandler(verify_card)],
            AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_amount)],
            CARD_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_card_name)],
            CONFIRM_RECEIPT: [CallbackQueryHandler(confirm_receipt)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )
    
    # اضافه کردن هندلرها
    application.add_handler(CommandHandler("start", start))
    application.add_handler(conv_handler)
    
    # شروع ربات
    logger.info("ربات شروع به کار کرد...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()