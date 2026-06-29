import os
import logging
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ChatMember
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    ConversationHandler, filters, ContextTypes, JobQueue
)
from telegram.error import TelegramError
from database import Database
from utils import (
    generate_listing_code, encrypt_password, decrypt_password,
    format_listing_display, is_channel_member
)

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Environment variables
BOT_TOKEN = os.getenv('BOT_TOKEN')
ADMIN_ID = int(os.getenv('ADMIN_ID', '0'))
CHANNEL_ID = int(os.getenv('CHANNEL_ID', '0'))
CARD_NUMBER = os.getenv('CARD_NUMBER', '')
CARD_OWNER = os.getenv('CARD_OWNER', '')

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN environment variable not set")

# Database
db = Database()

# Conversation states
(GAME_SELECT, TITLE, DESCRIPTION, PRICE, EMAIL, PHOTO,
 LISTING_CODE, PAYMENT_RECEIPT, ADMIN_MENU, ADMIN_ACTION) = range(10)

# Persian text
TEXTS = {
    'start': 'سلام! به بازار حساب‌های گیمی خوش آمدید.\n\nلطفا ابتدا در کانال ما عضو شوید.',
    'join_channel': 'عضویت در کانال',
    'already_member': 'شما قبلا عضو کانال هستید! 🎉',
    'not_member': 'لطفا ابتدا در کانال عضو شوید.',
    'main_menu': 'منوی اصلی:\n\nچه کاری می‌خواهید انجام دهید؟',
    'sell': '🛍️ فروش حساب',
    'buy': '🛒 خریداری حساب',
    'my_listings': '📋 لیست‌های من',
    'select_game': 'بازی را انتخاب کنید:',
    'clash_of_clans': '⚔️ Clash of Clans',
    'free_fire': '🔥 Free Fire',
    'pubg': '🎮 PUBG',
    'call_of_duty': '💣 Call of Duty',
    'enter_title': 'عنوان حساب را وارد کنید:',
    'enter_description': 'توضیحات حساب را وارد کنید:',
    'enter_price': 'قیمت را وارد کنید (تومان):',
    'enter_email': 'ایمیل خود را وارد کنید:',
    'send_photo': 'عکس حساب را ارسال کنید:',
    'listing_created': '✅ لیست شما با موفقیت ایجاد شد!\n\nکد لیست: {code}',
    'enter_listing_code': 'کد لیست را وارد کنید:',
    'listing_not_found': '❌ لیست پیدا نشد!',
    'listing_details': '{game}\n\n{title}\n\n{description}\n\nقیمت: {price} تومان\n\nفروشنده: {seller}',
    'payment_card': 'شماره کارت برای پرداخت:\n\n{card}\n\nنام مالک: {owner}',
    'send_receipt': 'رسید پرداخت را ارسال کنید:',
    'receipt_sent': '✅ رسید شما ارسال شد. منتظر تایید باشید.',
    'admin_panel': '👨‍💼 پنل مدیر',
    'view_listings': '📋 مشاهده لیست‌ها',
    'pending_payments': '💳 پرداخت‌های در انتظار',
    'manage_users': '👥 مدیریت کاربران',
    'broadcast': '📢 پخش پیام',
    'statistics': '📊 آمار',
    'approve': '✅ تایید',
    'reject': '❌ رد کردن',
    'ban': '🚫 مسدود کردن',
    'unban': '✅ رفع مسدودیت',
    'cancel': '❌ لغو',
    'error': '❌ خطایی رخ داد. لطفا دوباره تلاش کنید.',
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start command - check channel membership"""
    try:
        user = update.effective_user
        db.add_user(user.id, user.first_name or 'Unknown')
        
        # Check channel membership
        try:
            member = await context.bot.get_chat_member(CHANNEL_ID, user.id)
            if member.status in [ChatMember.MEMBER, ChatMember.ADMINISTRATOR, ChatMember.CREATOR]:
                await update.message.reply_text(
                    TEXTS['already_member'],
                    reply_markup=main_menu_keyboard()
                )
                return GAME_SELECT
        except TelegramError:
            pass
        
        # Not a member
        keyboard = [[InlineKeyboardButton(TEXTS['join_channel'], url=f"https://t.me/clashcoccity")]]
        await update.message.reply_text(
            TEXTS['start'],
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return ConversationHandler.END
    except Exception as e:
        logger.error(f"Error in start: {e}")
        await update.message.reply_text(TEXTS['error'])
        return ConversationHandler.END

def main_menu_keyboard():
    """Main menu keyboard"""
    keyboard = [
        [InlineKeyboardButton(TEXTS['sell'], callback_data='sell')],
        [InlineKeyboardButton(TEXTS['buy'], callback_data='buy')],
        [InlineKeyboardButton(TEXTS['my_listings'], callback_data='my_listings')],
    ]
    if ADMIN_ID > 0:
        keyboard.append([InlineKeyboardButton(TEXTS['admin_panel'], callback_data='admin')])
    return InlineKeyboardMarkup(keyboard)

async def main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show main menu"""
    try:
        query = update.callback_query
        await query.answer()
        await query.edit_message_text(
            text=TEXTS['main_menu'],
            reply_markup=main_menu_keyboard()
        )
        return GAME_SELECT
    except Exception as e:
        logger.error(f"Error in main_menu: {e}")
        return ConversationHandler.END

async def sell_game_select(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Select game for selling"""
    try:
        query = update.callback_query
        await query.answer()
        
        keyboard = [
            [InlineKeyboardButton(TEXTS['clash_of_clans'], callback_data='game_coc')],
            [InlineKeyboardButton(TEXTS['free_fire'], callback_data='game_ff')],
            [InlineKeyboardButton(TEXTS['pubg'], callback_data='game_pubg')],
            [InlineKeyboardButton(TEXTS['call_of_duty'], callback_data='game_cod')],
            [InlineKeyboardButton(TEXTS['cancel'], callback_data='cancel')],
        ]
        
        await query.edit_message_text(
            text=TEXTS['select_game'],
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return TITLE
    except Exception as e:
        logger.error(f"Error in sell_game_select: {e}")
        return ConversationHandler.END

async def game_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Game selected, ask for title"""
    try:
        query = update.callback_query
        await query.answer()
        
        game_map = {
            'game_coc': 'Clash of Clans',
            'game_ff': 'Free Fire',
            'game_pubg': 'PUBG',
            'game_cod': 'Call of Duty',
        }
        
        context.user_data['game'] = game_map.get(query.data, 'Unknown')
        
        await query.edit_message_text(text=TEXTS['enter_title'])
        return DESCRIPTION
    except Exception as e:
        logger.error(f"Error in game_selected: {e}")
        return ConversationHandler.END

async def title_received(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Title received, ask for description"""
    try:
        context.user_data['title'] = update.message.text
        await update.message.reply_text(TEXTS['enter_description'])
        return PRICE
    except Exception as e:
        logger.error(f"Error in title_received: {e}")
        await update.message.reply_text(TEXTS['error'])
        return ConversationHandler.END

async def description_received(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Description received, ask for price"""
    try:
        context.user_data['description'] = update.message.text
        await update.message.reply_text(TEXTS['enter_price'])
        return EMAIL
    except Exception as e:
        logger.error(f"Error in description_received: {e}")
        await update.message.reply_text(TEXTS['error'])
        return ConversationHandler.END

async def price_received(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Price received, ask for email"""
    try:
        context.user_data['price'] = update.message.text
        await update.message.reply_text(TEXTS['enter_email'])
        return PHOTO
    except Exception as e:
        logger.error(f"Error in price_received: {e}")
        await update.message.reply_text(TEXTS['error'])
        return ConversationHandler.END

async def email_received(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Email received, ask for photo"""
    try:
        context.user_data['email'] = update.message.text
        await update.message.reply_text(TEXTS['send_photo'])
        return PHOTO
    except Exception as e:
        logger.error(f"Error in email_received: {e}")
        await update.message.reply_text(TEXTS['error'])
        return ConversationHandler.END

async def photo_received(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Photo received, create listing"""
    try:
        if not update.message.photo:
            await update.message.reply_text(TEXTS['send_photo'])
            return PHOTO
        
        photo_id = update.message.photo[-1].file_id
        context.user_data['photo'] = photo_id
        
        # Create listing
        listing_code = generate_listing_code()
        listing_id = db.add_listing(
            user_id=update.effective_user.id,
            game=context.user_data['game'],
            title=context.user_data['title'],
            description=context.user_data['description'],
            price=context.user_data['price'],
            email=context.user_data['email'],
            photo=photo_id,
            code=listing_code
        )
        
        # Post to channel
        try:
            await context.bot.send_photo(
                chat_id=CHANNEL_ID,
                photo=photo_id,
                caption=f"🎮 {context.user_data['game']}\n\n{context.user_data['title']}\n\n{context.user_data['description']}\n\nقیمت: {context.user_data['price']} تومان\n\nکد: {listing_code}"
            )
        except TelegramError as e:
            logger.error(f"Error posting to channel: {e}")
        
        await update.message.reply_text(
            TEXTS['listing_created'].format(code=listing_code),
            reply_markup=main_menu_keyboard()
        )
        
        context.user_data.clear()
        return GAME_SELECT
    except Exception as e:
        logger.error(f"Error in photo_received: {e}")
        await update.message.reply_text(TEXTS['error'])
        return ConversationHandler.END

async def buy_listing_code(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Ask for listing code"""
    try:
        query = update.callback_query
        await query.answer()
        await query.edit_message_text(text=TEXTS['enter_listing_code'])
        return LISTING_CODE
    except Exception as e:
        logger.error(f"Error in buy_listing_code: {e}")
        return ConversationHandler.END

async def listing_code_received(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Listing code received, show details"""
    try:
        code = update.message.text.strip().upper()
        listing = db.get_listing_by_code(code)
        
        if not listing:
            await update.message.reply_text(TEXTS['listing_not_found'])
            return LISTING_CODE
        
        context.user_data['listing_id'] = listing['id']
        context.user_data['seller_id'] = listing['user_id']
        
        details = TEXTS['listing_details'].format(
            game=listing['game'],
            title=listing['title'],
            description=listing['description'],
            price=listing['price'],
            seller=listing['seller_name']
        )
        
        keyboard = [
            [InlineKeyboardButton('💳 پرداخت', callback_data='proceed_payment')],
            [InlineKeyboardButton(TEXTS['cancel'], callback_data='cancel')],
        ]
        
        await update.message.reply_text(
            details,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return PAYMENT_RECEIPT
    except Exception as e:
        logger.error(f"Error in listing_code_received: {e}")
        await update.message.reply_text(TEXTS['error'])
        return ConversationHandler.END

async def show_payment_card(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show payment card"""
    try:
        query = update.callback_query
        await query.answer()
        
        keyboard = [[InlineKeyboardButton('✅ پرداخت کردم', callback_data='payment_done')]]
        
        await query.edit_message_text(
            text=TEXTS['payment_card'].format(card=CARD_NUMBER, owner=CARD_OWNER),
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return PAYMENT_RECEIPT
    except Exception as e:
        logger.error(f"Error in show_payment_card: {e}")
        return ConversationHandler.END

async def payment_receipt_received(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Payment receipt received"""
    try:
        query = update.callback_query
        await query.answer()
        
        if not update.message.photo:
            await update.message.reply_text(TEXTS['send_receipt'])
            return PAYMENT_RECEIPT
        
        receipt_photo = update.message.photo[-1].file_id
        
        # Create purchase record
        db.add_purchase(
            user_id=update.effective_user.id,
            listing_id=context.user_data['listing_id'],
            receipt_photo=receipt_photo
        )
        
        # Forward to admin
        try:
            await context.bot.send_photo(
                chat_id=ADMIN_ID,
                photo=receipt_photo,
                caption=f"📸 رسید پرداخت جدید\n\nکاربر: {update.effective_user.first_name}\nلیست: {context.user_data['listing_id']}"
            )
        except TelegramError as e:
            logger.error(f"Error forwarding to admin: {e}")
        
        await update.message.reply_text(
            TEXTS['receipt_sent'],
            reply_markup=main_menu_keyboard()
        )
        
        context.user_data.clear()
        return GAME_SELECT
    except Exception as e:
        logger.error(f"Error in payment_receipt_received: {e}")
        await update.message.reply_text(TEXTS['error'])
        return ConversationHandler.END

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Admin panel"""
    try:
        if update.effective_user.id != ADMIN_ID:
            await update.callback_query.answer('❌ دسترسی رد شد')
            return ConversationHandler.END
        
        query = update.callback_query
        await query.answer()
        
        keyboard = [
            [InlineKeyboardButton(TEXTS['view_listings'], callback_data='admin_listings')],
            [InlineKeyboardButton(TEXTS['pending_payments'], callback_data='admin_payments')],
            [InlineKeyboardButton(TEXTS['manage_users'], callback_data='admin_users')],
            [InlineKeyboardButton(TEXTS['broadcast'], callback_data='admin_broadcast')],
            [InlineKeyboardButton(TEXTS['statistics'], callback_data='admin_stats')],
        ]
        
        await query.edit_message_text(
            text=TEXTS['admin_panel'],
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return ADMIN_ACTION
    except Exception as e:
        logger.error(f"Error in admin_panel: {e}")
        return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel operation"""
    try:
        query = update.callback_query
        await query.answer()
        context.user_data.clear()
        await query.edit_message_text(
            text=TEXTS['main_menu'],
            reply_markup=main_menu_keyboard()
        )
        return GAME_SELECT
    except Exception as e:
        logger.error(f"Error in cancel: {e}")
        return ConversationHandler.END

async def conversation_timeout(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle conversation timeout"""
    try:
        user_id = context.job.user_id
        logger.info(f"Conversation timeout for user {user_id}")
    except Exception as e:
        logger.error(f"Error in conversation_timeout: {e}")

def main():
    """Start the bot"""
    try:
        app = Application.builder().token(BOT_TOKEN).build()
        
        # Conversation handler
        conv_handler = ConversationHandler(
            entry_points=[CommandHandler('start', start)],
            states={
                GAME_SELECT: [
                    CallbackQueryHandler(sell_game_select, pattern='^sell$'),
                    CallbackQueryHandler(buy_listing_code, pattern='^buy$'),
                    CallbackQueryHandler(admin_panel, pattern='^admin$'),
                    CallbackQueryHandler(main_menu, pattern='^main_menu$'),
                ],
                TITLE: [
                    CallbackQueryHandler(game_selected, pattern='^game_'),
                    MessageHandler(filters.TEXT & ~filters.COMMAND, title_received),
                ],
                DESCRIPTION: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, description_received),
                ],
                PRICE: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, price_received),
                ],
                EMAIL: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, email_received),
                ],
                PHOTO: [
                    MessageHandler(filters.PHOTO, photo_received),
                ],
                LISTING_CODE: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, listing_code_received),
                ],
                PAYMENT_RECEIPT: [
                    CallbackQueryHandler(show_payment_card, pattern='^proceed_payment$'),
                    CallbackQueryHandler(payment_receipt_received, pattern='^payment_done$'),
                    MessageHandler(filters.PHOTO, payment_receipt_received),
                ],
                ADMIN_ACTION: [
                    CallbackQueryHandler(admin_panel, pattern='^admin$'),
                ],
            },
            fallbacks=[
                CallbackQueryHandler(cancel, pattern='^cancel$'),
                CommandHandler('start', start),
            ],
            conversation_timeout=3600,
            per_message=False,
        )
        
        app.add_handler(conv_handler)
        
        logger.info("Bot started successfully")
        app.run_polling(allowed_updates=Update.ALL_TYPES)
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        raise

if __name__ == '__main__':
    main()
