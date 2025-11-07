from keep_alive import keep_alive
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes, ConversationHandler
from datetime import datetime, timedelta
from PIL import Image, ImageDraw, ImageFont
import json
import os
import re
import io

# تنظیمات لاگینگ
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# تنظیمات ربات
BOT_TOKEN = os.environ.get('BOT_TOKEN', 'YOUR_BOT_TOKEN_HERE')
REQUIRED_CHANNEL = os.environ.get('REQUIRED_CHANNEL', '@your_channel_username')
SUPPORT_ID = os.environ.get('SUPPORT_ID', 'YOUR_SUPPORT_USERNAME')

# مسیر پوشه تصاویر
RECEIPTS_DIR = "receipt_templates"
OUTPUT_DIR = "generated_receipts"

# مراحل مکالمه
CARD_SOURCE, CARD_DEST, VERIFY_CARD, AMOUNT, CARD_NAME, CONFIRM_RECEIPT = range(6)

# فایل ذخیره‌سازی
USER_DATA_FILE = "users_data.json"

# ساخت پوشه‌ها
for directory in [RECEIPTS_DIR, OUTPUT_DIR]:
    if not os.path.exists(directory):
        os.makedirs(directory)

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

# تنظیمات موقعیت متن برای هر رسید
# این مختصات باید بر اساس تصاویر واقعی شما تنظیم شوند
RECEIPT_CONFIGS = {
    'receipt_up': {
        'template': 'receipt_up.jpg',
        'name': 'آپ',
        'positions': {
            'card_source': (100, 400),      # شماره کارت مبدا
            'card_dest': (100, 500),        # شماره کارت مقصد
            'amount': (100, 600),           # مبلغ
            'card_name': (100, 700),        # نام صاحب کارت مبدا
            'dest_owner': (100, 800),       # نام صاحب کارت مقصد
            'date': (100, 900),             # تاریخ
            'time': (400, 900),             # زمان
            'tracking': (100, 1000)         # شماره پیگیری
        },
        'font_size': 35,
        'color': (0, 0, 0)  # رنگ مشکی
    },
    'receipt_hamrah_card': {
        'template': 'receipt_hamrah_card.jpg',
        'name': 'همراه کارت',
        'positions': {
            'card_source': (120, 420),
            'card_dest': (120, 520),
            'amount': (120, 620),
            'card_name': (120, 720),
            'dest_owner': (120, 820),
            'date': (120, 920),
            'time': (420, 920),
            'tracking': (120, 1020)
        },
        'font_size': 36,
        'color': (0, 0, 0)
    },
    'receipt_iva': {
        'template': 'receipt_iva.jpg',
        'name': 'ایوا',
        'positions': {
            'card_source': (110, 410),
            'card_dest': (110, 510),
            'amount': (110, 610),
            'card_name': (110, 710),
            'dest_owner': (110, 810),
            'date': (110, 910),
            'time': (410, 910),
            'tracking': (110, 1010)
        },
        'font_size': 34,
        'color': (255, 255, 255)  # رنگ سفید
    },
    'receipt_top': {
        'template': 'receipt_top.jpg',
        'name': 'تاپ',
        'positions': {
            'card_source': (105, 415),
            'card_dest': (105, 515),
            'amount': (105, 615),
            'card_name': (105, 715),
            'dest_owner': (105, 815),
            'date': (105, 915),
            'time': (405, 915),
            'tracking': (105, 1015)
        },
        'font_size': 35,
        'color': (0, 0, 0)
    },
    'receipt_blue': {
        'template': 'receipt_blue.jpg',
        'name': 'بلو',
        'positions': {
            'card_source': (115, 425),
            'card_dest': (115, 525),
            'amount': (115, 625),
            'card_name': (115, 725),
            'dest_owner': (115, 825),
            'date': (115, 925),
            'time': (415, 925),
            'tracking': (115, 1025)
        },
        'font_size': 33,
        'color': (255, 255, 255)
    },
    'receipt_mellat': {
        'template': 'receipt_mellat.jpg',
        'name': 'همراه بانک ملت',
        'positions': {
            'card_source': (125, 435),
            'card_dest': (125, 535),
            'amount': (125, 635),
            'card_name': (125, 735),
            'dest_owner': (125, 835),
            'date': (125, 935),
            'time': (425, 935),
            'tracking': (125, 1035)
        },
        'font_size': 37,
        'color': (218, 0, 55)  # رنگ قرمز ملت
    },
    'receipt_tejarat': {
        'template': 'receipt_tejarat.jpg',
        'name': 'همراه بانک تجارت',
        'positions': {
            'card_source': (108, 418),
            'card_dest': (108, 518),
            'amount': (108, 618),
            'card_name': (108, 718),
            'dest_owner': (108, 818),
            'date': (108, 918),
            'time': (408, 918),
            'tracking': (108, 1018)
        },
        'font_size': 35,
        'color': (0, 51, 102)  # رنگ آبی تجارت
    },
    'receipt_refah': {
        'template': 'receipt_refah.jpg',
        'name': 'همراه بانک رفاه',
        'positions': {
            'card_source': (118, 428),
            'card_dest': (118, 528),
            'amount': (118, 628),
            'card_name': (118, 728),
            'dest_owner': (118, 828),
            'date': (118, 928),
            'time': (418, 928),
            'tracking': (118, 1028)
        },
        'font_size': 36,
        'color': (0, 112, 60)  # رنگ سبز رفاه
    },
    'receipt_melli_bam': {
        'template': 'receipt_melli_bam.jpg',
        'name': 'همراه بانک ملی بام',
        'positions': {
            'card_source': (112, 422),
            'card_dest': (112, 522),
            'amount': (112, 622),
            'card_name': (112, 722),
            'dest_owner': (112, 822),
            'date': (112, 922),
            'time': (412, 922),
            'tracking': (112, 1022)
        },
        'font_size': 34,
        'color': (0, 86, 184)  # رنگ آبی ملی
    },
    'receipt_724': {
        'template': 'receipt_724.jpg',
        'name': '724',
        'positions': {
            'card_source': (130, 440),
            'card_dest': (130, 540),
            'amount': (130, 640),
            'card_name': (130, 740),
            'dest_owner': (130, 840),
            'date': (130, 940),
            'time': (430, 940),
            'tracking': (130, 1040)
        },
        'font_size': 38,
        'color': (0, 0, 0)
    },
    'bank_sms': {
        'template': 'bank_sms.jpg',
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

def query_card_info(card_number):
    """استعلام شماره کارت"""
    card_clean = re.sub(r'\D', '', card_number)
    
    if len(card_clean) != 16:
        return None
    
    # دیتابیس شبیه‌سازی شده
    fake_database = {
        '6037': {'bank': 'ملی ایران', 'names': ['علی رضایی', 'محمد احمدی', 'حسین محمدی']},
        '6219': {'bank': 'سامان', 'names': ['فاطمه کریمی', 'زهرا حسینی', 'مریم اکبری']},
        '6104': {'bank': 'ملت', 'names': ['امیر تقی‌پور', 'رضا صادقی', 'مهدی کاظمی']},
        '6273': {'bank': 'تجارت', 'names': ['سارا یوسفی', 'نرگس رحیمی', 'نازنین جعفری']},
        '6362': {'bank': 'آینده', 'names': ['حمید نوری', 'جواد مرادی', 'بهرام شریفی']},
        '6280': {'bank': 'پاسارگاد', 'names': ['الهام موسوی', 'مینا کریمی', 'سمیرا احمدی']},
    }
    
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
    
    default_names = ['احمد رحمانی', 'حسن موسوی', 'علیرضا حسینی', 'محمدرضا کریمی']
    import random
    return {
        'success': True,
        'bank': 'سایر بانک‌ها',
        'card_number': card_number,
        'owner_name': random.choice(default_names)
    }

def create_receipt_image(receipt_type, data):
    """ساخت تصویر رسید"""
    try:
        config = RECEIPT_CONFIGS.get(receipt_type)
        if not config:
            logger.error(f"تنظیمات {receipt_type} یافت نشد")
            return None
        
        template_path = os.path.join(RECEIPTS_DIR, config['template'])
        
        # بررسی وجود تمپلیت
        if not os.path.exists(template_path):
            logger.warning(f"تمپلیت {template_path} یافت نشد - ساخت تصویر پیش‌فرض")
            # ساخت تصویر جایگزین با ابعاد استاندارد موبایل
            img = Image.new('RGB', (1080, 1920), color=(250, 250, 250))
            draw = ImageDraw.Draw(img)
            try:
                title_font = ImageFont.truetype("arial.ttf", 60)
            except:
                title_font = ImageFont.load_default()
            draw.text((540, 100), f"رسید {config['name']}", font=title_font, fill=(0, 0, 0), anchor="mm")
        else:
            img = Image.open(template_path)
            # تبدیل به RGB در صورت نیاز
            if img.mode != 'RGB':
                img = img.convert('RGB')
        
        draw = ImageDraw.Draw(img)
        
        # بارگذاری فونت
        try:
            font = ImageFont.truetype("arial.ttf", config['font_size'])
        except:
            try:
                # فونت‌های موجود در لینوکس
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", config['font_size'])
            except:
                try:
                    # فونت در ویندوز
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
        
        if 'card_name' in positions and data.get('card_name'):
            draw.text(positions['card_name'], data['card_name'], font=font, fill=color)
        
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
    """دریافت کارت مقصد و استعلام"""
    card_dest = update.message.text.strip()
    card_clean = re.sub(r'\D', '', card_dest)
    
    if len(card_clean) != 16:
        await update.message.reply_text("❌ شماره کارت باید 16 رقم باشد")
        return CARD_DEST
    
    processing_msg = await update.message.reply_text("🔍 در حال استعلام...")
    
    card_info = query_card_info(card_dest)
    
    if card_info and card_info['success']:
        context.user_data['card_dest'] = format_card_number(card_dest)
        context.user_data['card_dest_owner'] = card_info['owner_name']
        context.user_data['card_dest_bank'] = card_info.get('bank', 'نامشخص')
        
        await processing_msg.delete()
        
        keyboard = [
            [InlineKeyboardButton("✅ تایید", callback_data='verify_yes')],
            [InlineKeyboardButton("❌ اصلاح", callback_data='verify_no')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        verify_text = f"""
╔═══════════════════════╗
      استعلام کارت
╚═══════════════════════╝

💳 {context.user_data['card_dest']}
🏦 {card_info.get('bank', 'نامشخص')}
👤 {card_info['owner_name']}

❓ تایید می‌کنید؟
"""
        
        await update.message.reply_text(verify_text, reply_markup=reply_markup)
        return VERIFY_CARD
    else:
        await processing_msg.delete()
        await update.message.reply_text("❌ خطا در استعلام. دوباره وارد کنید:")
        return CARD_DEST

async def verify_card(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """تایید استعلام"""
    query = update.callback_query
    await query.answer()
    
    if query.data == 'verify_yes':
        await query.message.reply_text("💰 مبلغ (تومان):\n\n💡 مثال: 500000")
        return AMOUNT
    else:
        await query.message.reply_text("📝 شماره کارت مقصد را دوباره وارد کنید:")
        return CARD_DEST

async def get_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دریافت مبلغ"""
    amount = update.message.text.strip()
    
    if not re.match(r'^\d+$', amount.replace(',', '')):
        await update.message.reply_text("❌ مبلغ را به صورت عددی وارد کنید")
        return AMOUNT
    
    amount_formatted = "{:,}".format(int(amount.replace(',', '')))
    context.user_data['amount'] = amount_formatted
    
    await update.message.reply_text("👤 نام صاحب کارت مبدا:\n\n💡 مثال: محمد احمدی")
    return CARD_NAME

async def get_card_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دریافت نام و پیش‌نمایش"""
    card_name = update.message.text.strip()
    context.user_data['card_name'] = card_name
    
    receipt_type = context.user_data['receipt_type']
    config = RECEIPT_CONFIGS.get(receipt_type, {})
    receipt_name = config.get('name', 'نامشخص')
    
    preview_text = f"""
╔═══════════════════════╗
   پیش‌نمایش رسید {receipt_name}
╚═══════════════════════╝

💳 کارت مبدا: {context.user_data['card_source']}
👤 {card_name}

💳 کارت مقصد: {context.user_data['card_dest']}
👤 {context.user_data.get('card_dest_owner', 'نامشخص')}
🏦 {context.user_data.get('card_dest_bank', 'نامشخص')}

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
    
    # نمایش پیام در حال ساخت
    processing_msg = await query.message.reply_text("🎨 در حال ساخت رسید...")
    
    receipt_type = context.user_data['receipt_type']
    now = datetime.now()
    
    # داده‌های رسید
    receipt_data = {
        'card_source': context.user_data['card_source'],
        'card_dest': context.user_data['card_dest'],
        'amount': context.user_data['amount'],
        'card_name': context.user_data['card_name'],
        'dest_owner': context.user_data.get('card_dest_owner', 'نامشخص'),
        'date': now.strftime('%Y/%m/%d'),
        'time': now.strftime('%H:%M:%S'),
        'tracking': now.strftime('%Y%m%d%H%M%S')
    }
    
    # ساخت تصویر رسید
    receipt_image = create_receipt_image(receipt_type, receipt_data)
    
    if receipt_image:
        await processing_msg.delete()
        
        # ارسال تصویر رسید
        config = RECEIPT_CONFIGS.get(receipt_type, {})
        caption = f"""
✅ رسید {config.get('name', 'نامشخص')} با موفقیت ساخته شد

⚠️ هشدار: در صورت کلاهبرداری اکانت شما مسدود خواهد شد
"""
        
        await query.message.reply_photo(
            photo=receipt_image,
            caption=caption
        )
        
        # ثبت آمار
        user_id = str(update.effective_user.id)
        users_data[user_id]['receipts_created'] = users_data[user_id].get('receipts_created', 0) + 1
        save_users_data(users_data)
        
    else:
        await processing_msg.edit_text("❌ خطا در ساخت رسید. لطفاً دوباره تلاش کنید.")
    
    # بازگشت به منو
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
    
    # هندلر مکالمه
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
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(conv_handler)
    
    logger.info("✅ ربات شروع به کار کرد...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
        '
