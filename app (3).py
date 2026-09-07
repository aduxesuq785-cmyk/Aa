#!/usr/bin/env python3
"""
SOHAG BD SHOP - Complete Digital Marketplace
Single-file Flask Application with SQLite Database
Premium Dark Cyber Theme with Glassmorphism UI
"""

import os
import sys
import json
import hashlib
import secrets
import sqlite3
import datetime
import functools
import re
import uuid
import base64
from decimal import Decimal, ROUND_HALF_UP
from flask import (
    Flask, render_template_string, request, redirect, url_for,
    session, flash, jsonify, g, abort, make_response, get_flashed_messages
)
from werkzeug.security import generate_password_hash, check_password_hash

# ============================================================
# APPLICATION CONFIGURATION
# ============================================================

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)
app.config['DATABASE'] = 'sohag_bd_shop.db'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)


# ============================================================
# CUSTOM TEMPLATE RENDERING (DictLoader with full inheritance)
# ============================================================

import jinja2


def render_page(child_source, base_source, **kwargs):
    """Render a child template that extends a base, using Jinja2 DictLoader."""
    import re as _re

    # If the child does NOT use extends at all, render it standalone
    if '{% extends' not in child_source:
        return render_template_string(child_source, **kwargs)

    templates = {'_base.html': base_source}
    # Normalize extends tag to point to our registered base name
    normalized = _re.sub(
        r'\{%\s*extends\s+\w+\s*%\}',
        '{% extends "_base.html" %}',
        child_source
    )
    templates['_child.html'] = normalized

    loader = jinja2.DictLoader(templates)
    env = jinja2.Environment(loader=loader, autoescape=False)
    # Copy all Flask custom filters and globals
    env.filters.update(app.jinja_env.filters)
    env.globals.update(app.jinja_env.globals)

    # Build context with Flask globals + our context processor
    ctx = dict(
        url_for=url_for, request=request, session=session,
        get_flashed_messages=get_flashed_messages,
    )
    ctx.update(inject_globals())
    ctx.update(kwargs)

    template = env.get_template('_child.html')
    return template.render(**ctx)

# ============================================================
# DATABASE CONNECTION HELPERS
# ============================================================

def get_db():
    """Get database connection for current request."""
    if 'db' not in g:
        g.db = sqlite3.connect(app.config['DATABASE'])
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA journal_mode=WAL")
        g.db.execute("PRAGMA foreign_keys=ON")
    return g.db


@app.teardown_appcontext
def close_db(exception):
    """Close database connection when app context ends."""
    db = g.pop('db', None)
    if db is not None:
        db.close()


def init_db():
    """Initialize database tables and default data."""
    db = sqlite3.connect(app.config['DATABASE'])
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA journal_mode=WAL")
    db.execute("PRAGMA foreign_keys=ON")
    # Lightweight migrations for existing installations
    try:
        db.execute("ALTER TABLE users ADD COLUMN telegram_username TEXT DEFAULT ''")
    except sqlite3.OperationalError:
        pass

    # Create tables
    db.executescript('''
        -- Users table
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            full_name TEXT DEFAULT '',
            phone TEXT DEFAULT '',
            address TEXT DEFAULT '',
            city TEXT DEFAULT '',
            country TEXT DEFAULT 'Bangladesh',
            avatar TEXT DEFAULT '',
            bio TEXT DEFAULT '',
            wallet_balance REAL DEFAULT 0.00,
            referral_code TEXT UNIQUE,
            referred_by INTEGER,
            is_active INTEGER DEFAULT 1,
            is_verified INTEGER DEFAULT 0,
            last_login TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (referred_by) REFERENCES users(id)
        );

        -- Admins table
        CREATE TABLE IF NOT EXISTS admins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            full_name TEXT DEFAULT '',
            role TEXT DEFAULT 'admin',
            permissions TEXT DEFAULT '{}',
            is_active INTEGER DEFAULT 1,
            last_login TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        -- Categories table
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            slug TEXT UNIQUE NOT NULL,
            description TEXT DEFAULT '',
            icon TEXT DEFAULT '',
            color TEXT DEFAULT '#00f2fe',
            parent_id INTEGER,
            sort_order INTEGER DEFAULT 0,
            is_active INTEGER DEFAULT 1,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (parent_id) REFERENCES categories(id)
        );

        -- Products table
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            slug TEXT UNIQUE NOT NULL,
            description TEXT DEFAULT '',
            short_description TEXT DEFAULT '',
            category_id INTEGER,
            price REAL NOT NULL,
            original_price REAL DEFAULT 0,
            discount_percent REAL DEFAULT 0,
            currency TEXT DEFAULT 'BDT',
            product_type TEXT DEFAULT 'digital',
            image_url TEXT DEFAULT '',
            gallery_images TEXT DEFAULT '[]',
            delivery_type TEXT DEFAULT 'auto',
            delivery_content TEXT DEFAULT '',
            stock_quantity INTEGER DEFAULT -1,
            sold_count INTEGER DEFAULT 0,
            view_count INTEGER DEFAULT 0,
            rating REAL DEFAULT 0,
            review_count INTEGER DEFAULT 0,
            tags TEXT DEFAULT '',
            meta_title TEXT DEFAULT '',
            meta_description TEXT DEFAULT '',
            is_featured INTEGER DEFAULT 0,
            is_active INTEGER DEFAULT 1,
            created_by INTEGER,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (category_id) REFERENCES categories(id),
            FOREIGN KEY (created_by) REFERENCES admins(id)
        );

        -- Orders table
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id TEXT UNIQUE NOT NULL,
            user_id INTEGER NOT NULL,
            subtotal REAL NOT NULL,
            discount_amount REAL DEFAULT 0,
            coupon_code TEXT DEFAULT '',
            total_amount REAL NOT NULL,
            payment_method TEXT DEFAULT 'wallet',
            payment_status TEXT DEFAULT 'pending',
            order_status TEXT DEFAULT 'pending',
            delivery_status TEXT DEFAULT 'pending',
            notes TEXT DEFAULT '',
            ip_address TEXT DEFAULT '',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );

        -- Order Items table
        CREATE TABLE IF NOT EXISTS order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            product_id INTEGER,
            product_name TEXT NOT NULL,
            quantity INTEGER DEFAULT 1,
            unit_price REAL NOT NULL,
            total_price REAL NOT NULL,
            delivery_data TEXT DEFAULT '',
            is_delivered INTEGER DEFAULT 0,
            delivered_at TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (order_id) REFERENCES orders(id),
            FOREIGN KEY (product_id) REFERENCES products(id)
        );

        -- Deposits table
        CREATE TABLE IF NOT EXISTS deposits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            method TEXT NOT NULL,
            transaction_id TEXT DEFAULT '',
            sender_number TEXT DEFAULT '',
            receiver_number TEXT DEFAULT '',
            screenshot TEXT DEFAULT '',
            status TEXT DEFAULT 'pending',
            admin_note TEXT DEFAULT '',
            processed_by INTEGER,
            processed_at TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (processed_by) REFERENCES admins(id)
        );

        -- Wallet Transactions table
        CREATE TABLE IF NOT EXISTS wallet_transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            type TEXT NOT NULL,
            amount REAL NOT NULL,
            balance_before REAL NOT NULL,
            balance_after REAL NOT NULL,
            description TEXT DEFAULT '',
            reference_id TEXT DEFAULT '',
            reference_type TEXT DEFAULT '',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );

        -- Notifications table
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            title TEXT NOT NULL,
            message TEXT NOT NULL,
            type TEXT DEFAULT 'info',
            is_read INTEGER DEFAULT 0,
            link TEXT DEFAULT '',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );

        -- Support Messages table
        CREATE TABLE IF NOT EXISTS support_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticket_id TEXT UNIQUE NOT NULL,
            user_id INTEGER NOT NULL,
            subject TEXT NOT NULL,
            message TEXT NOT NULL,
            status TEXT DEFAULT 'open',
            priority TEXT DEFAULT 'normal',
            admin_reply TEXT DEFAULT '',
            replied_by INTEGER,
            replied_at TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (replied_by) REFERENCES admins(id)
        );

        -- Reviews table
        CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            product_id INTEGER,
            order_id INTEGER,
            rating INTEGER NOT NULL,
            comment TEXT DEFAULT '',
            is_approved INTEGER DEFAULT 1,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (product_id) REFERENCES products(id),
            FOREIGN KEY (order_id) REFERENCES orders(id)
        );

        -- Coupons table
        CREATE TABLE IF NOT EXISTS coupons (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE NOT NULL,
            discount_type TEXT DEFAULT 'percentage',
            discount_value REAL NOT NULL,
            min_order_amount REAL DEFAULT 0,
            max_discount REAL DEFAULT 0,
            usage_limit INTEGER DEFAULT -1,
            used_count INTEGER DEFAULT 0,
            valid_from TEXT,
            valid_until TEXT,
            is_active INTEGER DEFAULT 1,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        -- Settings table
        CREATE TABLE IF NOT EXISTS settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            setting_key TEXT UNIQUE NOT NULL,
            setting_value TEXT DEFAULT '',
            setting_type TEXT DEFAULT 'text',
            description TEXT DEFAULT ''
        );

        -- Activity Logs table
        CREATE TABLE IF NOT EXISTS activity_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            admin_id INTEGER,
            action TEXT NOT NULL,
            details TEXT DEFAULT '',
            ip_address TEXT DEFAULT '',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        -- Announcements table
        CREATE TABLE IF NOT EXISTS announcements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            type TEXT DEFAULT 'info',
            is_active INTEGER DEFAULT 1,
            show_on_homepage INTEGER DEFAULT 1,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        -- Wishlist table
        CREATE TABLE IF NOT EXISTS wishlist (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (product_id) REFERENCES products(id),
            UNIQUE(user_id, product_id)
        );

        -- Cart table
        CREATE TABLE IF NOT EXISTS cart (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity INTEGER DEFAULT 1,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (product_id) REFERENCES products(id),
            UNIQUE(user_id, product_id)
        );
    ''')

    # Insert default settings
    default_settings = [
        ('site_name', 'ARIYAN CODE BAZAR', 'text', 'Website Name'),
        ('site_tagline', 'Premium Digital Marketplace', 'text', 'Site Tagline'),
        ('site_description', 'Your one-stop digital marketplace for premium digital products', 'textarea', 'Site Description'),
        ('site_email', 'support@sohagbdshop.com', 'text', 'Support Email'),
        ('site_phone', '+880 1XXXXXXXXX', 'text', 'Support Phone'),
        ('currency', 'BDT', 'text', 'Default Currency'),
        ('currency_symbol', '৳', 'text', 'Currency Symbol'),
        ('bkash_number', '01XXXXXXXXX', 'text', 'bKash Number'),
        ('nagad_number', '01XXXXXXXXX', 'text', 'Nagad Number'),
        ('crypto_address', '0x...', 'text', 'Crypto/BEP20 Address'),
        ('min_deposit', '50', 'number', 'Minimum Deposit Amount'),
        ('max_deposit', '100000', 'number', 'Maximum Deposit Amount'),
        ('maintenance_mode', '0', 'toggle', 'Maintenance Mode'),
        ('registration_enabled', '1', 'toggle', 'Registration Enabled'),
        ('referral_bonus', '10', 'number', 'Referral Bonus Amount'),
        ('referral_minimum_purchase', '100', 'number', 'Minimum Purchase for Referral Bonus'),
        ('auto_approve_deposits', '0', 'toggle', 'Auto Approve Deposits'),
        ('featured_products_count', '8', 'number', 'Featured Products on Homepage'),
        ('items_per_page', '12', 'number', 'Items Per Page'),
        ('guest_checkout', '0', 'toggle', 'Allow Guest Checkout'),
    ]

    for key, value, stype, desc in default_settings:
        try:
            db.execute(
                'INSERT INTO settings (setting_key, setting_value, setting_type, description) VALUES (?, ?, ?, ?)',
                (key, value, stype, desc)
            )
        except sqlite3.IntegrityError:
            pass

    db.execute("UPDATE settings SET setting_value = 'ARIYAN CODE BAZAR' WHERE setting_key = 'site_name'")

    # Insert default admin
    try:
        db.execute(
            'INSERT INTO admins (username, email, password_hash, full_name, role) VALUES (?, ?, ?, ?, ?)',
            ('admin', 'admin@sohagbdshop.com', generate_password_hash('admin123'), 'Super Admin', 'superadmin')
        )
    except sqlite3.IntegrityError:
        pass

    # Insert default categories
    default_categories = [
        ('Software', 'software', 'Premium software licenses and tools', 'bx-code-alt', '#00f2fe'),
        ('Games', 'games', 'Game keys and digital gaming content', 'bx-game', '#a855f7'),
        ('Gift Cards', 'gift-cards', 'Digital gift cards for various platforms', 'bx-gift', '#ff0844'),
        ('Subscriptions', 'subscriptions', 'Premium subscription services', 'bx-crown', '#4facfe'),
        ('E-Books', 'e-books', 'Digital books and educational content', 'bx-book', '#2ecc71'),
        ('Templates', 'templates', 'Website and app templates', 'bx-layout', '#f59e0b'),
        ('Graphics', 'graphics', 'Design assets and graphic resources', 'bx-palette', '#ec4899'),
        ('Music', 'music', 'Audio files and music content', 'bx-music', '#8b5cf6'),
    ]

    for name, slug, desc, icon, color in default_categories:
        try:
            db.execute(
                'INSERT INTO categories (name, slug, description, icon, color) VALUES (?, ?, ?, ?, ?)',
                (name, slug, desc, icon, color)
            )
        except sqlite3.IntegrityError:
            pass

    # Insert sample products
    sample_products = [
        ('Windows 11 Pro License Key', 'windows-11-pro', 'Genuine Windows 11 Professional license key. Lifetime activation, instant delivery. Works worldwide. Includes all Pro features: BitLocker, Remote Desktop, Group Policy, Hyper-V, and more. One-time purchase, no subscription needed.', 'Get genuine Windows 11 Pro license with instant delivery and lifetime activation.', 1, 1499.00, 2499.00, 40, 'auto', '🔑', 100),
        ('Microsoft Office 2024 Pro Plus', 'office-2024-pro', 'Complete Microsoft Office suite including Word, Excel, PowerPoint, Outlook, Access, Publisher. Lifetime license with instant email delivery. Works on one PC. All languages supported.', 'Lifetime Microsoft Office 2024 Professional Plus license with instant delivery.', 1, 1999.00, 3499.00, 43, 'auto', '💼', 100),
        ('Netflix Premium 1 Month', 'netflix-premium-1m', 'Netflix Premium subscription for 1 month. 4K Ultra HD streaming on 4 screens simultaneously. Access to entire Netflix library including 4K content. Instant delivery via email.', 'Netflix Premium 1 Month subscription with 4K streaming on 4 screens.', 4, 299.00, 499.00, 40, 'auto', '🎬', 500),
        ('Spotify Premium 3 Months', 'spotify-premium-3m', 'Spotify Premium subscription for 3 months. Ad-free music streaming, offline downloads, high-quality audio. Instant delivery. Works worldwide.', 'Spotify Premium 3 months with ad-free music and offline downloads.', 4, 349.00, 599.00, 42, 'auto', '🎵', 300),
        ('Steam Wallet $50 Gift Card', 'steam-wallet-50', 'Steam Wallet $50 USD gift card code. Instant delivery. Redeemable on any Steam account. Use for games, DLC, in-game items, and more on the Steam platform.', 'Steam Wallet $50 gift card for games and digital content.', 3, 5499.00, 6000.00, 8, 'auto', '🎮', 200),
        ('Adobe Creative Cloud 1 Year', 'adobe-cc-1year', 'Adobe Creative Cloud full suite access for 1 year. Includes Photoshop, Illustrator, Premiere Pro, After Effects, and 20+ apps. 100GB cloud storage. All features unlocked.', 'Adobe Creative Cloud full suite 1-year subscription.', 4, 8999.00, 15999.00, 44, 'auto', '🎨', 50),
        ('Canva Pro 1 Year', 'canva-pro-1year', 'Canva Pro subscription for 1 year. Access to premium templates, stock photos, videos, graphics. Brand kit, background remover, magic resize. Team collaboration features.', 'Canva Pro 1 year with premium templates and design tools.', 4, 999.00, 2500.00, 60, 'auto', '🖌️', 150),
        ('ChatGPT Plus 1 Month', 'chatgpt-plus-1m', 'ChatGPT Plus subscription for 1 month. Access to GPT-4, faster response times, priority access during peak hours. Explore advanced AI capabilities.', 'ChatGPT Plus 1 month with GPT-4 access and priority.', 4, 1799.00, 2200.00, 18, 'auto', '🤖', 100),
        ('YouTube Premium 6 Months', 'youtube-premium-6m', 'YouTube Premium subscription for 6 months. Ad-free videos, background play, YouTube Music Premium, offline downloads. Family sharing available.', 'YouTube Premium 6 months with ad-free viewing and YouTube Music.', 4, 599.00, 999.00, 40, 'auto', '📺', 200),
        ('Discord Nitro 3 Months', 'discord-nitro-3m', 'Discord Nitro subscription for 3 months. Custom emoji anywhere, bigger file uploads (500MB), HD video, server boosts, animated avatars, and more perks.', 'Discord Nitro 3 months with premium features and server boost.', 4, 449.00, 799.00, 44, 'auto', '💬', 150),
        ('Minecraft Java Edition', 'minecraft-java', 'Minecraft Java Edition full game. Lifetime access. Play multiplayer, install mods, create servers. Works on Windows, Mac, and Linux. Instant delivery.', 'Minecraft Java Edition lifetime access with multiplayer and mods.', 2, 1499.00, 2499.00, 40, 'auto', '⛏️', 100),
        ('Visual Studio Code Pro Extensions Pack', 'vscode-pro-pack', 'Premium VS Code extensions pack. Includes advanced themes, productivity tools, code snippets, AI assistants, and debugging tools. Lifetime access to all included extensions.', 'Premium VS Code extensions lifetime access pack.', 1, 499.00, 1200.00, 58, 'auto', '💻', 80),
        ('Figma Professional Templates Bundle', 'figma-templates-bundle', '500+ professional Figma templates for UI/UX design. Includes mobile apps, web dashboards, landing pages, e-commerce templates. Regular updates included.', '500+ professional Figma design templates bundle.', 6, 1299.00, 3000.00, 57, 'auto', '📐', 60),
        ('Cybersecurity Course Bundle', 'cybersecurity-course', 'Complete cybersecurity course bundle. Ethical hacking, penetration testing, network security, malware analysis. 200+ hours of video content. Certificate included.', 'Complete cybersecurity training with 200+ hours of content.', 5, 1999.00, 5000.00, 60, 'auto', '🔐', 100),
        ('Cloud Storage 2TB 1 Year', 'cloud-storage-2tb', '2TB cloud storage for 1 year. Secure file storage and sharing. End-to-end encryption. Access from any device. Automatic backup. File versioning included.', '2TB secure cloud storage for 1 year with encryption.', 4, 1499.00, 3000.00, 50, 'auto', '☁️', 200),
        ('Premium Icon Pack - 10000+ Icons', 'premium-icon-pack', 'Over 10,000 premium icons in SVG, PNG, and ICO formats. Multiple styles: filled, outlined, rounded. Includes business, tech, social media, and more categories.', '10,000+ premium icons in multiple formats and styles.', 7, 399.00, 999.00, 60, 'auto', '🎯', 150),
        ('Stock Music Bundle - 500 Tracks', 'stock-music-bundle', '500 royalty-free music tracks. Various genres: corporate, cinematic, electronic, acoustic. High-quality WAV and MP3 formats. Commercial license included.', '500 royalty-free music tracks with commercial license.', 8, 2499.00, 5000.00, 50, 'auto', '🎸', 75),
        ('Flutter App Templates Pack', 'flutter-templates', '50+ Flutter app templates. Complete source code with Firebase integration. E-commerce, social media, fitness, education app templates. Regular updates.', '50+ Flutter app templates with complete source code.', 6, 3999.00, 8000.00, 50, 'auto', '📱', 40),
        ('NordVPN 2 Year Plan', 'nordvpn-2year', 'NordVPN 2-year subscription. 5500+ servers in 59 countries. No-logs policy. Kill switch. Split tunneling. Connect up to 6 devices simultaneously.', 'NordVPN 2-year plan with 5500+ servers worldwide.', 4, 3999.00, 7000.00, 43, 'auto', '🛡️', 100),
        ('Python Programming Masterclass', 'python-masterclass', 'Complete Python programming course from beginner to advanced. 150+ hours of content. Machine learning, web development, automation. Certificate included.', 'Complete Python programming masterclass with certificate.', 5, 1499.00, 4000.00, 63, 'auto', '🐍', 200),
    ]

    for name, slug, desc, short_desc, cat_id, price, orig_price, discount, del_type, img, stock in sample_products:
        try:
            db.execute(
                '''INSERT INTO products (name, slug, description, short_description, category_id, price, original_price,
                   discount_percent, product_type, image_url, delivery_type, stock_quantity, is_featured, created_by)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'digital', ?, ?, ?, 1, 1)''',
                (name, slug, desc, short_desc, cat_id, price, orig_price, discount, img, del_type, stock)
            )
        except sqlite3.IntegrityError:
            pass

    # Insert sample coupons
    try:
        db.execute(
            "INSERT INTO coupons (code, discount_type, discount_value, min_order_amount, max_discount, usage_limit) VALUES ('WELCOME10', 'percentage', 10, 100, 500, 1000)"
        )
        db.execute(
            "INSERT INTO coupons (code, discount_type, discount_value, min_order_amount, max_discount, usage_limit) VALUES ('FLAT50', 'fixed', 50, 200, 50, 500)"
        )
        db.execute(
            "INSERT INTO coupons (code, discount_type, discount_value, min_order_amount, max_discount, usage_limit) VALUES ('SAVE20', 'percentage', 20, 500, 2000, 200)"
        )
    except sqlite3.IntegrityError:
        pass

    # Insert default announcements
    try:
        db.execute(
            "INSERT INTO announcements (title, content, type) VALUES ('Welcome to SOHAG BD SHOP!', 'Your one-stop digital marketplace. Get genuine digital products at best prices with instant delivery.', 'info')"
        )
        db.execute(
            "INSERT INTO announcements (title, content, type) VALUES ('Special Offer!', 'Use code WELCOME10 to get 10% off your first order. Limited time offer!', 'success')"
        )
    except sqlite3.IntegrityError:
        pass

    db.commit()
    db.close()


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def get_setting(key, default=''):
    """Get a setting value from database."""
    db = get_db()
    row = db.execute('SELECT setting_value FROM settings WHERE setting_key = ?', (key,)).fetchone()
    return row['setting_value'] if row else default


def log_activity(user_id=None, admin_id=None, action='', details='', ip_address=''):
    """Log user/admin activity."""
    db = get_db()
    db.execute(
        'INSERT INTO activity_logs (user_id, admin_id, action, details, ip_address) VALUES (?, ?, ?, ?, ?)',
        (user_id, admin_id, action, details, ip_address or request.remote_addr or '')
    )
    db.commit()


def create_notification(user_id, title, message, ntype='info', link=''):
    """Create a notification for a user."""
    db = get_db()
    db.execute(
        'INSERT INTO notifications (user_id, title, message, type, link) VALUES (?, ?, ?, ?, ?)',
        (user_id, title, message, ntype, link)
    )
    db.commit()


def get_cart_count(user_id):
    """Get total items in user's cart."""
    db = get_db()
    result = db.execute('SELECT COALESCE(SUM(quantity), 0) as count FROM cart WHERE user_id = ?', (user_id,)).fetchone()
    return result['count'] if result else 0


def get_notification_count(user_id):
    """Get unread notification count for user."""
    db = get_db()
    result = db.execute('SELECT COUNT(*) as count FROM notifications WHERE user_id = ? AND is_read = 0', (user_id,)).fetchone()
    return result['count'] if result else 0


def format_currency(amount):
    """Format amount with currency symbol."""
    symbol = get_setting('currency_symbol', '৳')
    return f"{symbol}{amount:,.2f}"


def generate_order_id():
    """Generate unique order ID."""
    return f"ORD-{uuid.uuid4().hex[:8].upper()}"


def generate_ticket_id():
    """Generate unique support ticket ID."""
    return f"TKT-{uuid.uuid4().hex[:8].upper()}"


def update_product_rating(product_id):
    """Update product average rating."""
    db = get_db()
    result = db.execute(
        'SELECT AVG(rating) as avg_rating, COUNT(*) as count FROM reviews WHERE product_id = ? AND is_approved = 1',
        (product_id,)
    ).fetchone()
    avg_rating = result['avg_rating'] or 0
    review_count = result['count'] or 0
    db.execute(
        'UPDATE products SET rating = ?, review_count = ? WHERE id = ?',
        (round(avg_rating, 1), review_count, product_id)
    )
    db.commit()


# ============================================================
# TEMPLATE FILTERS
# ============================================================

@app.template_filter('currency')
def currency_filter(amount):
    return format_currency(amount)


@app.template_filter('timeago')
def timeago_filter(dt_str):
    if not dt_str:
        return ''
    try:
        dt = datetime.datetime.strptime(dt_str, '%Y-%m-%d %H:%M:%S')
    except:
        try:
            dt = datetime.datetime.strptime(dt_str, '%Y-%m-%d %H:%M:%S.%f')
        except:
            return dt_str
    now = datetime.datetime.utcnow()
    diff = now - dt
    seconds = diff.total_seconds()
    if seconds < 60:
        return 'just now'
    elif seconds < 3600:
        mins = int(seconds / 60)
        return f'{mins}m ago'
    elif seconds < 86400:
        hours = int(seconds / 3600)
        return f'{hours}h ago'
    elif seconds < 604800:
        days = int(seconds / 86400)
        return f'{days}d ago'
    else:
        return dt.strftime('%b %d, %Y')


@app.template_filter('truncate_text')
def truncate_text(text, length=100):
    if not text:
        return ''
    if len(text) <= length:
        return text
    return text[:length].rsplit(' ', 1)[0] + '...'


# ============================================================
# CONTEXT PROCESSORS
# ============================================================

@app.context_processor
def inject_globals():
    """Inject global variables into all templates."""
    user = None
    cart_count = 0
    notification_count = 0
    db = get_db()

    if 'user_id' in session:
        user = db.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()
        if user:
            cart_count = get_cart_count(user['id'])
            notification_count = get_notification_count(user['id'])

    return {
        'current_user': user,
        'cart_count': cart_count,
        'notification_count': notification_count,
        'now': datetime.datetime.utcnow(),
        'settings': {
            'site_name': get_setting('site_name', 'ARIYAN CODE BAZAR'),
            'site_tagline': get_setting('site_tagline', 'Premium Digital Marketplace'),
            'currency_symbol': get_setting('currency_symbol', '৳'),
            'maintenance_mode': get_setting('maintenance_mode', '0'),
        }
    }


# ============================================================
# AUTHENTICATION DECORATORS
# ============================================================

def login_required(f):
    """Decorator to require user login."""
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login to continue.', 'warning')
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    """Decorator to require admin login."""
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_id' not in session:
            flash('Admin access required.', 'danger')
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function


# ============================================================
# BASE LAYOUT TEMPLATE
# ============================================================

BASE_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}{{ settings.site_name }}{% endblock %}</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap" rel="stylesheet">
    <link href="https://unpkg.com/boxicons@2.1.4/css/boxicons.min.css" rel="stylesheet">
    <style>
        /* ===== CSS RESET & VARIABLES ===== */
        :root {
            --primary: #00f2fe;
            --primary-blue: #4facfe;
            --purple: #a855f7;
            --red: #ff0844;
            --green: #2ecc71;
            --yellow: #f59e0b;
            --bg-dark: #090910;
            --bg-card: rgba(15, 15, 30, 0.8);
            --bg-glass: rgba(255, 255, 255, 0.05);
            --bg-glass-hover: rgba(255, 255, 255, 0.1);
            --text-primary: #ffffff;
            --text-secondary: rgba(255, 255, 255, 0.7);
            --text-muted: rgba(255, 255, 255, 0.4);
            --border-color: rgba(255, 255, 255, 0.1);
            --shadow-neon: 0 0 20px rgba(0, 242, 254, 0.3);
            --shadow-card: 0 8px 32px rgba(0, 0, 0, 0.4);
            --gradient-primary: linear-gradient(135deg, #00f2fe, #4facfe);
            --gradient-purple: linear-gradient(135deg, #a855f7, #6366f1);
            --gradient-red: linear-gradient(135deg, #ff0844, #ff6b6b);
            --gradient-green: linear-gradient(135deg, #2ecc71, #27ae60);
            --glass-blur: blur(20px);
            --transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            --radius: 16px;
            --radius-sm: 10px;
            --radius-xs: 6px;
        }

        * { margin: 0; padding: 0; box-sizing: border-box; }

        html { scroll-behavior: smooth; }

        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background: var(--bg-dark);
            color: var(--text-primary);
            line-height: 1.6;
            min-height: 100vh;
            overflow-x: hidden;
        }

        /* ===== ANIMATED BACKGROUND ===== */
        .bg-particles {
            position: fixed;
            top: 0; left: 0;
            width: 100%; height: 100%;
            z-index: -1;
            overflow: hidden;
        }

        .bg-particles::before {
            content: '';
            position: absolute;
            top: -50%; left: -50%;
            width: 200%; height: 200%;
            background: radial-gradient(circle at 20% 50%, rgba(0, 242, 254, 0.08) 0%, transparent 50%),
                        radial-gradient(circle at 80% 20%, rgba(168, 85, 247, 0.08) 0%, transparent 50%),
                        radial-gradient(circle at 40% 80%, rgba(79, 172, 254, 0.06) 0%, transparent 50%);
            animation: bgFloat 20s ease-in-out infinite;
        }

        .aurora {
            position: fixed;
            top: 0; left: 0;
            width: 100%; height: 100%;
            z-index: -1;
            opacity: 0.3;
        }

        .aurora::before, .aurora::after {
            content: '';
            position: absolute;
            width: 600px; height: 600px;
            border-radius: 50%;
            filter: blur(120px);
            animation: auroraFloat 15s ease-in-out infinite;
        }

        .aurora::before {
            top: -200px; left: -200px;
            background: rgba(0, 242, 254, 0.15);
        }

        .aurora::after {
            bottom: -200px; right: -200px;
            background: rgba(168, 85, 247, 0.15);
            animation-delay: -7s;
        }

        @keyframes bgFloat {
            0%, 100% { transform: translate(0, 0) rotate(0deg); }
            33% { transform: translate(2%, -2%) rotate(1deg); }
            66% { transform: translate(-1%, 1%) rotate(-1deg); }
        }

        @keyframes auroraFloat {
            0%, 100% { transform: translate(0, 0) scale(1); }
            50% { transform: translate(50px, 30px) scale(1.1); }
        }

        /* ===== SCROLLBAR ===== */
        ::-webkit-scrollbar { width: 8px; }
        ::-webkit-scrollbar-track { background: var(--bg-dark); }
        ::-webkit-scrollbar-thumb {
            background: linear-gradient(var(--primary), var(--purple));
            border-radius: 4px;
        }

        /* ===== TYPOGRAPHY ===== */
        h1, h2, h3, h4, h5, h6 { font-weight: 700; line-height: 1.3; }
        a { color: var(--primary); text-decoration: none; transition: var(--transition); }
        a:hover { color: var(--primary-blue); }

        /* ===== GLASS CARD ===== */
        .glass-card {
            background: var(--bg-glass);
            backdrop-filter: var(--glass-blur);
            -webkit-backdrop-filter: var(--glass-blur);
            border: 1px solid var(--border-color);
            border-radius: var(--radius);
            padding: 24px;
            transition: var(--transition);
        }

        .glass-card:hover {
            background: var(--bg-glass-hover);
            border-color: rgba(0, 242, 254, 0.3);
            box-shadow: var(--shadow-neon);
            transform: translateY(-2px);
        }

        /* ===== NEON BUTTON ===== */
        .btn-neon {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
            padding: 12px 28px;
            background: var(--gradient-primary);
            color: #000;
            font-weight: 600;
            font-size: 14px;
            border: none;
            border-radius: var(--radius-sm);
            cursor: pointer;
            transition: var(--transition);
            position: relative;
            overflow: hidden;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        .btn-neon:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(0, 242, 254, 0.4);
            color: #000;
        }

        .btn-neon::before {
            content: '';
            position: absolute;
            top: 0; left: -100%;
            width: 100%; height: 100%;
            background: linear-gradient(90deg, transparent, rgba(255,255,255,0.3), transparent);
            transition: 0.5s;
        }

        .btn-neon:hover::before { left: 100%; }

        .btn-neon-purple {
            background: var(--gradient-purple);
            color: #fff;
        }

        .btn-neon-purple:hover {
            box-shadow: 0 8px 25px rgba(168, 85, 247, 0.4);
            color: #fff;
        }

        .btn-neon-red {
            background: var(--gradient-red);
            color: #fff;
        }

        .btn-neon-red:hover {
            box-shadow: 0 8px 25px rgba(255, 8, 68, 0.4);
            color: #fff;
        }

        .btn-neon-green {
            background: var(--gradient-green);
            color: #000;
        }

        .btn-neon-green:hover {
            box-shadow: 0 8px 25px rgba(46, 204, 113, 0.4);
            color: #000;
        }

        .btn-outline {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
            padding: 10px 24px;
            background: transparent;
            color: var(--primary);
            font-weight: 600;
            font-size: 14px;
            border: 1px solid var(--primary);
            border-radius: var(--radius-sm);
            cursor: pointer;
            transition: var(--transition);
        }

        .btn-outline:hover {
            background: rgba(0, 242, 254, 0.1);
            box-shadow: 0 0 15px rgba(0, 242, 254, 0.2);
            color: var(--primary);
        }

        .btn-sm { padding: 8px 16px; font-size: 12px; }
        .btn-lg { padding: 16px 36px; font-size: 16px; }
        .btn-icon {
            width: 40px; height: 40px;
            padding: 0; border-radius: 50%;
            display: inline-flex; align-items: center; justify-content: center;
        }

        /* ===== FORM STYLES ===== */
        .form-group { margin-bottom: 20px; }

        .form-group label {
            display: block;
            margin-bottom: 8px;
            font-weight: 500;
            color: var(--text-secondary);
            font-size: 14px;
        }

        .form-input {
            width: 100%;
            padding: 14px 16px;
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid var(--border-color);
            border-radius: var(--radius-sm);
            color: var(--text-primary);
            font-size: 14px;
            font-family: inherit;
            transition: var(--transition);
            outline: none;
        }

        .form-input:focus {
            border-color: var(--primary);
            box-shadow: 0 0 0 3px rgba(0, 242, 254, 0.1);
            background: rgba(255, 255, 255, 0.08);
        }

        .form-input::placeholder { color: var(--text-muted); }

        textarea.form-input {
            min-height: 120px;
            resize: vertical;
        }

        select.form-input {
            appearance: none;
            background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 12 12'%3E%3Cpath fill='%23ffffff80' d='M6 8L1 3h10z'/%3E%3C/svg%3E");
            background-repeat: no-repeat;
            background-position: right 16px center;
            padding-right: 40px;
        }

        .input-icon {
            position: relative;
        }

        .input-icon i {
            position: absolute;
            left: 16px;
            top: 50%;
            transform: translateY(-50%);
            color: var(--text-muted);
            font-size: 18px;
        }

        .input-icon .form-input {
            padding-left: 48px;
        }

        /* ===== NAVIGATION ===== */
        .navbar {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            z-index: 1000;
            background: rgba(9, 9, 16, 0.85);
            backdrop-filter: var(--glass-blur);
            -webkit-backdrop-filter: var(--glass-blur);
            border-bottom: 1px solid var(--border-color);
            padding: 0 24px;
            transition: var(--transition);
        }

        .navbar.scrolled {
            background: rgba(9, 9, 16, 0.95);
            box-shadow: 0 4px 30px rgba(0, 0, 0, 0.5);
        }

        .nav-container {
            max-width: 1400px;
            margin: 0 auto;
            display: flex;
            align-items: center;
            justify-content: space-between;
            height: 70px;
        }

        .nav-logo {
            display: flex;
            align-items: center;
            gap: 12px;
            font-size: 22px;
            font-weight: 800;
            color: var(--text-primary);
        }

        .nav-logo .logo-icon {
            width: 42px;
            height: 42px;
            background: var(--gradient-primary);
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 20px;
            color: #000;
            font-weight: 900;
        }

        .nav-logo .logo-text {
            background: var(--gradient-primary);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }

        .nav-links {
            display: flex;
            align-items: center;
            gap: 8px;
            list-style: none;
        }

        .nav-links a {
            padding: 8px 16px;
            color: var(--text-secondary);
            font-weight: 500;
            font-size: 14px;
            border-radius: var(--radius-xs);
            transition: var(--transition);
            display: flex;
            align-items: center;
            gap: 6px;
        }

        .nav-links a:hover, .nav-links a.active {
            color: var(--primary);
            background: rgba(0, 242, 254, 0.1);
        }

        .nav-actions {
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .nav-action-btn {
            position: relative;
            width: 42px;
            height: 42px;
            background: var(--bg-glass);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: var(--text-secondary);
            font-size: 20px;
            cursor: pointer;
            transition: var(--transition);
        }

        .nav-action-btn:hover {
            background: var(--bg-glass-hover);
            color: var(--primary);
            border-color: rgba(0, 242, 254, 0.3);
        }

        .nav-badge {
            position: absolute;
            top: -4px;
            right: -4px;
            min-width: 18px;
            height: 18px;
            background: var(--red);
            color: #fff;
            font-size: 10px;
            font-weight: 700;
            border-radius: 9px;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 0 5px;
        }

        .nav-user {
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 6px 12px 6px 6px;
            background: var(--bg-glass);
            border: 1px solid var(--border-color);
            border-radius: 50px;
            cursor: pointer;
            transition: var(--transition);
        }

        .nav-user:hover {
            background: var(--bg-glass-hover);
            border-color: rgba(0, 242, 254, 0.3);
        }

        .nav-user-avatar {
            width: 34px;
            height: 34px;
            border-radius: 50%;
            background: var(--gradient-primary);
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 700;
            font-size: 14px;
            color: #000;
        }

        .nav-user-name {
            font-size: 14px;
            font-weight: 600;
            color: var(--text-primary);
        }

        .nav-dropdown {
            position: absolute;
            top: calc(100% + 8px);
            right: 0;
            min-width: 220px;
            background: rgba(20, 20, 40, 0.95);
            backdrop-filter: var(--glass-blur);
            border: 1px solid var(--border-color);
            border-radius: var(--radius);
            padding: 8px;
            display: none;
            box-shadow: var(--shadow-card);
            z-index: 1001;
        }

        .nav-dropdown.show { display: block; }

        .nav-dropdown a {
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 12px 16px;
            color: var(--text-secondary);
            font-size: 14px;
            border-radius: var(--radius-xs);
            transition: var(--transition);
        }

        .nav-dropdown a:hover {
            background: var(--bg-glass-hover);
            color: var(--primary);
        }

        .nav-dropdown .dropdown-divider {
            height: 1px;
            background: var(--border-color);
            margin: 8px 0;
        }

        /* Mobile Navigation */
        .mobile-nav {
            display: none;
            position: fixed;
            bottom: 0;
            left: 0;
            right: 0;
            z-index: 1000;
            background: rgba(9, 9, 16, 0.95);
            backdrop-filter: var(--glass-blur);
            border-top: 1px solid var(--border-color);
            padding: 8px 0;
        }

        .mobile-nav-items {
            display: flex;
            justify-content: space-around;
            list-style: none;
        }

        .mobile-nav-items a {
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 4px;
            padding: 8px 12px;
            color: var(--text-muted);
            font-size: 10px;
            font-weight: 500;
            transition: var(--transition);
            position: relative;
        }

        .mobile-nav-items a i { font-size: 22px; }

        .mobile-nav-items a.active,
        .mobile-nav-items a:hover {
            color: var(--primary);
        }

        .mobile-nav-items a.active::before {
            content: '';
            position: absolute;
            top: -8px;
            left: 50%;
            transform: translateX(-50%);
            width: 30px;
            height: 3px;
            background: var(--gradient-primary);
            border-radius: 2px;
        }

        .hamburger {
            display: none;
            flex-direction: column;
            gap: 5px;
            cursor: pointer;
            padding: 8px;
        }

        .hamburger span {
            width: 24px;
            height: 2px;
            background: var(--text-primary);
            transition: var(--transition);
            border-radius: 2px;
        }

        .hamburger.active span:nth-child(1) { transform: rotate(45deg) translate(5px, 5px); }
        .hamburger.active span:nth-child(2) { opacity: 0; }
        .hamburger.active span:nth-child(3) { transform: rotate(-45deg) translate(5px, -5px); }

        /* ===== MAIN CONTENT ===== */
        .main-content {
            padding-top: 70px;
            min-height: 100vh;
        }

        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 0 24px;
        }

        .container-sm {
            max-width: 500px;
            margin: 0 auto;
            padding: 0 24px;
        }

        .container-md {
            max-width: 800px;
            margin: 0 auto;
            padding: 0 24px;
        }

        /* ===== PAGE HEADER ===== */
        .page-header {
            padding: 40px 0 20px;
        }

        .page-header h1 {
            font-size: 28px;
            margin-bottom: 8px;
            background: var(--gradient-primary);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }

        .page-header p {
            color: var(--text-secondary);
            font-size: 15px;
        }

        .breadcrumb {
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 13px;
            color: var(--text-muted);
            margin-bottom: 16px;
        }

        .breadcrumb a { color: var(--text-secondary); }
        .breadcrumb a:hover { color: var(--primary); }

        /* ===== PRODUCT GRID ===== */
        .product-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
            gap: 24px;
            padding: 20px 0;
        }

        .product-card {
            background: var(--bg-glass);
            backdrop-filter: var(--glass-blur);
            border: 1px solid var(--border-color);
            border-radius: var(--radius);
            overflow: hidden;
            transition: var(--transition);
            cursor: pointer;
        }

        .product-card:hover {
            transform: translateY(-5px);
            border-color: rgba(0, 242, 254, 0.3);
            box-shadow: 0 12px 40px rgba(0, 0, 0, 0.4), 0 0 20px rgba(0, 242, 254, 0.1);
        }

        .product-image {
            height: 200px;
            background: linear-gradient(135deg, rgba(0, 242, 254, 0.1), rgba(168, 85, 247, 0.1));
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 60px;
            position: relative;
            overflow: hidden;
        }

        .product-image::after {
            content: '';
            position: absolute;
            bottom: 0;
            left: 0;
            right: 0;
            height: 60px;
            background: linear-gradient(transparent, rgba(9, 9, 16, 0.8));
        }

        .product-badge {
            position: absolute;
            top: 12px;
            left: 12px;
            padding: 4px 10px;
            border-radius: 20px;
            font-size: 11px;
            font-weight: 700;
            text-transform: uppercase;
            z-index: 1;
        }

        .badge-discount {
            background: var(--red);
            color: #fff;
        }

        .badge-featured {
            background: var(--gradient-primary);
            color: #000;
        }

        .badge-new {
            background: var(--green);
            color: #000;
        }

        .product-wishlist {
            position: absolute;
            top: 12px;
            right: 12px;
            width: 36px;
            height: 36px;
            background: rgba(0, 0, 0, 0.5);
            backdrop-filter: blur(10px);
            border: none;
            border-radius: 50%;
            color: var(--text-secondary);
            font-size: 18px;
            cursor: pointer;
            transition: var(--transition);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 1;
        }

        .product-wishlist:hover, .product-wishlist.active {
            color: var(--red);
            background: rgba(255, 8, 68, 0.2);
        }

        .product-info {
            padding: 16px;
        }

        .product-category {
            font-size: 11px;
            text-transform: uppercase;
            color: var(--primary);
            font-weight: 600;
            letter-spacing: 1px;
            margin-bottom: 8px;
        }

        .product-title {
            font-size: 16px;
            font-weight: 600;
            margin-bottom: 8px;
            color: var(--text-primary);
            display: -webkit-box;
            -webkit-line-clamp: 2;
            -webkit-box-orient: vertical;
            overflow: hidden;
        }

        .product-desc {
            font-size: 13px;
            color: var(--text-muted);
            margin-bottom: 12px;
            display: -webkit-box;
            -webkit-line-clamp: 2;
            -webkit-box-orient: vertical;
            overflow: hidden;
        }

        .product-meta {
            display: flex;
            align-items: center;
            gap: 12px;
            margin-bottom: 12px;
            font-size: 12px;
            color: var(--text-muted);
        }

        .product-rating {
            display: flex;
            align-items: center;
            gap: 4px;
        }

        .product-rating i { color: #f59e0b; font-size: 14px; }

        .product-footer {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding-top: 12px;
            border-top: 1px solid var(--border-color);
        }

        .product-price {
            display: flex;
            align-items: baseline;
            gap: 8px;
        }

        .price-current {
            font-size: 20px;
            font-weight: 800;
            background: var(--gradient-primary);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }

        .price-original {
            font-size: 13px;
            color: var(--text-muted);
            text-decoration: line-through;
        }

        .product-add-cart {
            width: 40px;
            height: 40px;
            background: var(--gradient-primary);
            border: none;
            border-radius: 12px;
            color: #000;
            font-size: 18px;
            cursor: pointer;
            transition: var(--transition);
            display: flex;
            align-items: center;
            justify-content: center;
        }

        .product-add-cart:hover {
            transform: scale(1.1);
            box-shadow: 0 4px 15px rgba(0, 242, 254, 0.4);
        }

        /* ===== HERO SECTION ===== */
        .hero {
            padding: 80px 0 40px;
            text-align: center;
            position: relative;
        }

        .hero-title {
            font-size: clamp(36px, 6vw, 64px);
            font-weight: 900;
            margin-bottom: 20px;
            line-height: 1.1;
        }

        .hero-title .gradient-text {
            background: var(--gradient-primary);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }

        .hero-subtitle {
            font-size: clamp(16px, 2.5vw, 20px);
            color: var(--text-secondary);
            max-width: 600px;
            margin: 0 auto 32px;
            line-height: 1.7;
        }

        .hero-actions {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 16px;
            flex-wrap: wrap;
        }

        .hero-stats {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 48px;
            margin-top: 60px;
            flex-wrap: wrap;
        }

        .hero-stat {
            text-align: center;
        }

        .hero-stat-value {
            font-size: 32px;
            font-weight: 800;
            background: var(--gradient-primary);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }

        .hero-stat-label {
            font-size: 13px;
            color: var(--text-muted);
            margin-top: 4px;
        }

        /* ===== CATEGORIES GRID ===== */
        .categories-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
            gap: 16px;
            padding: 20px 0;
        }

        .category-card {
            background: var(--bg-glass);
            backdrop-filter: var(--glass-blur);
            border: 1px solid var(--border-color);
            border-radius: var(--radius);
            padding: 24px;
            text-align: center;
            transition: var(--transition);
            cursor: pointer;
            text-decoration: none;
        }

        .category-card:hover {
            transform: translateY(-4px);
            border-color: rgba(0, 242, 254, 0.3);
            box-shadow: var(--shadow-neon);
        }

        .category-icon {
            width: 60px;
            height: 60px;
            border-radius: 16px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 28px;
            margin: 0 auto 12px;
            background: rgba(0, 242, 254, 0.1);
            color: var(--primary);
        }

        .category-name {
            font-size: 15px;
            font-weight: 600;
            color: var(--text-primary);
            margin-bottom: 4px;
        }

        .category-count {
            font-size: 12px;
            color: var(--text-muted);
        }

        /* ===== DASHBOARD ===== */
        .dashboard-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
            gap: 20px;
            padding: 20px 0;
        }

        .stat-card {
            background: var(--bg-glass);
            backdrop-filter: var(--glass-blur);
            border: 1px solid var(--border-color);
            border-radius: var(--radius);
            padding: 24px;
            position: relative;
            overflow: hidden;
            transition: var(--transition);
        }

        .stat-card:hover {
            transform: translateY(-3px);
            box-shadow: var(--shadow-neon);
        }

        .stat-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 3px;
            background: var(--gradient-primary);
        }

        .stat-card.purple::before { background: var(--gradient-purple); }
        .stat-card.red::before { background: var(--gradient-red); }
        .stat-card.green::before { background: var(--gradient-green); }

        .stat-icon {
            width: 50px;
            height: 50px;
            border-radius: 14px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 24px;
            margin-bottom: 16px;
            background: rgba(0, 242, 254, 0.1);
            color: var(--primary);
        }

        .stat-card.purple .stat-icon { background: rgba(168, 85, 247, 0.1); color: var(--purple); }
        .stat-card.red .stat-icon { background: rgba(255, 8, 68, 0.1); color: var(--red); }
        .stat-card.green .stat-icon { background: rgba(46, 204, 113, 0.1); color: var(--green); }

        .stat-value {
            font-size: 28px;
            font-weight: 800;
            color: var(--text-primary);
            margin-bottom: 4px;
        }

        .stat-label {
            font-size: 13px;
            color: var(--text-muted);
        }

        /* ===== TABLE STYLES ===== */
        .table-container {
            overflow-x: auto;
            border-radius: var(--radius);
            border: 1px solid var(--border-color);
        }

        .data-table {
            width: 100%;
            border-collapse: collapse;
        }

        .data-table th {
            padding: 14px 16px;
            text-align: left;
            font-size: 12px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 1px;
            color: var(--text-muted);
            background: rgba(255, 255, 255, 0.02);
            border-bottom: 1px solid var(--border-color);
        }

        .data-table td {
            padding: 14px 16px;
            font-size: 14px;
            color: var(--text-secondary);
            border-bottom: 1px solid rgba(255, 255, 255, 0.03);
        }

        .data-table tr:hover td {
            background: rgba(255, 255, 255, 0.02);
        }

        /* ===== STATUS BADGES ===== */
        .status-badge {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
        }

        .status-pending {
            background: rgba(245, 158, 11, 0.15);
            color: #f59e0b;
        }

        .status-approved, .status-completed {
            background: rgba(46, 204, 113, 0.15);
            color: #2ecc71;
        }

        .status-rejected {
            background: rgba(255, 8, 68, 0.15);
            color: #ff0844;
        }

        .status-processing {
            background: rgba(79, 172, 254, 0.15);
            color: #4facfe;
        }

        .status-delivered {
            background: rgba(168, 85, 247, 0.15);
            color: #a855f7;
        }

        /* ===== MODAL ===== */
        .modal-overlay {
            position: fixed;
            top: 0; left: 0;
            width: 100%; height: 100%;
            background: rgba(0, 0, 0, 0.7);
            backdrop-filter: blur(10px);
            z-index: 2000;
            display: none;
            align-items: center;
            justify-content: center;
            padding: 24px;
        }

        .modal-overlay.show { display: flex; }

        .modal-content {
            background: rgba(20, 20, 40, 0.95);
            backdrop-filter: var(--glass-blur);
            border: 1px solid var(--border-color);
            border-radius: var(--radius);
            max-width: 500px;
            width: 100%;
            max-height: 90vh;
            overflow-y: auto;
            padding: 32px;
        }

        .modal-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 24px;
        }

        .modal-header h2 {
            font-size: 20px;
            font-weight: 700;
        }

        .modal-close {
            width: 36px; height: 36px;
            background: var(--bg-glass);
            border: 1px solid var(--border-color);
            border-radius: 10px;
            color: var(--text-secondary);
            font-size: 20px;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: var(--transition);
        }

        .modal-close:hover {
            background: rgba(255, 8, 68, 0.15);
            color: var(--red);
            border-color: rgba(255, 8, 68, 0.3);
        }

        /* ===== TOAST NOTIFICATIONS ===== */
        .toast-container {
            position: fixed;
            top: 80px;
            right: 24px;
            z-index: 3000;
            display: flex;
            flex-direction: column;
            gap: 8px;
        }

        .toast {
            padding: 16px 20px;
            background: rgba(20, 20, 40, 0.95);
            backdrop-filter: var(--glass-blur);
            border: 1px solid var(--border-color);
            border-radius: var(--radius-sm);
            color: var(--text-primary);
            font-size: 14px;
            display: flex;
            align-items: center;
            gap: 12px;
            min-width: 300px;
            max-width: 400px;
            animation: slideInRight 0.3s ease-out;
            box-shadow: var(--shadow-card);
        }

        .toast.success { border-left: 4px solid var(--green); }
        .toast.error { border-left: 4px solid var(--red); }
        .toast.warning { border-left: 4px solid var(--yellow); }
        .toast.info { border-left: 4px solid var(--primary); }

        @keyframes slideInRight {
            from { transform: translateX(100%); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
        }

        /* ===== PAGINATION ===== */
        .pagination {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
            padding: 32px 0;
        }

        .page-btn {
            width: 40px; height: 40px;
            background: var(--bg-glass);
            border: 1px solid var(--border-color);
            border-radius: 10px;
            color: var(--text-secondary);
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            transition: var(--transition);
            display: flex;
            align-items: center;
            justify-content: center;
        }

        .page-btn:hover, .page-btn.active {
            background: var(--gradient-primary);
            color: #000;
            border-color: transparent;
        }

        /* ===== SEARCH BAR ===== */
        .search-bar {
            position: relative;
            max-width: 500px;
        }

        .search-bar input {
            width: 100%;
            padding: 14px 48px 14px 48px;
            background: var(--bg-glass);
            border: 1px solid var(--border-color);
            border-radius: 50px;
            color: var(--text-primary);
            font-size: 14px;
            outline: none;
            transition: var(--transition);
        }

        .search-bar input:focus {
            border-color: var(--primary);
            box-shadow: 0 0 0 3px rgba(0, 242, 254, 0.1);
        }

        .search-bar i {
            position: absolute;
            left: 18px;
            top: 50%;
            transform: translateY(-50%);
            color: var(--text-muted);
            font-size: 18px;
        }

        /* ===== FOOTER ===== */
        .footer {
            background: rgba(9, 9, 16, 0.8);
            backdrop-filter: var(--glass-blur);
            border-top: 1px solid var(--border-color);
            padding: 60px 0 30px;
            margin-top: 60px;
        }

        .footer-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 40px;
            margin-bottom: 40px;
        }

        .footer-col h3 {
            font-size: 16px;
            font-weight: 700;
            margin-bottom: 16px;
            color: var(--text-primary);
        }

        .footer-col p {
            font-size: 14px;
            color: var(--text-secondary);
            line-height: 1.7;
        }

        .footer-links {
            list-style: none;
        }

        .footer-links li { margin-bottom: 10px; }

        .footer-links a {
            color: var(--text-secondary);
            font-size: 14px;
            transition: var(--transition);
        }

        .footer-links a:hover { color: var(--primary); }

        .footer-bottom {
            text-align: center;
            padding-top: 24px;
            border-top: 1px solid var(--border-color);
            font-size: 13px;
            color: var(--text-muted);
        }

        /* ===== SECTION ===== */
        .section {
            padding: 40px 0;
        }

        .section-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 24px;
            flex-wrap: wrap;
            gap: 16px;
        }

        .section-title {
            font-size: 24px;
            font-weight: 800;
        }

        .section-title .gradient-text {
            background: var(--gradient-primary);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }

        /* ===== LOADING / SKELETON ===== */
        .skeleton {
            background: linear-gradient(90deg, rgba(255,255,255,0.05) 25%, rgba(255,255,255,0.1) 50%, rgba(255,255,255,0.05) 75%);
            background-size: 200% 100%;
            animation: shimmer 1.5s infinite;
            border-radius: var(--radius-xs);
        }

        @keyframes shimmer {
            0% { background-position: -200% 0; }
            100% { background-position: 200% 0; }
        }

        .spinner {
            width: 40px; height: 40px;
            border: 3px solid var(--border-color);
            border-top-color: var(--primary);
            border-radius: 50%;
            animation: spin 0.8s linear infinite;
        }

        @keyframes spin { to { transform: rotate(360deg); } }

        /* ===== EMPTY STATE ===== */
        .empty-state {
            text-align: center;
            padding: 60px 20px;
        }

        .empty-state i {
            font-size: 60px;
            color: var(--text-muted);
            margin-bottom: 20px;
        }

        .empty-state h3 {
            font-size: 20px;
            margin-bottom: 8px;
        }

        .empty-state p {
            color: var(--text-muted);
            margin-bottom: 24px;
        }

        /* ===== TABS ===== */
        .tabs {
            display: flex;
            gap: 4px;
            padding: 4px;
            background: var(--bg-glass);
            border: 1px solid var(--border-color);
            border-radius: var(--radius-sm);
            margin-bottom: 24px;
            overflow-x: auto;
        }

        .tab-btn {
            padding: 10px 20px;
            background: transparent;
            border: none;
            color: var(--text-muted);
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            border-radius: var(--radius-xs);
            transition: var(--transition);
            white-space: nowrap;
        }

        .tab-btn:hover { color: var(--text-primary); }

        .tab-btn.active {
            background: var(--gradient-primary);
            color: #000;
        }

        /* ===== SIDEBAR LAYOUT ===== */
        .sidebar-layout {
            display: grid;
            grid-template-columns: 260px 1fr;
            gap: 24px;
            padding: 24px 0;
        }

        .sidebar {
            background: var(--bg-glass);
            backdrop-filter: var(--glass-blur);
            border: 1px solid var(--border-color);
            border-radius: var(--radius);
            padding: 20px;
            height: fit-content;
            position: sticky;
            top: 90px;
        }

        .sidebar-menu { list-style: none; }

        .sidebar-menu li a {
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 12px 16px;
            color: var(--text-secondary);
            font-size: 14px;
            font-weight: 500;
            border-radius: var(--radius-xs);
            transition: var(--transition);
            margin-bottom: 4px;
        }

        .sidebar-menu li a:hover,
        .sidebar-menu li a.active {
            background: rgba(0, 242, 254, 0.1);
            color: var(--primary);
        }

        .sidebar-menu li a i { font-size: 20px; }

        /* ===== ALERTS ===== */
        .alert {
            padding: 16px 20px;
            border-radius: var(--radius-sm);
            margin-bottom: 16px;
            font-size: 14px;
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .alert-success {
            background: rgba(46, 204, 113, 0.1);
            border: 1px solid rgba(46, 204, 113, 0.2);
            color: #2ecc71;
        }

        .alert-danger {
            background: rgba(255, 8, 68, 0.1);
            border: 1px solid rgba(255, 8, 68, 0.2);
            color: #ff0844;
        }

        .alert-warning {
            background: rgba(245, 158, 11, 0.1);
            border: 1px solid rgba(245, 158, 11, 0.2);
            color: #f59e0b;
        }

        .alert-info {
            background: rgba(0, 242, 254, 0.1);
            border: 1px solid rgba(0, 242, 254, 0.2);
            color: #00f2fe;
        }

        /* ===== RESPONSIVE ===== */
        @media (max-width: 1024px) {
            .sidebar-layout {
                grid-template-columns: 1fr;
            }
            .sidebar {
                position: static;
            }
        }

        @media (max-width: 768px) {
            .nav-links { display: none; }
            .hamburger { display: flex; }
            .mobile-nav { display: block; }
            .main-content { padding-bottom: 80px; }

            .product-grid {
                grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
                gap: 12px;
            }

            .product-image { height: 140px; }
            .product-info { padding: 12px; }
            .product-title { font-size: 14px; }
            .product-desc { display: none; }
            .price-current { font-size: 16px; }

            .hero { padding: 40px 0 20px; }
            .hero-stats { gap: 24px; }

            .dashboard-grid {
                grid-template-columns: repeat(2, 1fr);
                gap: 12px;
            }

            .container { padding: 0 16px; }
            .section { padding: 24px 0; }

            .nav-user-name { display: none; }

            .data-table th, .data-table td {
                padding: 10px 12px;
                font-size: 12px;
            }

            .footer-grid {
                grid-template-columns: 1fr 1fr;
                gap: 24px;
            }
        }

        @media (max-width: 480px) {
            .dashboard-grid {
                grid-template-columns: 1fr;
            }

            .categories-grid {
                grid-template-columns: repeat(2, 1fr);
                gap: 12px;
            }

            .hero-actions {
                flex-direction: column;
            }

            .footer-grid {
                grid-template-columns: 1fr;
            }
        }

        /* ===== ANIMATIONS ===== */
        @keyframes fadeInUp {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }

        .animate-in {
            animation: fadeInUp 0.5s ease-out;
        }

        .animate-delay-1 { animation-delay: 0.1s; }
        .animate-delay-2 { animation-delay: 0.2s; }
        .animate-delay-3 { animation-delay: 0.3s; }
        .animate-delay-4 { animation-delay: 0.4s; }

        /* ===== UTILITY ===== */
        .text-center { text-align: center; }
        .text-right { text-align: right; }
        .text-primary { color: var(--primary); }
        .text-green { color: var(--green); }
        .text-red { color: var(--red); }
        .text-yellow { color: var(--yellow); }
        .text-purple { color: var(--purple); }
        .text-muted { color: var(--text-muted); }
        .text-secondary { color: var(--text-secondary); }
        .fw-bold { font-weight: 700; }
        .fw-semibold { font-weight: 600; }
        .mt-1 { margin-top: 8px; }
        .mt-2 { margin-top: 16px; }
        .mt-3 { margin-top: 24px; }
        .mt-4 { margin-top: 32px; }
        .mb-1 { margin-bottom: 8px; }
        .mb-2 { margin-bottom: 16px; }
        .mb-3 { margin-bottom: 24px; }
        .mb-4 { margin-bottom: 32px; }
        .me-1 { margin-right: 8px; }
        .me-2 { margin-right: 16px; }
        .ms-1 { margin-left: 8px; }
        .d-flex { display: flex; }
        .align-center { align-items: center; }
        .justify-between { justify-content: space-between; }
        .gap-1 { gap: 8px; }
        .gap-2 { gap: 16px; }
        .gap-3 { gap: 24px; }
        .flex-wrap { flex-wrap: wrap; }
        .w-100 { width: 100%; }
        .hidden { display: none; }

        .copy-btn {
            background: var(--bg-glass);
            border: 1px solid var(--border-color);
            color: var(--primary);
            padding: 6px 12px;
            border-radius: var(--radius-xs);
            cursor: pointer;
            font-size: 12px;
            transition: var(--transition);
        }

        .copy-btn:hover {
            background: rgba(0, 242, 254, 0.1);
        }


        .brand-mark,.brand-orbit { width:88px;height:88px;margin:0 auto 20px;border-radius:28px;display:flex;align-items:center;justify-content:center;font-size:48px;font-weight:900;color:#071018;background:linear-gradient(135deg,#00f2fe,#a855f7,#ff0844,#f59e0b);background-size:300% 300%;animation:logoRainbow 4s ease infinite;box-shadow:0 0 35px rgba(0,242,254,.45)}
        @keyframes logoRainbow { 0%,100%{background-position:0% 50%;transform:rotate(-3deg)} 50%{background-position:100% 50%;transform:rotate(3deg)} }
        .guest-hero{text-align:center;padding:15vh 20px}.guest-hero h1{font-size:clamp(34px,7vw,76px);letter-spacing:2px}.guest-hero h1 b{background:linear-gradient(90deg,#00f2fe,#a855f7,#ff0844);background-size:200%;animation:logoRainbow 4s ease infinite;background-clip:text;-webkit-background-clip:text;color:transparent}.guest-hero p{color:var(--text-secondary);font-size:18px;margin:15px 0 30px}.auth-gate{max-width:520px;margin:100px auto;text-align:center}.auth-gate .hero-actions{margin-top:25px}

        {% block extra_css %}{% endblock %}
    </style>
</head>
<body>
    <!-- Background Effects -->
    <div class="bg-particles"></div>
    <div class="aurora"></div>

    <!-- Toast Container -->
    <div class="toast-container" id="toastContainer">
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                {% for category, message in messages %}
                <div class="toast {{ category }}">
                    <i class='bx {% if category == "success" %}bx-check-circle{% elif category == "danger" %}bx-error{% elif category == "warning" %}bx-error-circle{% else %}bx-info-circle{% endif %}'></i>
                    <span>{{ message }}</span>
                </div>
                {% endfor %}
            {% endif %}
        {% endwith %}
    </div>

    <!-- Navigation -->
    <nav class="navbar" id="navbar">
        <div class="nav-container">
            <a href="{{ url_for('home') }}" class="nav-logo">
                <div class="logo-icon">S</div>
                <span class="logo-text">{{ settings.site_name }}</span>
            </a>

            <ul class="nav-links">
                <li><a href="{{ url_for('home') }}" class="{% if request.endpoint == 'home' %}active{% endif %}"><i class='bx bx-home'></i> Home</a></li>
                <li><a href="{{ url_for('marketplace') }}" class="{% if request.endpoint == 'marketplace' %}active{% endif %}"><i class='bx bx-store'></i> Marketplace</a></li>
                <li><a href="{{ url_for('categories') }}" class="{% if request.endpoint == 'categories' %}active{% endif %}"><i class='bx bx-category'></i> Categories</a></li>
                {% if current_user %}
                <li><a href="{{ url_for('dashboard') }}" class="{% if request.endpoint == 'dashboard' %}active{% endif %}"><i class='bx bx-grid-alt'></i> Dashboard</a></li>
                {% endif %}
            </ul>

            <div class="nav-actions">
                {% if current_user %}
                    <a href="{{ url_for('cart_view') }}" class="nav-action-btn" title="Cart">
                        <i class='bx bx-cart'></i>
                        {% if cart_count > 0 %}
                        <span class="nav-badge">{{ cart_count }}</span>
                        {% endif %}
                    </a>
                    <a href="{{ url_for('notifications') }}" class="nav-action-btn" title="Notifications">
                        <i class='bx bx-bell'></i>
                        {% if notification_count > 0 %}
                        <span class="nav-badge">{{ notification_count }}</span>
                        {% endif %}
                    </a>
                    <div class="nav-user" onclick="toggleDropdown()">
                        <div class="nav-user-avatar">{{ current_user['username'][0]|upper }}</div>
                        <span class="nav-user-name">{{ current_user['username'] }}</span>
                        <i class='bx bx-chevron-down'></i>
                    </div>
                    <div class="nav-dropdown" id="userDropdown">
                        <a href="{{ url_for('dashboard') }}"><i class='bx bx-grid-alt'></i> Dashboard</a>
                        <a href="{{ url_for('profile') }}"><i class='bx bx-user'></i> Profile</a>
                        <a href="{{ url_for('wallet') }}"><i class='bx bx-wallet'></i> Wallet</a>
                        <a href="{{ url_for('orders') }}"><i class='bx bx-package'></i> Orders</a>
                        <a href="{{ url_for('support') }}"><i class='bx bx-support'></i> Support</a>
                        <div class="dropdown-divider"></div>
                        <a href="{{ url_for('logout') }}"><i class='bx bx-log-out'></i> Logout</a>
                    </div>
                {% else %}
                    <a href="{{ url_for('login') }}" class="btn-outline btn-sm">Login</a>
                    <a href="{{ url_for('register') }}" class="btn-neon btn-sm">Register</a>
                {% endif %}
            </div>

            <div class="hamburger" onclick="toggleMobileMenu()">
                <span></span><span></span><span></span>
            </div>
        </div>
    </nav>

    <!-- Mobile Navigation -->
    <div class="mobile-nav">
        <ul class="mobile-nav-items">
            <li><a href="{{ url_for('home') }}" class="{% if request.endpoint == 'home' %}active{% endif %}"><i class='bx bx-home'></i><span>Home</span></a></li>
            <li><a href="{{ url_for('marketplace') }}" class="{% if request.endpoint == 'marketplace' %}active{% endif %}"><i class='bx bx-store'></i><span>Shop</span></a></li>
            {% if current_user %}
            <li><a href="{{ url_for('cart_view') }}" class="{% if request.endpoint == 'cart_view' %}active{% endif %}" style="position:relative"><i class='bx bx-cart'></i><span>Cart</span>{% if cart_count > 0 %}<span class="nav-badge" style="top:-2px;right:-2px">{{ cart_count }}</span>{% endif %}</a></li>
            <li><a href="{{ url_for('dashboard') }}" class="{% if request.endpoint == 'dashboard' %}active{% endif %}"><i class='bx bx-grid-alt'></i><span>Dashboard</span></a></li>
            <li><a href="{{ url_for('profile') }}" class="{% if request.endpoint == 'profile' %}active{% endif %}"><i class='bx bx-user'></i><span>Profile</span></a></li>
            {% else %}
            <li><a href="{{ url_for('login') }}"><i class='bx bx-log-in'></i><span>Login</span></a></li>
            <li><a href="{{ url_for('register') }}"><i class='bx bx-user-plus'></i><span>Register</span></a></li>
            {% endif %}
        </ul>
    </div>

    <!-- Main Content -->
    <div class="main-content">
        {% block content %}{% endblock %}
    </div>

    <!-- Footer -->
    <footer class="footer">
        <div class="container">
            <div class="footer-grid">
                <div class="footer-col">
                    <div class="nav-logo" style="margin-bottom:16px">
                        <div class="logo-icon">S</div>
                        <span class="logo-text">{{ settings.site_name }}</span>
                    </div>
                    <p>Your premium digital marketplace for genuine software, games, subscriptions, and more. Instant delivery, best prices, 24/7 support.</p>
                </div>
                <div class="footer-col">
                    <h3>Quick Links</h3>
                    <ul class="footer-links">
                        <li><a href="{{ url_for('home') }}">Home</a></li>
                        <li><a href="{{ url_for('marketplace') }}">Marketplace</a></li>
                        <li><a href="{{ url_for('categories') }}">Categories</a></li>
                        {% if current_user %}<li><a href="{{ url_for('dashboard') }}">Dashboard</a></li>{% endif %}
                    </ul>
                </div>
                <div class="footer-col">
                    <h3>Support</h3>
                    <ul class="footer-links">
                        {% if current_user %}<li><a href="{{ url_for('support') }}">Help Center</a></li>{% endif %}
                        <li><a href="#">Terms of Service</a></li>
                        <li><a href="#">Privacy Policy</a></li>
                        <li><a href="#">Refund Policy</a></li>
                    </ul>
                </div>
                <div class="footer-col">
                    <h3>Contact</h3>
                    <ul class="footer-links">
                        <li><a href="#"><i class='bx bx-envelope'></i> support@sohagbdshop.com</a></li>
                        <li><a href="#"><i class='bx bx-phone'></i> +880 1XXXXXXXXX</a></li>
                        <li><a href="#"><i class='bx bx-map'></i> Bangladesh</a></li>
                    </ul>
                </div>
            </div>
            <div class="footer-bottom">
                &copy; 2024 {{ settings.site_name }}. All rights reserved. Made with <i class='bx bxs-heart' style='color:var(--red)'></i>
            </div>
        </div>
    </footer>

    <script>
        // Navigation scroll effect
        window.addEventListener('scroll', () => {
            const navbar = document.getElementById('navbar');
            if (navbar) {
                navbar.classList.toggle('scrolled', window.scrollY > 20);
            }
        });

        // Toggle user dropdown
        function toggleDropdown() {
            const dropdown = document.getElementById('userDropdown');
            if (dropdown) dropdown.classList.toggle('show');
        }

        // Close dropdown on outside click
        document.addEventListener('click', (e) => {
            const dropdown = document.getElementById('userDropdown');
            const userBtn = document.querySelector('.nav-user');
            if (dropdown && userBtn && !userBtn.contains(e.target) && !dropdown.contains(e.target)) {
                dropdown.classList.remove('show');
            }
        });

        // Mobile menu toggle
        function toggleMobileMenu() {
            const hamburger = document.querySelector('.hamburger');
            if (hamburger) hamburger.classList.toggle('active');
        }

        // Toast auto-dismiss
        document.querySelectorAll('.toast').forEach(toast => {
            setTimeout(() => {
                toast.style.animation = 'slideInRight 0.3s ease-out reverse';
                setTimeout(() => toast.remove(), 300);
            }, 4000);
        });

        // Copy to clipboard
        function copyText(text) {
            navigator.clipboard.writeText(text).then(() => {
                showToast('Copied to clipboard!', 'success');
            });
        }

        // Show toast notification
        function showToast(message, type = 'info') {
            const container = document.getElementById('toastContainer');
            const icons = { success: 'bx-check-circle', error: 'bx-error', warning: 'bx-error-circle', info: 'bx-info-circle' };
            const toast = document.createElement('div');
            toast.className = `toast ${type}`;
            toast.innerHTML = `<i class='bx ${icons[type] || icons.info}'></i><span>${message}</span>`;
            container.appendChild(toast);
            setTimeout(() => {
                toast.style.animation = 'slideInRight 0.3s ease-out reverse';
                setTimeout(() => toast.remove(), 300);
            }, 4000);
        }

        {% block extra_js %}{% endblock %}
    </script>
</body>
</html>
'''

# ============================================================
# HOME PAGE TEMPLATE
# ============================================================

GUEST_HOME_TEMPLATE = r'''
{% extends base %}
{% block title %}{{ settings.site_name }}{% endblock %}
{% block content %}
<section class="guest-hero"><div class="brand-orbit"><span>A</span></div><h1>ARIYAN <b>CODE BAZAR</b></h1><p>Premium digital products, made simple.</p><div class="hero-actions"><a href="{{ url_for('login') }}" class="btn-outline btn-lg">Login</a><a href="{{ url_for('register') }}" class="btn-neon btn-lg">Signup</a></div></div>
{% endblock %}
'''

AUTH_GATE_TEMPLATE = r'''
{% extends base %}
{% block title %}Login required - {{ settings.site_name }}{% endblock %}
{% block content %}<div class="container"><div class="auth-gate glass-card"><div class="brand-mark">A</div><h2>Login or Signup to continue</h2><p class="text-secondary">Please create an account or login to view <b>{{ product_name }}</b>.</p><div class="hero-actions"><a class="btn-neon" href="{{ url_for('login', next=request.path) }}">Login</a><a class="btn-outline" href="{{ url_for('register') }}">Signup</a></div></div></div>{% endblock %}
'''

HOME_TEMPLATE = '''
{% extends base %}
{% block title %}{{ settings.site_name }} - Premium Digital Marketplace{% endblock %}

{% block content %}
<!-- Hero Section -->
<section class="hero">
    <div class="container">
        <h1 class="hero-title animate-in">
            Premium <span class="gradient-text">Digital Products</span><br>
            At Your Fingertips
        </h1>
        <p class="hero-subtitle animate-in animate-delay-1">
            Discover genuine software licenses, game keys, subscriptions, and more.
            Instant delivery, best prices, and 24/7 support.
        </p>
        <div class="hero-actions animate-in animate-delay-2">
            <a href="{{ url_for('marketplace') }}" class="btn-neon btn-lg">
                <i class='bx bx-store'></i> Browse Products
            </a>
            {% if not current_user %}
            <a href="{{ url_for('register') }}" class="btn-outline btn-lg">
                <i class='bx bx-user-plus'></i> Create Account
            </a>
            {% endif %}
        </div>
        <div class="hero-stats animate-in animate-delay-3">
            <div class="hero-stat">
                <div class="hero-stat-value">{{ total_products }}+</div>
                <div class="hero-stat-label">Digital Products</div>
            </div>
            <div class="hero-stat">
                <div class="hero-stat-value">{{ total_users }}+</div>
                <div class="hero-stat-label">Happy Customers</div>
            </div>
            <div class="hero-stat">
                <div class="hero-stat-value">{{ total_orders }}+</div>
                <div class="hero-stat-label">Orders Completed</div>
            </div>
            <div class="hero-stat">
                <div class="hero-stat-value">24/7</div>
                <div class="hero-stat-label">Support Available</div>
            </div>
        </div>
    </div>
</section>

<!-- Announcements -->
{% if announcements %}
<section class="section">
    <div class="container">
        {% for ann in announcements %}
        <div class="alert alert-{{ ann['type'] }} animate-in" style="margin-bottom:8px">
            <i class='bx {% if ann["type"]=="success" %}bx-check-circle{% elif ann["type"]=="warning" %}bx-error-circle{% elif ann["type"]=="danger" %}bx-error{% else %}bx-info-circle{% endif %}'></i>
            <strong>{{ ann['title'] }}</strong> - {{ ann['content'] }}
        </div>
        {% endfor %}
    </div>
</section>
{% endif %}

<!-- Categories Section -->
<section class="section">
    <div class="container">
        <div class="section-header">
            <h2 class="section-title">Browse <span class="gradient-text">Categories</span></h2>
            <a href="{{ url_for('categories') }}" class="btn-outline btn-sm">View All <i class='bx bx-right-arrow-alt'></i></a>
        </div>
        <div class="categories-grid">
            {% for cat in categories %}
            <a href="{{ url_for('marketplace', category=cat['slug']) }}" class="category-card">
                <div class="category-icon" style="background:{{ cat['color'] }}20;color:{{ cat['color'] }}">
                    <i class='bx {{ cat["icon"] }}'></i>
                </div>
                <div class="category-name">{{ cat['name'] }}</div>
                <div class="category-count">{{ cat['product_count'] }} products</div>
            </a>
            {% endfor %}
        </div>
    </div>
</section>

<!-- Featured Products -->
{% if featured_products %}
<section class="section">
    <div class="container">
        <div class="section-header">
            <h2 class="section-title"><span class="gradient-text">Featured</span> Products</h2>
            <a href="{{ url_for('marketplace') }}" class="btn-outline btn-sm">View All <i class='bx bx-right-arrow-alt'></i></a>
        </div>
        <div class="product-grid">
            {% for product in featured_products %}
            <div class="product-card" onclick="window.location='{{ url_for('product_detail', slug=product['slug']) }}'">
                <div class="product-image">
                    {% if product['discount_percent'] > 0 %}
                    <span class="product-badge badge-discount">-{{ product['discount_percent']|int }}%</span>
                    {% endif %}
                    {% if product['is_featured'] %}
                    <span class="product-badge badge-featured" style="{% if product['discount_percent'] > 0 %}left:auto;right:12px{% endif %}">Featured</span>
                    {% endif %}
                    <span style="font-size:60px">{{ product['image_url'] or '📦' }}</span>
                </div>
                <div class="product-info">
                    <div class="product-category">{{ product['category_name'] or 'Digital' }}</div>
                    <div class="product-title">{{ product['name'] }}</div>
                    <div class="product-desc">{{ product['short_description']|truncate_text(80) }}</div>
                    <div class="product-meta">
                        <div class="product-rating">
                            <i class='bx bxs-star'></i>
                            <span>{{ product['rating'] }}</span>
                        </div>
                        <span><i class='bx bx-shopping-bag'></i> {{ product['sold_count'] }} sold</span>
                    </div>
                    <div class="product-footer">
                        <div class="product-price">
                            <span class="price-current">{{ product['price']|currency }}</span>
                            {% if product['original_price'] > product['price'] %}
                            <span class="price-original">{{ product['original_price']|currency }}</span>
                            {% endif %}
                        </div>
                        <button class="product-add-cart" onclick="event.stopPropagation(); addToCart({{ product['id'] }})" title="Add to Cart">
                            <i class='bx bx-cart-add'></i>
                        </button>
                    </div>
                </div>
            </div>
            {% endfor %}
        </div>
    </div>
</section>
{% endif %}

<!-- Latest Products -->
{% if latest_products %}
<section class="section">
    <div class="container">
        <div class="section-header">
            <h2 class="section-title">Latest <span class="gradient-text">Products</span></h2>
            <a href="{{ url_for('marketplace', sort='newest') }}" class="btn-outline btn-sm">View All <i class='bx bx-right-arrow-alt'></i></a>
        </div>
        <div class="product-grid">
            {% for product in latest_products %}
            <div class="product-card" onclick="window.location='{{ url_for('product_detail', slug=product['slug']) }}'">
                <div class="product-image">
                    {% if product['discount_percent'] > 0 %}
                    <span class="product-badge badge-discount">-{{ product['discount_percent']|int }}%</span>
                    {% endif %}
                    <span class="product-badge badge-new">New</span>
                    <span style="font-size:60px">{{ product['image_url'] or '📦' }}</span>
                </div>
                <div class="product-info">
                    <div class="product-category">{{ product['category_name'] or 'Digital' }}</div>
                    <div class="product-title">{{ product['name'] }}</div>
                    <div class="product-meta">
                        <div class="product-rating">
                            <i class='bx bxs-star'></i>
                            <span>{{ product['rating'] }}</span>
                        </div>
                        <span><i class='bx bx-shopping-bag'></i> {{ product['sold_count'] }} sold</span>
                    </div>
                    <div class="product-footer">
                        <div class="product-price">
                            <span class="price-current">{{ product['price']|currency }}</span>
                            {% if product['original_price'] > product['price'] %}
                            <span class="price-original">{{ product['original_price']|currency }}</span>
                            {% endif %}
                        </div>
                        <button class="product-add-cart" onclick="event.stopPropagation(); addToCart({{ product['id'] }})" title="Add to Cart">
                            <i class='bx bx-cart-add'></i>
                        </button>
                    </div>
                </div>
            </div>
            {% endfor %}
        </div>
    </div>
</section>
{% endif %}

<!-- Features Section -->
<section class="section">
    <div class="container">
        <div class="section-header" style="justify-content:center">
            <h2 class="section-title text-center">Why Choose <span class="gradient-text">{{ settings.site_name }}</span>?</h2>
        </div>
        <div class="dashboard-grid" style="grid-template-columns:repeat(auto-fill,minmax(280px,1fr))">
            <div class="stat-card">
                <div class="stat-icon"><i class='bx bx-bolt'></i></div>
                <h3 style="margin-bottom:8px">Instant Delivery</h3>
                <p class="text-secondary" style="font-size:14px">Get your digital products delivered instantly after purchase. No waiting, no delays.</p>
            </div>
            <div class="stat-card purple">
                <div class="stat-icon"><i class='bx bx-shield-quarter'></i></div>
                <h3 style="margin-bottom:8px">100% Genuine</h3>
                <p class="text-secondary" style="font-size:14px">All products are genuine licenses with warranty. We guarantee authenticity.</p>
            </div>
            <div class="stat-card red">
                <div class="stat-icon"><i class='bx bx-support'></i></div>
                <h3 style="margin-bottom:8px">24/7 Support</h3>
                <p class="text-secondary" style="font-size:14px">Our dedicated support team is available round the clock to help you.</p>
            </div>
            <div class="stat-card green">
                <div class="stat-icon"><i class='bx bx-money'></i></div>
                <h3 style="margin-bottom:8px">Best Prices</h3>
                <p class="text-secondary" style="font-size:14px">Get the best deals on digital products. Regular discounts and offers available.</p>
            </div>
        </div>
    </div>
</section>
{% endblock %}

{% block extra_js %}
function addToCart(productId) {
    fetch('/cart/add', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({product_id: productId, quantity: 1})
    })
    .then(r => r.json())
    .then(data => {
        if (data.success) {
            showToast(data.message, 'success');
            // Update cart badge
            const badges = document.querySelectorAll('.nav-badge');
            if (data.cart_count) {
                badges.forEach(b => { b.textContent = data.cart_count; b.style.display = 'flex'; });
            }
        } else {
            showToast(data.message || 'Error adding to cart', 'error');
        }
    })
    .catch(() => showToast('Please login to add items to cart', 'warning'));
}
{% endblock %}
'''

# ============================================================
# OTHER PAGE TEMPLATES
# ============================================================

LOGIN_TEMPLATE = '''
{% extends base %}
{% block title %}Login - {{ settings.site_name }}{% endblock %}
{% block content %}
<div class="container-sm" style="padding-top:60px;padding-bottom:60px">
    <div class="glass-card" style="max-width:440px;margin:0 auto">
        <div class="text-center mb-3">
            <div style="width:60px;height:60px;background:var(--gradient-primary);border-radius:16px;display:flex;align-items:center;justify-content:center;font-size:28px;color:#000;font-weight:900;margin:0 auto 16px">S</div>
            <h2 style="font-size:24px;margin-bottom:8px">Welcome Back</h2>
            <p class="text-secondary">Login to your {{ settings.site_name }} account</p>
        </div>
        <form method="POST" action="{{ url_for('login') }}">
            <div class="form-group">
                <label><i class='bx bx-user'></i> Username or Email</label>
                <div class="input-icon">
                    <i class='bx bx-user'></i>
                    <input type="text" name="username" class="form-input" placeholder="Enter your username or email" required>
                </div>
            </div>
            <div class="form-group">
                <label><i class='bx bx-lock'></i> Password</label>
                <div class="input-icon">
                    <i class='bx bx-lock'></i>
                    <input type="password" name="password" class="form-input" placeholder="Enter your password" required>
                </div>
            </div>
            <div class="d-flex justify-between align-center mb-3" style="font-size:14px">
                <label style="display:flex;align-items:center;gap:8px;cursor:pointer;color:var(--text-secondary)">
                    <input type="checkbox" name="remember" style="accent-color:var(--primary)"> Remember me
                </label>
            </div>
            <button type="submit" class="btn-neon w-100 btn-lg">
                <i class='bx bx-log-in'></i> Login
            </button>
        </form>
        <div class="text-center mt-3">
            <p class="text-secondary" style="font-size:14px">Don't have an account? <a href="{{ url_for('register') }}">Register now</a></p>
        </div>
    </div>
</div>
{% endblock %}
'''

REGISTER_TEMPLATE = r'''
{% extends base %}
{% block title %}Signup - {{ settings.site_name }}{% endblock %}
{% block content %}
<div class="container-sm" style="padding-top:40px;padding-bottom:60px">
 <div class="glass-card" style="max-width:480px;margin:0 auto">
  <div class="text-center mb-3"><div class="brand-mark">A</div><h2>Create Account</h2><p class="text-secondary">Join {{ settings.site_name }}</p></div>
  <form method="POST">
   <div class="form-group"><label>Full Name</label><input type="text" name="full_name" class="form-input" required></div>
   <div class="form-group"><label>Telegram username</label><input type="text" name="telegram_username" class="form-input" placeholder="@username" required></div>
   <div class="form-group"><label>Email</label><input type="email" name="email" class="form-input" required></div>
   <div class="form-group"><label>Phone</label><input type="text" name="phone" class="form-input" required></div>
   <div class="form-group"><label>Password</label><input type="password" name="password" class="form-input" required minlength="6"></div>
   <div class="form-group"><label>Confirm Password</label><input type="password" name="confirm_password" class="form-input" required></div>
   <button type="submit" class="btn-neon w-100 btn-lg"><i class="bx bx-user-plus"></i> Signup</button>
  </form>
  <div class="text-center mt-3"><p class="text-secondary">Already have an account? <a href="{{ url_for('login') }}">Login</a></p></div>
 </div>
</div>
{% endblock %}
''' 

DASHBOARD_TEMPLATE = '''
{% extends base %}
{% block title %}Dashboard - {{ settings.site_name }}{% endblock %}
{% block content %}
<div class="container">
    <div class="page-header">
        <h1>Dashboard</h1>
        <p>Welcome back, {{ current_user['full_name'] or current_user['username'] }}!</p>
    </div>

    <!-- Stats -->
    <div class="dashboard-grid">
        <div class="stat-card">
            <div class="stat-icon"><i class='bx bx-wallet'></i></div>
            <div class="stat-value">{{ current_user['wallet_balance']|currency }}</div>
            <div class="stat-label">Wallet Balance</div>
        </div>
        <div class="stat-card purple">
            <div class="stat-icon"><i class='bx bx-package'></i></div>
            <div class="stat-value">{{ order_count }}</div>
            <div class="stat-label">Total Orders</div>
        </div>
        <div class="stat-card green">
            <div class="stat-icon"><i class='bx bx-check-circle'></i></div>
            <div class="stat-value">{{ completed_orders }}</div>
            <div class="stat-label">Completed Orders</div>
        </div>
        <div class="stat-card red">
            <div class="stat-icon"><i class='bx bx-cart'></i></div>
            <div class="stat-value">{{ cart_count }}</div>
            <div class="stat-label">Items in Cart</div>
        </div>
    </div>

    <!-- Quick Actions -->
    <div class="section">
        <h3 style="margin-bottom:16px">Quick Actions</h3>
        <div class="dashboard-grid" style="grid-template-columns:repeat(auto-fill,minmax(200px,1fr))">
            <a href="{{ url_for('wallet') }}" class="glass-card text-center" style="text-decoration:none">
                <i class='bx bx-wallet' style="font-size:32px;color:var(--primary);display:block;margin-bottom:8px"></i>
                <span class="fw-semibold">My Wallet</span>
            </a>
            <a href="{{ url_for('deposit') }}" class="glass-card text-center" style="text-decoration:none">
                <i class='bx bx-plus-circle' style="font-size:32px;color:var(--green);display:block;margin-bottom:8px"></i>
                <span class="fw-semibold">Deposit</span>
            </a>
            <a href="{{ url_for('orders') }}" class="glass-card text-center" style="text-decoration:none">
                <i class='bx bx-package' style="font-size:32px;color:var(--purple);display:block;margin-bottom:8px"></i>
                <span class="fw-semibold">My Orders</span>
            </a>
            <a href="{{ url_for('marketplace') }}" class="glass-card text-center" style="text-decoration:none">
                <i class='bx bx-store' style="font-size:32px;color:var(--primary-blue);display:block;margin-bottom:8px"></i>
                <span class="fw-semibold">Marketplace</span>
            </a>
            <a href="{{ url_for('support') }}" class="glass-card text-center" style="text-decoration:none">
                <i class='bx bx-support' style="font-size:32px;color:var(--yellow);display:block;margin-bottom:8px"></i>
                <span class="fw-semibold">Support</span>
            </a>
            <a href="{{ url_for('profile') }}" class="glass-card text-center" style="text-decoration:none">
                <i class='bx bx-user' style="font-size:32px;color:var(--red);display:block;margin-bottom:8px"></i>
                <span class="fw-semibold">Profile</span>
            </a>
        </div>
    </div>

    <!-- Recent Orders -->
    {% if recent_orders %}
    <div class="section">
        <div class="section-header">
            <h3>Recent Orders</h3>
            <a href="{{ url_for('orders') }}" class="btn-outline btn-sm">View All</a>
        </div>
        <div class="table-container glass-card" style="padding:0">
            <table class="data-table">
                <thead>
                    <tr>
                        <th>Order ID</th>
                        <th>Items</th>
                        <th>Total</th>
                        <th>Status</th>
                        <th>Date</th>
                    </tr>
                </thead>
                <tbody>
                    {% for order in recent_orders %}
                    <tr>
                        <td><span class="fw-semibold text-primary">{{ order['order_id'] }}</span></td>
                        <td>{{ order['item_count'] }} item(s)</td>
                        <td class="fw-bold">{{ order['total_amount']|currency }}</td>
                        <td><span class="status-badge status-{{ order['order_status'] }}">{{ order['order_status']|title }}</span></td>
                        <td>{{ order['created_at']|timeago }}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
    {% endif %}

    <!-- Notifications -->
    {% if recent_notifications %}
    <div class="section">
        <div class="section-header">
            <h3>Recent Notifications</h3>
            <a href="{{ url_for('notifications') }}" class="btn-outline btn-sm">View All</a>
        </div>
        <div style="display:flex;flex-direction:column;gap:8px">
            {% for notif in recent_notifications %}
            <div class="glass-card" style="padding:16px;display:flex;align-items:center;gap:12px">
                <div style="width:40px;height:40px;border-radius:12px;display:flex;align-items:center;justify-content:center;background:{% if notif['type']=='success' %}rgba(46,204,113,0.1){% elif notif['type']=='warning' %}rgba(245,158,11,0.1){% elif notif['type']=='error' %}rgba(255,8,68,0.1){% else %}rgba(0,242,254,0.1){% endif %};color:{% if notif['type']=='success' %}var(--green){% elif notif['type']=='warning' %}var(--yellow){% elif notif['type']=='error' %}var(--red){% else %}var(--primary){% endif %}">
                    <i class='bx {% if notif["type"]=="success" %}bx-check-circle{% elif notif["type"]=="warning" %}bx-error-circle{% elif notif["type"]=="error" %}bx-error{% else %}bx-info-circle{% endif %}'></i>
                </div>
                <div style="flex:1">
                    <div class="fw-semibold" style="font-size:14px">{{ notif['title'] }}</div>
                    <div class="text-muted" style="font-size:13px">{{ notif['message']|truncate_text(100) }}</div>
                </div>
                <span class="text-muted" style="font-size:12px">{{ notif['created_at']|timeago }}</span>
            </div>
            {% endfor %}
        </div>
    </div>
    {% endif %}
</div>
{% endblock %}
'''

PROFILE_TEMPLATE = '''
{% extends base %}
{% block title %}Profile - {{ settings.site_name }}{% endblock %}
{% block content %}
<div class="container">
    <div class="page-header">
        <h1>My Profile</h1>
        <p>Manage your account settings</p>
    </div>

    <div class="sidebar-layout">
        <aside class="sidebar">
            <ul class="sidebar-menu">
                <li><a href="{{ url_for('dashboard') }}"><i class='bx bx-grid-alt'></i> Dashboard</a></li>
                <li><a href="{{ url_for('profile') }}" class="active"><i class='bx bx-user'></i> Profile</a></li>
                <li><a href="{{ url_for('wallet') }}"><i class='bx bx-wallet'></i> Wallet</a></li>
                <li><a href="{{ url_for('deposit') }}"><i class='bx bx-plus-circle'></i> Deposit</a></li>
                <li><a href="{{ url_for('orders') }}"><i class='bx bx-package'></i> Orders</a></li>
                <li><a href="{{ url_for('downloads') }}"><i class='bx bx-download'></i> Downloads</a></li>
                <li><a href="{{ url_for('wishlist_view') }}"><i class='bx bx-heart'></i> Wishlist</a></li>
                <li><a href="{{ url_for('notifications') }}"><i class='bx bx-bell'></i> Notifications</a></li>
                <li><a href="{{ url_for('support') }}"><i class='bx bx-support'></i> Support</a></li>
            </ul>
        </aside>

        <div>
            <div class="glass-card mb-3">
                <h3 style="margin-bottom:20px">Profile Information</h3>
                <form method="POST" action="{{ url_for('profile') }}">
                    <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px">
                        <div class="form-group">
                            <label>Full Name</label>
                            <input type="text" name="full_name" class="form-input" value="{{ current_user['full_name'] }}">
                        </div>
                        <div class="form-group">
                            <label>Username</label>
                            <input type="text" class="form-input" value="{{ current_user['username'] }}" disabled>
                        </div>
                        <div class="form-group">
                            <label>Email</label>
                            <input type="email" class="form-input" value="{{ current_user['email'] }}" disabled>
                        </div>
                        <div class="form-group">
                            <label>Phone</label>
                            <input type="text" name="phone" class="form-input" value="{{ current_user['phone'] }}">
                        </div>
                        <div class="form-group">
                            <label>City</label>
                            <input type="text" name="city" class="form-input" value="{{ current_user['city'] }}">
                        </div>
                        <div class="form-group">
                            <label>Country</label>
                            <input type="text" name="country" class="form-input" value="{{ current_user['country'] }}">
                        </div>
                    </div>
                    <div class="form-group">
                        <label>Address</label>
                        <textarea name="address" class="form-input" rows="3">{{ current_user['address'] }}</textarea>
                    </div>
                    <div class="form-group">
                        <label>Bio</label>
                        <textarea name="bio" class="form-input" rows="3">{{ current_user['bio'] }}</textarea>
                    </div>
                    <button type="submit" class="btn-neon"><i class='bx bx-save'></i> Update Profile</button>
                </form>
            </div>

            <div class="glass-card mb-3">
                <h3 style="margin-bottom:20px">Change Password</h3>
                <form method="POST" action="{{ url_for('change_password') }}">
                    <div class="form-group">
                        <label>Current Password</label>
                        <input type="password" name="current_password" class="form-input" required>
                    </div>
                    <div class="form-group">
                        <label>New Password</label>
                        <input type="password" name="new_password" class="form-input" required minlength="6">
                    </div>
                    <div class="form-group">
                        <label>Confirm New Password</label>
                        <input type="password" name="confirm_password" class="form-input" required>
                    </div>
                    <button type="submit" class="btn-neon-purple"><i class='bx bx-lock'></i> Change Password</button>
                </form>
            </div>

            <div class="glass-card">
                <h3 style="margin-bottom:20px">Referral Program</h3>
                <p class="text-secondary mb-2" style="font-size:14px">Share your referral code with friends. When they make their first purchase, you both earn rewards!</p>
                <div class="d-flex align-center gap-2">
                    <input type="text" class="form-input" value="{{ current_user['referral_code'] or 'N/A' }}" readonly>
                    <button class="copy-btn" onclick="copyText('{{ current_user['referral_code'] or '' }}')"><i class='bx bx-copy'></i> Copy</button>
                </div>
                <p class="text-muted mt-1" style="font-size:13px">Referral Bonus: {{ settings.currency_symbol }}{{ referral_bonus }} per successful referral</p>
            </div>
        </div>
    </div>
</div>
{% endblock %}
'''

WALLET_TEMPLATE = '''
{% extends base %}
{% block title %}Wallet - {{ settings.site_name }}{% endblock %}
{% block content %}
<div class="container">
    <div class="page-header">
        <h1>My Wallet</h1>
        <p>Manage your balance and transactions</p>
    </div>

    <div class="sidebar-layout">
        <aside class="sidebar">
            <ul class="sidebar-menu">
                <li><a href="{{ url_for('dashboard') }}"><i class='bx bx-grid-alt'></i> Dashboard</a></li>
                <li><a href="{{ url_for('profile') }}"><i class='bx bx-user'></i> Profile</a></li>
                <li><a href="{{ url_for('wallet') }}" class="active"><i class='bx bx-wallet'></i> Wallet</a></li>
                <li><a href="{{ url_for('deposit') }}"><i class='bx bx-plus-circle'></i> Deposit</a></li>
                <li><a href="{{ url_for('orders') }}"><i class='bx bx-package'></i> Orders</a></li>
                <li><a href="{{ url_for('downloads') }}"><i class='bx bx-download'></i> Downloads</a></li>
                <li><a href="{{ url_for('wishlist_view') }}"><i class='bx bx-heart'></i> Wishlist</a></li>
                <li><a href="{{ url_for('notifications') }}"><i class='bx bx-bell'></i> Notifications</a></li>
                <li><a href="{{ url_for('support') }}"><i class='bx bx-support'></i> Support</a></li>
            </ul>
        </aside>

        <div>
            <!-- Balance Card -->
            <div class="glass-card mb-3" style="background:linear-gradient(135deg,rgba(0,242,254,0.15),rgba(168,85,247,0.15));border-color:rgba(0,242,254,0.2)">
                <div class="d-flex justify-between align-center flex-wrap gap-2">
                    <div>
                        <p class="text-secondary mb-1">Available Balance</p>
                        <h1 style="font-size:36px;background:var(--gradient-primary);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text">{{ current_user['wallet_balance']|currency }}</h1>
                    </div>
                    <a href="{{ url_for('deposit') }}" class="btn-neon"><i class='bx bx-plus'></i> Add Funds</a>
                </div>
            </div>

            <!-- Transactions -->
            <div class="glass-card">
                <div class="section-header">
                    <h3>Transaction History</h3>
                </div>
                {% if transactions %}
                <div class="table-container" style="border:none">
                    <table class="data-table">
                        <thead>
                            <tr>
                                <th>Type</th>
                                <th>Description</th>
                                <th>Amount</th>
                                <th>Balance</th>
                                <th>Date</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for txn in transactions %}
                            <tr>
                                <td>
                                    <span class="status-badge {% if txn['type']=='credit' %}status-approved{% else %}status-rejected{% endif %}">
                                        {{ txn['type']|title }}
                                    </span>
                                </td>
                                <td>{{ txn['description'] }}</td>
                                <td class="fw-bold {% if txn['type']=='credit' %}text-green{% else %}text-red{% endif %}">
                                    {% if txn['type']=='credit' %}+{% else %}-{% endif %}{{ txn['amount']|currency }}
                                </td>
                                <td>{{ txn['balance_after']|currency }}</td>
                                <td>{{ txn['created_at']|timeago }}</td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
                {% else %}
                <div class="empty-state">
                    <i class='bx bx-receipt'></i>
                    <h3>No Transactions Yet</h3>
                    <p>Your transaction history will appear here</p>
                </div>
                {% endif %}
            </div>
        </div>
    </div>
</div>
{% endblock %}
'''

DEPOSIT_TEMPLATE = '''
{% extends base %}
{% block title %}Deposit - {{ settings.site_name }}{% endblock %}
{% block content %}
<div class="container">
    <div class="page-header">
        <h1>Deposit Funds</h1>
        <p>Add money to your wallet balance</p>
    </div>

    <div class="sidebar-layout">
        <aside class="sidebar">
            <ul class="sidebar-menu">
                <li><a href="{{ url_for('dashboard') }}"><i class='bx bx-grid-alt'></i> Dashboard</a></li>
                <li><a href="{{ url_for('profile') }}"><i class='bx bx-user'></i> Profile</a></li>
                <li><a href="{{ url_for('wallet') }}"><i class='bx bx-wallet'></i> Wallet</a></li>
                <li><a href="{{ url_for('deposit') }}" class="active"><i class='bx bx-plus-circle'></i> Deposit</a></li>
                <li><a href="{{ url_for('orders') }}"><i class='bx bx-package'></i> Orders</a></li>
                <li><a href="{{ url_for('downloads') }}"><i class='bx bx-download'></i> Downloads</a></li>
                <li><a href="{{ url_for('wishlist_view') }}"><i class='bx bx-heart'></i> Wishlist</a></li>
                <li><a href="{{ url_for('notifications') }}"><i class='bx bx-bell'></i> Notifications</a></li>
                <li><a href="{{ url_for('support') }}"><i class='bx bx-support'></i> Support</a></li>
            </ul>
        </aside>

        <div>
            <!-- Deposit Form -->
            <div class="glass-card mb-3">
                <h3 style="margin-bottom:20px">New Deposit Request</h3>

                <!-- Payment Method Tabs -->
                <div class="tabs" id="paymentTabs">
                    <button class="tab-btn active" onclick="selectMethod('bkash')">bKash</button>
                    <button class="tab-btn" onclick="selectMethod('nagad')">Nagad</button>
                    <button class="tab-btn" onclick="selectMethod('crypto')">Crypto/BEP20</button>
                </div>

                <!-- bKash Info -->
                <div id="bkash-info" class="alert alert-info mb-2">
                    <i class='bx bx-info-circle'></i>
                    <div>
                        <strong>Send money to:</strong> {{ bkash_number }}<br>
                        <small>Minimum: {{ settings.currency_symbol }}50 | Maximum: {{ settings.currency_symbol }}100,000</small>
                    </div>
                    <button class="copy-btn ms-1" onclick="copyText('{{ bkash_number }}')"><i class='bx bx-copy'></i></button>
                </div>

                <!-- Nagad Info -->
                <div id="nagad-info" class="alert alert-info mb-2" style="display:none">
                    <i class='bx bx-info-circle'></i>
                    <div>
                        <strong>Send money to:</strong> {{ nagad_number }}<br>
                        <small>Minimum: {{ settings.currency_symbol }}50 | Maximum: {{ settings.currency_symbol }}100,000</small>
                    </div>
                    <button class="copy-btn ms-1" onclick="copyText('{{ nagad_number }}')"><i class='bx bx-copy'></i></button>
                </div>

                <!-- Crypto Info -->
                <div id="crypto-info" class="alert alert-info mb-2" style="display:none">
                    <i class='bx bx-info-circle'></i>
                    <div>
                        <strong>Send to BEP20 Address:</strong><br>
                        <small style="word-break:break-all">{{ crypto_address }}</small>
                    </div>
                    <button class="copy-btn ms-1" onclick="copyText('{{ crypto_address }}')"><i class='bx bx-copy'></i></button>
                </div>

                <form method="POST" action="{{ url_for('deposit') }}">
                    <input type="hidden" name="method" id="depositMethod" value="bkash">
                    <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px">
                        <div class="form-group">
                            <label>Amount ({{ settings.currency_symbol }})</label>
                            <input type="number" name="amount" class="form-input" placeholder="Enter amount" min="50" max="100000" required>
                        </div>
                        <div class="form-group">
                            <label>Transaction ID</label>
                            <input type="text" name="transaction_id" class="form-input" placeholder="Enter transaction ID" required>
                        </div>
                    </div>
                    <div class="form-group">
                        <label>Your Sender Number</label>
                        <input type="text" name="sender_number" class="form-input" placeholder="Enter your sending number" required>
                    </div>
                    <button type="submit" class="btn-neon btn-lg"><i class='bx bx-send'></i> Submit Deposit Request</button>
                </form>
            </div>

            <!-- Deposit History -->
            <div class="glass-card">
                <h3 style="margin-bottom:20px">Deposit History</h3>
                {% if deposits %}
                <div class="table-container" style="border:none">
                    <table class="data-table">
                        <thead>
                            <tr>
                                <th>ID</th>
                                <th>Amount</th>
                                <th>Method</th>
                                <th>TXN ID</th>
                                <th>Status</th>
                                <th>Date</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for dep in deposits %}
                            <tr>
                                <td>#{{ dep['id'] }}</td>
                                <td class="fw-bold">{{ dep['amount']|currency }}</td>
                                <td>{{ dep['method']|title }}</td>
                                <td><span class="text-muted">{{ dep['transaction_id'] }}</span></td>
                                <td><span class="status-badge status-{{ dep['status'] }}">{{ dep['status']|title }}</span></td>
                                <td>{{ dep['created_at']|timeago }}</td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
                {% else %}
                <div class="empty-state">
                    <i class='bx bx-receipt'></i>
                    <h3>No Deposits Yet</h3>
                    <p>Your deposit history will appear here</p>
                </div>
                {% endif %}
            </div>
        </div>
    </div>
</div>
{% endblock %}

{% block extra_js %}
function selectMethod(method) {
    document.getElementById('depositMethod').value = method;
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    event.target.classList.add('active');
    document.getElementById('bkash-info').style.display = method === 'bkash' ? 'flex' : 'none';
    document.getElementById('nagad-info').style.display = method === 'nagad' ? 'flex' : 'none';
    document.getElementById('crypto-info').style.display = method === 'crypto' ? 'flex' : 'none';
}
{% endblock %}
'''

MARKETPLACE_TEMPLATE = '''
{% extends base %}
{% block title %}Marketplace - {{ settings.site_name }}{% endblock %}
{% block content %}
<div class="container">
    <div class="page-header">
        <h1>Marketplace</h1>
        <p>Browse our collection of premium digital products</p>
    </div>

    <!-- Search and Filters -->
    <div class="glass-card mb-3" style="padding:16px">
        <form method="GET" action="{{ url_for('marketplace') }}">
            <div style="display:flex;gap:12px;flex-wrap:wrap;align-items:center">
                <div class="search-bar" style="flex:1;min-width:200px">
                    <i class='bx bx-search'></i>
                    <input type="text" name="q" placeholder="Search products..." value="{{ request.args.get('q', '') }}">
                </div>
                <select name="category" class="form-input" style="width:auto;min-width:150px" onchange="this.form.submit()">
                    <option value="">All Categories</option>
                    {% for cat in all_categories %}
                    <option value="{{ cat['slug'] }}" {% if request.args.get('category') == cat['slug'] %}selected{% endif %}>{{ cat['name'] }}</option>
                    {% endfor %}
                </select>
                <select name="sort" class="form-input" style="width:auto;min-width:150px" onchange="this.form.submit()">
                    <option value="newest" {% if request.args.get('sort') == 'newest' %}selected{% endif %}>Newest First</option>
                    <option value="price_low" {% if request.args.get('sort') == 'price_low' %}selected{% endif %}>Price: Low to High</option>
                    <option value="price_high" {% if request.args.get('sort') == 'price_high' %}selected{% endif %}>Price: High to Low</option>
                    <option value="popular" {% if request.args.get('sort') == 'popular' %}selected{% endif %}>Most Popular</option>
                    <option value="rating" {% if request.args.get('sort') == 'rating' %}selected{% endif %}>Top Rated</option>
                </select>
                <select name="price_range" class="form-input" style="width:auto;min-width:140px" onchange="this.form.submit()">
                    <option value="">Any Price</option>
                    <option value="0-500" {% if request.args.get('price_range') == '0-500' %}selected{% endif %}>Under ৳500</option>
                    <option value="500-1000" {% if request.args.get('price_range') == '500-1000' %}selected{% endif %}>৳500 - ৳1000</option>
                    <option value="1000-5000" {% if request.args.get('price_range') == '1000-5000' %}selected{% endif %}>৳1000 - ৳5000</option>
                    <option value="5000-999999" {% if request.args.get('price_range') == '5000-999999' %}selected{% endif %}>৳5000+</option>
                </select>
                <button type="submit" class="btn-neon btn-sm"><i class='bx bx-search'></i> Search</button>
            </div>
        </form>
    </div>

    <!-- Active Filters -->
    {% if request.args.get('q') or request.args.get('category') or request.args.get('price_range') %}
    <div class="d-flex gap-1 flex-wrap mb-2">
        {% if request.args.get('q') %}
        <span class="status-badge status-processing">Search: {{ request.args.get('q') }}</span>
        {% endif %}
        {% if request.args.get('category') %}
        <span class="status-badge status-processing">Category: {{ request.args.get('category') }}</span>
        {% endif %}
        <a href="{{ url_for('marketplace') }}" class="status-badge status-rejected" style="cursor:pointer">Clear All</a>
    </div>
    {% endif %}

    <!-- Products Grid -->
    {% if products %}
    <div class="product-grid">
        {% for product in products %}
        <div class="product-card" onclick="window.location='{{ url_for('product_detail', slug=product['slug']) }}'">
            <div class="product-image">
                {% if product['discount_percent'] > 0 %}
                <span class="product-badge badge-discount">-{{ product['discount_percent']|int }}%</span>
                {% endif %}
                {% if product['is_featured'] %}
                <span class="product-badge badge-featured" style="{% if product['discount_percent'] > 0 %}left:auto;right:12px{% endif %}">Featured</span>
                {% endif %}
                <span style="font-size:60px">{{ product['image_url'] or '📦' }}</span>
                {% if current_user %}
                <button class="product-wishlist {% if product['id'] in wishlist_ids %}active{% endif %}" onclick="event.stopPropagation(); toggleWishlist({{ product['id'] }})" title="Add to Wishlist">
                    <i class='bx {% if product["id"] in wishlist_ids %}bxs-heart{% else %}bx-heart{% endif %}'></i>
                </button>
                {% endif %}
            </div>
            <div class="product-info">
                <div class="product-category">{{ product['category_name'] or 'Digital' }}</div>
                <div class="product-title">{{ product['name'] }}</div>
                <div class="product-desc">{{ product['short_description']|truncate_text(80) }}</div>
                <div class="product-meta">
                    <div class="product-rating">
                        <i class='bx bxs-star'></i>
                        <span>{{ product['rating'] }}</span>
                    </div>
                    <span><i class='bx bx-shopping-bag'></i> {{ product['sold_count'] }} sold</span>
                </div>
                <div class="product-footer">
                    <div class="product-price">
                        <span class="price-current">{{ product['price']|currency }}</span>
                        {% if product['original_price'] > product['price'] %}
                        <span class="price-original">{{ product['original_price']|currency }}</span>
                        {% endif %}
                    </div>
                    <button class="product-add-cart" onclick="event.stopPropagation(); addToCart({{ product['id'] }})" title="Add to Cart">
                        <i class='bx bx-cart-add'></i>
                    </button>
                </div>
            </div>
        </div>
        {% endfor %}
    </div>

    <!-- Pagination -->
    {% if total_pages > 1 %}
    <div class="pagination">
        {% if page > 1 %}
        <a href="{{ url_for('marketplace', page=page-1, **request.args) }}" class="page-btn"><i class='bx bx-chevron-left'></i></a>
        {% endif %}
        {% for p in range(1, total_pages + 1) %}
        {% if p == page %}
        <span class="page-btn active">{{ p }}</span>
        {% elif p <= 3 or p >= total_pages - 2 or (p >= page - 1 and p <= page + 1) %}
        <a href="{{ url_for('marketplace', page=p, **request.args) }}" class="page-btn">{{ p }}</a>
        {% elif p == 4 or p == total_pages - 3 %}
        <span class="page-btn">...</span>
        {% endif %}
        {% endfor %}
        {% if page < total_pages %}
        <a href="{{ url_for('marketplace', page=page+1, **request.args) }}" class="page-btn"><i class='bx bx-chevron-right'></i></a>
        {% endif %}
    </div>
    {% endif %}

    {% else %}
    <div class="empty-state">
        <i class='bx bx-package'></i>
        <h3>No Products Found</h3>
        <p>Try adjusting your search or filter criteria</p>
        <a href="{{ url_for('marketplace') }}" class="btn-neon">View All Products</a>
    </div>
    {% endif %}
</div>
{% endblock %}

{% block extra_js %}
function addToCart(productId) {
    fetch('/cart/add', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({product_id: productId, quantity: 1})
    })
    .then(r => r.json())
    .then(data => {
        if (data.success) {
            showToast(data.message, 'success');
        } else {
            showToast(data.message || 'Error', 'error');
        }
    })
    .catch(() => showToast('Please login first', 'warning'));
}

function toggleWishlist(productId) {
    fetch('/wishlist/toggle', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({product_id: productId})
    })
    .then(r => r.json())
    .then(data => {
        showToast(data.message, data.success ? 'success' : 'error');
        if (data.success) location.reload();
    });
}
{% endblock %}
'''

PRODUCT_DETAIL_TEMPLATE = '''
{% extends base %}
{% block title %}{{ product['name'] }} - {{ settings.site_name }}{% endblock %}
{% block content %}
<div class="container">
    <div class="breadcrumb">
        <a href="{{ url_for('home') }}">Home</a>
        <i class='bx bx-chevron-right'></i>
        <a href="{{ url_for('marketplace') }}">Marketplace</a>
        <i class='bx bx-chevron-right'></i>
        {% if product['category_name'] %}<a href="{{ url_for('marketplace', category=product['category_slug']) }}">{{ product['category_name'] }}</a><i class='bx bx-chevron-right'></i>{% endif %}
        <span>{{ product['name'] }}</span>
    </div>

    <div style="display:grid;grid-template-columns:1fr 1fr;gap:32px;padding:20px 0" class="product-detail-grid">
        <!-- Product Image -->
        <div class="glass-card" style="text-align:center;padding:60px">
            {% if product['discount_percent'] > 0 %}
            <span class="product-badge badge-discount" style="position:static;display:inline-block;margin-bottom:16px">-{{ product['discount_percent']|int }}%</span>
            {% endif %}
            <div style="font-size:120px;padding:40px 0">{{ product['image_url'] or '📦' }}</div>
        </div>

        <!-- Product Info -->
        <div>
            {% if product['category_name'] %}
            <span class="product-category" style="display:inline-block;margin-bottom:12px">{{ product['category_name'] }}</span>
            {% endif %}

            <h1 style="font-size:28px;margin-bottom:12px">{{ product['name'] }}</h1>

            <div class="d-flex align-center gap-3 mb-2">
                <div class="product-rating" style="font-size:16px">
                    {% for i in range(5) %}
                    <i class='bx {% if i < product["rating"]|int %}bxs-star{% elif i < product["rating"] %}bxs-star-half{% else %}bx-star{% endif %}' style="color:#f59e0b"></i>
                    {% endfor %}
                    <span style="margin-left:8px;color:var(--text-secondary)">{{ product['rating'] }} ({{ product['review_count'] }} reviews)</span>
                </div>
                <span class="text-muted">|</span>
                <span class="text-muted"><i class='bx bx-shopping-bag'></i> {{ product['sold_count'] }} sold</span>
            </div>

            <!-- Price -->
            <div class="glass-card mb-3" style="padding:20px;display:flex;align-items:baseline;gap:12px">
                <span style="font-size:36px;font-weight:900;background:var(--gradient-primary);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text">{{ product['price']|currency }}</span>
                {% if product['original_price'] > product['price'] %}
                <span style="font-size:18px;color:var(--text-muted);text-decoration:line-through">{{ product['original_price']|currency }}</span>
                <span class="status-badge status-rejected">Save {{ ((product['original_price'] - product['price']) / product['original_price'] * 100)|int }}%</span>
                {% endif %}
            </div>

            <!-- Short Description -->
            {% if product['short_description'] %}
            <p class="text-secondary mb-3" style="font-size:15px;line-height:1.7">{{ product['short_description'] }}</p>
            {% endif %}

            <!-- Stock Status -->
            <div class="mb-3">
                {% if product['stock_quantity'] > 0 or product['stock_quantity'] == -1 %}
                <span class="status-badge status-approved"><i class='bx bx-check-circle'></i> In Stock</span>
                {% else %}
                <span class="status-badge status-rejected"><i class='bx bx-x-circle'></i> Out of Stock</span>
                {% endif %}
                <span class="status-badge status-processing" style="margin-left:8px"><i class='bx bx-bolt'></i> Instant Delivery</span>
            </div>

            <!-- Add to Cart -->
            <div class="d-flex gap-2 mb-3">
                {% if product['stock_quantity'] > 0 or product['stock_quantity'] == -1 %}
                <div style="display:flex;align-items:center;gap:8px">
                    <button class="btn-outline btn-sm" onclick="updateQty(-1)" style="width:40px;height:40px;padding:0"><i class='bx bx-minus'></i></button>
                    <input type="number" id="qty" value="1" min="1" max="99" class="form-input" style="width:60px;text-align:center;padding:8px">
                    <button class="btn-outline btn-sm" onclick="updateQty(1)" style="width:40px;height:40px;padding:0"><i class='bx bx-plus'></i></button>
                </div>
                <button class="btn-neon btn-lg" onclick="addToCartDetail({{ product['id'] }})" style="flex:1">
                    <i class='bx bx-cart-add'></i> Add to Cart
                </button>
                {% if current_user %}
                <button class="btn-outline btn-lg" onclick="toggleWishlist({{ product['id'] }})">
                    <i class='bx bx-heart'></i>
                </button>
                {% endif %}
                {% else %}
                <button class="btn-neon btn-lg" disabled style="flex:1;opacity:0.5"><i class='bx bx-x'></i> Out of Stock</button>
                {% endif %}
            </div>

            <!-- Product Features -->
            <div class="glass-card" style="padding:16px">
                <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px">
                    <div class="d-flex align-center gap-1"><i class='bx bx-check-circle text-green'></i> <span>Genuine License</span></div>
                    <div class="d-flex align-center gap-1"><i class='bx bx-check-circle text-green'></i> <span>Instant Delivery</span></div>
                    <div class="d-flex align-center gap-1"><i class='bx bx-check-circle text-green'></i> <span>Lifetime Access</span></div>
                    <div class="d-flex align-center gap-1"><i class='bx bx-check-circle text-green'></i> <span>24/7 Support</span></div>
                </div>
            </div>
        </div>
    </div>

    <!-- Description -->
    <div class="glass-card mb-3">
        <div class="tabs">
            <button class="tab-btn active" onclick="showTab('description')">Description</button>
            <button class="tab-btn" onclick="showTab('reviews')">Reviews ({{ product['review_count'] }})</button>
        </div>

        <div id="tab-description">
            <div style="line-height:1.8;color:var(--text-secondary);font-size:15px;white-space:pre-wrap">{{ product['description'] }}</div>
        </div>

        <div id="tab-reviews" style="display:none">
            <!-- Review Form -->
            {% if current_user %}
            <div class="glass-card mb-3" style="background:rgba(255,255,255,0.03)">
                <h4 style="margin-bottom:16px">Write a Review</h4>
                <form method="POST" action="{{ url_for('add_review', product_id=product['id']) }}">
                    <div class="form-group">
                        <label>Rating</label>
                        <div class="d-flex gap-1" id="ratingStars">
                            {% for i in range(1,6) %}
                            <i class='bx bx-star' style="font-size:28px;cursor:pointer;color:var(--text-muted)" onclick="setRating({{ i }})" onmouseover="hoverRating({{ i }})" onmouseout="resetRating()"></i>
                            {% endfor %}
                            <input type="hidden" name="rating" id="ratingInput" value="5">
                        </div>
                    </div>
                    <div class="form-group">
                        <label>Your Review</label>
                        <textarea name="comment" class="form-input" placeholder="Share your experience..." rows="3"></textarea>
                    </div>
                    <button type="submit" class="btn-neon btn-sm"><i class='bx bx-send'></i> Submit Review</button>
                </form>
            </div>
            {% endif %}

            <!-- Reviews List -->
            {% if reviews %}
            {% for review in reviews %}
            <div class="glass-card mb-2" style="padding:16px">
                <div class="d-flex align-center gap-2 mb-1">
                    <div class="nav-user-avatar" style="width:36px;height:36px;font-size:14px">{{ review['username'][0]|upper }}</div>
                    <div>
                        <div class="fw-semibold" style="font-size:14px">{{ review['username'] }}</div>
                        <div class="d-flex gap-1">
                            {% for i in range(5) %}
                            <i class='bx {% if i < review["rating"] %}bxs-star{% else %}bx-star{% endif %}' style="color:#f59e0b;font-size:14px"></i>
                            {% endfor %}
                        </div>
                    </div>
                    <span class="text-muted ms-1" style="font-size:12px">{{ review['created_at']|timeago }}</span>
                </div>
                {% if review['comment'] %}
                <p class="text-secondary" style="font-size:14px;margin-top:8px">{{ review['comment'] }}</p>
                {% endif %}
            </div>
            {% endfor %}
            {% else %}
            <div class="text-center" style="padding:40px">
                <i class='bx bx-message-square-detail' style="font-size:48px;color:var(--text-muted);display:block;margin-bottom:12px"></i>
                <p class="text-muted">No reviews yet. Be the first to review!</p>
            </div>
            {% endif %}
        </div>
    </div>

    <!-- Related Products -->
    {% if related_products %}
    <div class="section">
        <div class="section-header">
            <h3>Related Products</h3>
        </div>
        <div class="product-grid">
            {% for product in related_products %}
            <div class="product-card" onclick="window.location='{{ url_for('product_detail', slug=product['slug']) }}'">
                <div class="product-image">
                    {% if product['discount_percent'] > 0 %}
                    <span class="product-badge badge-discount">-{{ product['discount_percent']|int }}%</span>
                    {% endif %}
                    <span style="font-size:60px">{{ product['image_url'] or '📦' }}</span>
                </div>
                <div class="product-info">
                    <div class="product-title">{{ product['name'] }}</div>
                    <div class="product-footer">
                        <div class="product-price">
                            <span class="price-current">{{ product['price']|currency }}</span>
                        </div>
                    </div>
                </div>
            </div>
            {% endfor %}
        </div>
    </div>
    {% endif %}
</div>

<style>
    @media (max-width: 768px) {
        .product-detail-grid { grid-template-columns: 1fr !important; }
    }
</style>
{% endblock %}

{% block extra_js %}
function updateQty(delta) {
    const input = document.getElementById('qty');
    let val = parseInt(input.value) + delta;
    if (val < 1) val = 1;
    if (val > 99) val = 99;
    input.value = val;
}

function addToCartDetail(productId) {
    const qty = parseInt(document.getElementById('qty').value) || 1;
    fetch('/cart/add', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({product_id: productId, quantity: qty})
    })
    .then(r => r.json())
    .then(data => {
        showToast(data.message, data.success ? 'success' : 'error');
    })
    .catch(() => showToast('Please login first', 'warning'));
}

let currentRating = 5;
function setRating(r) {
    currentRating = r;
    document.getElementById('ratingInput').value = r;
    updateStars(r);
}
function hoverRating(r) { updateStars(r); }
function resetRating() { updateStars(currentRating); }
function updateStars(r) {
    const stars = document.querySelectorAll('#ratingStars i');
    stars.forEach((s, i) => {
        s.className = i < r ? 'bx bxs-star' : 'bx bx-star';
        s.style.color = i < r ? '#f59e0b' : 'var(--text-muted)';
    });
}

function showTab(tab) {
    document.getElementById('tab-description').style.display = tab === 'description' ? 'block' : 'none';
    document.getElementById('tab-reviews').style.display = tab === 'reviews' ? 'block' : 'none';
    document.querySelectorAll('.tabs .tab-btn').forEach((b, i) => {
        b.classList.toggle('active', (i === 0 && tab === 'description') || (i === 1 && tab === 'reviews'));
    });
}

function toggleWishlist(productId) {
    fetch('/wishlist/toggle', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({product_id: productId})
    })
    .then(r => r.json())
    .then(data => showToast(data.message, data.success ? 'success' : 'error'));
}
{% endblock %}
'''

CART_TEMPLATE = '''
{% extends base %}
{% block title %}Cart - {{ settings.site_name }}{% endblock %}
{% block content %}
<div class="container">
    <div class="page-header">
        <h1>Shopping Cart</h1>
        <p>{{ cart_items|length }} item(s) in your cart</p>
    </div>

    {% if cart_items %}
    <div style="display:grid;grid-template-columns:1fr 360px;gap:24px" class="cart-grid">
        <!-- Cart Items -->
        <div>
            {% for item in cart_items %}
            <div class="glass-card mb-2" style="padding:16px">
                <div style="display:flex;align-items:center;gap:16px">
                    <div style="width:80px;height:80px;background:linear-gradient(135deg,rgba(0,242,254,0.1),rgba(168,85,247,0.1));border-radius:12px;display:flex;align-items:center;justify-content:center;font-size:36px;flex-shrink:0">
                        {{ item['image_url'] or '📦' }}
                    </div>
                    <div style="flex:1;min-width:0">
                        <a href="{{ url_for('product_detail', slug=item['slug']) }}" class="fw-semibold" style="font-size:15px;display:block;margin-bottom:4px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">{{ item['name'] }}</a>
                        <span class="text-muted" style="font-size:13px">{{ item['category_name'] or 'Digital' }}</span>
                    </div>
                    <div style="display:flex;align-items:center;gap:8px">
                        <button class="btn-outline btn-sm" onclick="updateCartQty({{ item['product_id'] }}, {{ item['quantity'] - 1 }})" style="width:32px;height:32px;padding:0"><i class='bx bx-minus'></i></button>
                        <span class="fw-bold" style="min-width:30px;text-align:center">{{ item['quantity'] }}</span>
                        <button class="btn-outline btn-sm" onclick="updateCartQty({{ item['product_id'] }}, {{ item['quantity'] + 1 }})" style="width:32px;height:32px;padding:0"><i class='bx bx-plus'></i></button>
                    </div>
                    <div class="text-right" style="min-width:100px">
                        <div class="fw-bold text-primary" style="font-size:16px">{{ (item['price'] * item['quantity'])|currency }}</div>
                        {% if item['quantity'] > 1 %}<div class="text-muted" style="font-size:12px">{{ item['price']|currency }} each</div>{% endif %}
                    </div>
                    <button class="btn-outline btn-sm" onclick="removeCartItem({{ item['product_id'] }})" style="color:var(--red);border-color:rgba(255,8,68,0.3)"><i class='bx bx-trash'></i></button>
                </div>
            </div>
            {% endfor %}
        </div>

        <!-- Order Summary -->
        <div>
            <div class="glass-card" style="position:sticky;top:90px">
                <h3 style="margin-bottom:20px">Order Summary</h3>

                <!-- Coupon -->
                <div class="form-group">
                    <label>Coupon Code</label>
                    <div style="display:flex;gap:8px">
                        <input type="text" id="couponCode" class="form-input" placeholder="Enter code" style="flex:1">
                        <button class="btn-outline btn-sm" onclick="applyCoupon()">Apply</button>
                    </div>
                    <div id="couponMsg" style="font-size:12px;margin-top:4px"></div>
                </div>

                <div style="border-top:1px solid var(--border-color);padding-top:16px">
                    <div class="d-flex justify-between mb-1">
                        <span class="text-secondary">Subtotal</span>
                        <span class="fw-bold">{{ subtotal|currency }}</span>
                    </div>
                    <div class="d-flex justify-between mb-1">
                        <span class="text-secondary">Discount</span>
                        <span class="fw-bold text-green" id="discountDisplay">-{{ discount|currency }}</span>
                    </div>
                    <div class="d-flex justify-between" style="padding-top:12px;border-top:1px solid var(--border-color)">
                        <span class="fw-bold" style="font-size:16px">Total</span>
                        <span class="fw-bold" style="font-size:20px;background:var(--gradient-primary);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text" id="totalDisplay">{{ total|currency }}</span>
                    </div>
                </div>

                {% if current_user['wallet_balance'] >= total %}
                <form method="POST" action="{{ url_for('checkout') }}" class="mt-3">
                    <input type="hidden" name="coupon" id="checkoutCoupon" value="">
                    <button type="submit" class="btn-neon w-100 btn-lg">
                        <i class='bx bx-check-circle'></i> Place Order ({{ total|currency }})
                    </button>
                    <p class="text-center text-muted mt-1" style="font-size:12px">
                        <i class='bx bx-wallet'></i> Paying from wallet balance: {{ current_user['wallet_balance']|currency }}
                    </p>
                </form>
                {% else %}
                <div class="mt-3">
                    <div class="alert alert-warning mb-2">
                        <i class='bx bx-error-circle'></i>
                        <span>Insufficient wallet balance. Please deposit funds first.</span>
                    </div>
                    <a href="{{ url_for('deposit') }}" class="btn-neon w-100 btn-lg">
                        <i class='bx bx-plus-circle'></i> Deposit Funds
                    </a>
                </div>
                {% endif %}
            </div>
        </div>
    </div>
    {% else %}
    <div class="empty-state">
        <i class='bx bx-cart'></i>
        <h3>Your Cart is Empty</h3>
        <p>Browse our marketplace and add some amazing products!</p>
        <a href="{{ url_for('marketplace') }}" class="btn-neon"><i class='bx bx-store'></i> Browse Products</a>
    </div>
    {% endif %}
</div>

<style>
    @media (max-width: 768px) {
        .cart-grid { grid-template-columns: 1fr !important; }
    }
</style>
{% endblock %}

{% block extra_js %}
function updateCartQty(productId, quantity) {
    fetch('/cart/update', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({product_id: productId, quantity: quantity})
    }).then(r => r.json()).then(data => {
        if (data.success) location.reload();
        else showToast(data.message, 'error');
    });
}

function removeCartItem(productId) {
    fetch('/cart/remove', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({product_id: productId})
    }).then(r => r.json()).then(data => {
        if (data.success) location.reload();
    });
}

function applyCoupon() {
    const code = document.getElementById('couponCode').value;
    if (!code) return;
    fetch('/coupon/apply', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({code: code})
    }).then(r => r.json()).then(data => {
        const msg = document.getElementById('couponMsg');
        if (data.success) {
            msg.innerHTML = '<span class="text-green">' + data.message + '</span>';
            document.getElementById('discountDisplay').textContent = '-' + data.discount;
            document.getElementById('totalDisplay').textContent = data.total;
            document.getElementById('checkoutCoupon').value = code;
        } else {
            msg.innerHTML = '<span class="text-red">' + data.message + '</span>';
        }
    });
}
{% endblock %}
'''

ORDERS_TEMPLATE = '''
{% extends base %}
{% block title %}My Orders - {{ settings.site_name }}{% endblock %}
{% block content %}
<div class="container">
    <div class="page-header">
        <h1>My Orders</h1>
        <p>Track and manage your orders</p>
    </div>

    <div class="sidebar-layout">
        <aside class="sidebar">
            <ul class="sidebar-menu">
                <li><a href="{{ url_for('dashboard') }}"><i class='bx bx-grid-alt'></i> Dashboard</a></li>
                <li><a href="{{ url_for('profile') }}"><i class='bx bx-user'></i> Profile</a></li>
                <li><a href="{{ url_for('wallet') }}"><i class='bx bx-wallet'></i> Wallet</a></li>
                <li><a href="{{ url_for('deposit') }}"><i class='bx bx-plus-circle'></i> Deposit</a></li>
                <li><a href="{{ url_for('orders') }}" class="active"><i class='bx bx-package'></i> Orders</a></li>
                <li><a href="{{ url_for('downloads') }}"><i class='bx bx-download'></i> Downloads</a></li>
                <li><a href="{{ url_for('wishlist_view') }}"><i class='bx bx-heart'></i> Wishlist</a></li>
                <li><a href="{{ url_for('notifications') }}"><i class='bx bx-bell'></i> Notifications</a></li>
                <li><a href="{{ url_for('support') }}"><i class='bx bx-support'></i> Support</a></li>
            </ul>
        </aside>

        <div>
            <!-- Tabs -->
            <div class="tabs">
                <button class="tab-btn active" onclick="filterOrders('all')">All Orders</button>
                <button class="tab-btn" onclick="filterOrders('pending')">Pending</button>
                <button class="tab-btn" onclick="filterOrders('completed')">Completed</button>
                <button class="tab-btn" onclick="filterOrders('rejected')">Rejected</button>
            </div>

            {% if orders %}
            {% for order in orders %}
            <div class="glass-card mb-2 order-item" data-status="{{ order['order_status'] }}">
                <div class="d-flex justify-between align-center flex-wrap gap-2 mb-2">
                    <div>
                        <span class="fw-bold text-primary">{{ order['order_id'] }}</span>
                        <span class="text-muted" style="font-size:13px;margin-left:12px">{{ order['created_at']|timeago }}</span>
                    </div>
                    <span class="status-badge status-{{ order['order_status'] }}">{{ order['order_status']|title }}</span>
                </div>

                {% for item in order['items'] %}
                <div class="d-flex align-center gap-2" style="padding:8px 0;{% if not loop.last %}border-bottom:1px solid rgba(255,255,255,0.03){% endif %}">
                    <div style="width:50px;height:50px;background:linear-gradient(135deg,rgba(0,242,254,0.1),rgba(168,85,247,0.1));border-radius:10px;display:flex;align-items:center;justify-content:center;font-size:24px;flex-shrink:0">
                        {{ item['image_url'] or '📦' }}
                    </div>
                    <div style="flex:1">
                        <div class="fw-semibold" style="font-size:14px">{{ item['product_name'] }}</div>
                        <div class="text-muted" style="font-size:12px">Qty: {{ item['quantity'] }} × {{ item['unit_price']|currency }}</div>
                    </div>
                    <div class="text-right">
                        <div class="fw-bold">{{ item['total_price']|currency }}</div>
                        {% if item['is_delivered'] and item['delivery_data'] %}
                        <button class="copy-btn" onclick="copyText('{{ item['delivery_data'] }}')" style="margin-top:4px">
                            <i class='bx bx-copy'></i> Copy Key
                        </button>
                        {% endif %}
                    </div>
                </div>
                {% endfor %}

                <div class="d-flex justify-between align-center" style="padding-top:12px;border-top:1px solid var(--border-color);margin-top:8px">
                    <span class="text-secondary">Total: <span class="fw-bold text-primary" style="font-size:18px">{{ order['total_amount']|currency }}</span></span>
                    <a href="{{ url_for('order_detail', order_id=order['order_id']) }}" class="btn-outline btn-sm"><i class='bx bx-show'></i> View Details</a>
                </div>
            </div>
            {% endfor %}
            {% else %}
            <div class="empty-state">
                <i class='bx bx-package'></i>
                <h3>No Orders Yet</h3>
                <p>Your order history will appear here</p>
                <a href="{{ url_for('marketplace') }}" class="btn-neon"><i class='bx bx-store'></i> Start Shopping</a>
            </div>
            {% endif %}
        </div>
    </div>
</div>
{% endblock %}

{% block extra_js %}
function filterOrders(status) {
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    event.target.classList.add('active');
    document.querySelectorAll('.order-item').forEach(item => {
        if (status === 'all' || item.dataset.status === status) {
            item.style.display = 'block';
        } else {
            item.style.display = 'none';
        }
    });
}
{% endblock %}
'''

ORDER_DETAIL_TEMPLATE = '''
{% extends base %}
{% block title %}Order {{ order['order_id'] }} - {{ settings.site_name }}{% endblock %}
{% block content %}
<div class="container">
    <div class="breadcrumb">
        <a href="{{ url_for('dashboard') }}">Dashboard</a>
        <i class='bx bx-chevron-right'></i>
        <a href="{{ url_for('orders') }}">Orders</a>
        <i class='bx bx-chevron-right'></i>
        <span>{{ order['order_id'] }}</span>
    </div>

    <div class="page-header">
        <div class="d-flex justify-between align-center flex-wrap gap-2">
            <div>
                <h1>Order {{ order['order_id'] }}</h1>
                <p>Placed on {{ order['created_at'] }}</p>
            </div>
            <span class="status-badge status-{{ order['order_status'] }}" style="font-size:14px;padding:8px 20px">{{ order['order_status']|title }}</span>
        </div>
    </div>

    <div style="display:grid;grid-template-columns:1fr 360px;gap:24px" class="cart-grid">
        <!-- Order Items -->
        <div>
            <div class="glass-card">
                <h3 style="margin-bottom:20px">Order Items</h3>
                {% for item in order_items %}
                <div style="padding:16px 0;{% if not loop.last %}border-bottom:1px solid var(--border-color){% endif %}">
                    <div class="d-flex align-center gap-3">
                        <div style="width:60px;height:60px;background:linear-gradient(135deg,rgba(0,242,254,0.1),rgba(168,85,247,0.1));border-radius:12px;display:flex;align-items:center;justify-content:center;font-size:28px;flex-shrink:0">
                            {{ item['image_url'] or '📦' }}
                        </div>
                        <div style="flex:1">
                            <div class="fw-semibold">{{ item['product_name'] }}</div>
                            <div class="text-muted" style="font-size:13px">Qty: {{ item['quantity'] }} × {{ item['unit_price']|currency }}</div>
                        </div>
                        <div class="text-right">
                            <div class="fw-bold" style="font-size:16px">{{ item['total_price']|currency }}</div>
                            {% if item['is_delivered'] %}
                            <span class="status-badge status-delivered mt-1"><i class='bx bx-check'></i> Delivered</span>
                            {% endif %}
                        </div>
                    </div>

                    <!-- Delivery Data -->
                    {% if item['is_delivered'] and item['delivery_data'] %}
                    <div class="glass-card mt-2" style="background:rgba(46,204,113,0.05);border-color:rgba(46,204,113,0.2);padding:16px">
                        <div class="d-flex justify-between align-center mb-1">
                            <span class="fw-semibold text-green"><i class='bx bx-key'></i> Delivery Key / License</span>
                            <button class="copy-btn" onclick="copyText('{{ item['delivery_data'] }}')"><i class='bx bx-copy'></i> Copy</button>
                        </div>
                        <code style="display:block;padding:12px;background:rgba(0,0,0,0.3);border-radius:8px;font-size:13px;word-break:break-all;color:var(--primary)">{{ item['delivery_data'] }}</code>
                    </div>
                    {% endif %}
                </div>
                {% endfor %}
            </div>
        </div>

        <!-- Order Summary -->
        <div>
            <div class="glass-card mb-3">
                <h3 style="margin-bottom:16px">Order Summary</h3>
                <div class="d-flex justify-between mb-1">
                    <span class="text-secondary">Subtotal</span>
                    <span>{{ order['subtotal']|currency }}</span>
                </div>
                {% if order['discount_amount'] > 0 %}
                <div class="d-flex justify-between mb-1">
                    <span class="text-secondary">Discount {% if order['coupon_code'] %}({{ order['coupon_code'] }}){% endif %}</span>
                    <span class="text-green">-{{ order['discount_amount']|currency }}</span>
                </div>
                {% endif %}
                <div class="d-flex justify-between" style="padding-top:12px;border-top:1px solid var(--border-color)">
                    <span class="fw-bold">Total</span>
                    <span class="fw-bold" style="font-size:20px;background:var(--gradient-primary);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text">{{ order['total_amount']|currency }}</span>
                </div>
            </div>

            <div class="glass-card">
                <h3 style="margin-bottom:16px">Order Info</h3>
                <div style="font-size:14px">
                    <div class="d-flex justify-between mb-1">
                        <span class="text-muted">Order ID</span>
                        <span class="fw-semibold">{{ order['order_id'] }}</span>
                    </div>
                    <div class="d-flex justify-between mb-1">
                        <span class="text-muted">Payment</span>
                        <span>{{ order['payment_method']|title }}</span>
                    </div>
                    <div class="d-flex justify-between mb-1">
                        <span class="text-muted">Status</span>
                        <span class="status-badge status-{{ order['payment_status'] }}">{{ order['payment_status']|title }}</span>
                    </div>
                    <div class="d-flex justify-between mb-1">
                        <span class="text-muted">Date</span>
                        <span>{{ order['created_at'] }}</span>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}
'''

CATEGORIES_TEMPLATE = '''
{% extends base %}
{% block title %}Categories - {{ settings.site_name }}{% endblock %}
{% block content %}
<div class="container">
    <div class="page-header">
        <h1>Categories</h1>
        <p>Browse products by category</p>
    </div>

    <div class="categories-grid" style="grid-template-columns:repeat(auto-fill,minmax(240px,1fr))">
        {% for cat in categories %}
        <a href="{{ url_for('marketplace', category=cat['slug']) }}" class="category-card">
            <div class="category-icon" style="background:{{ cat['color'] }}20;color:{{ cat['color'] }};width:70px;height:70px;font-size:32px;border-radius:20px">
                <i class='bx {{ cat["icon"] }}'></i>
            </div>
            <div class="category-name" style="font-size:18px;margin-top:12px">{{ cat['name'] }}</div>
            <div class="category-desc text-muted" style="font-size:13px;margin:8px 0">{{ cat['description']|truncate_text(80) }}</div>
            <div class="category-count">{{ cat['product_count'] }} products</div>
        </a>
        {% endfor %}
    </div>
</div>
{% endblock %}
'''

NOTIFICATIONS_TEMPLATE = '''
{% extends base %}
{% block title %}Notifications - {{ settings.site_name }}{% endblock %}
{% block content %}
<div class="container">
    <div class="page-header">
        <div class="d-flex justify-between align-center flex-wrap gap-2">
            <div>
                <h1>Notifications</h1>
                <p>Stay updated with your activities</p>
            </div>
            {% if notifications %}
            <a href="{{ url_for('mark_all_read') }}" class="btn-outline btn-sm"><i class='bx bx-check-double'></i> Mark All Read</a>
            {% endif %}
        </div>
    </div>

    {% if notifications %}
    <div style="display:flex;flex-direction:column;gap:8px">
        {% for notif in notifications %}
        <div class="glass-card" style="padding:16px;display:flex;align-items:center;gap:16px;{% if not notif['is_read'] %}border-color:rgba(0,242,254,0.3);background:rgba(0,242,254,0.03){% endif %}">
            <div style="width:44px;height:44px;border-radius:12px;display:flex;align-items:center;justify-content:center;background:{% if notif['type']=='success' %}rgba(46,204,113,0.1){% elif notif['type']=='warning' %}rgba(245,158,11,0.1){% elif notif['type']=='error' %}rgba(255,8,68,0.1){% else %}rgba(0,242,254,0.1){% endif %};color:{% if notif['type']=='success' %}var(--green){% elif notif['type']=='warning' %}var(--yellow){% elif notif['type']=='error' %}var(--red){% else %}var(--primary){% endif %};flex-shrink:0">
                <i class='bx {% if notif["type"]=="success" %}bx-check-circle{% elif notif["type"]=="warning" %}bx-error-circle{% elif notif["type"]=="error" %}bx-error{% else %}bx-info-circle{% endif %}' style="font-size:22px"></i>
            </div>
            <div style="flex:1">
                <div class="fw-semibold" style="font-size:14px">{{ notif['title'] }}</div>
                <div class="text-secondary" style="font-size:13px;margin-top:2px">{{ notif['message'] }}</div>
                <div class="text-muted" style="font-size:12px;margin-top:4px">{{ notif['created_at']|timeago }}</div>
            </div>
            {% if notif['link'] %}
            <a href="{{ notif['link'] }}" class="btn-outline btn-sm"><i class='bx bx-link'></i></a>
            {% endif %}
        </div>
        {% endfor %}
    </div>
    {% else %}
    <div class="empty-state">
        <i class='bx bx-bell'></i>
        <h3>No Notifications</h3>
        <p>You're all caught up!</p>
    </div>
    {% endif %}
</div>
{% endblock %}
'''

SUPPORT_TEMPLATE = '''
{% extends base %}
{% block title %}Support - {{ settings.site_name }}{% endblock %}
{% block content %}
<div class="container">
    <div class="page-header">
        <div class="d-flex justify-between align-center flex-wrap gap-2">
            <div>
                <h1>Customer Support</h1>
                <p>We're here to help you</p>
            </div>
            <button class="btn-neon" onclick="document.getElementById('newTicket').style.display='block'"><i class='bx bx-plus'></i> New Ticket</button>
        </div>
    </div>

    <!-- New Ticket Form -->
    <div id="newTicket" class="glass-card mb-3" style="display:none">
        <h3 style="margin-bottom:20px">Create Support Ticket</h3>
        <form method="POST" action="{{ url_for('support') }}">
            <div class="form-group">
                <label>Subject</label>
                <input type="text" name="subject" class="form-input" placeholder="Brief description of your issue" required>
            </div>
            <div class="form-group">
                <label>Priority</label>
                <select name="priority" class="form-input">
                    <option value="low">Low</option>
                    <option value="normal" selected>Normal</option>
                    <option value="high">High</option>
                    <option value="urgent">Urgent</option>
                </select>
            </div>
            <div class="form-group">
                <label>Message</label>
                <textarea name="message" class="form-input" placeholder="Describe your issue in detail..." rows="5" required></textarea>
            </div>
            <div class="d-flex gap-2">
                <button type="submit" class="btn-neon"><i class='bx bx-send'></i> Submit Ticket</button>
                <button type="button" class="btn-outline" onclick="document.getElementById('newTicket').style.display='none'">Cancel</button>
            </div>
        </form>
    </div>

    <!-- Tickets List -->
    {% if tickets %}
    <div style="display:flex;flex-direction:column;gap:12px">
        {% for ticket in tickets %}
        <div class="glass-card" style="padding:20px">
            <div class="d-flex justify-between align-center flex-wrap gap-2 mb-2">
                <div>
                    <span class="fw-bold text-primary">{{ ticket['ticket_id'] }}</span>
                    <span class="text-muted" style="margin-left:8px;font-size:13px">{{ ticket['created_at']|timeago }}</span>
                </div>
                <div class="d-flex gap-1">
                    <span class="status-badge status-{{ 'approved' if ticket['status']=='resolved' else ('pending' if ticket['status']=='open' else 'processing') }}">{{ ticket['status']|title }}</span>
                    <span class="status-badge" style="background:rgba(168,85,247,0.15);color:var(--purple)">{{ ticket['priority']|title }}</span>
                </div>
            </div>
            <h4 style="margin-bottom:8px">{{ ticket['subject'] }}</h4>
            <p class="text-secondary" style="font-size:14px">{{ ticket['message']|truncate_text(200) }}</p>

            {% if ticket['admin_reply'] %}
            <div class="glass-card mt-2" style="background:rgba(46,204,113,0.05);border-color:rgba(46,204,113,0.2);padding:16px">
                <div class="fw-semibold text-green mb-1"><i class='bx bx-support'></i> Admin Reply</div>
                <p class="text-secondary" style="font-size:14px">{{ ticket['admin_reply'] }}</p>
                <span class="text-muted" style="font-size:12px">{{ ticket['replied_at']|timeago }}</span>
            </div>
            {% endif %}
        </div>
        {% endfor %}
    </div>
    {% else %}
    <div class="empty-state">
        <i class='bx bx-support'></i>
        <h3>No Support Tickets</h3>
        <p>Need help? Create a new support ticket</p>
    </div>
    {% endif %}
</div>
{% endblock %}
'''

DOWNLOADS_TEMPLATE = '''
{% extends base %}
{% block title %}Downloads - {{ settings.site_name }}{% endblock %}
{% block content %}
<div class="container">
    <div class="page-header">
        <h1>Download Center</h1>
        <p>Access your purchased digital products</p>
    </div>

    {% if downloads %}
    <div style="display:flex;flex-direction:column;gap:12px">
        {% for dl in downloads %}
        <div class="glass-card" style="padding:20px">
            <div class="d-flex align-center gap-3 flex-wrap">
                <div style="width:60px;height:60px;background:linear-gradient(135deg,rgba(0,242,254,0.1),rgba(168,85,247,0.1));border-radius:12px;display:flex;align-items:center;justify-content:center;font-size:28px;flex-shrink:0">
                    {{ dl['image_url'] or '📦' }}
                </div>
                <div style="flex:1;min-width:200px">
                    <div class="fw-semibold" style="font-size:15px">{{ dl['product_name'] }}</div>
                    <div class="text-muted" style="font-size:13px">Order: {{ dl['order_id'] }} | Purchased: {{ dl['delivered_at'] or dl['created_at']|timeago }}</div>
                </div>
                <div class="d-flex gap-1">
                    {% if dl['delivery_data'] %}
                    <button class="copy-btn" onclick="copyText('{{ dl['delivery_data'] }}')"><i class='bx bx-copy'></i> Copy Key</button>
                    {% endif %}
                </div>
            </div>
            {% if dl['delivery_data'] %}
            <div class="mt-2" style="padding:12px;background:rgba(0,0,0,0.3);border-radius:8px">
                <code style="font-size:13px;word-break:break-all;color:var(--primary)">{{ dl['delivery_data'] }}</code>
            </div>
            {% endif %}
        </div>
        {% endfor %}
    </div>
    {% else %}
    <div class="empty-state">
        <i class='bx bx-download'></i>
        <h3>No Downloads Yet</h3>
        <p>Your purchased digital products will appear here</p>
        <a href="{{ url_for('marketplace') }}" class="btn-neon"><i class='bx bx-store'></i> Browse Products</a>
    </div>
    {% endif %}
</div>
{% endblock %}
'''

WISHLIST_TEMPLATE = '''
{% extends base %}
{% block title %}Wishlist - {{ settings.site_name }}{% endblock %}
{% block content %}
<div class="container">
    <div class="page-header">
        <h1>My Wishlist</h1>
        <p>{{ products|length }} item(s) in your wishlist</p>
    </div>

    {% if products %}
    <div class="product-grid">
        {% for product in products %}
        <div class="product-card" onclick="window.location='{{ url_for('product_detail', slug=product['slug']) }}'">
            <div class="product-image">
                {% if product['discount_percent'] > 0 %}
                <span class="product-badge badge-discount">-{{ product['discount_percent']|int }}%</span>
                {% endif %}
                <button class="product-wishlist active" onclick="event.stopPropagation(); toggleWishlist({{ product['id'] }})"><i class='bx bxs-heart'></i></button>
                <span style="font-size:60px">{{ product['image_url'] or '📦' }}</span>
            </div>
            <div class="product-info">
                <div class="product-category">{{ product['category_name'] or 'Digital' }}</div>
                <div class="product-title">{{ product['name'] }}</div>
                <div class="product-footer">
                    <div class="product-price">
                        <span class="price-current">{{ product['price']|currency }}</span>
                        {% if product['original_price'] > product['price'] %}
                        <span class="price-original">{{ product['original_price']|currency }}</span>
                        {% endif %}
                    </div>
                    <button class="product-add-cart" onclick="event.stopPropagation(); addToCart({{ product['id'] }})"><i class='bx bx-cart-add'></i></button>
                </div>
            </div>
        </div>
        {% endfor %}
    </div>
    {% else %}
    <div class="empty-state">
        <i class='bx bx-heart'></i>
        <h3>Wishlist is Empty</h3>
        <p>Save your favorite products here</p>
        <a href="{{ url_for('marketplace') }}" class="btn-neon"><i class='bx bx-store'></i> Browse Products</a>
    </div>
    {% endif %}
</div>
{% endblock %}

{% block extra_js %}
function addToCart(pid) {
    fetch('/cart/add', {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({product_id:pid,quantity:1})})
    .then(r=>r.json()).then(d=>{showToast(d.message,d.success?'success':'error')}).catch(()=>showToast('Login required','warning'));
}
function toggleWishlist(pid) {
    fetch('/wishlist/toggle',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({product_id:pid})})
    .then(r=>r.json()).then(d=>{showToast(d.message,d.success?'success':'error');if(d.success)location.reload();});
}
{% endblock %}
'''

ERROR_TEMPLATE = '''
{% extends base %}
{% block title %}{{ error_code }} - {{ settings.site_name }}{% endblock %}
{% block content %}
<div class="container text-center" style="padding:100px 20px">
    <div style="font-size:120px;margin-bottom:24px">
        {% if error_code == 404 %}🔍{% elif error_code == 500 %}⚠️{% else %}❌{% endif %}
    </div>
    <h1 style="font-size:64px;background:var(--gradient-primary);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;margin-bottom:16px">{{ error_code }}</h1>
    <p style="font-size:20px;color:var(--text-secondary);margin-bottom:32px">
        {% if error_code == 404 %}Page not found{% elif error_code == 500 %}Internal server error{% else %}Something went wrong{% endif %}
    </p>
    <a href="{{ url_for('home') }}" class="btn-neon btn-lg"><i class='bx bx-home'></i> Back to Home</a>
</div>
{% endblock %}
'''

# ============================================================
# ADMIN TEMPLATES
# ============================================================

ADMIN_LAYOUT = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}Admin{% endblock %} - {{ settings.site_name }}</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <link href="https://unpkg.com/boxicons@2.1.4/css/boxicons.min.css" rel="stylesheet">
    <style>
        :root {
            --primary: #00f2fe;
            --primary-blue: #4facfe;
            --purple: #a855f7;
            --red: #ff0844;
            --green: #2ecc71;
            --yellow: #f59e0b;
            --bg-dark: #090910;
            --bg-card: rgba(15, 15, 30, 0.8);
            --bg-glass: rgba(255, 255, 255, 0.05);
            --bg-glass-hover: rgba(255, 255, 255, 0.1);
            --text-primary: #ffffff;
            --text-secondary: rgba(255, 255, 255, 0.7);
            --text-muted: rgba(255, 255, 255, 0.4);
            --border-color: rgba(255, 255, 255, 0.1);
            --shadow-neon: 0 0 20px rgba(0, 242, 254, 0.3);
            --shadow-card: 0 8px 32px rgba(0, 0, 0, 0.4);
            --gradient-primary: linear-gradient(135deg, #00f2fe, #4facfe);
            --gradient-purple: linear-gradient(135deg, #a855f7, #6366f1);
            --glass-blur: blur(20px);
            --transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            --radius: 16px;
            --radius-sm: 10px;
            --radius-xs: 6px;
        }
        * { margin:0; padding:0; box-sizing:border-box; }
        body { font-family:'Inter',sans-serif; background:var(--bg-dark); color:var(--text-primary); line-height:1.6; }
        a { color:var(--primary); text-decoration:none; transition:var(--transition); }
        a:hover { color:var(--primary-blue); }
        .admin-layout { display:flex; min-height:100vh; }
        .admin-sidebar {
            width:260px; background:rgba(9,9,16,0.95); backdrop-filter:var(--glass-blur);
            border-right:1px solid var(--border-color); position:fixed; top:0; bottom:0; left:0;
            overflow-y:auto; z-index:100; padding:20px 0;
        }
        .admin-sidebar-logo {
            display:flex; align-items:center; gap:12px; padding:0 20px 24px;
            border-bottom:1px solid var(--border-color); margin-bottom:16px;
        }
        .admin-sidebar-logo .logo-icon {
            width:40px; height:40px; background:var(--gradient-primary); border-radius:12px;
            display:flex; align-items:center; justify-content:center; font-weight:900; color:#000;
        }
        .admin-sidebar-logo span { font-size:16px; font-weight:700; }
        .admin-nav { list-style:none; padding:0 12px; }
        .admin-nav li { margin-bottom:2px; }
        .admin-nav a {
            display:flex; align-items:center; gap:12px; padding:12px 16px;
            color:var(--text-secondary); font-size:14px; font-weight:500;
            border-radius:var(--radius-xs); transition:var(--transition);
        }
        .admin-nav a:hover, .admin-nav a.active {
            background:rgba(0,242,254,0.1); color:var(--primary);
        }
        .admin-nav a i { font-size:20px; }
        .admin-nav .nav-divider {
            height:1px; background:var(--border-color); margin:12px 0;
        }
        .admin-main { flex:1; margin-left:260px; padding:24px; }
        .admin-header {
            display:flex; align-items:center; justify-content:space-between;
            padding:16px 24px; background:var(--bg-glass); backdrop-filter:var(--glass-blur);
            border:1px solid var(--border-color); border-radius:var(--radius); margin-bottom:24px;
        }
        .glass-card {
            background:var(--bg-glass); backdrop-filter:var(--glass-blur);
            border:1px solid var(--border-color); border-radius:var(--radius); padding:24px;
            transition:var(--transition);
        }
        .glass-card:hover { background:var(--bg-glass-hover); }
        .btn-neon, .btn-outline, .btn-neon-purple, .btn-neon-red, .btn-neon-green {
            display:inline-flex; align-items:center; justify-content:center; gap:8px;
            padding:12px 24px; font-weight:600; font-size:14px; border:none;
            border-radius:var(--radius-sm); cursor:pointer; transition:var(--transition);
            font-family:inherit;
        }
        .btn-neon { background:var(--gradient-primary); color:#000; }
        .btn-neon:hover { transform:translateY(-2px); box-shadow:0 8px 25px rgba(0,242,254,0.4); color:#000; }
        .btn-neon-purple { background:var(--gradient-purple); color:#fff; }
        .btn-neon-red { background:linear-gradient(135deg,#ff0844,#ff6b6b); color:#fff; }
        .btn-neon-green { background:linear-gradient(135deg,#2ecc71,#27ae60); color:#000; }
        .btn-outline { background:transparent; color:var(--primary); border:1px solid var(--primary); }
        .btn-outline:hover { background:rgba(0,242,254,0.1); color:var(--primary); }
        .btn-sm { padding:8px 16px; font-size:12px; }
        .form-group { margin-bottom:16px; }
        .form-group label { display:block; margin-bottom:6px; font-weight:500; color:var(--text-secondary); font-size:14px; }
        .form-input {
            width:100%; padding:12px 14px; background:rgba(255,255,255,0.05);
            border:1px solid var(--border-color); border-radius:var(--radius-xs);
            color:var(--text-primary); font-size:14px; font-family:inherit;
            transition:var(--transition); outline:none;
        }
        .form-input:focus { border-color:var(--primary); box-shadow:0 0 0 3px rgba(0,242,254,0.1); }
        .form-input::placeholder { color:var(--text-muted); }
        textarea.form-input { min-height:100px; resize:vertical; }
        select.form-input { appearance:none; }
        .stat-card {
            background:var(--bg-glass); backdrop-filter:var(--glass-blur);
            border:1px solid var(--border-color); border-radius:var(--radius); padding:24px;
            position:relative; overflow:hidden;
        }
        .stat-card::before { content:''; position:absolute; top:0; left:0; right:0; height:3px; background:var(--gradient-primary); }
        .stat-card.purple::before { background:var(--gradient-purple); }
        .stat-card.red::before { background:linear-gradient(135deg,#ff0844,#ff6b6b); }
        .stat-card.green::before { background:linear-gradient(135deg,#2ecc71,#27ae60); }
        .stat-icon { width:50px; height:50px; border-radius:14px; display:flex; align-items:center; justify-content:center; font-size:24px; margin-bottom:12px; }
        .stat-value { font-size:28px; font-weight:800; }
        .stat-label { font-size:13px; color:var(--text-muted); }
        .data-table { width:100%; border-collapse:collapse; }
        .data-table th { padding:12px 14px; text-align:left; font-size:12px; font-weight:600; text-transform:uppercase; letter-spacing:1px; color:var(--text-muted); background:rgba(255,255,255,0.02); border-bottom:1px solid var(--border-color); }
        .data-table td { padding:12px 14px; font-size:14px; color:var(--text-secondary); border-bottom:1px solid rgba(255,255,255,0.03); }
        .data-table tr:hover td { background:rgba(255,255,255,0.02); }
        .table-container { overflow-x:auto; border-radius:var(--radius); border:1px solid var(--border-color); }
        .status-badge { display:inline-flex; align-items:center; gap:4px; padding:4px 12px; border-radius:20px; font-size:12px; font-weight:600; }
        .status-pending { background:rgba(245,158,11,0.15); color:#f59e0b; }
        .status-approved, .status-completed { background:rgba(46,204,113,0.15); color:#2ecc71; }
        .status-rejected { background:rgba(255,8,68,0.15); color:#ff0844; }
        .status-processing { background:rgba(79,172,254,0.15); color:#4facfe; }
        .alert { padding:14px 18px; border-radius:var(--radius-sm); margin-bottom:12px; font-size:14px; display:flex; align-items:center; gap:10px; }
        .alert-success { background:rgba(46,204,113,0.1); border:1px solid rgba(46,204,113,0.2); color:#2ecc71; }
        .alert-danger { background:rgba(255,8,68,0.1); border:1px solid rgba(255,8,68,0.2); color:#ff0844; }
        .alert-warning { background:rgba(245,158,11,0.1); border:1px solid rgba(245,158,11,0.2); color:#f59e0b; }
        .d-flex { display:flex; }
        .align-center { align-items:center; }
        .justify-between { justify-content:space-between; }
        .flex-wrap { flex-wrap:wrap; }
        .gap-1 { gap:8px; }
        .gap-2 { gap:16px; }
        .gap-3 { gap:24px; }
        .mb-1 { margin-bottom:8px; }
        .mb-2 { margin-bottom:16px; }
        .mb-3 { margin-bottom:24px; }
        .mt-2 { margin-top:16px; }
        .mt-3 { margin-top:24px; }
        .text-center { text-align:center; }
        .text-right { text-align:right; }
        .text-primary { color:var(--primary); }
        .text-green { color:var(--green); }
        .text-red { color:var(--red); }
        .text-yellow { color:var(--yellow); }
        .text-muted { color:var(--text-muted); }
        .text-secondary { color:var(--text-secondary); }
        .fw-bold { font-weight:700; }
        .fw-semibold { font-weight:600; }
        .w-100 { width:100%; }
        .toast-container { position:fixed; top:20px; right:20px; z-index:3000; display:flex; flex-direction:column; gap:8px; }
        .toast { padding:14px 18px; background:rgba(20,20,40,0.95); backdrop-filter:var(--glass-blur); border:1px solid var(--border-color); border-radius:var(--radius-sm); font-size:14px; display:flex; align-items:center; gap:10px; min-width:280px; animation:slideInRight 0.3s ease-out; box-shadow:var(--shadow-card); }
        .toast.success { border-left:4px solid var(--green); }
        .toast.error { border-left:4px solid var(--red); }
        .toast.warning { border-left:4px solid var(--yellow); }
        @keyframes slideInRight { from{transform:translateX(100%);opacity:0} to{transform:translateX(0);opacity:1} }
        .dashboard-grid { display:grid; grid-template-columns:repeat(auto-fill,minmax(240px,1fr)); gap:20px; }
        .admin-hamburger { display:none; position:fixed; top:16px; left:16px; z-index:200; width:42px; height:42px; background:var(--bg-glass); border:1px solid var(--border-color); border-radius:12px; cursor:pointer; align-items:center; justify-content:center; font-size:20px; color:var(--text-primary); }
        @media(max-width:768px) {
            .admin-sidebar { transform:translateX(-100%); transition:var(--transition); }
            .admin-sidebar.show { transform:translateX(0); }
            .admin-main { margin-left:0; padding:16px; padding-top:70px; }
            .admin-hamburger { display:flex; }
            .dashboard-grid { grid-template-columns:1fr 1fr; }
        }
        @media(max-width:480px) {
            .dashboard-grid { grid-template-columns:1fr; }
        }
    </style>
</head>
<body>
    <div class="toast-container" id="toastContainer">
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                {% for category, message in messages %}
                <div class="toast {{ category }}"><span>{{ message }}</span></div>
                {% endfor %}
            {% endif %}
        {% endwith %}
    </div>

    <button class="admin-hamburger" onclick="document.querySelector('.admin-sidebar').classList.toggle('show')">
        <i class='bx bx-menu'></i>
    </button>

    <div class="admin-layout">
        <aside class="admin-sidebar">
            <div class="admin-sidebar-logo">
                <div class="logo-icon">S</div>
                <span>Admin Panel</span>
            </div>
            <ul class="admin-nav">
                <li><a href="{{ url_for('admin_dashboard') }}" class="{% if request.endpoint == 'admin_dashboard' %}active{% endif %}"><i class='bx bx-grid-alt'></i> Dashboard</a></li>
                <li><a href="{{ url_for('admin_products') }}" class="{% if request.endpoint == 'admin_products' %}active{% endif %}"><i class='bx bx-package'></i> Products</a></li>
                <li><a href="{{ url_for('admin_categories') }}" class="{% if request.endpoint == 'admin_categories' %}active{% endif %}"><i class='bx bx-category'></i> Categories</a></li>
                <li><a href="{{ url_for('admin_orders') }}" class="{% if request.endpoint == 'admin_orders' %}active{% endif %}"><i class='bx bx-cart'></i> Orders</a></li>
                <li><a href="{{ url_for('admin_deposits') }}" class="{% if request.endpoint == 'admin_deposits' %}active{% endif %}"><i class='bx bx-money'></i> Deposits</a></li>
                <li><a href="{{ url_for('admin_users') }}" class="{% if request.endpoint == 'admin_users' %}active{% endif %}"><i class='bx bx-group'></i> Users</a></li>
                <li><a href="{{ url_for('admin_coupons') }}" class="{% if request.endpoint == 'admin_coupons' %}active{% endif %}"><i class='bx bx-purchase-tag'></i> Coupons</a></li>
                <li><a href="{{ url_for('admin_support') }}" class="{% if request.endpoint == 'admin_support' %}active{% endif %}"><i class='bx bx-support'></i> Support</a></li>
                <li><a href="{{ url_for('admin_announcements') }}" class="{% if request.endpoint == 'admin_announcements' %}active{% endif %}"><i class='bx bx-megaphone'></i> Announcements</a></li>
                <div class="nav-divider"></div>
                <li><a href="{{ url_for('admin_settings') }}" class="{% if request.endpoint == 'admin_settings' %}active{% endif %}"><i class='bx bx-cog'></i> Settings</a></li>
                <li><a href="{{ url_for('admin_logs') }}" class="{% if request.endpoint == 'admin_logs' %}active{% endif %}"><i class='bx bx-history'></i> Activity Log</a></li>
                <div class="nav-divider"></div>
                <li><a href="{{ url_for('home') }}"><i class='bx bx-link-external'></i> View Site</a></li>
                <li><a href="{{ url_for('admin_logout') }}"><i class='bx bx-log-out'></i> Logout</a></li>
            </ul>
        </aside>

        <main class="admin-main">
            {% block admin_content %}{% endblock %}
        </main>
    </div>

    <script>
        document.querySelectorAll('.toast').forEach(t => {
            setTimeout(() => { t.style.opacity='0'; setTimeout(()=>t.remove(),300); }, 4000);
        });
        function showToast(msg, type='info') {
            const c = document.getElementById('toastContainer');
            const t = document.createElement('div');
            t.className = 'toast ' + type;
            t.innerHTML = '<span>' + msg + '</span>';
            c.appendChild(t);
            setTimeout(() => { t.style.opacity='0'; setTimeout(()=>t.remove(),300); }, 4000);
        }
        {% block extra_js %}{% endblock %}
    </script>
</body>
</html>
'''

ADMIN_LOGIN_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Admin Login - SOHAG BD SHOP</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <link href="https://unpkg.com/boxicons@2.1.4/css/boxicons.min.css" rel="stylesheet">
    <style>
        * { margin:0; padding:0; box-sizing:border-box; }
        body { font-family:'Inter',sans-serif; background:#090910; color:#fff; min-height:100vh; display:flex; align-items:center; justify-content:center; }
        .login-card {
            background:rgba(255,255,255,0.05); backdrop-filter:blur(20px); border:1px solid rgba(255,255,255,0.1);
            border-radius:20px; padding:40px; max-width:420px; width:100%; margin:20px;
        }
        .login-card h2 { text-align:center; font-size:24px; margin-bottom:8px; }
        .login-card p { text-align:center; color:rgba(255,255,255,0.6); margin-bottom:24px; font-size:14px; }
        .form-group { margin-bottom:16px; }
        .form-group label { display:block; margin-bottom:6px; font-size:14px; font-weight:500; color:rgba(255,255,255,0.7); }
        .form-input {
            width:100%; padding:12px 14px; background:rgba(255,255,255,0.05);
            border:1px solid rgba(255,255,255,0.1); border-radius:10px; color:#fff;
            font-size:14px; font-family:inherit; outline:none; transition:all 0.3s;
        }
        .form-input:focus { border-color:#00f2fe; box-shadow:0 0 0 3px rgba(0,242,254,0.1); }
        .btn-submit {
            width:100%; padding:14px; background:linear-gradient(135deg,#00f2fe,#4facfe);
            border:none; border-radius:10px; color:#000; font-size:16px; font-weight:700;
            cursor:pointer; transition:all 0.3s; font-family:inherit; margin-top:8px;
        }
        .btn-submit:hover { transform:translateY(-2px); box-shadow:0 8px 25px rgba(0,242,254,0.4); }
        .alert { padding:12px 16px; border-radius:10px; margin-bottom:16px; font-size:14px; }
        .alert-danger { background:rgba(255,8,68,0.1); border:1px solid rgba(255,8,68,0.2); color:#ff0844; }
        .logo { width:60px; height:60px; background:linear-gradient(135deg,#00f2fe,#4facfe); border-radius:16px; display:flex; align-items:center; justify-content:center; font-size:28px; color:#000; font-weight:900; margin:0 auto 16px; }
    </style>
</head>
<body>
    <div class="login-card">
        <div class="logo">S</div>
        <h2>Admin Login</h2>
        <p>SOHAG BD SHOP Admin Panel</p>
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% for cat, msg in messages %}
            <div class="alert alert-{{ cat }}">{{ msg }}</div>
            {% endfor %}
        {% endwith %}
        <form method="POST">
            <div class="form-group">
                <label>Username</label>
                <input type="text" name="username" class="form-input" placeholder="Enter admin username" required>
            </div>
            <div class="form-group">
                <label>Password</label>
                <input type="password" name="password" class="form-input" placeholder="Enter admin password" required>
            </div>
            <button type="submit" class="btn-submit"><i class='bx bx-log-in'></i> Login</button>
        </form>
    </div>
</body>
</html>
'''

ADMIN_DASHBOARD_TEMPLATE = '''
{% extends admin_base %}
{% block title %}Dashboard{% endblock %}
{% block admin_content %}
<div class="admin-header">
    <div>
        <h2 style="font-size:22px">Dashboard</h2>
        <p class="text-secondary" style="font-size:14px">Welcome back, {{ admin['full_name'] or admin['username'] }}</p>
    </div>
    <span class="text-muted" style="font-size:13px">{{ now.strftime('%B %d, %Y') }}</span>
</div>

<!-- Stats -->
<div class="dashboard-grid mb-3">
    <div class="stat-card">
        <div class="stat-icon" style="background:rgba(0,242,254,0.1);color:var(--primary)"><i class='bx bx-dollar'></i></div>
        <div class="stat-value">{{ total_revenue|currency }}</div>
        <div class="stat-label">Total Revenue</div>
    </div>
    <div class="stat-card purple">
        <div class="stat-icon" style="background:rgba(168,85,247,0.1);color:var(--purple)"><i class='bx bx-cart'></i></div>
        <div class="stat-value">{{ total_orders }}</div>
        <div class="stat-label">Total Orders</div>
    </div>
    <div class="stat-card green">
        <div class="stat-icon" style="background:rgba(46,204,113,0.1);color:var(--green)"><i class='bx bx-group'></i></div>
        <div class="stat-value">{{ total_users }}</div>
        <div class="stat-label">Total Users</div>
    </div>
    <div class="stat-card red">
        <div class="stat-icon" style="background:rgba(255,8,68,0.1);color:var(--red)"><i class='bx bx-package'></i></div>
        <div class="stat-value">{{ total_products }}</div>
        <div class="stat-label">Total Products</div>
    </div>
</div>

<!-- Quick Stats Row -->
<div class="dashboard-grid mb-3">
    <div class="stat-card">
        <div class="d-flex justify-between align-center">
            <div>
                <div class="stat-label">Pending Deposits</div>
                <div class="stat-value" style="font-size:24px;color:var(--yellow)">{{ pending_deposits }}</div>
            </div>
            <a href="{{ url_for('admin_deposits') }}" class="btn-outline btn-sm">View</a>
        </div>
    </div>
    <div class="stat-card">
        <div class="d-flex justify-between align-center">
            <div>
                <div class="stat-label">Pending Orders</div>
                <div class="stat-value" style="font-size:24px;color:var(--primary-blue)">{{ pending_orders_count }}</div>
            </div>
            <a href="{{ url_for('admin_orders') }}" class="btn-outline btn-sm">View</a>
        </div>
    </div>
    <div class="stat-card">
        <div class="d-flex justify-between align-center">
            <div>
                <div class="stat-label">Open Tickets</div>
                <div class="stat-value" style="font-size:24px;color:var(--red)">{{ open_tickets }}</div>
            </div>
            <a href="{{ url_for('admin_support') }}" class="btn-outline btn-sm">View</a>
        </div>
    </div>
    <div class="stat-card">
        <div class="d-flex justify-between align-center">
            <div>
                <div class="stat-label">Today's Revenue</div>
                <div class="stat-value" style="font-size:24px;color:var(--green)">{{ today_revenue|currency }}</div>
            </div>
        </div>
    </div>
</div>

<!-- Recent Orders -->
<div class="glass-card mb-3">
    <div class="d-flex justify-between align-center mb-2">
        <h3>Recent Orders</h3>
        <a href="{{ url_for('admin_orders') }}" class="btn-outline btn-sm">View All</a>
    </div>
    {% if recent_orders %}
    <div class="table-container" style="border:none">
        <table class="data-table">
            <thead>
                <tr>
                    <th>Order ID</th>
                    <th>User</th>
                    <th>Amount</th>
                    <th>Status</th>
                    <th>Date</th>
                    <th>Action</th>
                </tr>
            </thead>
            <tbody>
                {% for order in recent_orders %}
                <tr>
                    <td class="fw-bold text-primary">{{ order['order_id'] }}</td>
                    <td>{{ order['username'] }}</td>
                    <td class="fw-bold">{{ order['total_amount']|currency }}</td>
                    <td><span class="status-badge status-{{ order['order_status'] }}">{{ order['order_status']|title }}</span></td>
                    <td>{{ order['created_at']|timeago }}</td>
                    <td><a href="{{ url_for('admin_order_detail', order_id=order['order_id']) }}" class="btn-outline btn-sm">View</a></td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
    {% else %}
    <p class="text-muted text-center" style="padding:24px">No recent orders</p>
    {% endif %}
</div>

<!-- Recent Deposits -->
<div class="glass-card">
    <div class="d-flex justify-between align-center mb-2">
        <h3>Recent Deposits</h3>
        <a href="{{ url_for('admin_deposits') }}" class="btn-outline btn-sm">View All</a>
    </div>
    {% if recent_deposits %}
    <div class="table-container" style="border:none">
        <table class="data-table">
            <thead>
                <tr>
                    <th>ID</th>
                    <th>User</th>
                    <th>Amount</th>
                    <th>Method</th>
                    <th>Status</th>
                    <th>Action</th>
                </tr>
            </thead>
            <tbody>
                {% for dep in recent_deposits %}
                <tr>
                    <td>#{{ dep['id'] }}</td>
                    <td>{{ dep['username'] }}</td>
                    <td class="fw-bold">{{ dep['amount']|currency }}</td>
                    <td>{{ dep['method']|title }}</td>
                    <td><span class="status-badge status-{{ dep['status'] }}">{{ dep['status']|title }}</span></td>
                    <td>
                        {% if dep['status'] == 'pending' %}
                        <a href="{{ url_for('admin_deposit_action', deposit_id=dep['id'], action='approve') }}" class="btn-neon-green btn-sm" onclick="return confirm('Approve this deposit?')">Approve</a>
                        <a href="{{ url_for('admin_deposit_action', deposit_id=dep['id'], action='reject') }}" class="btn-neon-red btn-sm" onclick="return confirm('Reject this deposit?')">Reject</a>
                        {% else %}
                        <span class="text-muted">-</span>
                        {% endif %}
                    </td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
    {% else %}
    <p class="text-muted text-center" style="padding:24px">No recent deposits</p>
    {% endif %}
</div>
{% endblock %}
'''

ADMIN_PRODUCTS_TEMPLATE = '''
{% extends admin_base %}
{% block title %}Products{% endblock %}
{% block admin_content %}
<div class="admin-header">
    <h2>Products Management</h2>
    <a href="{{ url_for('admin_product_add') }}" class="btn-neon"><i class='bx bx-plus'></i> Add Product</a>
</div>

{% if products %}
<div class="glass-card" style="padding:0;overflow:hidden">
    <div class="table-container" style="border:none">
        <table class="data-table">
            <thead>
                <tr>
                    <th>ID</th>
                    <th>Product</th>
                    <th>Category</th>
                    <th>Price</th>
                    <th>Stock</th>
                    <th>Sold</th>
                    <th>Status</th>
                    <th>Actions</th>
                </tr>
            </thead>
            <tbody>
                {% for p in products %}
                <tr>
                    <td>#{{ p['id'] }}</td>
                    <td>
                        <div class="d-flex align-center gap-1">
                            <span style="font-size:20px">{{ p['image_url'] or '📦' }}</span>
                            <span class="fw-semibold">{{ p['name']|truncate_text(30) }}</span>
                        </div>
                    </td>
                    <td>{{ p['category_name'] or '-' }}</td>
                    <td class="fw-bold">{{ p['price']|currency }}</td>
                    <td>{% if p['stock_quantity'] == -1 %}∞{% else %}{{ p['stock_quantity'] }}{% endif %}</td>
                    <td>{{ p['sold_count'] }}</td>
                    <td><span class="status-badge {% if p['is_active'] %}status-approved{% else %}status-rejected{% endif %}">{% if p['is_active'] %}Active{% else %}Inactive{% endif %}</span></td>
                    <td>
                        <a href="{{ url_for('admin_product_edit', product_id=p['id']) }}" class="btn-outline btn-sm"><i class='bx bx-edit'></i></a>
                        <a href="{{ url_for('admin_product_delete', product_id=p['id']) }}" class="btn-neon-red btn-sm" onclick="return confirm('Delete this product?')"><i class='bx bx-trash'></i></a>
                    </td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
</div>
{% else %}
<div class="glass-card text-center" style="padding:60px">
    <i class='bx bx-package' style="font-size:48px;color:var(--text-muted);display:block;margin-bottom:16px"></i>
    <h3>No Products</h3>
    <p class="text-muted mb-3">Add your first product</p>
    <a href="{{ url_for('admin_product_add') }}" class="btn-neon"><i class='bx bx-plus'></i> Add Product</a>
</div>
{% endif %}
{% endblock %}
'''

ADMIN_PRODUCT_FORM_TEMPLATE = '''
{% extends admin_base %}
{% block title %}{{ 'Edit' if product else 'Add' }} Product{% endblock %}
{% block admin_content %}
<div class="admin-header">
    <h2>{{ 'Edit' if product else 'Add New' }} Product</h2>
    <a href="{{ url_for('admin_products') }}" class="btn-outline"><i class='bx bx-arrow-back'></i> Back</a>
</div>

<div class="glass-card">
    <form method="POST">
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px">
            <div class="form-group">
                <label>Product Name *</label>
                <input type="text" name="name" class="form-input" value="{{ product['name'] if product else '' }}" required>
            </div>
            <div class="form-group">
                <label>Category</label>
                <select name="category_id" class="form-input">
                    <option value="">Select Category</option>
                    {% for cat in categories %}
                    <option value="{{ cat['id'] }}" {% if product and product['category_id'] == cat['id'] %}selected{% endif %}>{{ cat['name'] }}</option>
                    {% endfor %}
                </select>
            </div>
            <div class="form-group">
                <label>Price ({{ settings.currency_symbol }}) *</label>
                <input type="number" name="price" class="form-input" step="0.01" value="{{ product['price'] if product else '' }}" required>
            </div>
            <div class="form-group">
                <label>Original Price</label>
                <input type="number" name="original_price" class="form-input" step="0.01" value="{{ product['original_price'] if product else '' }}">
            </div>
            <div class="form-group">
                <label>Discount %</label>
                <input type="number" name="discount_percent" class="form-input" step="0.01" value="{{ product['discount_percent'] if product else '0' }}">
            </div>
            <div class="form-group">
                <label>Stock Quantity (-1 for unlimited)</label>
                <input type="number" name="stock_quantity" class="form-input" value="{{ product['stock_quantity'] if product else '-1' }}">
            </div>
            <div class="form-group">
                <label>Image (emoji or URL)</label>
                <input type="text" name="image_url" class="form-input" value="{{ product['image_url'] if product else '' }}" placeholder="📦">
            </div>
            <div class="form-group">
                <label>Delivery Type</label>
                <select name="delivery_type" class="form-input">
                    <option value="auto" {% if product and product['delivery_type']=='auto' %}selected{% endif %}>Auto (Instant)</option>
                    <option value="manual" {% if product and product['delivery_type']=='manual' %}selected{% endif %}>Manual</option>
                </select>
            </div>
        </div>
        <div class="form-group">
            <label>Short Description</label>
            <input type="text" name="short_description" class="form-input" value="{{ product['short_description'] if product else '' }}">
        </div>
        <div class="form-group">
            <label>Description</label>
            <textarea name="description" class="form-input" rows="5">{{ product['description'] if product else '' }}</textarea>
        </div>
        <div class="form-group">
            <label>Delivery Content (Keys/License - one per line for auto delivery)</label>
            <textarea name="delivery_content" class="form-input" rows="5" placeholder="Enter keys, one per line">{{ product['delivery_content'] if product else '' }}</textarea>
        </div>
        <div class="d-flex gap-1">
            <label style="display:flex;align-items:center;gap:8px;cursor:pointer;font-size:14px">
                <input type="checkbox" name="is_featured" value="1" {% if product and product['is_featured'] %}checked{% endif %}> Featured
            </label>
            <label style="display:flex;align-items:center;gap:8px;cursor:pointer;font-size:14px;margin-left:16px">
                <input type="checkbox" name="is_active" value="1" {% if not product or product['is_active'] %}checked{% endif %}> Active
            </label>
        </div>
        <div class="mt-3">
            <button type="submit" class="btn-neon"><i class='bx bx-save'></i> {{ 'Update' if product else 'Create' }} Product</button>
        </div>
    </form>
</div>
{% endblock %}
'''

ADMIN_ORDERS_TEMPLATE = '''
{% extends admin_base %}
{% block title %}Orders{% endblock %}
{% block admin_content %}
<div class="admin-header">
    <h2>Orders Management</h2>
    <span class="text-muted">{{ orders|length }} total orders</span>
</div>

{% if orders %}
<div class="glass-card" style="padding:0;overflow:hidden">
    <div class="table-container" style="border:none">
        <table class="data-table">
            <thead>
                <tr>
                    <th>Order ID</th>
                    <th>User</th>
                    <th>Items</th>
                    <th>Total</th>
                    <th>Payment</th>
                    <th>Status</th>
                    <th>Date</th>
                    <th>Actions</th>
                </tr>
            </thead>
            <tbody>
                {% for o in orders %}
                <tr>
                    <td class="fw-bold text-primary">{{ o['order_id'] }}</td>
                    <td>{{ o['username'] }}</td>
                    <td>{{ o['item_count'] }}</td>
                    <td class="fw-bold">{{ o['total_amount']|currency }}</td>
                    <td><span class="status-badge status-{{ o['payment_status'] }}">{{ o['payment_status']|title }}</span></td>
                    <td><span class="status-badge status-{{ o['order_status'] }}">{{ o['order_status']|title }}</span></td>
                    <td>{{ o['created_at']|timeago }}</td>
                    <td>
                        <a href="{{ url_for('admin_order_detail', order_id=o['order_id']) }}" class="btn-outline btn-sm"><i class='bx bx-show'></i></a>
                    </td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
</div>
{% else %}
<div class="glass-card text-center" style="padding:60px">
    <i class='bx bx-cart' style="font-size:48px;color:var(--text-muted);display:block;margin-bottom:16px"></i>
    <h3>No Orders Yet</h3>
</div>
{% endif %}
{% endblock %}
'''

ADMIN_ORDER_DETAIL_TEMPLATE = '''
{% extends admin_base %}
{% block title %}Order {{ order['order_id'] }}{% endblock %}
{% block admin_content %}
<div class="admin-header">
    <div>
        <h2>Order {{ order['order_id'] }}</h2>
        <p class="text-secondary">Placed by {{ order['username'] }} on {{ order['created_at'] }}</p>
    </div>
    <a href="{{ url_for('admin_orders') }}" class="btn-outline"><i class='bx bx-arrow-back'></i> Back</a>
</div>

<div style="display:grid;grid-template-columns:1fr 360px;gap:24px">
    <!-- Order Items -->
    <div class="glass-card">
        <h3 class="mb-2">Order Items</h3>
        {% for item in order_items %}
        <div style="padding:12px 0;{% if not loop.last %}border-bottom:1px solid var(--border-color){% endif %}">
            <div class="d-flex justify-between align-center">
                <div>
                    <div class="fw-semibold">{{ item['product_name'] }}</div>
                    <div class="text-muted" style="font-size:13px">Qty: {{ item['quantity'] }} × {{ item['unit_price']|currency }}</div>
                </div>
                <div class="text-right">
                    <div class="fw-bold">{{ item['total_price']|currency }}</div>
                    <span class="status-badge {% if item['is_delivered'] %}status-approved{% else %}status-pending{% endif %}">{% if item['is_delivered'] %}Delivered{% else %}Pending{% endif %}</span>
                </div>
            </div>
            {% if not item['is_delivered'] %}
            <form method="POST" action="{{ url_for('admin_deliver_item', item_id=item['id']) }}" class="mt-2">
                <div class="d-flex gap-1">
                    <input type="text" name="delivery_data" class="form-input" placeholder="Enter delivery key/license" required style="flex:1">
                    <button type="submit" class="btn-neon-green btn-sm"><i class='bx bx-send'></i> Deliver</button>
                </div>
            </form>
            {% else %}
            <div class="mt-2" style="padding:8px 12px;background:rgba(46,204,113,0.05);border:1px solid rgba(46,204,113,0.15);border-radius:8px;font-size:13px">
                <span class="text-green"><i class='bx bx-check'></i> Delivered:</span>
                <code style="color:var(--primary);margin-left:8px">{{ item['delivery_data'] }}</code>
            </div>
            {% endif %}
        </div>
        {% endfor %}
    </div>

    <!-- Order Info -->
    <div>
        <div class="glass-card mb-3">
            <h3 class="mb-2">Summary</h3>
            <div class="d-flex justify-between mb-1"><span class="text-muted">Subtotal</span><span>{{ order['subtotal']|currency }}</span></div>
            {% if order['discount_amount'] > 0 %}
            <div class="d-flex justify-between mb-1"><span class="text-muted">Discount</span><span class="text-green">-{{ order['discount_amount']|currency }}</span></div>
            {% endif %}
            <div class="d-flex justify-between" style="padding-top:12px;border-top:1px solid var(--border-color)"><span class="fw-bold">Total</span><span class="fw-bold" style="font-size:20px;color:var(--primary)">{{ order['total_amount']|currency }}</span></div>
        </div>

        <div class="glass-card mb-3">
            <h3 class="mb-2">Update Status</h3>
            <form method="POST" action="{{ url_for('admin_order_update', order_id=order['order_id']) }}">
                <div class="form-group">
                    <label>Order Status</label>
                    <select name="order_status" class="form-input">
                        <option value="pending" {% if order['order_status']=='pending' %}selected{% endif %}>Pending</option>
                        <option value="processing" {% if order['order_status']=='processing' %}selected{% endif %}>Processing</option>
                        <option value="completed" {% if order['order_status']=='completed' %}selected{% endif %}>Completed</option>
                        <option value="rejected" {% if order['order_status']=='rejected' %}selected{% endif %}>Rejected</option>
                    </select>
                </div>
                <div class="form-group">
                    <label>Payment Status</label>
                    <select name="payment_status" class="form-input">
                        <option value="pending" {% if order['payment_status']=='pending' %}selected{% endif %}>Pending</option>
                        <option value="paid" {% if order['payment_status']=='paid' %}selected{% endif %}>Paid</option>
                        <option value="refunded" {% if order['payment_status']=='refunded' %}selected{% endif %}>Refunded</option>
                    </select>
                </div>
                <button type="submit" class="btn-neon w-100"><i class='bx bx-save'></i> Update</button>
            </form>
        </div>
    </div>
</div>
{% endblock %}
'''

ADMIN_DEPOSITS_TEMPLATE = '''
{% extends admin_base %}
{% block title %}Deposits{% endblock %}
{% block admin_content %}
<div class="admin-header">
    <h2>Deposits Management</h2>
    <div class="tabs" style="margin:0;background:transparent;border:none;padding:0">
        <a href="{{ url_for('admin_deposits', status='pending') }}" class="tab-btn {% if request.args.get('status','pending')=='pending' %}active{% endif %}">Pending</a>
        <a href="{{ url_for('admin_deposits', status='approved') }}" class="tab-btn {% if request.args.get('status')=='approved' %}active{% endif %}">Approved</a>
        <a href="{{ url_for('admin_deposits', status='rejected') }}" class="tab-btn {% if request.args.get('status')=='rejected' %}active{% endif %}">Rejected</a>
        <a href="{{ url_for('admin_deposits', status='all') }}" class="tab-btn {% if request.args.get('status')=='all' %}active{% endif %}">All</a>
    </div>
</div>

{% if deposits %}
<div class="glass-card" style="padding:0;overflow:hidden">
    <div class="table-container" style="border:none">
        <table class="data-table">
            <thead>
                <tr>
                    <th>ID</th>
                    <th>User</th>
                    <th>Amount</th>
                    <th>Method</th>
                    <th>TXN ID</th>
                    <th>Sender</th>
                    <th>Status</th>
                    <th>Date</th>
                    <th>Actions</th>
                </tr>
            </thead>
            <tbody>
                {% for d in deposits %}
                <tr>
                    <td>#{{ d['id'] }}</td>
                    <td>{{ d['username'] }}</td>
                    <td class="fw-bold">{{ d['amount']|currency }}</td>
                    <td>{{ d['method']|title }}</td>
                    <td><span class="text-muted" style="font-size:12px">{{ d['transaction_id'] }}</span></td>
                    <td>{{ d['sender_number'] }}</td>
                    <td><span class="status-badge status-{{ d['status'] }}">{{ d['status']|title }}</span></td>
                    <td>{{ d['created_at']|timeago }}</td>
                    <td>
                        {% if d['status'] == 'pending' %}
                        <a href="{{ url_for('admin_deposit_action', deposit_id=d['id'], action='approve') }}" class="btn-neon-green btn-sm" onclick="return confirm('Approve deposit of {{ d['amount']|currency }}?')"><i class='bx bx-check'></i></a>
                        <a href="{{ url_for('admin_deposit_action', deposit_id=d['id'], action='reject') }}" class="btn-neon-red btn-sm" onclick="return confirm('Reject this deposit?')"><i class='bx bx-x'></i></a>
                        {% else %}
                        <span class="text-muted">-</span>
                        {% endif %}
                    </td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
</div>
{% else %}
<div class="glass-card text-center" style="padding:60px">
    <i class='bx bx-money' style="font-size:48px;color:var(--text-muted);display:block;margin-bottom:16px"></i>
    <h3>No Deposits Found</h3>
</div>
{% endif %}
{% endblock %}
'''

ADMIN_USERS_TEMPLATE = '''
{% extends admin_base %}
{% block title %}Users{% endblock %}
{% block admin_content %}
<div class="admin-header">
    <h2>Users Management</h2>
    <span class="text-muted">{{ users|length }} registered users</span>
</div>

{% if users %}
<div class="glass-card" style="padding:0;overflow:hidden">
    <div class="table-container" style="border:none">
        <table class="data-table">
            <thead>
                <tr>
                    <th>ID</th>
                    <th>User</th>
                    <th>Email</th>
                    <th>Phone</th>
                    <th>Balance</th>
                    <th>Orders</th>
                    <th>Status</th>
                    <th>Joined</th>
                    <th>Actions</th>
                </tr>
            </thead>
            <tbody>
                {% for u in users %}
                <tr>
                    <td>#{{ u['id'] }}</td>
                    <td>
                        <div class="d-flex align-center gap-1">
                            <div style="width:30px;height:30px;background:var(--gradient-primary);border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:12px;font-weight:700;color:#000">{{ u['username'][0]|upper }}</div>
                            <div>
                                <div class="fw-semibold">{{ u['username'] }}</div>
                                <div class="text-muted" style="font-size:11px">{{ u['full_name'] }}</div>
                            </div>
                        </div>
                    </td>
                    <td>{{ u['email'] }}</td>
                    <td>{{ u['phone'] or '-' }}</td>
                    <td class="fw-bold">{{ u['wallet_balance']|currency }}</td>
                    <td>{{ u['order_count'] }}</td>
                    <td><span class="status-badge {% if u['is_active'] %}status-approved{% else %}status-rejected{% endif %}">{% if u['is_active'] %}Active{% else %}Banned{% endif %}</span></td>
                    <td>{{ u['created_at']|timeago }}</td>
                    <td>
                        <a href="{{ url_for('admin_user_toggle', user_id=u['id']) }}" class="{% if u['is_active'] %}btn-neon-red{% else %}btn-neon-green{% endif %} btn-sm" onclick="return confirm('{{ 'Ban' if u['is_active'] else 'Unban' }} this user?')">
                            {% if u['is_active'] %}<i class='bx bx-block'></i>{% else %}<i class='bx bx-check'></i>{% endif %}
                        </a>
                    </td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
</div>
{% endif %}
{% endblock %}
'''

ADMIN_CATEGORIES_TEMPLATE = '''
{% extends admin_base %}
{% block title %}Categories{% endblock %}
{% block admin_content %}
<div class="admin-header">
    <h2>Categories Management</h2>
</div>

<div class="glass-card mb-3">
    <h3 class="mb-2">{{ 'Edit' if edit_cat else 'Add New' }} Category</h3>
    <form method="POST" action="{{ url_for('admin_categories') }}">
        {% if edit_cat %}<input type="hidden" name="category_id" value="{{ edit_cat['id'] }}">{% endif %}
        <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:16px">
            <div class="form-group">
                <label>Name</label>
                <input type="text" name="name" class="form-input" value="{{ edit_cat['name'] if edit_cat else '' }}" required>
            </div>
            <div class="form-group">
                <label>Icon (Boxicons class)</label>
                <input type="text" name="icon" class="form-input" value="{{ edit_cat['icon'] if edit_cat else '' }}" placeholder="bx-code-alt">
            </div>
            <div class="form-group">
                <label>Color</label>
                <input type="color" name="color" class="form-input" value="{{ edit_cat['color'] if edit_cat else '#00f2fe' }}" style="height:44px;padding:4px">
            </div>
        </div>
        <div class="form-group">
            <label>Description</label>
            <input type="text" name="description" class="form-input" value="{{ edit_cat['description'] if edit_cat else '' }}">
        </div>
        <div class="d-flex gap-1">
            <button type="submit" class="btn-neon"><i class='bx bx-save'></i> {{ 'Update' if edit_cat else 'Add' }}</button>
            {% if edit_cat %}<a href="{{ url_for('admin_categories') }}" class="btn-outline">Cancel</a>{% endif %}
        </div>
    </form>
</div>

{% if categories %}
<div class="glass-card" style="padding:0;overflow:hidden">
    <div class="table-container" style="border:none">
        <table class="data-table">
            <thead>
                <tr><th>ID</th><th>Icon</th><th>Name</th><th>Slug</th><th>Products</th><th>Status</th><th>Actions</th></tr>
            </thead>
            <tbody>
                {% for c in categories %}
                <tr>
                    <td>#{{ c['id'] }}</td>
                    <td><div style="width:36px;height:36px;background:{{ c['color'] }}20;color:{{ c['color'] }};border-radius:10px;display:flex;align-items:center;justify-content:center"><i class='bx {{ c["icon"] }}'></i></div></td>
                    <td class="fw-semibold">{{ c['name'] }}</td>
                    <td class="text-muted">{{ c['slug'] }}</td>
                    <td>{{ c['product_count'] }}</td>
                    <td><span class="status-badge {% if c['is_active'] %}status-approved{% else %}status-rejected{% endif %}">{% if c['is_active'] %}Active{% else %}Inactive{% endif %}</span></td>
                    <td>
                        <a href="{{ url_for('admin_categories', edit=c['id']) }}" class="btn-outline btn-sm"><i class='bx bx-edit'></i></a>
                        <a href="{{ url_for('admin_category_delete', cat_id=c['id']) }}" class="btn-neon-red btn-sm" onclick="return confirm('Delete this category?')"><i class='bx bx-trash'></i></a>
                    </td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
</div>
{% endif %}
{% endblock %}
'''

ADMIN_SUPPORT_TEMPLATE = '''
{% extends admin_base %}
{% block title %}Support{% endblock %}
{% block admin_content %}
<div class="admin-header">
    <h2>Support Tickets</h2>
</div>

{% if tickets %}
<div style="display:flex;flex-direction:column;gap:12px">
    {% for t in tickets %}
    <div class="glass-card">
        <div class="d-flex justify-between align-center flex-wrap gap-2 mb-2">
            <div>
                <span class="fw-bold text-primary">{{ t['ticket_id'] }}</span>
                <span class="text-muted" style="margin-left:8px">by {{ t['username'] }}</span>
                <span class="text-muted" style="margin-left:8px">{{ t['created_at']|timeago }}</span>
            </div>
            <div class="d-flex gap-1">
                <span class="status-badge status-{{ 'approved' if t['status']=='resolved' else ('pending' if t['status']=='open' else 'processing') }}">{{ t['status']|title }}</span>
                <span class="status-badge" style="background:rgba(168,85,247,0.15);color:var(--purple)">{{ t['priority']|title }}</span>
            </div>
        </div>
        <h4 class="mb-1">{{ t['subject'] }}</h4>
        <p class="text-secondary mb-2" style="font-size:14px">{{ t['message'] }}</p>

        {% if t['admin_reply'] %}
        <div style="padding:12px;background:rgba(46,204,113,0.05);border:1px solid rgba(46,204,113,0.15);border-radius:8px;margin-bottom:12px">
            <div class="fw-semibold text-green mb-1"><i class='bx bx-support'></i> Admin Reply:</div>
            <p class="text-secondary" style="font-size:14px">{{ t['admin_reply'] }}</p>
        </div>
        {% endif %}

        <form method="POST" action="{{ url_for('admin_support_reply', ticket_id=t['ticket_id']) }}">
            <div class="d-flex gap-1">
                <input type="text" name="reply" class="form-input" placeholder="Type your reply..." required style="flex:1">
                <select name="status" class="form-input" style="width:auto">
                    <option value="open" {% if t['status']=='open' %}selected{% endif %}>Open</option>
                    <option value="in_progress" {% if t['status']=='in_progress' %}selected{% endif %}>In Progress</option>
                    <option value="resolved" {% if t['status']=='resolved' %}selected{% endif %}>Resolved</option>
                </select>
                <button type="submit" class="btn-neon btn-sm"><i class='bx bx-send'></i> Reply</button>
            </div>
        </form>
    </div>
    {% endfor %}
</div>
{% else %}
<div class="glass-card text-center" style="padding:60px">
    <i class='bx bx-support' style="font-size:48px;color:var(--text-muted);display:block;margin-bottom:16px"></i>
    <h3>No Support Tickets</h3>
</div>
{% endif %}
{% endblock %}
'''

ADMIN_COUPONS_TEMPLATE = '''
{% extends admin_base %}
{% block title %}Coupons{% endblock %}
{% block admin_content %}
<div class="admin-header">
    <h2>Coupons Management</h2>
</div>

<div class="glass-card mb-3">
    <h3 class="mb-2">Add New Coupon</h3>
    <form method="POST" action="{{ url_for('admin_coupons') }}">
        <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(180px,1fr));gap:16px">
            <div class="form-group"><label>Code</label><input type="text" name="code" class="form-input" required placeholder="e.g. SAVE20"></div>
            <div class="form-group"><label>Type</label><select name="discount_type" class="form-input"><option value="percentage">Percentage</option><option value="fixed">Fixed</option></select></div>
            <div class="form-group"><label>Value</label><input type="number" name="discount_value" class="form-input" required step="0.01"></div>
            <div class="form-group"><label>Min Order</label><input type="number" name="min_order_amount" class="form-input" value="0"></div>
            <div class="form-group"><label>Max Discount</label><input type="number" name="max_discount" class="form-input" value="0"></div>
            <div class="form-group"><label>Usage Limit</label><input type="number" name="usage_limit" class="form-input" value="-1"></div>
        </div>
        <button type="submit" class="btn-neon"><i class='bx bx-plus'></i> Add Coupon</button>
    </form>
</div>

{% if coupons %}
<div class="glass-card" style="padding:0;overflow:hidden">
    <div class="table-container" style="border:none">
        <table class="data-table">
            <thead>
                <tr><th>Code</th><th>Type</th><th>Value</th><th>Min Order</th><th>Used</th><th>Limit</th><th>Status</th><th>Actions</th></tr>
            </thead>
            <tbody>
                {% for c in coupons %}
                <tr>
                    <td class="fw-bold text-primary">{{ c['code'] }}</td>
                    <td>{{ c['discount_type']|title }}</td>
                    <td>{% if c['discount_type']=='percentage' %}{{ c['discount_value'] }}%{% else %}{{ c['discount_value']|currency }}{% endif %}</td>
                    <td>{{ c['min_order_amount']|currency }}</td>
                    <td>{{ c['used_count'] }}</td>
                    <td>{% if c['usage_limit']==-1 %}∞{% else %}{{ c['usage_limit'] }}{% endif %}</td>
                    <td><span class="status-badge {% if c['is_active'] %}status-approved{% else %}status-rejected{% endif %}">{% if c['is_active'] %}Active{% else %}Inactive{% endif %}</span></td>
                    <td><a href="{{ url_for('admin_coupon_delete', coupon_id=c['id']) }}" class="btn-neon-red btn-sm" onclick="return confirm('Delete?')"><i class='bx bx-trash'></i></a></td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
</div>
{% endif %}
{% endblock %}
'''

ADMIN_SETTINGS_TEMPLATE = '''
{% extends admin_base %}
{% block title %}Settings{% endblock %}
{% block admin_content %}
<div class="admin-header">
    <h2>System Settings</h2>
</div>

<div class="glass-card">
    <form method="POST" action="{{ url_for('admin_settings') }}">
        {% for setting in settings_list %}
        <div class="form-group">
            <label>{{ setting['description'] or setting['setting_key'] }}</label>
            {% if setting['setting_type'] == 'toggle' %}
            <select name="{{ setting['setting_key'] }}" class="form-input">
                <option value="0" {% if setting['setting_value']=='0' %}selected{% endif %}>Disabled</option>
                <option value="1" {% if setting['setting_value']=='1' %}selected{% endif %}>Enabled</option>
            </select>
            {% elif setting['setting_type'] == 'textarea' %}
            <textarea name="{{ setting['setting_key'] }}" class="form-input">{{ setting['setting_value'] }}</textarea>
            {% else %}
            <input type="{{ 'number' if setting['setting_type']=='number' else 'text' }}" name="{{ setting['setting_key'] }}" class="form-input" value="{{ setting['setting_value'] }}">
            {% endif %}
        </div>
        {% endfor %}
        <button type="submit" class="btn-neon btn-lg"><i class='bx bx-save'></i> Save Settings</button>
    </form>
</div>
{% endblock %}
'''

ADMIN_ANNOUNCEMENTS_TEMPLATE = '''
{% extends admin_base %}
{% block title %}Announcements{% endblock %}
{% block admin_content %}
<div class="admin-header">
    <h2>Announcements</h2>
</div>

<div class="glass-card mb-3">
    <h3 class="mb-2">New Announcement</h3>
    <form method="POST" action="{{ url_for('admin_announcements') }}">
        <div style="display:grid;grid-template-columns:1fr 120px;gap:16px">
            <div class="form-group"><label>Title</label><input type="text" name="title" class="form-input" required></div>
            <div class="form-group"><label>Type</label><select name="type" class="form-input"><option value="info">Info</option><option value="success">Success</option><option value="warning">Warning</option><option value="danger">Danger</option></select></div>
        </div>
        <div class="form-group"><label>Content</label><textarea name="content" class="form-input" required></textarea></div>
        <button type="submit" class="btn-neon"><i class='bx bx-plus'></i> Add Announcement</button>
    </form>
</div>

{% if announcements %}
<div style="display:flex;flex-direction:column;gap:8px">
    {% for a in announcements %}
    <div class="glass-card d-flex justify-between align-center" style="padding:16px">
        <div>
            <span class="status-badge status-{{ 'approved' if a['type']=='success' else ('rejected' if a['type']=='danger' else ('pending' if a['type']=='warning' else 'processing')) }}">{{ a['type']|title }}</span>
            <span class="fw-semibold" style="margin-left:8px">{{ a['title'] }}</span>
            <div class="text-muted" style="font-size:13px;margin-top:4px">{{ a['content']|truncate_text(100) }}</div>
        </div>
        <a href="{{ url_for('admin_announcement_delete', ann_id=a['id']) }}" class="btn-neon-red btn-sm" onclick="return confirm('Delete?')"><i class='bx bx-trash'></i></a>
    </div>
    {% endfor %}
</div>
{% endif %}
{% endblock %}
'''

ADMIN_LOGS_TEMPLATE = '''
{% extends admin_base %}
{% block title %}Activity Logs{% endblock %}
{% block admin_content %}
<div class="admin-header">
    <h2>Activity Logs</h2>
</div>

{% if logs %}
<div class="glass-card" style="padding:0;overflow:hidden">
    <div class="table-container" style="border:none">
        <table class="data-table">
            <thead>
                <tr><th>ID</th><th>Action</th><th>Details</th><th>IP</th><th>Time</th></tr>
            </thead>
            <tbody>
                {% for log in logs %}
                <tr>
                    <td>#{{ log['id'] }}</td>
                    <td class="fw-semibold">{{ log['action'] }}</td>
                    <td class="text-muted" style="font-size:13px">{{ log['details']|truncate_text(60) }}</td>
                    <td class="text-muted">{{ log['ip_address'] }}</td>
                    <td>{{ log['created_at']|timeago }}</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
</div>
{% else %}
<div class="glass-card text-center" style="padding:60px">
    <i class='bx bx-history' style="font-size:48px;color:var(--text-muted);display:block;margin-bottom:16px"></i>
    <h3>No Activity Logs</h3>
</div>
{% endif %}
{% endblock %}
'''

# ============================================================
# USER ROUTES
# ============================================================

@app.route('/')
def home():
    """Homepage with featured products and categories."""
    db = get_db()
    if 'user_id' not in session:
        return render_page(GUEST_HOME_TEMPLATE, BASE_TEMPLATE)
    categories = db.execute('''
        SELECT c.*, (SELECT COUNT(*) FROM products WHERE category_id = c.id AND is_active = 1) as product_count
        FROM categories c WHERE c.is_active = 1 ORDER BY c.sort_order, c.name
    ''').fetchall()

    featured_products = db.execute('''
        SELECT p.*, c.name as category_name, c.slug as category_slug
        FROM products p LEFT JOIN categories c ON p.category_id = c.id
        WHERE p.is_active = 1 AND p.is_featured = 1
        ORDER BY p.sold_count DESC LIMIT 8
    ''').fetchall()

    latest_products = db.execute('''
        SELECT p.*, c.name as category_name, c.slug as category_slug
        FROM products p LEFT JOIN categories c ON p.category_id = c.id
        WHERE p.is_active = 1
        ORDER BY p.created_at DESC LIMIT 8
    ''').fetchall()

    announcements = db.execute('SELECT * FROM announcements WHERE is_active = 1 AND show_on_homepage = 1 ORDER BY created_at DESC').fetchall()

    total_products = db.execute('SELECT COUNT(*) as c FROM products WHERE is_active = 1').fetchone()['c']
    total_users = db.execute('SELECT COUNT(*) as c FROM users').fetchone()['c']
    total_orders = db.execute('SELECT COUNT(*) as c FROM orders WHERE order_status = "completed"').fetchone()['c']

    return render_page(HOME_TEMPLATE, BASE_TEMPLATE,
        categories=categories, featured_products=featured_products,
        latest_products=latest_products, announcements=announcements,
        total_products=total_products, total_users=total_users, total_orders=total_orders)


@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login page."""
    if 'user_id' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        db = get_db()
        user = db.execute('SELECT * FROM users WHERE (username = ? OR email = ?) AND is_active = 1',
                         (username, username)).fetchone()

        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['id']
            db.execute('UPDATE users SET last_login = ? WHERE id = ?',
                      (datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'), user['id']))
            db.commit()
            log_activity(user_id=user['id'], action='login', details='User logged in')
            flash('Welcome back!', 'success')
            next_url = request.args.get('next', url_for('dashboard'))
            return redirect(next_url)
        else:
            flash('Invalid username or password.', 'danger')

    return render_page(LOGIN_TEMPLATE, BASE_TEMPLATE)


@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration page."""
    if 'user_id' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        telegram_username = request.form.get('telegram_username', '').strip()
        username = re.sub(r'[^a-zA-Z0-9_]', '', telegram_username.lstrip('@')).lower() or f'user{secrets.token_hex(3)}'
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        referral_code = ''

        # Validation
        if not all([full_name, telegram_username, email, phone, password]):
            flash('All required fields must be filled.', 'danger')
            return redirect(url_for('register'))

        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return redirect(url_for('register'))

        if len(password) < 6:
            flash('Password must be at least 6 characters.', 'danger')
            return redirect(url_for('register'))

        if not re.match(r'^[a-zA-Z0-9_]+$', username):
            flash('Username can only contain letters, numbers, and underscores.', 'danger')
            return redirect(url_for('register'))

        db = get_db()

        # Check if username/email exists
        existing = db.execute('SELECT id FROM users WHERE username = ? OR email = ?', (username, email)).fetchone()
        if existing:
            flash('Username or email already exists.', 'danger')
            return redirect(url_for('register'))

        # Handle referral
        referred_by = None
        if referral_code:
            referrer = db.execute('SELECT id FROM users WHERE referral_code = ?', (referral_code,)).fetchone()
            if referrer:
                referred_by = referrer['id']

        # Create user
        user_referral_code = f"REF{secrets.token_hex(4).upper()}"
        db.execute('''
            INSERT INTO users (username, email, password_hash, full_name, phone, telegram_username, referral_code, referred_by)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (username, email, generate_password_hash(password), full_name, phone, telegram_username, user_referral_code, referred_by))

        user_id = db.execute('SELECT last_insert_rowid()').fetchone()[0]

        # Welcome bonus
        db.execute('UPDATE users SET wallet_balance = 0 WHERE id = ?', (user_id,))

        # Create welcome notification
        db.execute('INSERT INTO notifications (user_id, title, message, type) VALUES (?, ?, ?, ?)',
                  (user_id, 'Welcome to SOHAG BD SHOP!',
                   'Your account has been created successfully. Start exploring our marketplace!',
                   'success'))

        db.commit()
        log_activity(user_id=user_id, action='register', details=f'New user registered: {username}')

        session['user_id'] = user_id
        flash('Account created successfully! Welcome to SOHAG BD SHOP!', 'success')
        return redirect(url_for('dashboard'))

    return render_page(REGISTER_TEMPLATE, BASE_TEMPLATE)


@app.route('/logout')
def logout():
    """User logout."""
    session.pop('user_id', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('home'))


@app.route('/dashboard')
@login_required
def dashboard():
    """User dashboard."""
    db = get_db()
    user_id = session['user_id']

    order_count = db.execute('SELECT COUNT(*) as c FROM orders WHERE user_id = ?', (user_id,)).fetchone()['c']
    completed_orders = db.execute('SELECT COUNT(*) as c FROM orders WHERE user_id = ? AND order_status = "completed"', (user_id,)).fetchone()['c']

    recent_orders = db.execute('''
        SELECT o.*, (SELECT COUNT(*) FROM order_items WHERE order_id = o.id) as item_count
        FROM orders o WHERE o.user_id = ? ORDER BY o.created_at DESC LIMIT 5
    ''', (user_id,)).fetchall()

    recent_notifications = db.execute(
        'SELECT * FROM notifications WHERE user_id = ? ORDER BY created_at DESC LIMIT 5', (user_id,)
    ).fetchall()

    return render_page(DASHBOARD_TEMPLATE, BASE_TEMPLATE,
        order_count=order_count, completed_orders=completed_orders,
        recent_orders=recent_orders, recent_notifications=recent_notifications)


@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """User profile page."""
    db = get_db()
    user_id = session['user_id']

    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        phone = request.form.get('phone', '').strip()
        city = request.form.get('city', '').strip()
        country = request.form.get('country', '').strip()
        address = request.form.get('address', '').strip()
        bio = request.form.get('bio', '').strip()

        db.execute('''
            UPDATE users SET full_name=?, phone=?, city=?, country=?, address=?, bio=?, updated_at=?
            WHERE id=?
        ''', (full_name, phone, city, country, address, bio,
              datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'), user_id))
        db.commit()

        flash('Profile updated successfully!', 'success')
        return redirect(url_for('profile'))

    referral_bonus = get_setting('referral_bonus', '10')
    return render_page(PROFILE_TEMPLATE, BASE_TEMPLATE, referral_bonus=referral_bonus)


@app.route('/change-password', methods=['POST'])
@login_required
def change_password():
    """Change user password."""
    db = get_db()
    user = db.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()

    current_password = request.form.get('current_password', '')
    new_password = request.form.get('new_password', '')
    confirm_password = request.form.get('confirm_password', '')

    if not check_password_hash(user['password_hash'], current_password):
        flash('Current password is incorrect.', 'danger')
    elif new_password != confirm_password:
        flash('New passwords do not match.', 'danger')
    elif len(new_password) < 6:
        flash('Password must be at least 6 characters.', 'danger')
    else:
        db.execute('UPDATE users SET password_hash = ? WHERE id = ?',
                  (generate_password_hash(new_password), session['user_id']))
        db.commit()
        flash('Password changed successfully!', 'success')

    return redirect(url_for('profile'))


@app.route('/wallet')
@login_required
def wallet():
    """User wallet page."""
    db = get_db()
    transactions = db.execute(
        'SELECT * FROM wallet_transactions WHERE user_id = ? ORDER BY created_at DESC LIMIT 50',
        (session['user_id'],)
    ).fetchall()
    return render_page(WALLET_TEMPLATE, BASE_TEMPLATE, transactions=transactions)


@app.route('/deposit', methods=['GET', 'POST'])
@login_required
def deposit():
    """Deposit page."""
    db = get_db()

    if request.method == 'POST':
        amount = float(request.form.get('amount', 0))
        method = request.form.get('method', 'bkash')
        transaction_id = request.form.get('transaction_id', '').strip()
        sender_number = request.form.get('sender_number', '').strip()

        min_dep = float(get_setting('min_deposit', '50'))
        max_dep = float(get_setting('max_deposit', '100000'))

        if amount < min_dep:
            flash(f'Minimum deposit amount is {format_currency(min_dep)}', 'danger')
        elif amount > max_dep:
            flash(f'Maximum deposit amount is {format_currency(max_dep)}', 'danger')
        elif not transaction_id:
            flash('Transaction ID is required.', 'danger')
        else:
            db.execute('''
                INSERT INTO deposits (user_id, amount, method, transaction_id, sender_number)
                VALUES (?, ?, ?, ?, ?)
            ''', (session['user_id'], amount, method, transaction_id, sender_number))
            db.commit()

            create_notification(session['user_id'], 'Deposit Request Submitted',
                              f'Your deposit request of {format_currency(amount)} via {method.title()} has been submitted and is pending approval.',
                              'info')

            flash('Deposit request submitted successfully! It will be processed shortly.', 'success')
            return redirect(url_for('deposit'))

    deposits = db.execute(
        'SELECT * FROM deposits WHERE user_id = ? ORDER BY created_at DESC', (session['user_id'],)
    ).fetchall()

    return render_page(DEPOSIT_TEMPLATE, BASE_TEMPLATE, deposits=deposits,
        bkash_number=get_setting('bkash_number', '01XXXXXXXXX'),
        nagad_number=get_setting('nagad_number', '01XXXXXXXXX'),
        crypto_address=get_setting('crypto_address', '0x...'))


@app.route('/marketplace')
def marketplace():
    """Product marketplace page."""
    db = get_db()
    page = int(request.args.get('page', 1))
    per_page = int(get_setting('items_per_page', '12'))
    category_slug = request.args.get('category', '')
    search_query = request.args.get('q', '')
    sort = request.args.get('sort', 'newest')
    price_range = request.args.get('price_range', '')

    query = '''
        SELECT p.*, c.name as category_name, c.slug as category_slug
        FROM products p LEFT JOIN categories c ON p.category_id = c.id
        WHERE p.is_active = 1
    '''
    params = []

    if category_slug:
        query += ' AND c.slug = ?'
        params.append(category_slug)

    if search_query:
        query += ' AND (p.name LIKE ? OR p.description LIKE ? OR p.tags LIKE ?)'
        search_param = f'%{search_query}%'
        params.extend([search_param, search_param, search_param])

    if price_range:
        try:
            min_price, max_price = price_range.split('-')
            query += ' AND p.price >= ? AND p.price <= ?'
            params.extend([float(min_price), float(max_price)])
        except:
            pass

    # Count total
    count_query = query.replace(
        'SELECT p.*, c.name as category_name, c.slug as category_slug',
        'SELECT COUNT(*) as total'
    )
    total = db.execute(count_query, params).fetchone()['total']
    total_pages = max(1, (total + per_page - 1) // per_page)

    # Sort
    if sort == 'price_low':
        query += ' ORDER BY p.price ASC'
    elif sort == 'price_high':
        query += ' ORDER BY p.price DESC'
    elif sort == 'popular':
        query += ' ORDER BY p.sold_count DESC'
    elif sort == 'rating':
        query += ' ORDER BY p.rating DESC'
    else:
        query += ' ORDER BY p.created_at DESC'

    query += ' LIMIT ? OFFSET ?'
    params.extend([per_page, (page - 1) * per_page])

    products = db.execute(query, params).fetchall()

    all_categories = db.execute('SELECT * FROM categories WHERE is_active = 1 ORDER BY name').fetchall()

    wishlist_ids = []
    if 'user_id' in session:
        witems = db.execute('SELECT product_id FROM wishlist WHERE user_id = ?', (session['user_id'],)).fetchall()
        wishlist_ids = [w['product_id'] for w in witems]

    return render_page(MARKETPLACE_TEMPLATE, BASE_TEMPLATE,
        products=products, all_categories=all_categories, page=page,
        total_pages=total_pages, wishlist_ids=wishlist_ids)


@app.route('/product/<slug>')
def product_detail(slug):
    """Product detail page."""
    if 'user_id' not in session:
        return render_page(AUTH_GATE_TEMPLATE, BASE_TEMPLATE, product_name=slug.replace('-', ' ').title())
    db = get_db()
    product = db.execute('''
        SELECT p.*, c.name as category_name, c.slug as category_slug
        FROM products p LEFT JOIN categories c ON p.category_id = c.id
        WHERE p.slug = ? AND p.is_active = 1
    ''', (slug,)).fetchone()

    if not product:
        abort(404)

    # Increment view count
    db.execute('UPDATE products SET view_count = view_count + 1 WHERE id = ?', (product['id'],))
    db.commit()

    reviews = db.execute('''
        SELECT r.*, u.username FROM reviews r
        JOIN users u ON r.user_id = u.id
        WHERE r.product_id = ? AND r.is_approved = 1
        ORDER BY r.created_at DESC
    ''', (product['id'],)).fetchall()

    related_products = db.execute('''
        SELECT p.*, c.name as category_name FROM products p
        LEFT JOIN categories c ON p.category_id = c.id
        WHERE p.category_id = ? AND p.id != ? AND p.is_active = 1
        ORDER BY RANDOM() LIMIT 4
    ''', (product['category_id'], product['id'])).fetchall()

    return render_page(PRODUCT_DETAIL_TEMPLATE, BASE_TEMPLATE,
        product=product, reviews=reviews, related_products=related_products)


@app.route('/add-review/<int:product_id>', methods=['POST'])
@login_required
def add_review(product_id):
    """Add product review."""
    db = get_db()
    rating = int(request.form.get('rating', 5))
    comment = request.form.get('comment', '').strip()

    if rating < 1 or rating > 5:
        flash('Rating must be between 1 and 5.', 'danger')
        return redirect(request.referrer)

    # Check if already reviewed
    existing = db.execute('SELECT id FROM reviews WHERE user_id = ? AND product_id = ?',
                         (session['user_id'], product_id)).fetchone()

    if existing:
        db.execute('UPDATE reviews SET rating = ?, comment = ? WHERE id = ?',
                  (rating, comment, existing['id']))
    else:
        db.execute('INSERT INTO reviews (user_id, product_id, rating, comment) VALUES (?, ?, ?, ?)',
                  (session['user_id'], product_id, rating, comment))

    update_product_rating(product_id)
    db.commit()
    flash('Review submitted successfully!', 'success')

    product = db.execute('SELECT slug FROM products WHERE id = ?', (product_id,)).fetchone()
    return redirect(url_for('product_detail', slug=product['slug']))


@app.route('/categories')
def categories():
    """Categories page."""
    db = get_db()
    cats = db.execute('''
        SELECT c.*, (SELECT COUNT(*) FROM products WHERE category_id = c.id AND is_active = 1) as product_count
        FROM categories c WHERE c.is_active = 1 ORDER BY c.sort_order, c.name
    ''').fetchall()
    return render_page(CATEGORIES_TEMPLATE, BASE_TEMPLATE, categories=cats)


# ============================================================
# CART ROUTES
# ============================================================

@app.route('/cart')
@login_required
def cart_view():
    """Cart page."""
    db = get_db()
    cart_items = db.execute('''
        SELECT c.*, p.name, p.price, p.image_url, p.slug, p.stock_quantity,
               cat.name as category_name
        FROM cart c
        JOIN products p ON c.product_id = p.id
        LEFT JOIN categories cat ON p.category_id = cat.id
        WHERE c.user_id = ? AND p.is_active = 1
    ''', (session['user_id'],)).fetchall()

    subtotal = sum(item['price'] * item['quantity'] for item in cart_items)
    discount = 0
    total = subtotal - discount

    return render_page(CART_TEMPLATE, BASE_TEMPLATE,
        cart_items=cart_items, subtotal=subtotal, discount=discount, total=total)


@app.route('/cart/add', methods=['POST'])
@login_required
def cart_add():
    """Add item to cart."""
    data = request.get_json() if request.is_json else request.form
    product_id = data.get('product_id')
    quantity = int(data.get('quantity', 1))

    db = get_db()
    product = db.execute('SELECT * FROM products WHERE id = ? AND is_active = 1', (product_id,)).fetchone()

    if not product:
        return jsonify({'success': False, 'message': 'Product not found'})

    existing = db.execute('SELECT * FROM cart WHERE user_id = ? AND product_id = ?',
                         (session['user_id'], product_id)).fetchone()

    if existing:
        db.execute('UPDATE cart SET quantity = quantity + ? WHERE id = ?', (quantity, existing['id']))
    else:
        db.execute('INSERT INTO cart (user_id, product_id, quantity) VALUES (?, ?, ?)',
                  (session['user_id'], product_id, quantity))

    db.commit()
    cart_count = get_cart_count(session['user_id'])

    if request.is_json:
        return jsonify({'success': True, 'message': f'{product["name"]} added to cart!', 'cart_count': cart_count})

    flash(f'{product["name"]} added to cart!', 'success')
    return redirect(request.referrer or url_for('marketplace'))


@app.route('/cart/update', methods=['POST'])
@login_required
def cart_update():
    """Update cart item quantity."""
    data = request.get_json()
    product_id = data.get('product_id')
    quantity = int(data.get('quantity', 1))

    db = get_db()
    if quantity <= 0:
        db.execute('DELETE FROM cart WHERE user_id = ? AND product_id = ?', (session['user_id'], product_id))
    else:
        db.execute('UPDATE cart SET quantity = ? WHERE user_id = ? AND product_id = ?',
                  (quantity, session['user_id'], product_id))

    db.commit()
    return jsonify({'success': True})


@app.route('/cart/remove', methods=['POST'])
@login_required
def cart_remove():
    """Remove item from cart."""
    data = request.get_json()
    product_id = data.get('product_id')

    db = get_db()
    db.execute('DELETE FROM cart WHERE user_id = ? AND product_id = ?', (session['user_id'], product_id))
    db.commit()

    return jsonify({'success': True, 'message': 'Item removed from cart'})


# ============================================================
# CHECKOUT & ORDERS
# ============================================================

@app.route('/checkout', methods=['POST'])
@login_required
def checkout():
    """Process checkout."""
    db = get_db()
    user_id = session['user_id']

    cart_items = db.execute('''
        SELECT c.*, p.name, p.price, p.stock_quantity, p.delivery_content, p.delivery_type, p.image_url
        FROM cart c JOIN products p ON c.product_id = p.id
        WHERE c.user_id = ? AND p.is_active = 1
    ''', (user_id,)).fetchall()

    if not cart_items:
        flash('Your cart is empty.', 'warning')
        return redirect(url_for('marketplace'))

    subtotal = sum(item['price'] * item['quantity'] for item in cart_items)

    # Apply coupon
    coupon_code = request.form.get('coupon', '').strip()
    discount = 0
    if coupon_code:
        coupon = db.execute('SELECT * FROM coupons WHERE code = ? AND is_active = 1', (coupon_code,)).fetchone()
        if coupon and (coupon['usage_limit'] == -1 or coupon['used_count'] < coupon['usage_limit']):
            if subtotal >= coupon['min_order_amount']:
                if coupon['discount_type'] == 'percentage':
                    discount = subtotal * coupon['discount_value'] / 100
                    if coupon['max_discount'] > 0:
                        discount = min(discount, coupon['max_discount'])
                else:
                    discount = coupon['discount_value']
                discount = min(discount, subtotal)

    total = subtotal - discount

    # Check wallet balance
    user = db.execute('SELECT wallet_balance FROM users WHERE id = ?', (user_id,)).fetchone()
    if user['wallet_balance'] < total:
        flash('Insufficient wallet balance. Please deposit funds.', 'danger')
        return redirect(url_for('cart_view'))

    # Create order
    order_id = generate_order_id()
    db.execute('''
        INSERT INTO orders (order_id, user_id, subtotal, discount_amount, coupon_code, total_amount,
                           payment_method, payment_status, order_status, ip_address)
        VALUES (?, ?, ?, ?, ?, ?, 'wallet', 'paid', 'processing', ?)
    ''', (order_id, user_id, subtotal, discount, coupon_code, total, request.remote_addr or ''))

    order_db_id = db.execute('SELECT last_insert_rowid()').fetchone()[0]

    # Create order items and handle delivery
    for item in cart_items:
        delivery_data = ''
        if item['delivery_type'] == 'auto' and item['delivery_content']:
            keys = [k.strip() for k in item['delivery_content'].split('\n') if k.strip()]
            if keys:
                delivery_data = keys[0]
                # Remove used key
                remaining = '\n'.join(keys[1:])
                db.execute('UPDATE products SET delivery_content = ? WHERE id = ?', (remaining, item['product_id']))

        db.execute('''
            INSERT INTO order_items (order_id, product_id, product_name, quantity, unit_price, total_price,
                                    delivery_data, is_delivered, delivered_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (order_db_id, item['product_id'], item['name'], item['quantity'],
              item['price'], item['price'] * item['quantity'],
              delivery_data, 1 if delivery_data else 0,
              datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S') if delivery_data else None))

        # Update stock and sold count
        if item['stock_quantity'] != -1:
            db.execute('UPDATE products SET stock_quantity = stock_quantity - ? WHERE id = ? AND stock_quantity > 0',
                      (item['quantity'], item['product_id']))
        db.execute('UPDATE products SET sold_count = sold_count + ? WHERE id = ?', (item['quantity'], item['product_id']))

    # Deduct from wallet
    balance_before = user['wallet_balance']
    balance_after = balance_before - total
    db.execute('UPDATE users SET wallet_balance = ? WHERE id = ?', (balance_after, user_id))

    # Record wallet transaction
    db.execute('''
        INSERT INTO wallet_transactions (user_id, type, amount, balance_before, balance_after, description,
                                        reference_id, reference_type)
        VALUES (?, 'debit', ?, ?, ?, ?, ?, 'order')
    ''', (user_id, total, balance_before, balance_after, f'Order {order_id}', order_id))

    # Update coupon usage
    if coupon_code and discount > 0:
        db.execute('UPDATE coupons SET used_count = used_count + 1 WHERE code = ?', (coupon_code,))

    # Clear cart
    db.execute('DELETE FROM cart WHERE user_id = ?', (user_id,))

    # Handle referral bonus
    user_data = db.execute('SELECT referred_by FROM users WHERE id = ?', (user_id,)).fetchone()
    if user_data and user_data['referred_by']:
        ref_min = float(get_setting('referral_minimum_purchase', '100'))
        if total >= ref_min:
            ref_bonus = float(get_setting('referral_bonus', '10'))
            referrer = db.execute('SELECT wallet_balance FROM users WHERE id = ?', (user_data['referred_by'],)).fetchone()
            if referrer:
                db.execute('UPDATE users SET wallet_balance = wallet_balance + ? WHERE id = ?',
                          (ref_bonus, user_data['referred_by']))
                db.execute('''
                    INSERT INTO wallet_transactions (user_id, type, amount, balance_before, balance_after, description, reference_type)
                    VALUES (?, 'credit', ?, ?, ?, ?, 'referral')
                ''', (user_data['referred_by'], ref_bonus, referrer['wallet_balance'],
                      referrer['wallet_balance'] + ref_bonus, f'Referral bonus from {order_id}'))
                create_notification(user_data['referred_by'], 'Referral Bonus!',
                                  f'You received {format_currency(ref_bonus)} referral bonus!', 'success')

    db.commit()
    log_activity(user_id=user_id, action='order', details=f'Order placed: {order_id}')

    # Notification
    create_notification(user_id, 'Order Placed Successfully!',
                       f'Your order {order_id} has been placed. Total: {format_currency(total)}', 'success')

    flash(f'Order placed successfully! Order ID: {order_id}', 'success')
    return redirect(url_for('order_detail', order_id=order_id))


@app.route('/orders')
@login_required
def orders():
    """User orders page."""
    db = get_db()
    user_orders = db.execute('''
        SELECT o.*, (SELECT COUNT(*) FROM order_items WHERE order_id = o.id) as item_count
        FROM orders o WHERE o.user_id = ? ORDER BY o.created_at DESC
    ''', (session['user_id'],)).fetchall()

    # Attach items to each order
    orders_with_items = []
    for order in user_orders:
        items = db.execute('''
            SELECT oi.*, p.image_url FROM order_items oi
            LEFT JOIN products p ON oi.product_id = p.id
            WHERE oi.order_id = ?
        ''', (order['id'],)).fetchall()
        orders_with_items.append({**dict(order), 'items': items})

    return render_page(ORDERS_TEMPLATE, BASE_TEMPLATE, orders=orders_with_items)


@app.route('/order/<order_id>')
@login_required
def order_detail(order_id):
    """Order detail page."""
    db = get_db()
    order = db.execute('''
        SELECT o.*, u.username FROM orders o
        JOIN users u ON o.user_id = u.id
        WHERE o.order_id = ? AND o.user_id = ?
    ''', (order_id, session['user_id'])).fetchone()

    if not order:
        abort(404)

    order_items = db.execute('''
        SELECT oi.*, p.image_url FROM order_items oi
        LEFT JOIN products p ON oi.product_id = p.id
        WHERE oi.order_id = ?
    ''', (order['id'],)).fetchall()

    return render_page(ORDER_DETAIL_TEMPLATE, BASE_TEMPLATE,
        order=order, order_items=order_items)


# ============================================================
# OTHER USER ROUTES
# ============================================================

@app.route('/notifications')
@login_required
def notifications():
    """User notifications page."""
    db = get_db()
    notifs = db.execute('SELECT * FROM notifications WHERE user_id = ? ORDER BY created_at DESC',
                       (session['user_id'],)).fetchall()
    return render_page(NOTIFICATIONS_TEMPLATE, BASE_TEMPLATE, notifications=notifs)


@app.route('/notifications/mark-all-read')
@login_required
def mark_all_read():
    """Mark all notifications as read."""
    db = get_db()
    db.execute('UPDATE notifications SET is_read = 1 WHERE user_id = ?', (session['user_id'],))
    db.commit()
    return redirect(url_for('notifications'))


@app.route('/downloads')
@login_required
def downloads():
    """User downloads page."""
    db = get_db()
    dl_items = db.execute('''
        SELECT oi.*, o.order_id, p.image_url
        FROM order_items oi
        JOIN orders o ON oi.order_id = o.id
        LEFT JOIN products p ON oi.product_id = p.id
        WHERE o.user_id = ? AND oi.is_delivered = 1 AND oi.delivery_data != ''
        ORDER BY oi.delivered_at DESC
    ''', (session['user_id'],)).fetchall()
    return render_page(DOWNLOADS_TEMPLATE, BASE_TEMPLATE, downloads=dl_items)


@app.route('/wishlist')
@login_required
def wishlist_view():
    """User wishlist page."""
    db = get_db()
    products = db.execute('''
        SELECT p.*, c.name as category_name FROM wishlist w
        JOIN products p ON w.product_id = p.id
        LEFT JOIN categories c ON p.category_id = c.id
        WHERE w.user_id = ? AND p.is_active = 1
        ORDER BY w.created_at DESC
    ''', (session['user_id'],)).fetchall()
    return render_page(WISHLIST_TEMPLATE, BASE_TEMPLATE, products=products)


@app.route('/wishlist/toggle', methods=['POST'])
@login_required
def toggle_wishlist():
    """Toggle product in wishlist."""
    data = request.get_json()
    product_id = data.get('product_id')

    db = get_db()
    existing = db.execute('SELECT id FROM wishlist WHERE user_id = ? AND product_id = ?',
                         (session['user_id'], product_id)).fetchone()

    if existing:
        db.execute('DELETE FROM wishlist WHERE id = ?', (existing['id'],))
        message = 'Removed from wishlist'
    else:
        db.execute('INSERT INTO wishlist (user_id, product_id) VALUES (?, ?)',
                  (session['user_id'], product_id))
        message = 'Added to wishlist'

    db.commit()
    return jsonify({'success': True, 'message': message})


@app.route('/support', methods=['GET', 'POST'])
@login_required
def support():
    """Support page."""
    db = get_db()

    if request.method == 'POST':
        subject = request.form.get('subject', '').strip()
        message = request.form.get('message', '').strip()
        priority = request.form.get('priority', 'normal')

        if subject and message:
            ticket_id = generate_ticket_id()
            db.execute('''
                INSERT INTO support_messages (ticket_id, user_id, subject, message, priority)
                VALUES (?, ?, ?, ?, ?)
            ''', (ticket_id, session['user_id'], subject, message, priority))
            db.commit()
            flash(f'Support ticket {ticket_id} created successfully!', 'success')
            return redirect(url_for('support'))

    tickets = db.execute(
        'SELECT * FROM support_messages WHERE user_id = ? ORDER BY created_at DESC',
        (session['user_id'],)
    ).fetchall()

    return render_page(SUPPORT_TEMPLATE, BASE_TEMPLATE, tickets=tickets)


@app.route('/coupon/apply', methods=['POST'])
@login_required
def apply_coupon():
    """Apply coupon code."""
    data = request.get_json()
    code = data.get('code', '').strip().upper()

    db = get_db()
    coupon = db.execute('SELECT * FROM coupons WHERE code = ? AND is_active = 1', (code,)).fetchone()

    if not coupon:
        return jsonify({'success': False, 'message': 'Invalid coupon code'})

    if coupon['usage_limit'] != -1 and coupon['used_count'] >= coupon['usage_limit']:
        return jsonify({'success': False, 'message': 'Coupon usage limit reached'})

    # Calculate discount
    cart_items = db.execute('''
        SELECT c.quantity, p.price FROM cart c
        JOIN products p ON c.product_id = p.id WHERE c.user_id = ?
    ''', (session['user_id'],)).fetchall()

    subtotal = sum(item['price'] * item['quantity'] for item in cart_items)

    if subtotal < coupon['min_order_amount']:
        return jsonify({'success': False, 'message': f'Minimum order amount is {format_currency(coupon["min_order_amount"])}'})

    if coupon['discount_type'] == 'percentage':
        discount = subtotal * coupon['discount_value'] / 100
        if coupon['max_discount'] > 0:
            discount = min(discount, coupon['max_discount'])
    else:
        discount = coupon['discount_value']

    discount = min(discount, subtotal)
    total = subtotal - discount

    return jsonify({
        'success': True,
        'message': f'Coupon applied! You save {format_currency(discount)}',
        'discount': format_currency(discount),
        'total': format_currency(total)
    })


# ============================================================
# ADMIN ROUTES
# ============================================================

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """Admin login page."""
    if 'admin_id' in session:
        return redirect(url_for('admin_dashboard'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        db = get_db()
        admin = db.execute('SELECT * FROM admins WHERE username = ? AND is_active = 1',
                          (username,)).fetchone()

        if admin and check_password_hash(admin['password_hash'], password):
            session['admin_id'] = admin['id']
            db.execute('UPDATE admins SET last_login = ? WHERE id = ?',
                      (datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'), admin['id']))
            db.commit()
            log_activity(admin_id=admin['id'], action='admin_login', details='Admin logged in')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid credentials.', 'danger')

    return render_page(ADMIN_LOGIN_TEMPLATE, ADMIN_LOGIN_TEMPLATE)


@app.route('/admin/logout')
def admin_logout():
    """Admin logout."""
    session.pop('admin_id', None)
    flash('Logged out.', 'info')
    return redirect(url_for('admin_login'))


@app.route('/admin')
@admin_required
def admin_dashboard():
    """Admin dashboard."""
    db = get_db()

    total_revenue = db.execute('SELECT COALESCE(SUM(total_amount), 0) as total FROM orders WHERE payment_status = "paid"').fetchone()['total']
    total_orders = db.execute('SELECT COUNT(*) as c FROM orders').fetchone()['c']
    total_users = db.execute('SELECT COUNT(*) as c FROM users').fetchone()['c']
    total_products = db.execute('SELECT COUNT(*) as c FROM products').fetchone()['c']
    pending_deposits = db.execute('SELECT COUNT(*) as c FROM deposits WHERE status = "pending"').fetchone()['c']
    pending_orders_count = db.execute('SELECT COUNT(*) as c FROM orders WHERE order_status = "pending"').fetchone()['c']
    open_tickets = db.execute('SELECT COUNT(*) as c FROM support_messages WHERE status = "open"').fetchone()['c']

    today = datetime.datetime.utcnow().strftime('%Y-%m-%d')
    today_revenue = db.execute(
        'SELECT COALESCE(SUM(total_amount), 0) as total FROM orders WHERE payment_status = "paid" AND DATE(created_at) = ?',
        (today,)
    ).fetchone()['total']

    recent_orders = db.execute('''
        SELECT o.*, u.username FROM orders o
        JOIN users u ON o.user_id = u.id
        ORDER BY o.created_at DESC LIMIT 10
    ''').fetchall()

    recent_deposits = db.execute('''
        SELECT d.*, u.username FROM deposits d
        JOIN users u ON d.user_id = u.id
        ORDER BY d.created_at DESC LIMIT 10
    ''').fetchall()

    admin = db.execute('SELECT * FROM admins WHERE id = ?', (session['admin_id'],)).fetchone()

    return render_page(ADMIN_DASHBOARD_TEMPLATE, ADMIN_LAYOUT,
        admin=admin, total_revenue=total_revenue, total_orders=total_orders,
        total_users=total_users, total_products=total_products,
        pending_deposits=pending_deposits, pending_orders_count=pending_orders_count,
        open_tickets=open_tickets, today_revenue=today_revenue,
        recent_orders=recent_orders, recent_deposits=recent_deposits,
        now=datetime.datetime.utcnow())


@app.route('/admin/products')
@admin_required
def admin_products():
    """Admin products list."""
    db = get_db()
    products = db.execute('''
        SELECT p.*, c.name as category_name FROM products p
        LEFT JOIN categories c ON p.category_id = c.id
        ORDER BY p.created_at DESC
    ''').fetchall()
    return render_page(ADMIN_PRODUCTS_TEMPLATE, ADMIN_LAYOUT, products=products)


@app.route('/admin/products/add', methods=['GET', 'POST'])
@admin_required
def admin_product_add():
    """Add new product."""
    db = get_db()

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        slug = name.lower().replace(' ', '-').replace('--', '-')
        slug = re.sub(r'[^a-z0-9-]', '', slug) + f'-{secrets.token_hex(3)}'

        db.execute('''
            INSERT INTO products (name, slug, description, short_description, category_id, price, original_price,
                discount_percent, stock_quantity, image_url, delivery_type, delivery_content, is_featured, is_active, created_by)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            name, slug,
            request.form.get('description', ''),
            request.form.get('short_description', ''),
            request.form.get('category_id') or None,
            float(request.form.get('price', 0)),
            float(request.form.get('original_price', 0) or 0),
            float(request.form.get('discount_percent', 0) or 0),
            int(request.form.get('stock_quantity', -1)),
            request.form.get('image_url', ''),
            request.form.get('delivery_type', 'auto'),
            request.form.get('delivery_content', ''),
            1 if request.form.get('is_featured') else 0,
            1 if request.form.get('is_active') else 0,
            session['admin_id']
        ))
        db.commit()
        flash('Product added successfully!', 'success')
        return redirect(url_for('admin_products'))

    categories = db.execute('SELECT * FROM categories WHERE is_active = 1 ORDER BY name').fetchall()
    return render_page(ADMIN_PRODUCT_FORM_TEMPLATE, ADMIN_LAYOUT,
        product=None, categories=categories)


@app.route('/admin/products/edit/<int:product_id>', methods=['GET', 'POST'])
@admin_required
def admin_product_edit(product_id):
    """Edit product."""
    db = get_db()
    product = db.execute('SELECT * FROM products WHERE id = ?', (product_id,)).fetchone()

    if not product:
        abort(404)

    if request.method == 'POST':
        db.execute('''
            UPDATE products SET name=?, description=?, short_description=?, category_id=?,
                price=?, original_price=?, discount_percent=?, stock_quantity=?,
                image_url=?, delivery_type=?, delivery_content=?,
                is_featured=?, is_active=?, updated_at=?
            WHERE id=?
        ''', (
            request.form.get('name', ''),
            request.form.get('description', ''),
            request.form.get('short_description', ''),
            request.form.get('category_id') or None,
            float(request.form.get('price', 0)),
            float(request.form.get('original_price', 0) or 0),
            float(request.form.get('discount_percent', 0) or 0),
            int(request.form.get('stock_quantity', -1)),
            request.form.get('image_url', ''),
            request.form.get('delivery_type', 'auto'),
            request.form.get('delivery_content', ''),
            1 if request.form.get('is_featured') else 0,
            1 if request.form.get('is_active') else 0,
            datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),
            product_id
        ))
        db.commit()
        flash('Product updated successfully!', 'success')
        return redirect(url_for('admin_products'))

    categories = db.execute('SELECT * FROM categories WHERE is_active = 1 ORDER BY name').fetchall()
    return render_page(ADMIN_PRODUCT_FORM_TEMPLATE, ADMIN_LAYOUT,
        product=product, categories=categories)


@app.route('/admin/products/delete/<int:product_id>')
@admin_required
def admin_product_delete(product_id):
    """Delete product (cleans up related records first)."""
    db = get_db()
    # Clean up related records
    db.execute('DELETE FROM reviews WHERE product_id = ?', (product_id,))
    db.execute('DELETE FROM wishlist WHERE product_id = ?', (product_id,))
    db.execute('DELETE FROM cart WHERE product_id = ?', (product_id,))
    # Keep order_items for history but unlink product reference
    db.execute('UPDATE order_items SET product_id = NULL WHERE product_id = ?', (product_id,))
    db.execute('DELETE FROM products WHERE id = ?', (product_id,))
    db.commit()
    flash('Product deleted.', 'info')
    return redirect(url_for('admin_products'))


@app.route('/admin/orders')
@admin_required
def admin_orders():
    """Admin orders list."""
    db = get_db()
    orders = db.execute('''
        SELECT o.*, u.username,
               (SELECT COUNT(*) FROM order_items WHERE order_id = o.id) as item_count
        FROM orders o JOIN users u ON o.user_id = u.id
        ORDER BY o.created_at DESC
    ''').fetchall()
    return render_page(ADMIN_ORDERS_TEMPLATE, ADMIN_LAYOUT, orders=orders)


@app.route('/admin/orders/<order_id>', methods=['GET', 'POST'])
@admin_required
def admin_order_detail(order_id):
    """Admin order detail."""
    db = get_db()
    order = db.execute('''
        SELECT o.*, u.username FROM orders o
        JOIN users u ON o.user_id = u.id WHERE o.order_id = ?
    ''', (order_id,)).fetchone()

    if not order:
        abort(404)

    order_items = db.execute('''
        SELECT oi.*, p.image_url FROM order_items oi
        LEFT JOIN products p ON oi.product_id = p.id WHERE oi.order_id = ?
    ''', (order['id'],)).fetchall()

    return render_page(ADMIN_ORDER_DETAIL_TEMPLATE, ADMIN_LAYOUT,
        order=order, order_items=order_items)


@app.route('/admin/orders/<order_id>/update', methods=['POST'])
@admin_required
def admin_order_update(order_id):
    """Update order status."""
    db = get_db()
    order_status = request.form.get('order_status')
    payment_status = request.form.get('payment_status')

    db.execute('''
        UPDATE orders SET order_status = ?, payment_status = ?, updated_at = ?
        WHERE order_id = ?
    ''', (order_status, payment_status,
          datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'), order_id))

    order = db.execute('SELECT * FROM orders WHERE order_id = ?', (order_id,)).fetchone()
    if order:
        create_notification(order['user_id'], 'Order Status Updated',
                           f'Your order {order_id} status has been updated to {order_status}.', 'info')

    db.commit()
    flash('Order updated.', 'success')
    return redirect(url_for('admin_order_detail', order_id=order_id))


@app.route('/admin/deliver/<int:item_id>', methods=['POST'])
@admin_required
def admin_deliver_item(item_id):
    """Deliver order item."""
    db = get_db()
    delivery_data = request.form.get('delivery_data', '').strip()

    if delivery_data:
        db.execute('''
            UPDATE order_items SET delivery_data = ?, is_delivered = 1, delivered_at = ?
            WHERE id = ?
        ''', (delivery_data, datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'), item_id))

        item = db.execute('SELECT oi.*, o.user_id, o.order_id FROM order_items oi JOIN orders o ON oi.order_id = o.id WHERE oi.id = ?', (item_id,)).fetchone()
        if item:
            create_notification(item['user_id'], 'Product Delivered!',
                               f'Your product "{item["product_name"]}" from order {item["order_id"]} has been delivered.',
                               'success', url_for('order_detail', order_id=item['order_id']))

        db.commit()
        flash('Item delivered successfully!', 'success')

    return redirect(request.referrer or url_for('admin_orders'))


@app.route('/admin/deposits')
@admin_required
def admin_deposits():
    """Admin deposits list."""
    db = get_db()
    status = request.args.get('status', 'pending')

    if status == 'all':
        deposits = db.execute('''
            SELECT d.*, u.username FROM deposits d
            JOIN users u ON d.user_id = u.id ORDER BY d.created_at DESC
        ''').fetchall()
    else:
        deposits = db.execute('''
            SELECT d.*, u.username FROM deposits d
            JOIN users u ON d.user_id = u.id WHERE d.status = ?
            ORDER BY d.created_at DESC
        ''', (status,)).fetchall()

    return render_page(ADMIN_DEPOSITS_TEMPLATE, ADMIN_LAYOUT, deposits=deposits)


@app.route('/admin/deposits/<int:deposit_id>/<action>')
@admin_required
def admin_deposit_action(deposit_id, action):
    """Approve or reject deposit."""
    db = get_db()
    deposit = db.execute('SELECT * FROM deposits WHERE id = ?', (deposit_id,)).fetchone()

    if not deposit:
        abort(404)

    if action == 'approve':
        # Add to wallet
        user = db.execute('SELECT wallet_balance FROM users WHERE id = ?', (deposit['user_id'],)).fetchone()
        balance_before = user['wallet_balance']
        balance_after = balance_before + deposit['amount']

        db.execute('UPDATE users SET wallet_balance = ? WHERE id = ?', (balance_after, deposit['user_id']))
        db.execute('UPDATE deposits SET status = "approved", processed_by = ?, processed_at = ? WHERE id = ?',
                  (session['admin_id'], datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'), deposit_id))

        db.execute('''
            INSERT INTO wallet_transactions (user_id, type, amount, balance_before, balance_after, description, reference_id, reference_type)
            VALUES (?, 'credit', ?, ?, ?, ?, ?, 'deposit')
        ''', (deposit['user_id'], deposit['amount'], balance_before, balance_after,
              f'Deposit via {deposit["method"].title()}', f'DEP-{deposit_id}'))

        create_notification(deposit['user_id'], 'Deposit Approved!',
                           f'Your deposit of {format_currency(deposit["amount"])} has been approved and added to your wallet.',
                           'success')

        flash('Deposit approved!', 'success')

    elif action == 'reject':
        db.execute('UPDATE deposits SET status = "rejected", processed_by = ?, processed_at = ? WHERE id = ?',
                  (session['admin_id'], datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'), deposit_id))

        create_notification(deposit['user_id'], 'Deposit Rejected',
                           f'Your deposit of {format_currency(deposit["amount"])} has been rejected. Please contact support.',
                           'error')

        flash('Deposit rejected.', 'info')

    db.commit()
    return redirect(url_for('admin_deposits'))


@app.route('/admin/users')
@admin_required
def admin_users():
    """Admin users list."""
    db = get_db()
    users = db.execute('''
        SELECT u.*, (SELECT COUNT(*) FROM orders WHERE user_id = u.id) as order_count
        FROM users u ORDER BY u.created_at DESC
    ''').fetchall()
    return render_page(ADMIN_USERS_TEMPLATE, ADMIN_LAYOUT, users=users)


@app.route('/admin/users/<int:user_id>/toggle')
@admin_required
def admin_user_toggle(user_id):
    """Toggle user active status."""
    db = get_db()
    user = db.execute('SELECT is_active FROM users WHERE id = ?', (user_id,)).fetchone()
    if user:
        new_status = 0 if user['is_active'] else 1
        db.execute('UPDATE users SET is_active = ? WHERE id = ?', (new_status, user_id))
        db.commit()
        flash(f'User {"banned" if not new_status else "unbanned"}.', 'info')
    return redirect(url_for('admin_users'))


@app.route('/admin/categories', methods=['GET', 'POST'])
@admin_required
def admin_categories():
    """Admin categories management."""
    db = get_db()

    if request.method == 'POST':
        cat_id = request.form.get('category_id')
        name = request.form.get('name', '').strip()
        icon = request.form.get('icon', '').strip()
        color = request.form.get('color', '#00f2fe')
        description = request.form.get('description', '').strip()
        slug = name.lower().replace(' ', '-')
        slug = re.sub(r'[^a-z0-9-]', '', slug)

        if cat_id:
            db.execute('UPDATE categories SET name=?, slug=?, icon=?, color=?, description=? WHERE id=?',
                      (name, slug, icon, color, description, cat_id))
            flash('Category updated!', 'success')
        else:
            try:
                db.execute('INSERT INTO categories (name, slug, icon, color, description) VALUES (?, ?, ?, ?, ?)',
                          (name, slug, icon, color, description))
                flash('Category added!', 'success')
            except sqlite3.IntegrityError:
                flash('Category already exists.', 'danger')

        db.commit()
        return redirect(url_for('admin_categories'))

    edit_cat = None
    edit_id = request.args.get('edit')
    if edit_id:
        edit_cat = db.execute('SELECT * FROM categories WHERE id = ?', (edit_id,)).fetchone()

    categories = db.execute('''
        SELECT c.*, (SELECT COUNT(*) FROM products WHERE category_id = c.id) as product_count
        FROM categories c ORDER BY c.sort_order, c.name
    ''').fetchall()

    return render_page(ADMIN_CATEGORIES_TEMPLATE, ADMIN_LAYOUT,
        categories=categories, edit_cat=edit_cat)


@app.route('/admin/categories/delete/<int:cat_id>')
@admin_required
def admin_category_delete(cat_id):
    """Delete category (sets products' category to NULL first)."""
    db = get_db()
    # Unlink products from this category first
    db.execute('UPDATE products SET category_id = NULL WHERE category_id = ?', (cat_id,))
    db.execute('DELETE FROM categories WHERE id = ?', (cat_id,))
    db.commit()
    flash('Category deleted.', 'info')
    return redirect(url_for('admin_categories'))


@app.route('/admin/coupons', methods=['GET', 'POST'])
@admin_required
def admin_coupons():
    """Admin coupons management."""
    db = get_db()

    if request.method == 'POST':
        code = request.form.get('code', '').strip().upper()
        discount_type = request.form.get('discount_type', 'percentage')
        discount_value = float(request.form.get('discount_value', 0))
        min_order_amount = float(request.form.get('min_order_amount', 0))
        max_discount = float(request.form.get('max_discount', 0))
        usage_limit = int(request.form.get('usage_limit', -1))

        try:
            db.execute('''
                INSERT INTO coupons (code, discount_type, discount_value, min_order_amount, max_discount, usage_limit)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (code, discount_type, discount_value, min_order_amount, max_discount, usage_limit))
            db.commit()
            flash(f'Coupon {code} created!', 'success')
        except sqlite3.IntegrityError:
            flash('Coupon code already exists.', 'danger')

        return redirect(url_for('admin_coupons'))

    coupons = db.execute('SELECT * FROM coupons ORDER BY created_at DESC').fetchall()
    return render_page(ADMIN_COUPONS_TEMPLATE, ADMIN_LAYOUT, coupons=coupons)


@app.route('/admin/coupons/delete/<int:coupon_id>')
@admin_required
def admin_coupon_delete(coupon_id):
    """Delete coupon."""
    db = get_db()
    db.execute('DELETE FROM coupons WHERE id = ?', (coupon_id,))
    db.commit()
    flash('Coupon deleted.', 'info')
    return redirect(url_for('admin_coupons'))


@app.route('/admin/support', methods=['GET', 'POST'])
@admin_required
def admin_support():
    """Admin support management."""
    db = get_db()
    tickets = db.execute('''
        SELECT sm.*, u.username FROM support_messages sm
        JOIN users u ON sm.user_id = u.id
        ORDER BY sm.created_at DESC
    ''').fetchall()
    return render_page(ADMIN_SUPPORT_TEMPLATE, ADMIN_LAYOUT, tickets=tickets)


@app.route('/admin/support/reply/<ticket_id>', methods=['POST'])
@admin_required
def admin_support_reply(ticket_id):
    """Reply to support ticket."""
    db = get_db()
    reply = request.form.get('reply', '').strip()
    status = request.form.get('status', 'open')

    if reply:
        db.execute('''
            UPDATE support_messages SET admin_reply = ?, replied_by = ?, replied_at = ?, status = ?, updated_at = ?
            WHERE ticket_id = ?
        ''', (reply, session['admin_id'], datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),
              status, datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'), ticket_id))

        ticket = db.execute('SELECT * FROM support_messages WHERE ticket_id = ?', (ticket_id,)).fetchone()
        if ticket:
            create_notification(ticket['user_id'], 'Support Reply',
                               f'Your ticket {ticket_id} has been replied to.',
                               'info', url_for('support'))

        db.commit()
        flash('Reply sent!', 'success')

    return redirect(url_for('admin_support'))


@app.route('/admin/settings', methods=['GET', 'POST'])
@admin_required
def admin_settings():
    """Admin settings page."""
    db = get_db()

    if request.method == 'POST':
        for key, value in request.form.items():
            db.execute('UPDATE settings SET setting_value = ? WHERE setting_key = ?', (value, key))
        db.commit()
        flash('Settings saved!', 'success')
        return redirect(url_for('admin_settings'))

    settings_list = db.execute('SELECT * FROM settings ORDER BY id').fetchall()
    return render_page(ADMIN_SETTINGS_TEMPLATE, ADMIN_LAYOUT, settings_list=settings_list)


@app.route('/admin/announcements', methods=['GET', 'POST'])
@admin_required
def admin_announcements():
    """Admin announcements."""
    db = get_db()

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        content = request.form.get('content', '').strip()
        atype = request.form.get('type', 'info')

        if title and content:
            db.execute('INSERT INTO announcements (title, content, type) VALUES (?, ?, ?)',
                      (title, content, atype))
            db.commit()
            flash('Announcement added!', 'success')

        return redirect(url_for('admin_announcements'))

    announcements = db.execute('SELECT * FROM announcements ORDER BY created_at DESC').fetchall()
    return render_page(ADMIN_ANNOUNCEMENTS_TEMPLATE, ADMIN_LAYOUT, announcements=announcements)


@app.route('/admin/announcements/delete/<int:ann_id>')
@admin_required
def admin_announcement_delete(ann_id):
    """Delete announcement."""
    db = get_db()
    db.execute('DELETE FROM announcements WHERE id = ?', (ann_id,))
    db.commit()
    flash('Announcement deleted.', 'info')
    return redirect(url_for('admin_announcements'))


@app.route('/admin/logs')
@admin_required
def admin_logs():
    """Admin activity logs."""
    db = get_db()
    logs = db.execute('SELECT * FROM activity_logs ORDER BY created_at DESC LIMIT 200').fetchall()
    return render_page(ADMIN_LOGS_TEMPLATE, ADMIN_LAYOUT, logs=logs)


# ============================================================
# ERROR HANDLERS
# ============================================================

@app.errorhandler(404)
def not_found(e):
    """404 error page."""
    return render_page(ERROR_TEMPLATE, BASE_TEMPLATE, error_code=404), 404


@app.errorhandler(500)
def server_error(e):
    """500 error page."""
    return render_page(ERROR_TEMPLATE, BASE_TEMPLATE, error_code=500), 500


# ============================================================
# API ENDPOINTS
# ============================================================

@app.route('/api/products')
def api_products():
    """API: Get products."""
    db = get_db()
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 20))
    category = request.args.get('category', '')
    search = request.args.get('q', '')

    query = 'SELECT * FROM products WHERE is_active = 1'
    params = []

    if category:
        query += ' AND category_id = (SELECT id FROM categories WHERE slug = ?)'
        params.append(category)

    if search:
        query += ' AND (name LIKE ? OR description LIKE ?)'
        params.extend([f'%{search}%', f'%{search}%'])

    total = db.execute(query.replace('SELECT *', 'SELECT COUNT(*) as c'), params).fetchone()['c']

    query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
    params.extend([per_page, (page - 1) * per_page])

    products = db.execute(query, params).fetchall()

    return jsonify({
        'products': [dict(p) for p in products],
        'total': total,
        'page': page,
        'per_page': per_page
    })


@app.route('/api/categories')
def api_categories():
    """API: Get categories."""
    db = get_db()
    cats = db.execute('SELECT * FROM categories WHERE is_active = 1 ORDER BY sort_order').fetchall()
    return jsonify({'categories': [dict(c) for c in cats]})


# ============================================================
# INITIALIZE AND RUN
# ============================================================

# Initialize database on startup
init_db()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
