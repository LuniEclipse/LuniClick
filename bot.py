import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import sqlite3
import random
import os

TOKEN = '8878924452:AAESshZV4YhInNNOR2YXwsMwwfqlVsxjCj8'  # Вставьте токен
ADMIN_IDS = [7778727422]

bot = telebot.TeleBot(TOKEN)

conn = sqlite3.connect('clicker.db', check_same_thread=False)
cursor = conn.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    clicks INTEGER DEFAULT 0,
    coins INTEGER DEFAULT 0,
    click_level INTEGER DEFAULT 1,
    coin_level INTEGER DEFAULT 1,
    crit_level INTEGER DEFAULT 1,
    luck_level INTEGER DEFAULT 1,
    username TEXT
)
''')
cursor.execute('''
CREATE TABLE IF NOT EXISTS inventory (
    user_id INTEGER,
    item_name TEXT,
    quantity INTEGER DEFAULT 0,
    PRIMARY KEY (user_id, item_name)
)
''')
conn.commit()

ALL_ITEMS = ['🎁 Бокс', '🥡 Супер Бокс', '🎲 Кость', '🪎 Сундук', '💜 Ультра Харт', '💟 Холик', '🧠 Мозг']

def get_username(user):
    return user.username or f"id{user.id}"

def init_inventory(user_id):
    for item in ALL_ITEMS:
        cursor.execute('INSERT OR IGNORE INTO inventory (user_id, item_name, quantity) VALUES (?, ?, 0)', (user_id, item))
    conn.commit()

def get_inventory_list(user_id):
    cursor.execute('SELECT item_name, quantity FROM inventory WHERE user_id = ? AND quantity > 0 ORDER BY item_name', (user_id,))
    return cursor.fetchall()

# Главная клавиатура
def main_keyboard():
    markup = InlineKeyboardMarkup(row_width=2)
    try:
        click_button = InlineKeyboardButton(
            text="Клик!",
            callback_data="click",
            icon_custom_emoji_id="5298916708893878211"
        )
    except:
        click_button = InlineKeyboardButton("🔨 Клик!", callback_data="click")
    
    markup.add(
        click_button,
        InlineKeyboardButton("✨ Скиллухи", callback_data="shop"),
        InlineKeyboardButton("🎒 Склад", callback_data="inventory"),
        InlineKeyboardButton("🏩 Магазин", callback_data="item_shop"),
        InlineKeyboardButton("📊 Топ игроков", callback_data="top")
    )
    return markup

def skill_shop_keyboard(user_id):
    cursor.execute('SELECT click_level, coin_level, crit_level, luck_level, coins FROM users WHERE user_id = ?', (user_id,))
    click_lvl, coin_lvl, crit_lvl, luck_lvl, coins = cursor.fetchone()
    
    click_price = 100 * (click_lvl ** 1.5)
    coin_price = 100 * (coin_lvl ** 1.5)
    crit_price = 1500 * (crit_lvl ** 1.2)
    luck_price = 3500 * (luck_lvl ** 1.2)
    
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton(f"⚡ Удвоение кликов (ур. {click_lvl}) - {int(click_price)}💰", callback_data="buy_click"),
        InlineKeyboardButton(f"💰 Удвоение монет (ур. {coin_lvl}) - {int(coin_price)}💰", callback_data="buy_coin"),
        InlineKeyboardButton(f"🪓 Крит (ур. {crit_lvl}) - {int(crit_price)}💰 | {3 + (crit_lvl-1)*0.5}% | x3", callback_data="buy_crit"),
        InlineKeyboardButton(f"🍀 Удача (ур. {luck_lvl}) - {int(luck_price)}💰 | {1 + (luck_lvl-1)*0.5}% | x2", callback_data="buy_luck"),
        InlineKeyboardButton("◀ Назад", callback_data="back")
    )
    return markup, click_price, coin_price, crit_price, luck_price

def item_shop_keyboard():
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton("🎁 Бокс - 420💰", callback_data="buy_item_🎁 Бокс"),
        InlineKeyboardButton("🥡 Супер Бокс - 2500💰", callback_data="buy_item_🥡 Супер Бокс"),
        InlineKeyboardButton("🎲 Кость - 10000💰", callback_data="buy_item_🎲 Кость"),
        InlineKeyboardButton("🪎 Сундук - 6500💰", callback_data="buy_item_🪎 Сундук"),
        InlineKeyboardButton("💜 Ультра Харт - 150000💰", callback_data="buy_item_💜 Ультра Харт"),
        InlineKeyboardButton("💟 Холик - 125000💰", callback_data="buy_item_💟 Холик"),
        InlineKeyboardButton("🧠 Мозг - 5000000💰", callback_data="buy_item_🧠 Мозг"),
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
        text += "\n📌 Команды:\n• юзнуть (номер)\n• дать (номер) (@user) (кол-во)"
    
    if message_id:
        bot.edit_message_text(text, chat_id, message_id, reply_markup=markup)
    else:
        bot.send_message(chat_id, text, reply_markup=markup)

def use_item(user_id, username, item_index):
    items = get_inventory_list(user_id)
    
    if item_index < 1 or item_index > len(items):
        return False, "❌ Неверный номер!"
    
    item_name, quantity = items[item_index - 1]
    
    if quantity <= 0:
        return False, "❌ Нет предмета!"
    
    cursor.execute('UPDATE inventory SET quantity = quantity - 1 WHERE user_id = ? AND item_name = ?', (user_id, item_name))
    conn.commit()
    
    result_text = f"🎁 @{username} использовал {item_name}!\n\n"
    
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
            result_text += f"🎲 6! Джекпот! +{coins_gain}💰"
        else:
            result_text += f"🎲 Выпало {roll}"
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
        result_text += "✨ Все скиллы +1!"
    elif item_name in ['💟 Холик', '🧠 Мозг']:
        result_text += "✨ Коллекционный предмет! ✨"
    
    conn.commit()
    return True, result_text

def transfer_item(from_user_id, item_index, target_username, quantity):
    items = get_inventory_list(from_user_id)
    
    if item_index < 1 or item_index > len(items):
        return False, "❌ Неверный номер!"
    
    item_name, have_qty = items[item_index - 1]
    
    if have_qty < quantity:
        return False, f"❌ Есть только {have_qty} шт."
    
    if target_username.startswith('@'):
        target_username = target_username[1:]
    
    cursor.execute('SELECT user_id FROM users WHERE username = ?', (target_username,))
    result = cursor.fetchone()
    
    if not result:
        return False, f"❌ @{target_username} не найден!"
    
    target_user_id = result[0]
    
    cursor.execute('UPDATE inventory SET quantity = quantity - ? WHERE user_id = ? AND item_name = ?', (quantity, from_user_id, item_name))
    cursor.execute('INSERT OR IGNORE INTO inventory (user_id, item_name, quantity) VALUES (?, ?, 0)', (target_user_id, item_name))
    cursor.execute('UPDATE inventory SET quantity = quantity + ? WHERE user_id = ? AND item_name = ?', (quantity, target_user_id, item_name))
    conn.commit()
    
    return True, f"✅ Передано {quantity} шт. @{target_username}!"

# ========== КОМАНДЫ ==========

@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    username = get_username(message.from_user)
    
    cursor.execute('INSERT OR IGNORE INTO users (user_id, username, crit_level, luck_level) VALUES (?, ?, 1, 1)', (user_id, username))
    conn.commit()
    init_inventory(user_id)
    
    bot.send_message(message.chat.id,
        f"🎑🍀 Приветствую! Добро пожаловать в ЛуниКликер, @{username}! 💕\n\nКликай кнопку, покупай предметы, улучшай Скиллухи, вырывайся в топ! 💕",
        reply_markup=main_keyboard())

@bot.message_handler(func=lambda message: message.text and message.text.lower() in ['кли', 'кликер'])
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
        bot.send_message(message.chat.id, "❌ Напишите /start")

@bot.message_handler(func=lambda message: message.text and message.text.lower().startswith('юзнуть'))
def use_command(message):
    user_id = message.from_user.id
    username = get_username(message.from_user)
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
    except:
        bot.reply_to(message, "❌ Ошибка!")

@bot.message_handler(func=lambda message: message.text and message.text.lower().startswith('дать'))
def give_item_command(message):
    user_id = message.from_user.id
    init_inventory(user_id)
    
    try:
        parts = message.text.split()
        if len(parts) != 4:
            bot.reply_to(message, "❌ Используйте: дать (номер) (@username) (количество)")
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
    except:
        bot.reply_to(message, "❌ Ошибка!")

@bot.message_handler(commands=['give'])
def give_admin(message):
    if message.from_user.id not in ADMIN_IDS:
        return
    
    try:
        parts = message.text.split()
        target = parts[1]
        amount = int(parts[2])
        
        if target.startswith('@'):
            username = target[1:]
            cursor.execute('SELECT user_id FROM users WHERE username = ?', (username,))
        else:
            cursor.execute('SELECT user_id FROM users WHERE user_id = ?', (int(target),))
        
        result = cursor.fetchone()
        if result:
            cursor.execute('UPDATE users SET coins = coins + ? WHERE user_id = ?', (amount, result[0]))
            conn.commit()
            bot.reply_to(message, f"✅ Выдано {amount}💰!")
    except:
        bot.reply_to(message, "❌ Ошибка!")

# ========== КНОПКИ ==========

@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    user_id = call.from_user.id
    cursor.execute('SELECT click_level, coin_level, crit_level, luck_level, clicks, coins, username FROM users WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    
    if not result:
        bot.answer_callback_query(call.id, "❌ Напишите /start")
        init_inventory(user_id)
        return
    
    click_lvl, coin_lvl, crit_lvl, luck_lvl, clicks, coins, username = result
    
    if call.data == "click":
        gain = click_lvl
        coins_gain = coin_lvl
        
        crit_chance = 3 + (crit_lvl - 1) * 0.5
        if random.random() * 100 < crit_chance:
            gain *= 3
            coins_gain *= 3
            crit_text = "\n🔥 КРИТ x3!"
        else:
            crit_text = ""
        
        luck_chance = 1 + (luck_lvl - 1) * 0.5
        if random.random() * 100 < luck_chance:
            gain *= 2
            coins_gain *= 2
            luck_text = "\n🍀 УДАЧА x2!"
        else:
            luck_text = ""
        
        clicks += gain
        coins += coins_gain
        
        cursor.execute('UPDATE users SET clicks = ?, coins = ? WHERE user_id = ?', (clicks, coins, user_id))
        conn.commit()
        
        bot.edit_message_text(
            f"📊 @{username}:\n🔨 {clicks} кликов\n💰 {coins} монет\n\n+{gain}/{coins_gain}{crit_text}{luck_text}",
            call.message.chat.id, call.message.message_id, reply_markup=main_keyboard())
    
    elif call.data == "shop":
        markup, cp, cnp, crp, lp = skill_shop_keyboard(user_id)
        bot.edit_message_text(
            f"✨ СКИЛЛУХИ\n💰 {coins}\n\n⚡ Клики ур.{click_lvl} - {int(cp)}💰\n💰 Монеты ур.{coin_lvl} - {int(cnp)}💰\n🪓 Крит ур.{crit_lvl} - {int(crp)}💰\n🍀 Удача ур.{luck_lvl} - {int(lp)}💰",
            call.message.chat.id, call.message.message_id, reply_markup=markup)
    
    elif call.data == "inventory":
        init_inventory(user_id)
        show_inventory(user_id, call.message.chat.id, call.message.message_id)
    
    elif call.data == "item_shop":
        bot.edit_message_text(
            "🏩 МАГАЗИН\n\n🎁 Бокс 420💰\n🥡 Супер Бокс 2500💰\n🎲 Кость 10000💰\n🪎 Сундук 6500💰\n💜 Ультра Харт 150000💰\n💟 Холик 125000💰\n🧠 Мозг 5000000💰",
            call.message.chat.id, call.message.message_id, reply_markup=item_shop_keyboard())
    
    elif call.data == "top":
        cursor.execute('SELECT username, clicks FROM users ORDER BY clicks DESC LIMIT 10')
        top = cursor.fetchall()
        text = "🏆 ТОП-10\n\n" + "\n".join([f"{i}. @{n} — {c} кликов" for i, (n, c) in enumerate(top, 1)])
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=main_keyboard())
    
    elif call.data == "back":
        bot.edit_message_text(
            f"📊 @{username}:\n🔨 {clicks} кликов\n💰 {coins} монет",
            call.message.chat.id, call.message.message_id, reply_markup=main_keyboard())
    
    elif call.data.startswith("buy_item_"):
        item = call.data[9:]
        prices = {
            '🎁 Бокс': 420, '🥡 Супер Бокс': 2500, '🎲 Кость': 10000,
            '🪎 Сундук': 6500, '💜 Ультра Харт': 150000,
            '💟 Холик': 125000, '🧠 Мозг': 5000000
        }
        price = prices.get(item, 0)
        if coins >= price:
            coins -= price
            cursor.execute('UPDATE users SET coins = ? WHERE user_id = ?', (coins, user_id))
            init_inventory(user_id)
            cursor.execute('UPDATE inventory SET quantity = quantity + 1 WHERE user_id = ? AND item_name = ?', (user_id, item))
            conn.commit()
            bot.answer_callback_query(call.id, f"✅ Куплен {item}!")
            bot.edit_message_text(
                f"🏩 МАГАЗИН\nУ вас: {coins}💰\n\n🎁 420💰\n🥡 2500💰\n🎲 10000💰\n🪎 6500💰\n💜 150000💰\n💟 125000💰\n🧠 5000000💰",
                call.message.chat.id, call.message.message_id, reply_markup=item_shop_keyboard())
        else:
            bot.answer_callback_query(call.id, "❌ Не хватает!")
    
    elif call.data in ["buy_click", "buy_coin", "buy_crit", "buy_luck"]:
        markup, cp, cnp, crp, lp = skill_shop_keyboard(user_id)
        price = int({'buy_click': cp, 'buy_coin': cnp, 'buy_crit': crp, 'buy_luck': lp}[call.data])
        lvl_name = {'buy_click': 'click_level', 'buy_coin': 'coin_level', 'buy_crit': 'crit_level', 'buy_luck': 'luck_level'}[call.data]
        cur = {'buy_click': click_lvl, 'buy_coin': coin_lvl, 'buy_crit': crit_lvl, 'buy_luck': luck_lvl}[call.data]
        
        if coins >= price and cur < 50:
            coins -= price
            new = cur + 1
            cursor.execute(f'UPDATE users SET {lvl_name} = ?, coins = ? WHERE user_id = ?', (new, coins, user_id))
            conn.commit()
            bot.answer_callback_query(call.id, f"✅ Уровень {new}!")
            
            nmk, ncp, ncnp, ncrp, nlp = skill_shop_keyboard(user_id)
            bot.edit_message_text(
                f"✨ СКИЛЛУХИ\n💰 {coins}\n\n⚡ Клики ур.{new if call.data == 'buy_click' else click_lvl} - {int(ncp)}💰\n💰 Монеты ур.{new if call.data == 'buy_coin' else coin_lvl} - {int(ncnp)}💰\n🪓 Крит ур.{new if call.data == 'buy_crit' else crit_lvl} - {int(ncrp)}💰\n🍀 Удача ур.{new if call.data == 'buy_luck' else luck_lvl} - {int(nlp)}💰",
                call.message.chat.id, call.message.message_id, reply_markup=nmk)
        else:
            bot.answer_callback_query(call.id, "❌ Не хватает или макс. уровень (50)!")

# ЗАПУСК
if __name__ == '__main__':
    print("✅ БОТ ЗАПУЩЕН!")
    bot.infinity_polling()
