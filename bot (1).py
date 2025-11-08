import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes, ConversationHandler
from datetime import datetime, timedelta
from PIL import Image, ImageDraw, ImageFont
import json
import os
import re
import io
import requests
from io import BytesIO

# تنظیمات لاگینگ
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# تنظیمات ربات
BOT_TOKEN = os.environ.get('BOT_TOKEN', 'YOUR_BOT_TOKEN_HERE')
REQUIRED_CHANNEL = os.environ.get('REQUIRED_CHANNEL', '@your_channel_username')
SUPPORT_ID = os.environ.get('SUPPORT_ID', 'YOUR_SUPPORT_USERNAME')

# لینک تصاویر در GitHub - این لینک را تغییر دهید
GITHUB_REPO_URL = "https://raw.githubusercontent.com/amirking2313/telegram-bot4/main/receipt_templates/"
```

**⚠️ نکته:** اگر branch شما `master` است، `main` را به `master` تغییر دهید.

### مثال لینک صحیح:
```
https://raw.githubusercontent.com/amirking2313/telegram-bot4/main/receipt_templates/receipt_up.jpg
```

---

## 📦 فایل‌های نهایی پروژه:
```
telegram-receipt-bot/
├── main.py                    ← کد اصلی ربات (Artifact 1)
├── requirements.txt           ← کتابخانه‌ها (Artifact 2)
├── Procfile                   ← برای Heroku
├── runtime.txt                ← نسخه Python
└── users_data.json            ← خودکار ساخته می‌شود
```

**تصاویر در GitHub:**
```
your-github-repo/
└── receipt_templates/
    ├── receipt_up.jpg
    ├── receipt_hamrah_card.jpg
    └── ... (بقیه تصاویر)

# مراحل مکالمه
CARD_SOURCE, CARD_DEST, DEST_OWNER_NAME, AMOUNT, SOURCE_OWNER_NAME, CONFIRM_RECEIPT = range(6)

# فایل ذخیره‌سازی
USER_DATA_FILE = "users_data.json"
OUTPUT_DIR = "generated_receipts"

# ساخت پوشه خروجی
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

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

# تنظیمات رسیدها با لینک‌های GitHub
RECEIPT_CONFIGS = {
    'receipt_up': {
        'template_url': GITHUB_REPO_URL + 'receipt_up.jpg',
        'name': 'آپ',
        'positions': {
            'card_source': (100, 400),
            'card_dest': (100, 500),
            'amount': (100, 600),
            'source_owner': (100, 700),
            'dest_owner': (100, 800),
            'date': (100, 900),
            'time': (400, 900),
            'tracking': (100, 1000)
        },
        'font_size': 35,
        'color': (0, 0, 0)
    },
    'receipt_hamrah_card': {
        'template_url': GITHUB_REPO_URL + 'receipt_hamrah_card.jpg',
        'name': 'همراه کارت',
        'positions': {
            'card_source': (120, 420),
            'card_dest': (120, 520),
            'amount': (120, 620),
            'source_owner': (120, 720),
            'dest_owner': (120, 820),
            'date': (120, 920),
            'time': (420, 920),
            'tracking': (120, 1020)
        },
        'font_size': 36,
        'color': (0, 0, 0)
    },
    'receipt_iva': {
        'template_url': GITHUB_REPO_URL + 'receipt_iva.jpg',
        'name': 'ایوا',
        'positions': {
            'card_source': (110, 410),
            'card_dest': (110, 510),
            'amount': (110, 610),
            'source_owner': (110, 710),
            'dest_owner': (110, 810),
            'date': (110, 910),
            'time': (410, 910),
            'tracking': (110, 1010)
        },
        'font_size': 34,
        'color': (255, 255, 255)
    },
    'receipt_top': {
        'template_url': GITHUB_REPO_URL + 'receipt_top.jpg',
        'name': 'تاپ',
        'positions': {
            'card_source': (105, 415),
            'card_dest': (105, 515),
            'amount': (105, 615),
            'source_owner': (105, 715),
            'dest_owner': (105, 815),
            'date': (105, 915),
            'time': (405, 915),
            'tracking': (105, 1015)
        },
        'font_size': 35,
        'color': (0, 0, 0)
    },
    'receipt_blue': {
        'template_url': GITHUB_REPO_URL + 'receipt_blue.jpg',
        'name': 'بلو',
        'positions': {
            'card_source': (115, 425),
            'card_dest': (115, 525),
            'amount': (115, 625),
            'source_owner': (115, 725),
            'dest_owner': (115, 825),
            'date': (115, 925),
            'time': (415, 925),
            'tracking': (115, 1025)
        },
        'font_size': 33,
        'color': (255, 255, 255)
    },
    'receipt_mellat': {
        'template_url': GITHUB_REPO_URL + 'receipt_mellat.jpg',
        'name': 'همراه بانک ملت',
        'positions': {
            'card_source': (125, 435),
            'card_dest': (125, 535),
            'amount': (125, 635),
            'source_owner': (125, 735),
            'dest_owner': (125, 835),
            'date': (125, 935),
            'time': (425, 935),
            'tracking': (125, 1035)
        },
        'font_size': 37,
        'color': (218, 0, 55)
    },
    'receipt_tejarat': {
        'template_url': GITHUB_REPO_URL + 'receipt_tejarat.jpg',
        'name': 'همراه بانک تجارت',
        'positions': {
            'card_source': (108, 418),
            'card_dest': (108, 518),
            'amount': (108, 618),
            'source_owner': (108, 718),
            'dest_owner': (108, 818),
            'date': (108, 918),
            'time': (408, 918),
            'tracking': (108, 1018)
        },
        'font_size': 35,
        'color': (0, 51, 102)
    },
    'receipt_refah': {
        'template_url': GITHUB_REPO_URL + 'receipt_refah.jpg',
        'name': 'همراه بانک رفاه',
        'positions': {
            'card_source': (118, 428),
            'card_dest': (118, 528),
            'amount': (118, 628),
            'source_owner': (118, 728),
            'dest_owner': (118, 828),
            'date': (118, 928),
            'time': (418, 928),
            'tracking': (118, 1028)
        },
        'font_size': 36,
        'color': (0, 112, 60)
    },
    'receipt_melli_bam': {
        'template_url': GITHUB_REPO_URL + 'receipt_melli_bam.jpg',
        'name': 'همراه بانک ملی بام',
        'positions': {
            'card_source': (112, 422),
            'card_dest': (112, 522),
            'amount': (112, 622),
            'source_owner': (112, 722),
            'dest_owner': (112, 822),
            'date': (112, 922),
            'time': (412, 922),
            'tracking': (112, 1022)
        },
        'font_size': 34,
        'color': (0, 86, 184)
    },
    'receipt_724': {
        'template_url': GITHUB_REPO_URL + 'receipt_724.jpg',
        'name': '724',
        'positions': {
            'card_source': (130, 440),
            'card_dest': (130, 540),
            'amount': (130, 640),
            'source_owner': (130, 740),
            'dest_owner': (130, 840),
            'date': (130, 940),
            'time': (430, 940),
            'tracking': (130, 1040)
        },
        'font_size': 38,
        'color': (0, 0, 0)
    },
    'bank_sms': {
        'template_url': GITHUB_REPO_URL + 'bank_sms.jpg',
        'name': 'پیامک بانکی',
        'positions': {
            'card_source': (80, 350),
            'card_dest': (80, 430),
            'amount': (80, 510),
            'date': (80, 590),
            'time': (300, 590),
            'tracking': (80, 670)
        },
        'font_size': 30,
        'color': (0, 0, 0)
    }
}

def format_card_number(card):
    """فرمت کردن شماره کارت"""
    card_clean = re.sub(r'\D', '', card)
    if len(card_clean) == 16:
        return f"{card_clean[:4]}-{card_clean[4:8]}-{card_clean[8:12]}-{card_clean[12:]}"
    return card

def download_image_from_url(url):
    """دانلود تصویر از URL"""
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return Image.open(BytesIO(response.content))
        else:
            logger.error(f"خطا در دانلود تصویر: {response.status_code}")
            return None
    except Exception as e:
        logger.error(f"خطا در دانلود تصویر: {e}")
        return None

def create_receipt_image(receipt_type, data):
    """ساخت تصویر رسید"""
    try:
        config = RECEIPT_CONFIGS.get(receipt_type)
        if not config:
            logger.error(f"تنظیمات {receipt_type} یافت نشد")
            return None
        
        # دانلود تصویر از GitHub
        img = download_image_from_url(config['template_url'])
        
        if not img:
            logger.warning(f"تمپلیت {config['template_url']} دانلود نشد - ساخت تصویر پیش‌فرض")
            img = Image.new('RGB', (1080, 1920), color=(250, 250, 250))
            draw = ImageDraw.Draw(img)
            try:
                title_font = ImageFont.truetype("arial.ttf", 60)
            except:
                title_font = ImageFont.load_default()
            draw.text((540, 100), f"رسید {config['name']}", font=title_font, fill=(0, 0, 0), anchor="mm")
        
        # تبدیل به RGB
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        draw = ImageDraw.Draw(img)
        
        # بارگذاری فونت
        try:
            font = ImageFont.truetype("arial.ttf", config['font_size'])
        except:
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", config['font_size'])
            except:
                try:
                    font = ImageFont.truetype("C:\\Windows\\Fonts\\arial.ttf", config['font_size'])
                except:
                    font = ImageFont.load_default()
                    logger.warning("از فونت پیش‌فرض استفاده شد")
        
        positions = config['positions']
        color = config['color']
        
        # نوشتن اطلاعات
        if 'card_source' in positions and data.get('card_source'):
            draw.text(positions['card_source'], data['card_source'], font=font, fill=color)
        
        if 'card_dest' in positions and data.get('card_dest'):
            draw.text(positions['card_dest'], data['card_dest'], font=font, fill=color)
        
        if 'amount' in positions and data.get('amount'):
            draw.text(positions['amount'], f"{data['amount']} تومان", font=font, fill=color)
        
        if 'source_owner' in positions and data.get('source_owner'):
            draw.text(positions['source_owner'], data['source_owner'], font=font, fill=color)
        
        if 'dest_owner' in positions and data.get('dest_owner'):
            draw.text(positions['dest_owner'], data['dest_owner'], font=font, fill=color)
        
        if 'date' in positions and data.get('date'):
            draw.text(positions['date'], data['date'], font=font, fill=color)
        
        if 'time' in positions and data.get('time'):
            draw.text(positions['time'], data['time'], font=font, fill=color)
        
        if 'tracking' in positions and data.get('tracking'):
            draw.text(positions['tracking'], data['tracking'], font=font, fill=color)
        
        # ذخیره در بافر
        output = io.BytesIO()
        img.save(output, format='JPEG', quality=95)
        output.seek(0)
        
        return output
        
    except Exception as e:
        logger.error(f"خطا در ساخت رسید: {e}")
        return None

async def check_channel_membership(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """بررسی عضویت در کانال"""
    user_id = update.effective_user.id
    try:
        member = await context.bot.get_chat_member(REQUIRED_CHANNEL, user_id)
        return member.status in ['member', 'administrator', 'creator']
    except Exception as e:
        logger.error(f"خطا در بررسی عضویت: {e}")
        return False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دستور شروع"""
    user = update.effective_user
    user_id = str(user.id)
    
    if user_id not in users_data:
        users_data[user_id] = {
            'points': 0,
            'is_premium': False,
            'last_daily_claim': None,
            'receipts_created': 0
        }
        save_users_data(users_data)
    
    last_name = user.last_name or ''
    username = f"@{user.username}" if user.username else 'ندارد'
    
    welcome_text = f"""
╔═══════════════════════╗
        خوش آمدید
╚═══════════════════════╝

👤 نام: {user.first_name} {last_name}
🆔 یوزرنیم: {username}
🔢 آیدی: {user.id}
💰 امتیاز: {users_data[user_id]['points']}
📊 تعداد رسید: {users_data[user_id]['receipts_created']}

🎉 به ربات رسید ساز خوش‌آمدی!
"""
    
    await update.message.reply_text(welcome_text)
    await show_main_menu(update, context)

async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش منوی اصلی"""
    keyboard = [
        [InlineKeyboardButton("💳 آپ", callback_data='receipt_up'),
         InlineKeyboardButton("💳 همراه کارت", callback_data='receipt_hamrah_card')],
        [InlineKeyboardButton("💳 ایوا", callback_data='receipt_iva'),
         InlineKeyboardButton("💳 تاپ", callback_data='receipt_top')],
        [InlineKeyboardButton("💳 بلو", callback_data='receipt_blue'),
         InlineKeyboardButton("💳 همراه بانک ملت", callback_data='receipt_mellat')],
        [InlineKeyboardButton("💳 همراه بانک تجارت", callback_data='receipt_tejarat'),
         InlineKeyboardButton("💳 همراه بانک رفاه", callback_data='receipt_refah')],
        [InlineKeyboardButton("💳 همراه بانک ملی", callback_data='receipt_melli_bam'),
         InlineKeyboardButton("💳 724", callback_data='receipt_724')],
        [InlineKeyboardButton("📱 پیامک بانکی", callback_data='bank_sms')],
        [InlineKeyboardButton("⭐️ خرید VIP", callback_data='buy_premium'),
         InlineKeyboardButton("🎁 سکه روزانه", callback_data='daily_coin')]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    text = "❓ چه نوع رسیدی می‌خواهید بسازید؟"
    
    if update.callback_query:
        await update.callback_query.message.reply_text(text, reply_markup=reply_markup)
    else:
        await update.message.reply_text(text, reply_markup=reply_markup)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """مدیریت دکمه‌ها"""
    query = update.callback_query
    await query.answer()
    
    user_id = str(update.effective_user.id)
    
    if query.data == 'daily_coin':
        is_member = await check_channel_membership(update, context)
        
        if not is_member:
            keyboard = [[InlineKeyboardButton("🔗 عضویت در کانال", url=f"https://t.me/{REQUIRED_CHANNEL.replace('@', '')}")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.message.reply_text("⚠️ ابتدا در کانال عضو شوید:", reply_markup=reply_markup)
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
                    f"⏰ امتیاز روزانه دریافت شده\n"
                    f"⏳ زمان باقیمانده: {hours}:{minutes:02d}"
                )
                return ConversationHandler.END
        
        users_data[user_id]['points'] += 10
        users_data[user_id]['last_daily_claim'] = now.isoformat()
        save_users_data(users_data)
        
        await query.message.reply_text(
            f"✅ +10 امتیاز دریافت شد!\n"
            f"💰 امتیاز کل: {users_data[user_id]['points']}"
        )
        return ConversationHandler.END
    
    elif query.data == 'buy_premium':
        await query.message.reply_text(
            f"⭐️ خرید حساب ویژه:\n"
            f"👤 @{SUPPORT_ID}"
        )
        return ConversationHandler.END
    
    elif query.data.startswith('receipt_') or query.data == 'bank_sms':
        context.user_data['receipt_type'] = query.data
        await query.message.reply_text("📝 شماره کارت مبدا:\n\n💡 مثال: 6037997112345678")
        return CARD_SOURCE
    
    return ConversationHandler.END

async def get_card_source(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دریافت کارت مبدا"""
    card_source = update.message.text.strip()
    card_clean = re.sub(r'\D', '', card_source)
    
    if len(card_clean) != 16:
        await update.message.reply_text("❌ شماره کارت باید 16 رقم باشد")
        return CARD_SOURCE
    
    context.user_data['card_source'] = format_card_number(card_source)
    await update.message.reply_text("📝 شماره کارت مقصد:\n\n💡 مثال: 6219861123456789")
    return CARD_DEST

async def get_card_dest(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دریافت کارت مقصد"""
    card_dest = update.message.text.strip()
    card_clean = re.sub(r'\D', '', card_dest)
    
    if len(card_clean) != 16:
        await update.message.reply_text("❌ شماره کارت باید 16 رقم باشد")
        return CARD_DEST
    
    context.user_data['card_dest'] = format_card_number(card_dest)
    await update.message.reply_text("👤 نام صاحب کارت مقصد:\n\n💡 مثال: علی احمدی")
    return DEST_OWNER_NAME

async def get_dest_owner_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دریافت نام صاحب کارت مقصد"""
    dest_owner = update.message.text.strip()
    context.user_data['dest_owner'] = dest_owner
    await update.message.reply_text("💰 مبلغ (تومان):\n\n💡 مثال: 500000")
    return AMOUNT

async def get_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دریافت مبلغ"""
    amount = update.message.text.strip()
    
    if not re.match(r'^\d+$', amount.replace(',', '')):
        await update.message.reply_text("❌ مبلغ را به صورت عددی وارد کنید")
        return AMOUNT
    
    amount_formatted = "{:,}".format(int(amount.replace(',', '')))
    context.user_data['amount'] = amount_formatted
    
    await update.message.reply_text("👤 نام صاحب کارت مبدا:\n\n💡 مثال: محمد رضایی")
    return SOURCE_OWNER_NAME

async def get_source_owner_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دریافت نام صاحب کارت مبدا و پیش‌نمایش"""
    source_owner = update.message.text.strip()
    context.user_data['source_owner'] = source_owner
    
    receipt_type = context.user_data['receipt_type']
    config = RECEIPT_CONFIGS.get(receipt_type, {})
    receipt_name = config.get('name', 'نامشخص')
    
    preview_text = f"""
╔═══════════════════════╗
   پیش‌نمایش رسید {receipt_name}
╚═══════════════════════╝

💳 کارت مبدا: {context.user_data['card_source']}
👤 {source_owner}

💳 کارت مقصد: {context.user_data['card_dest']}
👤 {context.user_data['dest_owner']}

💰 {context.user_data['amount']} تومان
📅 {datetime.now().strftime('%Y/%m/%d')}
🕐 {datetime.now().strftime('%H:%M:%S')}

❓ تایید می‌کنید؟
"""
    
    keyboard = [
        [InlineKeyboardButton("✅ ساخت رسید", callback_data='confirm_yes')],
        [InlineKeyboardButton("❌ لغو", callback_data='confirm_no')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(preview_text, reply_markup=reply_markup)
    return CONFIRM_RECEIPT

async def confirm_receipt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ساخت رسید نهایی"""
    query = update.callback_query
    await query.answer()
    
    if query.data == 'confirm_no':
        await query.message.reply_text("❌ لغو شد")
        await show_main_menu(update, context)
        return ConversationHandler.END
    
    processing_msg = await query.message.reply_text("🎨 در حال ساخت رسید...")
    
    receipt_type = context.user_data['receipt_type']
    now = datetime.now()
    
    receipt_data = {
        'card_source': context.user_data['card_source'],
        'card_dest': context.user_data['card_dest'],
        'amount': context.user_data['amount'],
        'source_owner': context.user_data['source_owner'],
        'dest_owner': context.user_data['dest_owner'],
        'date': now.strftime('%Y/%m/%d'),
        'time': now.strftime('%H:%M:%S'),
        'tracking': now.strftime('%Y%m%d%H%M%S')
    }
    
    receipt_image = create_receipt_image(receipt_type, receipt_data)
    
    if receipt_image:
        await processing_msg.delete()
        
        config = RECEIPT_CONFIGS.get(receipt_type, {})
        caption = f"""
✅ رسید {config.get('name', 'نامشخص')} با موفقیت ساخته شد

⚠️ هشدار: در صورت کلاهبرداری اکانت شما مسدود خواهد شد
"""
        
        await query.message.reply_photo(
            photo=receipt_image,
            caption=caption
        )
        
        user_id = str(update.effective_user.id)
        users_data[user_id]['receipts_created'] = users_data[user_id].get('receipts_created', 0) + 1
        save_users_data(users_data)
        
    else:
        await processing_msg.edit_text("❌ خطا در ساخت رسید. لطفاً دوباره تلاش کنید.")
    
    await show_main_menu(update, context)
    
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """لغو عملیات"""
    await update.message.reply_text("❌ لغو شد")
    await show_main_menu(update, context)
    return ConversationHandler.END

def main():
    """تابع اصلی"""
    application = Application.builder().token(BOT_TOKEN).build()
    
    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(button_handler)],
        states={
            CARD_SOURCE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_card_source)],
            CARD_DEST: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_card_dest)],
            DEST_OWNER_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_dest_owner_name)],
            AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_amount)],
            SOURCE_OWNER_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_source_owner_name)],
            CONFIRM_RECEIPT: [CallbackQueryHandler(confirm_receipt)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(conv_handler)
    
    logger.info("✅ ربات شروع به کار کرد...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()

