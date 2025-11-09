import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
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

# مراحل مکالمه
CARD_SOURCE, CARD_DEST, DEST_OWNER_NAME, AMOUNT, SOURCE_OWNER_NAME, CONFIRM_RECEIPT = range(6)

# فایل ذخیره‌سازی
USER_DATA_FILE = "users_data.json"
OUTPUT_DIR = "generated_receipts"

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

# تنظیمات رسیدها با مختصات دقیق
RECEIPT_CONFIGS = {
    'receipt_up': {
        'template': 'receipt_up.jpg',
        'name': 'آپ',
        'positions': {
            'card_source': (150, 400),
            'card_dest': (150, 500),
            'amount': (150, 600),
            'source_owner': (150, 700),
            'dest_owner': (150, 800),
            'date': (150, 900),
            'time': (450, 900),
            'tracking': (150, 1000)
        },
        'font_size': 38,
        'color': (0, 0, 0),
        'direction': 'rtl'
    },
    'receipt_hamrah_card': {
        'template': 'receipt_hamrah_card.jpg',
        'name': 'همراه کارت',
        'positions': {
            'card_source': (160, 410),
            'card_dest': (160, 510),
            'amount': (160, 610),
            'source_owner': (160, 710),
            'dest_owner': (160, 810),
            'date': (160, 910),
            'time': (460, 910),
            'tracking': (160, 1010)
        },
        'font_size': 36,
        'color': (0, 0, 0),
        'direction': 'rtl'
    },
    'receipt_iva': {
        'template': 'receipt_iva.jpg',
        'name': 'ایوا',
        'positions': {
            'card_source': (170, 420),
            'card_dest': (170, 520),
            'amount': (170, 620),
            'source_owner': (170, 720),
            'dest_owner': (170, 820),
            'date': (170, 920),
            'time': (470, 920),
            'tracking': (170, 1020)
        },
        'font_size': 35,
        'color': (255, 255, 255),
        'direction': 'rtl'
    },
    'receipt_top': {
        'template': 'receipt_top.jpg',
        'name': 'تاپ',
        'positions': {
            'card_source': (165, 415),
            'card_dest': (165, 515),
            'amount': (165, 615),
            'source_owner': (165, 715),
            'dest_owner': (165, 815),
            'date': (165, 915),
            'time': (465, 915),
            'tracking': (165, 1015)
        },
        'font_size': 37,
        'color': (0, 0, 0),
        'direction': 'rtl'
    },
    'receipt_blue': {
        'template': 'receipt_blue.jpg',
        'name': 'بلو',
        'positions': {
            'card_source': (155, 405),
            'card_dest': (155, 505),
            'amount': (155, 605),
            'source_owner': (155, 705),
            'dest_owner': (155, 805),
            'date': (155, 905),
            'time': (455, 905),
            'tracking': (155, 1005)
        },
        'font_size': 34,
        'color': (255, 255, 255),
        'direction': 'rtl'
    },
    'receipt_mellat': {
        'template': 'receipt_mellat.jpg',
        'name': 'همراه بانک ملت',
        'positions': {
            'card_source': (145, 395),
            'card_dest': (145, 495),
            'amount': (145, 595),
            'source_owner': (145, 695),
            'dest_owner': (145, 795),
            'date': (145, 895),
            'time': (445, 895),
            'tracking': (145, 995)
        },
        'font_size': 39,
        'color': (218, 0, 55),
        'direction': 'rtl'
    },
    'receipt_tejarat': {
        'template': 'receipt_tejarat.jpg',
        'name': 'همراه بانک تجارت',
        'positions': {
            'card_source': (158, 408),
            'card_dest': (158, 508),
            'amount': (158, 608),
            'source_owner': (158, 708),
            'dest_owner': (158, 808),
            'date': (158, 908),
            'time': (458, 908),
            'tracking': (158, 1008)
        },
        'font_size': 37,
        'color': (0, 51, 102),
        'direction': 'rtl'
    },
    'receipt_refah': {
        'template': 'receipt_refah.jpg',
        'name': 'همراه بانک رفاه',
        'positions': {
            'card_source': (162, 412),
            'card_dest': (162, 512),
            'amount': (162, 612),
            'source_owner': (162, 712),
            'dest_owner': (162, 812),
            'date': (162, 912),
            'time': (462, 912),
            'tracking': (162, 1012)
        },
        'font_size': 38,
        'color': (0, 112, 60),
        'direction': 'rtl'
    },
    'receipt_melli_bam': {
        'template': 'receipt_melli_bam.jpg',
        'name': 'همراه بانک ملی بام',
        'positions': {
            'card_source': (152, 402),
            'card_dest': (152, 502),
            'amount': (152, 602),
            'source_owner': (152, 702),
            'dest_owner': (152, 802),
            'date': (152, 902),
            'time': (452, 902),
            'tracking': (152, 1002)
        },
        'font_size': 36,
        'color': (0, 86, 184),
        'direction': 'rtl'
    },
    'receipt_724': {
        'template': 'receipt_724.jpg',
        'name': '724',
        'positions': {
            'card_source': (140, 390),
            'card_dest': (140, 490),
            'amount': (140, 590),
            'source_owner': (140, 690),
            'dest_owner': (140, 790),
            'date': (140, 890),
            'time': (440, 890),
            'tracking': (140, 990)
        },
        'font_size': 40,
        'color': (0, 0, 0),
        'direction': 'rtl'
    },
    'bank_sms': {
        'template': 'bank_sms.jpg',
        'name': 'پیامک بانکی',
        'positions': {
            'card_source': (120, 360),
            'card_dest': (120, 440),
            'amount': (120, 520),
            'date': (120, 600),
            'time': (370, 600),
            'tracking': (120, 680)
        },
        'font_size': 32,
        'color': (0, 0, 0),
        'direction': 'rtl'
    }
}

def format_card_number(card):
    """فرمت کردن شماره کارت"""
    card_clean = re.sub(r'\D', '', card)
    if len(card_clean) == 16:
        return f"{card_clean[:4]}-{card_clean[4:8]}-{card_clean[8:12]}-{card_clean[12:]}"
    return card

def fix_persian_text(text):
    """درست کردن متن فارسی"""
    try:
        from arabic_reshaper import reshape
        from bidi.algorithm import get_display
        reshaped = reshape(text)
        bidi = get_display(reshaped)
        return bidi
    except ImportError:
        # اگر کتابخانه نصب نبود، متن رو معکوس می‌کنیم (راه حل موقت)
        logger.warning("⚠️ کتابخانه‌های فارسی نصب نیست - استفاده از روش جایگزین")
        return text[::-1]
    except:
        return text

def create_receipt_image(receipt_type, data):
    """ساخت تصویر رسید"""
    try:
        config = RECEIPT_CONFIGS.get(receipt_type)
        if not config:
            logger.error(f"❌ تنظیمات {receipt_type} یافت نشد")
            return None
        
        # مسیر کامل فایل
        template_path = os.path.join(RECEIPTS_DIR, config['template'])
        abs_path = os.path.abspath(template_path)
        
        logger.info(f"🔍 جستجوی فایل: {abs_path}")
        
        # بررسی وجود فایل
        if not os.path.exists(template_path):
            logger.error(f"❌ فایل یافت نشد: {template_path}")
            logger.error(f"📁 پوشه فعلی: {os.getcwd()}")
            logger.error(f"📋 فایل‌های موجود در {RECEIPTS_DIR}:")
            
            if os.path.exists(RECEIPTS_DIR):
                files = os.listdir(RECEIPTS_DIR)
                for f in files:
                    logger.error(f"   - {f}")
            else:
                logger.error(f"   پوشه {RECEIPTS_DIR} وجود ندارد!")
            
            # ساخت رسید جایگزین با متن
            img = Image.new('RGB', (1080, 1920), color=(245, 245, 245))
            draw = ImageDraw.Draw(img)
            
            try:
                font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 50)
                font_medium = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 35)
                font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 28)
            except:
                font_large = ImageFont.load_default()
                font_medium = ImageFont.load_default()
                font_small = ImageFont.load_default()
            
            # رسم هدر
            draw.rectangle([(0, 0), (1080, 150)], fill=(41, 128, 185))
            title_text = fix_persian_text(f"رسید {config['name']}")
            draw.text((540, 75), title_text, font=font_large, fill=(255, 255, 255), anchor="mm")
            
            # رسم محتوا
            y_pos = 250
            line_height = 100
            
            info_items = [
                (f"کارت مبدا: {data.get('card_source', 'N/A')}", (0, 0, 0)),
                (f"کارت مقصد: {data.get('card_dest', 'N/A')}", (0, 0, 0)),
                (f"مبلغ: {data.get('amount', 'N/A')} تومان", (0, 150, 0)),
                (f"فرستنده: {data.get('source_owner', 'N/A')}", (0, 0, 0)),
                (f"گیرنده: {data.get('dest_owner', 'N/A')}", (0, 0, 0)),
                (f"تاریخ: {data.get('date', 'N/A')}", (100, 100, 100)),
                (f"زمان: {data.get('time', 'N/A')}", (100, 100, 100)),
                (f"شماره پیگیری: {data.get('tracking', 'N/A')}", (150, 0, 0)),
            ]
            
            for text, color in info_items:
                fixed_text = fix_persian_text(text)
                draw.text((540, y_pos), fixed_text, font=font_medium, fill=color, anchor="mm")
                y_pos += line_height
            
            # پیام خطا در پایین
            draw.rectangle([(50, 1700), (1030, 1850)], fill=(231, 76, 60))
            error_text = "Template image not found!"
            draw.text((540, 1775), error_text, font=font_small, fill=(255, 255, 255), anchor="mm")
            
        else:
            logger.info(f"✅ فایل یافت شد: {template_path}")
            
            # بارگذاری تصویر
            img = Image.open(template_path)
            
            # تبدیل به RGB
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            logger.info(f"✅ اندازه تصویر: {img.size}")
            
            draw = ImageDraw.Draw(img)
            
            # بارگذاری فونت
            font = None
            font_paths = [
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                "/System/Library/Fonts/Supplemental/Arial.ttf",
                "C:\\Windows\\Fonts\\arial.ttf",
                "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
                "arial.ttf"
            ]
            
            for font_path in font_paths:
                try:
                    font = ImageFont.truetype(font_path, config['font_size'])
                    logger.info(f"✅ فونت بارگذاری شد: {font_path}")
                    break
                except:
                    continue
            
            if not font:
                logger.warning("⚠️ استفاده از فونت پیش‌فرض")
                font = ImageFont.load_default()
            
            positions = config['positions']
            color = config['color']
            
            # نوشتن اطلاعات
            if 'card_source' in positions and data.get('card_source'):
                text = fix_persian_text(data['card_source'])
                draw.text(positions['card_source'], text, font=font, fill=color)
            
            if 'card_dest' in positions and data.get('card_dest'):
                text = fix_persian_text(data['card_dest'])
                draw.text(positions['card_dest'], text, font=font, fill=color)
            
            if 'amount' in positions and data.get('amount'):
                text = fix_persian_text(f"{data['amount']} تومان")
                draw.text(positions['amount'], text, font=font, fill=color)
            
            if 'source_owner' in positions and data.get('source_owner'):
                text = fix_persian_text(data['source_owner'])
                draw.text(positions['source_owner'], text, font=font, fill=color)
            
            if 'dest_owner' in positions and data.get('dest_owner'):
                text = fix_persian_text(data['dest_owner'])
                draw.text(positions['dest_owner'], text, font=font, fill=color)
            
            if 'date' in positions and data.get('date'):
                text = fix_persian_text(data['date'])
                draw.text(positions['date'], text, font=font, fill=color)
            
            if 'time' in positions and data.get('time'):
                text = fix_persian_text(data['time'])
                draw.text(positions['time'], text, font=font, fill=color)
            
            if 'tracking' in positions and data.get('tracking'):
                text = fix_persian_text(data['tracking'])
                draw.text(positions['tracking'], text, font=font, fill=color)
        
        # ذخیره در بافر
        output = io.BytesIO()
        img.save(output, format='JPEG', quality=95)
        output.seek(0)
        
        logger.info("✅ رسید با موفقیت ساخته شد")
        return output
        
    except Exception as e:
        logger.error(f"❌ خطا در ساخت رسید: {e}")
        import traceback
        logger.error(traceback.format_exc())
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
        await processing_msg.edit_text("""
❌ خطا در ساخت رسید

لطفاً مطمئن شوید:
1️⃣ تصاویر رسیدها در پوشه receipt_templates آپلود شده‌اند
2️⃣ نام فایل‌ها دقیقاً مانند این است:
   - receipt_up.jpg
   - receipt_hamrah_card.jpg
   - و غیره...
3️⃣ فرمت تصاویر JPG است

📋 برای کمک به ادمین پیام دهید: @{SUPPORT_ID}
""")
    
    await show_main_menu(update, context)
    
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """لغو عملیات"""
    await update.message.reply_text("❌ لغو شد")
    await show_main_menu(update, context)
    return ConversationHandler.END

def main():
    """تابع اصلی"""
    # چاپ اطلاعات برای Debug
    logger.info("="*50)
    logger.info("🚀 شروع ربات رسید ساز")
    logger.info("="*50)
    logger.info(f"📁 مسیر فعلی: {os.getcwd()}")
    logger.info(f"📁 مسیر مطلق تصاویر: {os.path.abspath(RECEIPTS_DIR)}")
    
    if os.path.exists(RECEIPTS_DIR):
        files = os.listdir(RECEIPTS_DIR)
        logger.info(f"✅ پوشه {RECEIPTS_DIR} وجود دارد")
        logger.info(f"📋 تعداد فایل‌ها: {len(files)}")
        if files:
            logger.info("📋 فایل‌های موجود:")
            for f in files:
                file_path = os.path.join(RECEIPTS_DIR, f)
                file_size = os.path.getsize(file_path)
                logger.info(f"   ✓ {f} ({file_size} bytes)")
        else:
            logger.warning("⚠️ پوشه خالی است! لطفاً تصاویر را آپلود کنید")
    else:
        logger.error(f"❌ پوشه {RECEIPTS_DIR} وجود ندارد!")
        logger.info("📁 ساخت پوشه...")
        os.makedirs(RECEIPTS_DIR)
        logger.info("✅ پوشه ساخته شد. لطفاً تصاویر را آپلود کنید")
    
    logger.info("="*50)
    
    # ساخت اپلیکیشن
    application = Application.builder().token(BOT_TOKEN).build()
    
    # هندلر مکالمه
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
    logger.info("🔗 برای تست به ربات خود پیام دهید: /start")
    logger.info("="*50)
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
