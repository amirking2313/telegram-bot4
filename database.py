import sqlite3
import logging
from datetime import datetime
from contextlib import contextmanager
from cryptography.fernet import Fernet
import os

logger = logging.getLogger(__name__)

class Database:
    def __init__(self, db_path: str = 'bot_data.db'):
        self.db_path = db_path
        self.cipher = Fernet(os.getenv('ENCRYPTION_KEY', Fernet.generate_key()).decode() if isinstance(os.getenv('ENCRYPTION_KEY', Fernet.generate_key()), bytes) else os.getenv('ENCRYPTION_KEY', Fernet.generate_key()))
        self.init_db()
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            conn.close()
    
    def init_db(self):
        """Initialize database tables"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Users table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY,
                        user_id INTEGER UNIQUE NOT NULL,
                        first_name TEXT,
                        is_banned BOOLEAN DEFAULT 0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Listings table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS listings (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        game TEXT NOT NULL,
                        title TEXT NOT NULL,
                        description TEXT,
                        price TEXT,
                        email TEXT,
                        photo TEXT,
                        code TEXT UNIQUE NOT NULL,
                        status TEXT DEFAULT 'pending',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users(user_id)
                    )
                ''')
                
                # Purchases table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS purchases (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        listing_id INTEGER NOT NULL,
                        receipt_photo TEXT,
                        status TEXT DEFAULT 'pending',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users(user_id),
                        FOREIGN KEY (listing_id) REFERENCES listings(id)
                    )
                ''')
                
                logger.info("Database initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            raise
    
    def add_user(self, user_id: int, first_name: str) -> bool:
        """Add or update user"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR IGNORE INTO users (user_id, first_name)
                    VALUES (?, ?)
                ''', (user_id, first_name))
                return True
        except Exception as e:
            logger.error(f"Error adding user: {e}")
            return False
    
    def add_listing(self, user_id: int, game: str, title: str, description: str,
                   price: str, email: str, photo: str, code: str) -> int:
        """Add listing"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO listings (user_id, game, title, description, price, email, photo, code)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (user_id, game, title, description, price, email, photo, code))
                return cursor.lastrowid
        except Exception as e:
            logger.error(f"Error adding listing: {e}")
            return 0
    
    def get_listing_by_code(self, code: str) -> dict:
        """Get listing by code"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT l.*, u.first_name as seller_name
                    FROM listings l
                    JOIN users u ON l.user_id = u.user_id
                    WHERE l.code = ? AND l.status = 'approved'
                ''', (code,))
                row = cursor.fetchone()
                return dict(row) if row else None
        except Exception as e:
            logger.error(f"Error getting listing: {e}")
            return None
    
    def get_user_listings(self, user_id: int) -> list:
        """Get user's listings"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT * FROM listings WHERE user_id = ? ORDER BY created_at DESC
                ''', (user_id,))
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error getting user listings: {e}")
            return []
    
    def add_purchase(self, user_id: int, listing_id: int, receipt_photo: str) -> int:
        """Add purchase"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO purchases (user_id, listing_id, receipt_photo)
                    VALUES (?, ?, ?)
                ''', (user_id, listing_id, receipt_photo))
                return cursor.lastrowid
        except Exception as e:
            logger.error(f"Error adding purchase: {e}")
            return 0
    
    def get_pending_purchases(self) -> list:
        """Get pending purchases"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT p.*, l.title, u.first_name
                    FROM purchases p
                    JOIN listings l ON p.listing_id = l.id
                    JOIN users u ON p.user_id = u.user_id
                    WHERE p.status = 'pending'
                    ORDER BY p.created_at DESC
                ''')
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error getting pending purchases: {e}")
            return []
    
    def approve_listing(self, listing_id: int) -> bool:
        """Approve listing"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('UPDATE listings SET status = ? WHERE id = ?', ('approved', listing_id))
                return True
        except Exception as e:
            logger.error(f"Error approving listing: {e}")
            return False
    
    def reject_listing(self, listing_id: int) -> bool:
        """Reject listing"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('UPDATE listings SET status = ? WHERE id = ?', ('rejected', listing_id))
                return True
        except Exception as e:
            logger.error(f"Error rejecting listing: {e}")
            return False
    
    def ban_user(self, user_id: int) -> bool:
        """Ban user"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('UPDATE users SET is_banned = 1 WHERE user_id = ?', (user_id,))
                return True
        except Exception as e:
            logger.error(f"Error banning user: {e}")
            return False
    
    def unban_user(self, user_id: int) -> bool:
        """Unban user"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('UPDATE users SET is_banned = 0 WHERE user_id = ?', (user_id,))
                return True
        except Exception as e:
            logger.error(f"Error unbanning user: {e}")
            return False
    
    def is_user_banned(self, user_id: int) -> bool:
        """Check if user is banned"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT is_banned FROM users WHERE user_id = ?', (user_id,))
                row = cursor.fetchone()
                return row['is_banned'] if row else False
        except Exception as e:
            logger.error(f"Error checking ban status: {e}")
            return False
    
    def get_statistics(self) -> dict:
        """Get bot statistics"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('SELECT COUNT(*) as count FROM users')
                total_users = cursor.fetchone()['count']
                
                cursor.execute('SELECT COUNT(*) as count FROM listings WHERE status = "approved"')
                total_listings = cursor.fetchone()['count']
                
                cursor.execute('SELECT COUNT(*) as count FROM purchases WHERE status = "completed"')
                total_purchases = cursor.fetchone()['count']
                
                return {
                    'total_users': total_users,
                    'total_listings': total_listings,
                    'total_purchases': total_purchases,
                }
        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            return {}
