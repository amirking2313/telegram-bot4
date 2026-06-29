import random
import string
import logging
from cryptography.fernet import Fernet
import os

logger = logging.getLogger(__name__)

def generate_listing_code() -> str:
    """Generate unique listing code like #ACC1042"""
    try:
        random_num = random.randint(1000, 9999)
        return f"#ACC{random_num}"
    except Exception as e:
        logger.error(f"Error generating listing code: {e}")
        return "#ACC0000"

def get_cipher():
    """Get Fernet cipher for encryption"""
    try:
        key = os.getenv('ENCRYPTION_KEY')
        if not key:
            key = Fernet.generate_key()
            logger.warning("ENCRYPTION_KEY not set, generating new key")
        return Fernet(key if isinstance(key, bytes) else key.encode())
    except Exception as e:
        logger.error(f"Error getting cipher: {e}")
        return None

def encrypt_password(password: str) -> str:
    """Encrypt password"""
    try:
        cipher = get_cipher()
        if not cipher:
            return password
        encrypted = cipher.encrypt(password.encode())
        return encrypted.decode()
    except Exception as e:
        logger.error(f"Error encrypting password: {e}")
        return password

def decrypt_password(encrypted: str) -> str:
    """Decrypt password"""
    try:
        cipher = get_cipher()
        if not cipher:
            return encrypted
        decrypted = cipher.decrypt(encrypted.encode())
        return decrypted.decode()
    except Exception as e:
        logger.error(f"Error decrypting password: {e}")
        return encrypted

def format_listing_display(listing: dict) -> str:
    """Format listing for display"""
    try:
        return f"""
🎮 {listing.get('game', 'Unknown')}

📝 {listing.get('title', 'No title')}

📄 {listing.get('description', 'No description')}

💰 قیمت: {listing.get('price', '0')} تومان

👤 فروشنده: {listing.get('seller_name', 'Unknown')}

🔖 کد: {listing.get('code', 'N/A')}
        """
    except Exception as e:
        logger.error(f"Error formatting listing: {e}")
        return "خطا در نمایش لیست"

def is_channel_member(member_status: str) -> bool:
    """Check if user is channel member"""
    try:
        from telegram import ChatMember
        return member_status in [
            ChatMember.MEMBER,
            ChatMember.ADMINISTRATOR,
            ChatMember.CREATOR
        ]
    except Exception as e:
        logger.error(f"Error checking channel membership: {e}")
        return False
