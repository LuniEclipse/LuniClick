import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import sqlite3
import random
import re

# ===== НАСТРОЙКИ (ИЗМЕНИТЕ ЭТО!) =====
TOKEN = '8878924452:AAESshZV4YhInNNOR2YXwsMwwfqlVsxjCj8'  # Вставьте сюда токен от @BotFather
ADMIN_IDS = [7778727422]  # Вставьте свой Telegram ID
# ======================================

bot = telebot.TeleBot(TOKEN)

# База данных
conn = sqlite3.connect('clicker.db', check_same_thread=False)
cursor = conn.cursor()

# Таблица пользователей
cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    clicks INTEGER DEFAULT 0,
    coins INTEGER DEFAULT 0,
    click_level INTEGER DEFAULT 1,
    coin_level INTEGER DEFAULT 1,
    username TEXT
)
''')

# Таблица инвентаря
cursor.execute('''
CREATE TABLE IF NOT EXISTS inventory (
    user_id INTEGER,
    item_name TEXT,
    quantity INTEGER DEFAULT 0,
    PRIMARY KEY (user_id, item_name)
)
''')
conn.commit()

# Список всех предметов
ALL_ITEMS = ['🎁 Бокс', '🥡 Супер Бокс', '🎲 Кость', '🪎 Сундук', '💜 Ультра Харт']

# Функции
def get_username(user):
    return user.username or f"id{user.id}"

def init_inventory(user_id):
    """Инициализирует инвентарь для пользователя (все предметы с 0)"""
    for item in ALL_ITEMS:
        cursor.execute('INSERT OR IGNORE INTO inventory (user_id, item_name, quantity) VALUES (?, ?, 0)', (user_id, item))
    conn.commit()

def get_inventory_list(user_id):
    """Возвращает список предметов, у которых количество > 0"""
    cursor.execute('SELECT item_name, quantity FROM inventory WHERE user_id = ? AND quantity > 0 ORDER BY item_name', (user_id,))
    return cursor.fetchall()

# Главная клавиатура
def main_keyboard():
    markup = InlineKeyboardMarkup(row_width=2)

    # Кнопка Клик с премиум-эмодзи
    try:
        click_button = InlineKeyboardButton(
            text="Клик!",
            callback_data="click",
            icon_custom_emoji_id="5298916708893878211"
        )
    except:
        # Если ID не сработал, используем обычную иконку
        click_button = InlineKeyboardButton("🔨 Клик!", callback_data="click")

    markup.add(
        click_button,
        InlineKeyboardButton("✨ Скиллухи", callback_data="shop"),
        InlineKeyboardButton("🎒 Склад", callback_data="inventory"),
        InlineKeyboardButton("🏩 Магазин", callback_data="item_shop"),
        InlineKeyboardButton("📊 Топ игроков", callback_data="top")
    )
    return markup

# Клавиатура для магазина скиллов
def skill_shop_keyboard(user_id):
    cursor.execute('SELECT click_level, coin_level FROM users WHERE user_id = ?', (user_id,))
    click_lvl, coin_lvl = cursor.fetchone()

    click_price = 100 * (click_lvl ** 1.5)
    coin_price = 100 * (coin_lvl ** 1.5)

    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton(f"⚡ Удвоение кликов (ур. {click_lvl}) - {int(click_price)}💰", callback_data="buy_click"),
        InlineKeyboardButton(f"💰 Удвоение монет (ур. {coin_lvl}) - {int(coin_price)}💰", callback_data="buy_coin"),
        InlineKeyboardButton("◀ Назад", callback_data="back")
    )
    return markup, click_price, coin_price

# Клавиатура для магазина предметов
def item_shop_keyboard():
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton("🎁 Бокс - 420💰", callback_data="buy_item_🎁 Бокс"),
        InlineKeyboardButton("🥡 Супер Бокс - 2500💰", callback_data="buy_item_🥡 Супер Бокс"),
        InlineKeyboardButton("🎲 Кость - 10000💰", callback_data="buy_item_🎲 Кость"),
        InlineKeyboardButton("🪎 Сундук - 6500💰", callback_data="buy_item_🪎 Сундук"),
        InlineKeyboardButton("💜 Ультра Харт - 150000💰", callback_data="buy_item_💜 Ультра Харт"),
        InlineKeyboardButton("◀ Назад", callback_data="back")
    )
    return markup

def show_inventory(user_id, chat_id, message_id=None):
    items = get_inventory_list(user_id)

    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("◀ Назад", callback_data="back"))

    if not items:
        text = "🗃 Твой складик:\n\nУ тебя пусто.. 😅"
    else:
        text = "🗃 Твой складик:\n\n"
        for i, (item_name, quantity) in enumerate(items, 1):
            text += f"{i}. {item_name} — {quantity} шт.\n"
        text += "\n📌 Команды:\n• юзнуть (номер) — использовать предмет\n• дать (номер) (@username) (кол-во) — передать предмет"

    if message_id:
        bot.edit_message_text(text, chat_id, message_id, reply_markup=markup)
    else:
        bot.send_message(chat_id, text, reply_markup=markup)

def use_item(user_id, username, item_index):
    items = get_inventory_list(user_id)

    if item_index < 1 or item_index > len(items):
        return False, "❌ Неверный номер предмета!"

    item_name, quantity = items[item_index - 1]

    if quantity <= 0:
        return False, "❌ У вас нет этого предмета!"

    # Уменьшаем количество
    cursor.execute('UPDATE inventory SET quantity = quantity - 1 WHERE user_id = ? AND item_name = ?', (user_id, item_name))
    conn.commit()

    result_text = f"🎁 @{username} использовал {item_name}!\n\n"

    # Эффекты предметов
    if item_name == '🎁 Бокс':
        rand = random.random()
        if rand < 0.8:
            coins_gain = random.randint(50, 1500)
            cursor.execute('UPDATE users SET coins = coins + ? WHERE user_id = ?', (coins_gain, user_id))
            result_text += f"💰 +{coins_gain} монет!"
        elif rand < 0.9:
            gain = random.randint(1, 8)
            cursor.execute('UPDATE inventory SET quantity = quantity + ? WHERE user_id = ? AND item_name = ?', (gain, user_id, '🥡 Супер Бокс'))
            result_text += f"🎁 +{gain} 🥡 Супер Бокс!"
        else:
            gain = random.randint(1, 3)
            cursor.execute('UPDATE inventory SET quantity = quantity + ? WHERE user_id = ? AND item_name = ?', (gain, user_id, '🎲 Кость'))
            result_text += f"🎲 +{gain} 🎲 Кость!"

    elif item_name == '🥡 Супер Бокс':
        coins_gain = random.randint(500, 5000)
        cursor.execute('UPDATE users SET coins = coins + ? WHERE user_id = ?', (coins_gain, user_id))
        result_text += f"💰 +{coins_gain} монет!"
        if random.random() < 0.3:
            gain = random.randint(1, 3)
            cursor.execute('UPDATE inventory SET quantity = quantity + ? WHERE user_id = ? AND item_name = ?', (gain, user_id, '🎁 Бокс'))
            result_text += f"\n🎁 Бонус! +{gain} 🎁 Бокс!"

    elif item_name == '🎲 Кость':
        roll = random.randint(1, 6)
        if roll == 6:
            coins_gain = random.randint(1000, 10000)
            cursor.execute('UPDATE users SET coins = coins + ? WHERE user_id = ?', (coins_gain, user_id))
            result_text += f"🎲 Выпало 6! Джекпот! 💰 +{coins_gain} монет!"
        else:
            result_text += f"🎲 Выпало {roll}. Повезёт в следующий раз!"

    elif item_name == '🪎 Сундук':
        coins_gain = random.randint(500, 3000)
        cursor.execute('UPDATE users SET coins = coins + ? WHERE user_id = ?', (coins_gain, user_id))
        result_text += f"💰 +{coins_gain} монет!"
        if random.random() < 0.2:
            gain = random.randint(1, 2)
            cursor.execute('UPDATE inventory SET quantity = quantity + ? WHERE user_id = ? AND item_name = ?', (gain, user_id, '🎁 Бокс'))
            result_text += f"\n📦 +{gain} 🎁 Бокс!"

    elif item_name == '💜 Ультра Харт':
        cursor.execute('UPDATE users SET click_level = click_level + 1, coin_level = coin_level + 1 WHERE user_id = ?', (user_id,))
        result_text += "✨ Все скиллы повышены на 1 уровень! ✨"

    conn.commit()
    return True, result_text

def transfer_item(from_user_id, item_index, target_username, quantity):
    """Передача предмета другому игроку"""
    items = get_inventory_list(from_user_id)

    if item_index < 1 or item_index > len(items):
        return False, "❌ Неверный номер предмета!"

    item_name, have_qty = items[item_index - 1]

    if have_qty < quantity:
        return False, f"❌ У вас только {have_qty} шт. {item_name}!"

    # Находим получателя по юзернейму
    if target_username.startswith('@'):
        target_username = target_username[1:]

    cursor.execute('SELECT user_id FROM users WHERE username = ?', (target_username,))
    result = cursor.fetchone()

    if not result:
        return False, f"❌ Пользователь @{target_username} не найден в базе!"

    target_user_id = result[0]

    # Передаём предметы
    cursor.execute('UPDATE inventory SET quantity = quantity - ? WHERE user_id = ? AND item_name = ?', (quantity, from_user_id, item_name))
    cursor.execute('INSERT OR IGNORE INTO inventory (user_id, item_name, quantity) VALUES (?, ?, 0)', (target_user_id, item_name))
    cursor.execute('UPDATE inventory SET quantity = quantity + ? WHERE user_id = ? AND item_name = ?', (quantity, target_user_id, item_name))
    conn.commit()

    return True, f"✅ Вы передали {quantity} шт. {item_name} пользователю @{target_username}!"

# ========== КОМАНДЫ ==========

@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    username = get_username(message.from_user)

    cursor.execute('INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)', (user_id, username))
    conn.commit()
    init_inventory(user_id)  # ВАЖНО: теперь инвентарь создаётся для всех!

    bot.send_message(message.chat.id,
        f"🎮 Добро пожаловать в Кликер, @{username}!\n\nКликай на кнопку и зарабатывай монеты!",
        reply_markup=main_keyboard())

# Команда кли (без слеша) - открывает меню
@bot.message_handler(func=lambda message: message.text and message.text.lower() == 'кли')
def menu_cmd(message):
    user_id = message.from_user.id
    cursor.execute('SELECT clicks, coins FROM users WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()

    if result:
        clicks, coins = result
        bot.send_message(message.chat.id,
            f"📊 Статистика @{get_username(message.from_user)}:\n\n🔨 Кликов: {clicks}\n💰 Монет: {coins}",
            reply_markup=main_keyboard())
    else:
        bot.send_message(message.chat.id, "❌ Сначала напишите /start мне в личку!")

# Команда кликер (без слеша) - то же самое
@bot.message_handler(func=lambda message: message.text and message.text.lower() == 'кликер')
def clicker_cmd(message):
    menu_cmd(message)

# Команда юзнуть (без слеша)
@bot.message_handler(func=lambda message: message.text and message.text.lower().startswith('юзнуть'))
def use_command(message):
    user_id = message.from_user.id
    username = get_username(message.from_user)

    # Проверяем, есть ли инвентарь у пользователя
    init_inventory(user_id)

    try:
        parts = message.text.split()
        if len(parts) != 2:
            bot.reply_to(message, "❌ Используйте: юзнуть (номер)")
            return

        item_num = int(parts[1])
        success, result = use_item(user_id, username, item_num)
        bot.reply_to(message, result)

        if success:
            show_inventory(user_id, message.chat.id)

    except ValueError:
        bot.reply_to(message, "❌ Номер должен быть числом!")

# Команда дать (без слеша) - передача предметов
@bot.message_handler(func=lambda message: message.text and message.text.lower().startswith('дать'))
def give_item_command(message):
    user_id = message.from_user.id

    # Проверяем, есть ли инвентарь
    init_inventory(user_id)

    try:
        # Формат: дать 1 @username 5  или  дать 1 username 5
        parts = message.text.split()
        if len(parts) != 4:
            bot.reply_to(message, "❌ Используйте: дать (номер предмета) (@username) (количество)\nПример: дать 1 @ivan 5")
            return

        item_num = int(parts[1])
        target = parts[2]
        quantity = int(parts[3])

        if quantity <= 0:
            bot.reply_to(message, "❌ Количество должно быть больше 0!")
            return

        success, result = transfer_item(user_id, item_num, target, quantity)
        bot.reply_to(message, result)

        if success:
            show_inventory(user_id, message.chat.id)

    except ValueError:
        bot.reply_to(message, "❌ Номер и количество должны быть числами!")
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {e}")

# Админ-команда /give (выдача монет)
@bot.message_handler(commands=['give'])
def give_coins(message):
    if message.from_user.id not in ADMIN_IDS:
        bot.reply_to(message, "❌ У вас нет прав!")
        return

    try:
        parts = message.text.split()
        if len(parts) != 3:
            bot.reply_to(message, "❌ Используйте: /give @username 100")
            return

        target = parts[1]
        amount = int(parts[2])

        if target.startswith('@'):
            username = target[1:]
            cursor.execute('SELECT user_id FROM users WHERE username = ?', (username,))
        else:
            user_id = int(target)
            cursor.execute('SELECT user_id FROM users WHERE user_id = ?', (user_id,))

        result = cursor.fetchone()
        if not result:
            bot.reply_to(message, f"❌ Пользователь не найден!")
            return

        user_id = result[0]
        cursor.execute('UPDATE users SET coins = coins + ? WHERE user_id = ?', (amount, user_id))
        conn.commit()
        bot.reply_to(message, f"✅ Выдано {amount}💰!")

    except:
        bot.reply_to(message, "❌ Ошибка!")

# ========== ОБРАБОТКА КНОПОК ==========

@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    user_id = call.from_user.id
    cursor.execute('SELECT click_level, coin_level, clicks, coins, username FROM users WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()

    if not result:
        bot.answer_callback_query(call.id, "❌ Напишите /start")
        init_inventory(user_id)
        return

    click_lvl, coin_lvl, clicks, coins, username = result

    # КЛИК
    if call.data == "click":
        gain = click_lvl
        coins_gain = coin_lvl
        clicks += gain
        coins += coins_gain
        cursor.execute('UPDATE users SET clicks = ?, coins = ? WHERE user_id = ?', (clicks, coins, user_id))
        conn.commit()
        bot.edit_message_text(
            f"📊 Статистика @{username}:\n\n🔨 Кликов: {clicks}\n💰 Монет: {coins}\n\n+{gain} клик(ов), +{coins_gain} монет(ы)!",
            call.message.chat.id, call.message.message_id, reply_markup=main_keyboard())

    # МАГАЗИН СКИЛЛОВ
    elif call.data == "shop":
        markup, click_price, coin_price = skill_shop_keyboard(user_id)
        bot.edit_message_text(
            f"🛒 СКИЛЛУХИ\nУ вас: {coins}💰\n\n⚡ Удвоение кликов (ур.{click_lvl}): {int(click_price)}💰\n💰 Удвоение монет (ур.{coin_lvl}): {int(coin_price)}💰",
            call.message.chat.id, call.message.message_id, reply_markup=markup)

    # ПОКУПКА СКИЛЛОВ
    elif call.data == "buy_click":
        markup, click_price, coin_price = skill_shop_keyboard(user_id)
        click_price = int(click_price)
        if coins >= click_price and click_lvl < 50:
            coins -= click_price
            click_lvl += 1
            cursor.execute('UPDATE users SET click_level = ?, coins = ? WHERE user_id = ?', (click_lvl, coins, user_id))
            conn.commit()
            bot.answer_callback_query(call.id, f"✅ Уровень {click_lvl}")
            new_markup, new_click_price, new_coin_price = skill_shop_keyboard(user_id)
            bot.edit_message_text(
                f"🛒 СКИЛЛУХИ\nУ вас: {coins}💰\n\n⚡ Удвоение кликов (ур.{click_lvl}): {int(new_click_price)}💰\n💰 Удвоение монет (ур.{coin_lvl}): {int(new_coin_price)}💰",
                call.message.chat.id, call.message.message_id, reply_markup=new_markup)
        else:
            bot.answer_callback_query(call.id, "❌ Не хватает монет или макс. уровень!")

    elif call.data == "buy_coin":
        markup, click_price, coin_price = skill_shop_keyboard(user_id)
        coin_price = int(coin_price)
        if coins >= coin_price and coin_lvl < 50:
            coins -= coin_price
            coin_lvl += 1
            cursor.execute('UPDATE users SET coin_level = ?, coins = ? WHERE user_id = ?', (coin_lvl, coins, user_id))
            conn.commit()
            bot.answer_callback_query(call.id, f"✅ Уровень {coin_lvl}")
            new_markup, new_click_price, new_coin_price = skill_shop_keyboard(user_id)
            bot.edit_message_text(
                f"🛒 СКИЛЛУХИ\nУ вас: {coins}💰\n\n⚡ Удвоение кликов (ур.{click_lvl}): {int(new_click_price)}💰\n💰 Удвоение монет (ур.{coin_lvl}): {int(new_coin_price)}💰",
                call.message.chat.id, call.message.message_id, reply_markup=new_markup)
        else:
            bot.answer_callback_query(call.id, "❌ Не хватает монет или макс. уровень!")

    # ИНВЕНТАРЬ
    elif call.data == "inventory":
        init_inventory(user_id)
        show_inventory(user_id, call.message.chat.id, call.message.message_id)

    # МАГАЗИН ПРЕДМЕТОВ
    elif call.data == "item_shop":
        bot.edit_message_text(
            "🏪 МАГАЗИН ПРЕДМЕТОВ\n\n🎁 Бокс (420💰) — открывает монеты или предметы\n🥡 Супер Бокс (2500💰) — много монет + бонус\n🎲 Кость (10000💰) — удача!\n🪎 Сундук (6500💰) — монеты + бокс\n💜 Ультра Харт (150000💰) — +1 уровень всех скиллов",
            call.message.chat.id, call.message.message_id, reply_markup=item_shop_keyboard())

    # ПОКУПКА ПРЕДМЕТОВ
    elif call.data.startswith("buy_item_"):
        item_name = call.data[9:]
        prices = {
            '🎁 Бокс': 420,
            '🥡 Супер Бокс': 2500,
            '🎲 Кость': 10000,
            '🪎 Сундук': 6500,
            '💜 Ультра Харт': 150000
        }
        price = prices.get(item_name, 0)

        if coins >= price:
            coins -= price
            cursor.execute('UPDATE users SET coins = ? WHERE user_id = ?', (coins, user_id))
            init_inventory(user_id)
            cursor.execute('UPDATE inventory SET quantity = quantity + 1 WHERE user_id = ? AND item_name = ?', (user_id, item_name))
            conn.commit()
            bot.answer_callback_query(call.id, f"✅ Куплен {item_name}!")

            cursor.execute('SELECT coins FROM users WHERE user_id = ?', (user_id,))
            new_coins = cursor.fetchone()[0]
            bot.edit_message_text(
                f"🏪 МАГАЗИН ПРЕДМЕТОВ\n\nУ вас: {new_coins}💰\n\n🎁 Бокс (420💰)\n🥡 Супер Бокс (2500💰)\n🎲 Кость (10000💰)\n🪎 Сундук (6500💰)\n💜 Ультра Харт (150000💰)",
                call.message.chat.id, call.message.message_id, reply_markup=item_shop_keyboard())
        else:
            bot.answer_callback_query(call.id, "❌ Не хватает монет!")

    # ТОП
    elif call.data == "top":
        cursor.execute('SELECT username, clicks FROM users ORDER BY clicks DESC LIMIT 10')
        top_users = cursor.fetchall()
        top_text = "🏆 ТОП-10 ПО КЛИКАМ 🏆\n\n"
        for i, (name, clicks_count) in enumerate(top_users, 1):
            top_text += f"{i}. @{name} — {clicks_count} кликов\n"
        bot.edit_message_text(top_text, call.message.chat.id, call.message.message_id, reply_markup=main_keyboard())

    # НАЗАД
    elif call.data == "back":
        cursor.execute('SELECT clicks, coins FROM users WHERE user_id = ?', (user_id,))
        clicks, coins = cursor.fetchone()
        bot.edit_message_text(
            f"📊 Статистика @{username}:\n\n🔨 Кликов: {clicks}\n💰 Монет: {coins}",
            call.message.chat.id, call.message.message_id, reply_markup=main_keyboard())

# ЗАПУСК
# ========== ДЛЯ RENDER.COM ==========
from flask import Flask
import threading
import os

app = Flask(__name__)

@app.route('/')
def index():
    return "Бот работает!"

def run_bot():
    print("✅ БОТ ЗАПУЩЕН!")
    bot.infinity_polling()

if __name__ == '__main__':
    # Запускаем бота в отдельном потоке
    bot_thread = threading.Thread(target=run_bot)
    bot_thread.start()
    
    # Запускаем Flask сервер (нужен для Render)
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
