import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import sqlite3
import random
import os
from flask import Flask
import threading

TOKEN = '8878924452:AAESshZV4YhInNNOR2YXwsMwwfqlVsxjCj8'
ADMIN_IDS = [7778727422]

bot = telebot.TeleBot(TOKEN)

conn = sqlite3.connect('clicker.db', check_same_thread=False)
cursor = conn.cursor()

cursor.execute('CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, clicks INTEGER DEFAULT 0, coins INTEGER DEFAULT 0, click_level INTEGER DEFAULT 1, coin_level INTEGER DEFAULT 1, crit_level INTEGER DEFAULT 1, luck_level INTEGER DEFAULT 1, username TEXT)')
cursor.execute('CREATE TABLE IF NOT EXISTS inventory (user_id INTEGER, item_name TEXT, quantity INTEGER DEFAULT 0, PRIMARY KEY (user_id, item_name))')
conn.commit()

ALL_ITEMS = ['🎁 Бокс', '🥡 Супер Бокс', '🎲 Кость', '🪎 Сундук', '💜 Ультра Харт', '💟 Холик', '🧠 Мозг']

def get_username(user): return user.username or f"id{user.id}"

def init_inventory(user_id):
    for item in ALL_ITEMS:
        cursor.execute('INSERT OR IGNORE INTO inventory (user_id, item_name, quantity) VALUES (?, ?, 0)', (user_id, item))
    conn.commit()

def get_inv(user_id): return cursor.execute('SELECT item_name, quantity FROM inventory WHERE user_id=? AND quantity>0 ORDER BY item_name', (user_id,)).fetchall()

def main_keyboard():
    markup = InlineKeyboardMarkup(row_width=2)
    try: btn = InlineKeyboardButton(text="Клик!", callback_data="click", icon_custom_emoji_id="5298916708893878211")
    except: btn = InlineKeyboardButton("🔨 Клик!", callback_data="click")
    markup.add(btn, InlineKeyboardButton("✨ Скиллухи", callback_data="shop"), InlineKeyboardButton("🎒 Склад", callback_data="inventory"), InlineKeyboardButton("🏩 Магазин", callback_data="item_shop"), InlineKeyboardButton("📊 Топ", callback_data="top"))
    return markup

def skill_shop(user_id):
    click_lvl, coin_lvl, crit_lvl, luck_lvl, coins = cursor.execute('SELECT click_level, coin_level, crit_level, luck_level, coins FROM users WHERE user_id=?', (user_id,)).fetchone()
    cp, cnp, crp, lp = 100*(click_lvl**1.5), 100*(coin_lvl**1.5), 1500*(crit_lvl**1.2), 3500*(luck_lvl**1.2)
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(InlineKeyboardButton(f"⚡ Клики ур.{click_lvl} - {int(cp)}💰", callback_data="buy_click"), InlineKeyboardButton(f"💰 Монеты ур.{coin_lvl} - {int(cnp)}💰", callback_data="buy_coin"), InlineKeyboardButton(f"🪓 Крит ур.{crit_lvl} - {int(crp)}💰", callback_data="buy_crit"), InlineKeyboardButton(f"🍀 Удача ур.{luck_lvl} - {int(lp)}💰", callback_data="buy_luck"), InlineKeyboardButton("◀ Назад", callback_data="back"))
    return markup, cp, cnp, crp, lp

def item_shop_kb():
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(InlineKeyboardButton("🎁 Бокс - 420💰", callback_data="buy_item_🎁 Бокс"), InlineKeyboardButton("🥡 Супер Бокс - 2500💰", callback_data="buy_item_🥡 Супер Бокс"), InlineKeyboardButton("🎲 Кость - 10000💰", callback_data="buy_item_🎲 Кость"), InlineKeyboardButton("🪎 Сундук - 6500💰", callback_data="buy_item_🪎 Сундук"), InlineKeyboardButton("💜 Ультра Харт - 150000💰", callback_data="buy_item_💜 Ультра Харт"), InlineKeyboardButton("💟 Холик - 125000💰", callback_data="buy_item_💟 Холик"), InlineKeyboardButton("🧠 Мозг - 5000000💰", callback_data="buy_item_🧠 Мозг"), InlineKeyboardButton("◀ Назад", callback_data="back"))
    return markup

def show_inv(user_id, chat_id, msg_id=None):
    items = get_inv(user_id)
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("◀ Назад", callback_data="back"))
    if not items: text = "🗃 Пусто.. 😅"
    else:
        text = "🗃 Твой складик:\n"
        for i, (n, q) in enumerate(items, 1): text += f"{i}. {n} — {q} шт.\n"
        text += "\nюзнуть (номер) | дать (номер) (@user) (кол-во)"
    if msg_id: bot.edit_message_text(text, chat_id, msg_id, reply_markup=markup)
    else: bot.send_message(chat_id, text, reply_markup=markup)

def use_item(user_id, username, idx):
    items = get_inv(user_id)
    if idx<1 or idx>len(items): return False, "❌ Неверный номер!"
    name, qty = items[idx-1]
    if qty<=0: return False, "❌ Нет предмета!"
    cursor.execute('UPDATE inventory SET quantity=quantity-1 WHERE user_id=? AND item_name=?', (user_id, name))
    conn.commit()
    res = f"🎁 @{username} использовал {name}!\n\n"
    if name == '🎁 Бокс':
        r = random.random()
        if r<0.8:
            g = random.randint(50,1500)
            cursor.execute('UPDATE users SET coins=coins+? WHERE user_id=?', (g, user_id))
            res += f"💰 +{g} монет!"
        elif r<0.9:
            g = random.randint(1,8)
            cursor.execute('UPDATE inventory SET quantity=quantity+? WHERE user_id=? AND item_name=?', (g, user_id, '🥡 Супер Бокс'))
            res += f"🎁 +{g} 🥡 Супер Бокс!"
        else:
            g = random.randint(1,3)
            cursor.execute('UPDATE inventory SET quantity=quantity+? WHERE user_id=? AND item_name=?', (g, user_id, '🎲 Кость'))
            res += f"🎲 +{g} 🎲 Кость!"
    elif name == '🥡 Супер Бокс':
        g = random.randint(500,5000)
        cursor.execute('UPDATE users SET coins=coins+? WHERE user_id=?', (g, user_id))
        res += f"💰 +{g} монет!"
        if random.random()<0.3:
            g = random.randint(1,3)
            cursor.execute('UPDATE inventory SET quantity=quantity+? WHERE user_id=? AND item_name=?', (g, user_id, '🎁 Бокс'))
            res += f"\n🎁 +{g} 🎁 Бокс!"
    elif name == '🎲 Кость':
        r = random.randint(1,6)
        if r==6:
            g = random.randint(1000,10000)
            cursor.execute('UPDATE users SET coins=coins+? WHERE user_id=?', (g, user_id))
            res += f"🎲 6! Джекпот! +{g}💰"
        else: res += f"🎲 Выпало {r}"
    elif name == '🪎 Сундук':
        g = random.randint(500,3000)
        cursor.execute('UPDATE users SET coins=coins+? WHERE user_id=?', (g, user_id))
        res += f"💰 +{g} монет!"
        if random.random()<0.2:
            g = random.randint(1,2)
            cursor.execute('UPDATE inventory SET quantity=quantity+? WHERE user_id=? AND item_name=?', (g, user_id, '🎁 Бокс'))
            res += f"\n📦 +{g} 🎁 Бокс!"
    elif name == '💜 Ультра Харт':
        cursor.execute('UPDATE users SET click_level=click_level+1, coin_level=coin_level+1 WHERE user_id=?', (user_id,))
        res += "✨ Все скиллы +1!"
    elif name in ['💟 Холик', '🧠 Мозг']:
        res += "✨ Коллекционный предмет! ✨"
    conn.commit()
    return True, res

def transfer(from_id, idx, target, qty):
    items = get_inv(from_id)
    if idx<1 or idx>len(items): return False, "❌ Неверный номер!"
    name, have = items[idx-1]
    if have<qty: return False, f"❌ Есть только {have} шт."
    if target.startswith('@'): target=target[1:]
    r = cursor.execute('SELECT user_id FROM users WHERE username=?', (target,)).fetchone()
    if not r: return False, f"❌ @{target} не найден!"
    tid = r[0]
    cursor.execute('UPDATE inventory SET quantity=quantity-? WHERE user_id=? AND item_name=?', (qty, from_id, name))
    cursor.execute('INSERT OR IGNORE INTO inventory VALUES (?,?,0)', (tid, name))
    cursor.execute('UPDATE inventory SET quantity=quantity+? WHERE user_id=? AND item_name=?', (qty, tid, name))
    conn.commit()
    return True, f"✅ Передано {qty} шт. @{target}!"

@bot.message_handler(commands=['start'])
def start(m):
    uid = m.from_user.id
    name = get_username(m.from_user)
    cursor.execute('INSERT OR IGNORE INTO users (user_id, username, crit_level, luck_level) VALUES (?,?,1,1)', (uid, name))
    conn.commit()
    init_inventory(uid)
    bot.send_message(m.chat.id, f"🎑🍀 Приветствую! Добро пожаловать в ЛуниКликер, @{name}! 💕\n\nКликай кнопку, покупай предметы, улучшай Скиллухи, вырывайся в топ! 💕", reply_markup=main_keyboard())

@bot.message_handler(func=lambda m: m.text and m.text.lower() in ['кли', 'кликер'])
def menu(m):
    uid = m.from_user.id
    r = cursor.execute('SELECT clicks, coins FROM users WHERE user_id=?', (uid,)).fetchone()
    if r: bot.send_message(m.chat.id, f"📊 @{get_username(m.from_user)}:\n🔨 {r[0]} кликов\n💰 {r[1]} монет", reply_markup=main_keyboard())
    else: bot.send_message(m.chat.id, "❌ /start")

@bot.message_handler(func=lambda m: m.text and m.text.lower().startswith('юзнуть'))
def use_cmd(m):
    uid = m.from_user.id
    name = get_username(m.from_user)
    init_inventory(uid)
    try:
        parts = m.text.split()
        if len(parts)!=2: bot.reply_to(m, "❌ юзнуть (номер)"); return
        ok, res = use_item(uid, name, int(parts[1]))
        bot.reply_to(m, res)
        if ok: show_inv(uid, m.chat.id)
    except: bot.reply_to(m, "❌ Ошибка!")

@bot.message_handler(func=lambda m: m.text and m.text.lower().startswith('дать'))
def give_cmd(m):
    uid = m.from_user.id
    init_inventory(uid)
    try:
        parts = m.text.split()
        if len(parts)!=4: bot.reply_to(m, "❌ дать (номер) (@user) (кол-во)"); return
        ok, res = transfer(uid, int(parts[1]), parts[2], int(parts[3]))
        bot.reply_to(m, res)
        if ok: show_inv(uid, m.chat.id)
    except: bot.reply_to(m, "❌ Ошибка!")

@bot.message_handler(commands=['give'])
def give_admin(m):
    if m.from_user.id not in ADMIN_IDS: return
    try:
        parts = m.text.split()
        t = parts[1]
        amt = int(parts[2])
        if t.startswith('@'): uid = cursor.execute('SELECT user_id FROM users WHERE username=?', (t[1:],)).fetchone()[0]
        else: uid = int(t)
        cursor.execute('UPDATE users SET coins=coins+? WHERE user_id=?', (amt, uid))
        conn.commit()
        bot.reply_to(m, f"✅ Выдано {amt}💰")
    except: bot.reply_to(m, "❌ Ошибка!")

@bot.callback_query_handler(func=lambda call: True)
def cb(call):
    uid = call.from_user.id
    r = cursor.execute('SELECT click_level, coin_level, crit_level, luck_level, clicks, coins, username FROM users WHERE user_id=?', (uid,)).fetchone()
    if not r: bot.answer_callback_query(call.id, "❌ /start"); init_inventory(uid); return
    cl, col, crl, lul, clicks, coins, name = r

    if call.data == "click":
        g, cg = cl, col
        crc = 3 + (crl-1)*0.5
        if random.random()*100 < crc: g*=3; cg*=3; crit_txt = "\n🔥 КРИТ x3!"
        else: crit_txt = ""
        lc = 1 + (lul-1)*0.5
        if random.random()*100 < lc: g*=2; cg*=2; luck_txt = "\n🍀 УДАЧА x2!"
        else: luck_txt = ""
        clicks += g; coins += cg
        cursor.execute('UPDATE users SET clicks=?, coins=? WHERE user_id=?', (clicks, coins, uid))
        conn.commit()
        bot.edit_message_text(f"📊 @{name}:\n🔨 {clicks}\n💰 {coins}\n+{g}/{cg}{crit_txt}{luck_txt}", call.message.chat.id, call.message.message_id, reply_markup=main_keyboard())

    elif call.data == "shop":
        mk, cp, cnp, crp, lp = skill_shop(uid)
        bot.edit_message_text(f"✨ СКИЛЛУХИ\n💰 {coins}\n⚡ Клики ур.{cl} - {int(cp)}💰\n💰 Монеты ур.{col} - {int(cnp)}💰\n🪓 Крит ур.{crl} - {int(crp)}💰\n🍀 Удача ур.{lul} - {int(lp)}💰", call.message.chat.id, call.message.message_id, reply_markup=mk)

    elif call.data == "inventory":
        init_inventory(uid)
        show_inv(uid, call.message.chat.id, call.message.message_id)

    elif call.data == "item_shop":
        bot.edit_message_text("🏩 МАГАЗИН\n\n🎁 420💰\n🥡 2500💰\n🎲 10000💰\n🪎 6500💰\n💜 150000💰\n💟 125000💰\n🧠 5000000💰", call.message.chat.id, call.message.message_id, reply_markup=item_shop_kb())

    elif call.data == "top":
        top = cursor.execute('SELECT username, clicks FROM users ORDER BY clicks DESC LIMIT 10').fetchall()
        text = "🏆 ТОП-10\n\n" + "\n".join([f"{i}. @{n} — {c}" for i,(n,c) in enumerate(top,1)])
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=main_keyboard())

    elif call.data == "back":
        bot.edit_message_text(f"📊 @{name}:\n🔨 {clicks}\n💰 {coins}", call.message.chat.id, call.message.message_id, reply_markup=main_keyboard())

    elif call.data.startswith("buy_item_"):
        item = call.data[9:]
        prices = {'🎁 Бокс':420, '🥡 Супер Бокс':2500, '🎲 Кость':10000, '🪎 Сундук':6500, '💜 Ультра Харт':150000, '💟 Холик':125000, '🧠 Мозг':5000000}
        price = prices.get(item,0)
        if coins >= price:
            coins -= price
            cursor.execute('UPDATE users SET coins=? WHERE user_id=?', (coins, uid))
            init_inventory(uid)
            cursor.execute('UPDATE inventory SET quantity=quantity+1 WHERE user_id=? AND item_name=?', (uid, item))
            conn.commit()
            bot.answer_callback_query(call.id, f"✅ Куплен {item}!")
            bot.edit_message_text(f"🏩 МАГАЗИН\nУ вас: {coins}💰\n\n🎁 420💰\n🥡 2500💰\n🎲 10000💰\n🪎 6500💰\n💜 150000💰\n💟 125000💰\n🧠 5000000💰", call.message.chat.id, call.message.message_id, reply_markup=item_shop_kb())
        else: bot.answer_callback_query(call.id, "❌ Не хватает!")

    elif call.data in ["buy_click", "buy_coin", "buy_crit", "buy_luck"]:
        mk, cp, cnp, crp, lp = skill_shop(uid)
        price = int({'buy_click':cp, 'buy_coin':cnp, 'buy_crit':crp, 'buy_luck':lp}[call.data])
        lvl_name = {'buy_click':'click_level', 'buy_coin':'coin_level', 'buy_crit':'crit_level', 'buy_luck':'luck_level'}[call.data]
        cur = {'buy_click':cl, 'buy_coin':col, 'buy_crit':crl, 'buy_luck':lul}[call.data]
        if coins >= price and cur < 50:
            coins -= price
            new = cur+1
            cursor.execute(f'UPDATE users SET {lvl_name}=?, coins=? WHERE user_id=?', (new, coins, uid))
            conn.commit()
            bot.answer_callback_query(call.id, f"✅ Уровень {new}!")
            nmk, ncp, ncnp, ncrp, nlp = skill_shop(uid)
            bot.edit_message_text(f"✨ СКИЛЛУХИ\n💰 {coins}\n⚡ Клики ур.{new if call.data=='buy_click' else cl} - {int(ncp)}💰\n💰 Монеты ур.{new if call.data=='buy_coin' else col} - {int(ncnp)}💰\n🪓 Крит ур.{new if call.data=='buy_crit' else crl} - {int(ncrp)}💰\n🍀 Удача ур.{new if call.data=='buy_luck' else lul} - {int(nlp)}💰", call.message.chat.id, call.message.message_id, reply_markup=nmk)
        else: bot.answer_callback_query(call.id, "❌ Не хватает!")

# ========== ДЛЯ RENDER.COM ==========
app = Flask(__name__)

@app.route('/')
def index():
    return "Бот работает!"

def run_bot():
    print("✅ БОТ ЗАПУЩЕН!")
    bot.infinity_polling()

if __name__ == '__main__':
    bot_thread = threading.Thread(target=run_bot)
    bot_thread.start()
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
