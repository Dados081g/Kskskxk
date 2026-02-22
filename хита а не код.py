import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes, ConversationHandler
from datetime import datetime
import sqlite3
import asyncio

# Настройка логирования
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Токен бота
BOT_TOKEN = "8052146904:AAFi3NVytf2BcmHxoxree31HG6s2ndQoK5o"
ADMIN_ID = 8052146904  # Замените на ваш Telegram ID

# Состояния для ConversationHandler
WAITING_FOR_SCREENSHOT = 1
WAITING_FOR_USER_ID = 2
WAITING_FOR_AMOUNT = 3
WAITING_FOR_KEY = 4
WAITING_FOR_USER_ID_BLOCK = 5
WAITING_FOR_KEY_ID = 6

# Подключение к базе данных
def init_db():
    conn = sqlite3.connect('bot_database.db')
    c = conn.cursor()
    
    # Таблица пользователей
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (user_id INTEGER PRIMARY KEY, 
                  username TEXT,
                  balance INTEGER DEFAULT 0,
                  is_blocked INTEGER DEFAULT 0,
                  registration_date TEXT)''')
    
    # Таблица ключей
    c.execute('''CREATE TABLE IF NOT EXISTS keys
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  key_text TEXT UNIQUE,
                  product TEXT,
                  duration TEXT,
                  is_sold INTEGER DEFAULT 0,
                  price INTEGER,
                  user_id INTEGER,
                  purchase_date TEXT)''')
    
    # Таблица чеков
    c.execute('''CREATE TABLE IF NOT EXISTS receipts
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER,
                  amount INTEGER,
                  screenshot_file_id TEXT,
                  status TEXT DEFAULT 'pending',
                  date TEXT)''')
    
    conn.commit()
    conn.close()

# Инициализация базы данных
init_db()

# Функция для проверки админа
def is_admin(user_id):
    return user_id == ADMIN_ID

# Функция для проверки блокировки
def is_user_blocked(user_id):
    conn = sqlite3.connect('bot_database.db')
    c = conn.cursor()
    c.execute("SELECT is_blocked FROM users WHERE user_id = ?", (user_id,))
    result = c.fetchone()
    conn.close()
    return result and result[0] == 1

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username
    
    # Регистрация пользователя
    conn = sqlite3.connect('bot_database.db')
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO users (user_id, username, registration_date) VALUES (?, ?, ?)",
              (user_id, username, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()
    
    if is_user_blocked(user_id):
        await update.message.reply_text("❌ Вы заблокированы в боте.")
        return
    
    keyboard = [
        [InlineKeyboardButton("📱 Android", callback_data="category_android")],
        [InlineKeyboardButton("🍎 iOS", callback_data="category_ios")],
        [InlineKeyboardButton("👤 Профиль", callback_data="profile")],
        [InlineKeyboardButton("💰 Пополнить баланс", callback_data="top_up")]
    ]
    
    if is_admin(user_id):
        keyboard.append([InlineKeyboardButton("👑 Админ панель", callback_data="admin_panel")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    welcome_text = "🌟 *Добро пожаловать в магазин ключей!* 🌟\n\nВыберите категорию:"
    await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode='Markdown')

# Обработка callback запросов
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    
    if is_user_blocked(user_id) and not is_admin(user_id):
        await query.edit_message_text("❌ Вы заблокированы в боте.")
        return
    
    data = query.data
    
    if data == "category_android":
        keyboard = [
            [InlineKeyboardButton("🎮 Zolo", callback_data="product_zolo")],
            [InlineKeyboardButton("🎯 Dexo", callback_data="product_dexo")],
            [InlineKeyboardButton("⚡ Zmod", callback_data="product_zmod")],
            [InlineKeyboardButton("🤖 Jarvis", callback_data="product_jarvis")],
            [InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("📱 *Android категория*\n\nВыберите продукт:", reply_markup=reply_markup, parse_mode='Markdown')
    
    elif data == "category_ios":
        keyboard = [
            [InlineKeyboardButton("⭐ Star", callback_data="product_star")],
            [InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("🍎 *iOS категория*\n\nВыберите продукт:", reply_markup=reply_markup, parse_mode='Markdown')
    
    elif data == "product_zolo":
        keyboard = [
            [InlineKeyboardButton("1 день - 170₽", callback_data="buy_zolo_1")],
            [InlineKeyboardButton("3 дня - 400₽", callback_data="buy_zolo_3")],
            [InlineKeyboardButton("7 дней - 800₽", callback_data="buy_zolo_7")],
            [InlineKeyboardButton("🔙 Назад", callback_data="category_android")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("*Zolo*\n\nВыберите тариф:", reply_markup=reply_markup, parse_mode='Markdown')
    
    elif data == "product_dexo":
        keyboard = [
            [InlineKeyboardButton("1 день - 170₽", callback_data="buy_dexo_1")],
            [InlineKeyboardButton("3 дня - 400₽", callback_data="buy_dexo_3")],
            [InlineKeyboardButton("7 дней - 800₽", callback_data="buy_dexo_7")],
            [InlineKeyboardButton("🔙 Назад", callback_data="category_android")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("*Dexo*\n\nВыберите тариф:", reply_markup=reply_markup, parse_mode='Markdown')
    
    elif data == "product_zmod":
        keyboard = [
            [InlineKeyboardButton("1 день - 150₽", callback_data="buy_zmod_1")],
            [InlineKeyboardButton("3 дня - 350₽", callback_data="buy_zmod_3")],
            [InlineKeyboardButton("7 дней - 600₽", callback_data="buy_zmod_7")],
            [InlineKeyboardButton("🔙 Назад", callback_data="category_android")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("*Zmod*\n\nВыберите тариф:", reply_markup=reply_markup, parse_mode='Markdown')
    
    elif data == "product_jarvis":
        keyboard = [
            [InlineKeyboardButton("1 день - 140₽", callback_data="buy_jarvis_1")],
            [InlineKeyboardButton("3 дня - 300₽", callback_data="buy_jarvis_3")],
            [InlineKeyboardButton("7 дней - 600₽", callback_data="buy_jarvis_7")],
            [InlineKeyboardButton("🔙 Назад", callback_data="category_android")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("*Jarvis*\n\nВыберите тариф:", reply_markup=reply_markup, parse_mode='Markdown')
    
    elif data == "product_star":
        keyboard = [
            [InlineKeyboardButton("1 день - 179₽", callback_data="buy_star_1")],
            [InlineKeyboardButton("7 дней - 699₽", callback_data="buy_star_7")],
            [InlineKeyboardButton("🔙 Назад", callback_data="category_ios")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("*Star*\n\nВыберите тариф:", reply_markup=reply_markup, parse_mode='Markdown')
    
    elif data.startswith("buy_"):
        await handle_purchase(query, context)
    
    elif data == "profile":
        await show_profile(query, context)
    
    elif data == "top_up":
        keyboard = [
            [InlineKeyboardButton("💳 Сбербанк", callback_data="show_card")],
            [InlineKeyboardButton("✅ Я оплатил", callback_data="i_paid")],
            [InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        text = ("💰 *Пополнение баланса*\n\n"
                "Выберите способ оплаты:")
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    
    elif data == "show_card":
        keyboard = [
            [InlineKeyboardButton("✅ Я оплатил", callback_data="i_paid")],
            [InlineKeyboardButton("🔙 Назад", callback_data="top_up")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        text = ("💳 *Реквизиты для оплаты*\n\n"
                "Сбербанк: `2202 2083 0536 9622`\n\n"
                "После оплаты нажмите кнопку 'Я оплатил'")
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    
    elif data == "i_paid":
        context.user_data['awaiting_screenshot'] = True
        await query.edit_message_text("📸 Отправьте скриншот чека об оплате:")
        return WAITING_FOR_SCREENSHOT
    
    elif data == "admin_panel" and is_admin(user_id):
        await show_admin_panel(query, context)
    
    elif data.startswith("admin_"):
        await handle_admin_actions(query, context)
    
    elif data == "back_to_main":
        await start(query, context)

# Покупка ключа
async def handle_purchase(query, context):
    user_id = query.from_user.id
    
    # Получаем баланс пользователя
    conn = sqlite3.connect('bot_database.db')
    c = conn.cursor()
    c.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,))
    balance = c.fetchone()[0]
    
    # Парсим данные о покупке
    parts = query.data.split('_')
    product = parts[1]
    duration = parts[2]
    
    prices = {
        'zolo': {'1': 170, '3': 400, '7': 800},
        'dexo': {'1': 170, '3': 400, '7': 800},
        'zmod': {'1': 150, '3': 350, '7': 600},
        'jarvis': {'1': 140, '3': 300, '7': 600},
        'star': {'1': 179, '7': 699}
    }
    
    price = prices[product][duration]
    
    if balance < price:
        await query.edit_message_text(f"❌ Недостаточно средств!\nНеобходимо: {price}₽\nВаш баланс: {balance}₽\n\nПополните баланс в профиле.")
        return
    
    # Поиск ключа в базе
    c.execute("""SELECT id, key_text FROM keys 
                 WHERE product = ? AND duration = ? AND is_sold = 0 LIMIT 1""", 
              (product, duration))
    key = c.fetchone()
    
    if key:
        # Выдаем ключ
        c.execute("""UPDATE keys SET is_sold = 1, user_id = ?, purchase_date = ?
                     WHERE id = ?""", (user_id, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), key[0]))
        # Обновляем баланс
        c.execute("UPDATE users SET balance = balance - ? WHERE user_id = ?", (price, user_id))
        conn.commit()
        
        await query.edit_message_text(f"✅ *Покупка успешна!*\n\n"
                                    f"Товар: {product.capitalize()} {duration}дн\n"
                                    f"Цена: {price}₽\n"
                                    f"Ключ: `{key[1]}`\n\n"
                                    f"Спасибо за покупку! 🎉",
                                    parse_mode='Markdown')
    else:
        await query.edit_message_text("❌ К сожалению, ключи временно закончились. Попробуйте позже.")
    
    conn.close()

# Профиль пользователя
async def show_profile(query, context):
    user_id = query.from_user.id
    
    conn = sqlite3.connect('bot_database.db')
    c = conn.cursor()
    
    # Получаем баланс
    c.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,))
    balance = c.fetchone()
    balance = balance[0] if balance else 0
    
    # Получаем купленные ключи
    c.execute("SELECT COUNT(*) FROM keys WHERE user_id = ? AND is_sold = 1", (user_id,))
    keys_count = c.fetchone()[0]
    
    conn.close()
    
    profile_text = (f"👤 *Ваш профиль*\n\n"
                    f"🆔 ID: `{user_id}`\n"
                    f"💰 Баланс: *{balance}₽*\n"
                    f"🔑 Куплено ключей: *{keys_count}*\n")
    
    keyboard = [
        [InlineKeyboardButton("💰 Пополнить", callback_data="top_up")],
        [InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(profile_text, reply_markup=reply_markup, parse_mode='Markdown')

# Обработка скриншотов
async def handle_screenshot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get('awaiting_screenshot'):
        user_id = update.effective_user.id
        photo = update.message.photo[-1].file_id
        
        conn = sqlite3.connect('bot_database.db')
        c = conn.cursor()
        c.execute("""INSERT INTO receipts (user_id, screenshot_file_id, date)
                     VALUES (?, ?, ?)""", 
                  (user_id, photo, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        receipt_id = c.lastrowid
        conn.commit()
        conn.close()
        
        # Уведомление админу
        await context.bot.send_message(
            ADMIN_ID,
            f"📨 *Новый чек!*\n\n"
            f"ID: `{receipt_id}`\n"
            f"Пользователь: `{user_id}`\n"
            f"Для подтверждения: /confirm_{receipt_id}",
            parse_mode='Markdown'
        )
        await context.bot.send_photo(ADMIN_ID, photo)
        
        await update.message.reply_text("✅ Чек отправлен на проверку! Ожидайте подтверждения.")
        context.user_data['awaiting_screenshot'] = False
        return ConversationHandler.END
    return

# Админ панель
async def show_admin_panel(query, context):
    keyboard = [
        [InlineKeyboardButton("💰 Пополнить баланс", callback_data="admin_add_balance")],
        [InlineKeyboardButton("💸 Уменьшить баланс", callback_data="admin_remove_balance")],
        [InlineKeyboardButton("🔑 Добавить ключ", callback_data="admin_add_key")],
        [InlineKeyboardButton("🚫 Заблокировать", callback_data="admin_block_user")],
        [InlineKeyboardButton("✅ Разблокировать", callback_data="admin_unblock_user")],
        [InlineKeyboardButton("📊 Статистика", callback_data="admin_stats")],
        [InlineKeyboardButton("📋 Чеки", callback_data="admin_receipts")],
        [InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text("👑 *Админ панель*\n\nВыберите действие:", reply_markup=reply_markup, parse_mode='Markdown')

async def handle_admin_actions(query, context):
    data = query.data
    
    if data == "admin_stats":
        conn = sqlite3.connect('bot_database.db')
        c = conn.cursor()
        
        c.execute("SELECT COUNT(*) FROM users")
        total_users = c.fetchone()[0]
        
        c.execute("SELECT COUNT(*) FROM keys WHERE is_sold = 1")
        sold_keys = c.fetchone()[0]
        
        c.execute("SELECT SUM(balance) FROM users")
        total_balance = c.fetchone()[0] or 0
        
        c.execute("SELECT COUNT(*) FROM receipts WHERE status = 'pending'")
        pending_receipts = c.fetchone()[0]
        
        conn.close()
        
        stats_text = (f"📊 *Статистика*\n\n"
                     f"👥 Всего пользователей: {total_users}\n"
                     f"🔑 Продано ключей: {sold_keys}\n"
                     f"💰 Общий баланс: {total_balance}₽\n"
                     f"📨 Ожидают чеки: {pending_receipts}")
        
        keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="admin_panel")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(stats_text, reply_markup=reply_markup, parse_mode='Markdown')
    
    elif data == "admin_receipts":
        conn = sqlite3.connect('bot_database.db')
        c = conn.cursor()
        c.execute("SELECT id, user_id, amount, status FROM receipts WHERE status = 'pending'")
        receipts = c.fetchall()
        conn.close()
        
        if receipts:
            text = "📨 *Ожидающие чеки*\n\n"
            for r in receipts:
                text += f"ID: `{r[0]}` | Пользователь: `{r[1]}` | Сумма: {r[2] or 'не указана'}₽\n"
            text += "\nИспользуйте /confirm_ID для подтверждения"
        else:
            text = "📨 Нет ожидающих чеков"
        
        keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="admin_panel")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

# Команда подтверждения чека
async def confirm_receipt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ У вас нет прав администратора")
        return
    
    try:
        receipt_id = int(context.args[0])
        
        conn = sqlite3.connect('bot_database.db')
        c = conn.cursor()
        
        # Получаем информацию о чеке
        c.execute("SELECT user_id, amount FROM receipts WHERE id = ? AND status = 'pending'", (receipt_id,))
        receipt = c.fetchone()
        
        if receipt:
            user_id, amount = receipt
            
            # Обновляем статус чека
            c.execute("UPDATE receipts SET status = 'confirmed' WHERE id = ?", (receipt_id,))
            
            # Обновляем баланс пользователя
            c.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount, user_id))
            
            conn.commit()
            
            # Уведомляем пользователя
            await context.bot.send_message(
                user_id,
                f"✅ *Чек подтвержден!*\n\nВаш баланс пополнен на {amount}₽",
                parse_mode='Markdown'
            )
            
            await update.message.reply_text(f"✅ Чек {receipt_id} подтвержден, баланс пользователя пополнен на {amount}₽")
        else:
            await update.message.reply_text("❌ Чек не найден или уже обработан")
        
        conn.close()
    except (IndexError, ValueError):
        await update.message.reply_text("❌ Использование: /confirm_ID")

# Обработчик текстовых сообщений
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if is_user_blocked(user_id) and not is_admin(user_id):
        await update.message.reply_text("❌ Вы заблокированы в боте.")
        return
    
    text = update.message.text
    
    if text.startswith('/add_key') and is_admin(user_id):
        # Формат: /add_key продукт длительность цена ключ
        try:
            parts = text.split()
            if len(parts) == 5:
                _, product, duration, price, key_text = parts
                
                conn = sqlite3.connect('bot_database.db')
                c = conn.cursor()
                c.execute("""INSERT INTO keys (key_text, product, duration, price)
                             VALUES (?, ?, ?, ?)""", (key_text, product, duration, int(price)))
                conn.commit()
                conn.close()
                
                await update.message.reply_text(f"✅ Ключ добавлен!\nПродукт: {product}\nДлительность: {duration}\nЦена: {price}₽")
            else:
                await update.message.reply_text("❌ Формат: /add_key продукт длительность цена ключ\nПример: /add_key zolo 1 170 ABC-123")
        except Exception as e:
            await update.message.reply_text(f"❌ Ошибка: {e}")

# Запуск бота
def main():
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Обработчики команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("confirm", confirm_receipt))
    
    # Обработчик callback запросов
    application.add_handler(Cal)