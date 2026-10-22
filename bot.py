import telebot
from telebot import types
import requests
import sqlite3
import datetime
import random
import string
import hashlib
import base64
import socket
import os
import time
import dns.resolver
import qrcode
import io
from flask import Flask, request

# --- НАСТРОЙКИ ---
TOKEN = "8669608672:AAGag-1axn1qx24xtK0OAb2jSMGkcMnW2AI"
ADMIN_ID = 8633674798 
ADMIN_PIN = "1337"
URL = "https://osint-panel-6r67.onrender.com"

bot = telebot.TeleBot(TOKEN, threaded=False)
app = Flask(__name__)

# --- БАЗА ДАННЫХ ---
def init_db():
    conn = sqlite3.connect('bot_logs.db')
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS logs (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT, command TEXT, query TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS users (user_id TEXT PRIMARY KEY)')
    conn.commit()
    conn.close()

init_db()

# --- МЕНЮ ---
def get_main_menu():
    m = types.InlineKeyboardMarkup()
    m.add(types.InlineKeyboardButton("🌐 СЕТЬ И IP", callback_data='cat_net'))
    m.add(types.InlineKeyboardButton("👤 ЛЮДИ", callback_data='cat_people'))
    m.add(types.InlineKeyboardButton("🛠️ УТИЛИТЫ", callback_data='cat_utils'))
    m.add(types.InlineKeyboardButton("🔐 АДМИН", callback_data='menu_admin'))
    return m

def get_net_menu():
    m = types.InlineKeyboardMarkup()
    m.add(types.InlineKeyboardButton("🌍 Инфо по IP", callback_data='menu_ip'))
    m.add(types.InlineKeyboardButton("🔐 WHOIS", callback_data='menu_whois'))
    m.add(types.InlineKeyboardButton("🌐 DNS", callback_data='menu_dns'))
    m.add(types.InlineKeyboardButton("🛠️ Порты", callback_data='menu_port'))
    m.add(types.InlineKeyboardButton("📶 Пинг", callback_data='menu_ping'))
    m.add(types.InlineKeyboardButton("◀️ Назад", callback_data='main_back'))
    return m

def get_people_menu():
    m = types.InlineKeyboardMarkup()
    m.add(types.InlineKeyboardButton("👤 Ник", callback_data='menu_nick'))
    m.add(types.InlineKeyboardButton("📞 Номер", callback_data='menu_phone'))
    m.add(types.InlineKeyboardButton("📧 Почта", callback_data='menu_email'))
    m.add(types.InlineKeyboardButton("📱 TG ID", callback_data='menu_tgid'))
    m.add(types.InlineKeyboardButton("🆔 VK ID", callback_data='menu_vkid'))
    m.add(types.InlineKeyboardButton("◀️ Назад", callback_data='main_back'))
    return m

def get_utils_menu():
    m = types.InlineKeyboardMarkup()
    m.add(types.InlineKeyboardButton("💱 Валюта", callback_data='menu_currency'))
    m.add(types.InlineKeyboardButton("🔑 Пароль", callback_data='menu_pass'))
    m.add(types.InlineKeyboardButton("🧮 Калькулятор", callback_data='menu_calc'))
    m.add(types.InlineKeyboardButton("🌤 Погода", callback_data='menu_weather'))
    m.add(types.InlineKeyboardButton("🔐 Base64", callback_data='menu_base64'))
    m.add(types.InlineKeyboardButton("◀️ Назад", callback_data='main_back'))
    return m

def get_admin_menu():
    m = types.InlineKeyboardMarkup()
    m.add(types.InlineKeyboardButton("👥 Юзеры", callback_data='admin_users'))
    m.add(types.InlineKeyboardButton("📊 Стат", callback_data='admin_stats'))
    m.add(types.InlineKeyboardButton("📢 Рассылка", callback_data='admin_broadcast'))
    m.add(types.InlineKeyboardButton("◀️ Назад", callback_data='main_back'))
    return m

# --- СТАРТ ---
@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "🕵️ OSINT Бот v27.0\nВыбери меню или введи команду:", reply_markup=get_main_menu())

# --- ОБРАБОТЧИК КНОПОК ---
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    bot.answer_callback_query(call.id)
    
    if call.data == 'cat_net': bot.edit_message_text("СЕТЬ:", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=get_net_menu())
    elif call.data == 'cat_people': bot.edit_message_text("ЛЮДИ:", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=get_people_menu())
    elif call.data == 'cat_utils': bot.edit_message_text("УТИЛИТЫ:", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=get_utils_menu())
    elif call.data == 'main_back': bot.edit_message_text("Меню:", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=get_main_menu())
    
    elif call.data == 'menu_ip': msg = bot.send_message(call.message.chat.id, "IP:"); bot.register_next_step_handler(msg, process_ip)
    elif call.data == 'menu_whois': msg = bot.send_message(call.message.chat.id, "Домен:"); bot.register_next_step_handler(msg, process_whois)
    elif call.data == 'menu_dns': msg = bot.send_message(call.message.chat.id, "Домен:"); bot.register_next_step_handler(msg, process_dns)
    elif call.data == 'menu_port': msg = bot.send_message(call.message.chat.id, "IP:"); bot.register_next_step_handler(msg, process_port)
    elif call.data == 'menu_ping': msg = bot.send_message(call.message.chat.id, "Хост:"); bot.register_next_step_handler(msg, process_ping)
    elif call.data == 'menu_nick': msg = bot.send_message(call.message.chat.id, "Ник:"); bot.register_next_step_handler(msg, process_nick)
    elif call.data == 'menu_phone': msg = bot.send_message(call.message.chat.id, "Номер:"); bot.register_next_step_handler(msg, process_phone)
    elif call.data == 'menu_email': process_email(call.message)
    elif call.data == 'menu_tgid': msg = bot.send_message(call.message.chat.id, "TG:"); bot.register_next_step_handler(msg, process_tgid)
    elif call.data == 'menu_vkid': msg = bot.send_message(call.message.chat.id, "VK:"); bot.register_next_step_handler(msg, process_vkid)
    elif call.data == 'menu_currency': process_currency(call.message)
    elif call.data == 'menu_pass': msg = bot.send_message(call.message.chat.id, "Длина:"); bot.register_next_step_handler(msg, process_pass)
    elif call.data == 'menu_calc': msg = bot.send_message(call.message.chat.id, "Пример:"); bot.register_next_step_handler(msg, process_calc)
    elif call.data == 'menu_weather': msg = bot.send_message(call.message.chat.id, "Город:"); bot.register_next_step_handler(msg, process_weather)
    elif call.data == 'menu_base64': msg = bot.send_message(call.message.chat.id, "Текст:"); bot.register_next_step_handler(msg, process_base64)
    
    elif call.data == 'menu_admin':
        if call.from_user.id != ADMIN_ID: return bot.answer_callback_query(call.id, "Нет прав", show_alert=True)
        msg = bot.send_message(call.message.chat.id, "PIN:"); bot.register_next_step_handler(msg, check_admin_pin)
    elif call.data == 'admin_users':
        conn = sqlite3.connect('bot_logs.db'); c = conn.cursor(); c.execute("SELECT user_id FROM users LIMIT 20"); users = c.fetchall(); conn.close()
        res = "Юзеры:\n"
        for u in users: res += str(u[0]) + "\n"
        bot.send_message(call.message.chat.id, res)
    elif call.data == 'admin_stats':
        conn = sqlite3.connect('bot_logs.db'); c = conn.cursor(); c.execute("SELECT COUNT(*) FROM users"); u = c.fetchone()[0]; c.execute("SELECT COUNT(*) FROM logs"); l = c.fetchone()[0]; conn.close()
        bot.send_message(call.message.chat.id, "Юзеров: " + str(u) + "\nЛогов: " + str(l))
    elif call.data == 'admin_broadcast': msg = bot.send_message(call.message.chat.id, "Текст:"); bot.register_next_step_handler(msg, process_broadcast)

# --- БАЗОВЫЕ ФУНКЦИИ ---
def process_ip(message):
    try:
        r = requests.get("http://ip-api.com/json/" + message.text.strip()); d = r.json()
        if d['status'] == 'success': bot.reply_to(message, "IP: " + d['query'] + "\nСтрана: " + d['country'])
        else: bot.reply_to(message, "Неверный IP")
    except: bot.reply_to(message, "Ошибка")

def process_nick(message):
    u = message.text.strip().replace("@", "")
    try:
        r = requests.get("https://github.com/" + u)
        if r.status_code == 200: bot.reply_to(message, "GitHub: https://github.com/" + u)
        else: bot.reply_to(message, "Не найден")
    except: bot.reply_to(message, "Ошибка")

def process_phone(message):
    c = ''.join(filter(str.isdigit, message.text))
    if len(c) < 10: bot.reply_to(message, "Короткий"); return
    bot.reply_to(message, "Номер: " + c + "\nhttps://wa.me/" + c)

def process_email(message):
    try:
        r = requests.get("https://www.1secmail.com/api/v1/?action=genRandomMailbox&count=1"); e = r.json()[0]
        bot.reply_to(message, "Почта: " + e)
    except: bot.reply_to(message, "Ошибка")

def process_whois(message):
    d = message.text.strip()
    try:
        r = requests.get("https://rdap.org/domain/" + d, timeout=5)
        if r.status_code == 200: bot.reply_to(message, "Домен есть: " + d)
        else: bot.reply_to(message, "Не найден")
    except: bot.reply_to(message, "Ошибка")

def process_dns(message):
    d = message.text.strip(); msg = bot.reply_to(message, "Запрос..."); res = "DNS " + d + ":\n"
    try:
        for ans in dns.resolver.resolve(d, 'A'): res += "A: " + str(ans) + "\n"
    except: res += "Нет A-записей\n"
    bot.edit_message_text(res, chat_id=message.chat.id, message_id=msg.message_id)

def process_port(message):
    ip = message.text.strip(); msg = bot.reply_to(message, "Скан..."); res = "Порты " + ip + ":\n"
    for p in [21,22,80,443]:
        s = socket.socket(); s.settimeout(0.5)
        if s.connect_ex((ip, p)) == 0: res += "+ " + str(p) + "\n"
        s.close()
    bot.edit_message_text(res, chat_id=message.chat.id, message_id=msg.message_id)

def process_ping(message):
    host = message.text.strip(); msg = bot.reply_to(message, "Пинг...")
    try:
        start = time.time(); socket.create_connection((host, 80), timeout=3); ping = round((time.time() - start)*1000, 2)
        bot.edit_message_text("Пинг: " + str(ping) + " мс", chat_id=message.chat.id, message_id=msg.message_id)
    except: bot.edit_message_text("Недоступен", chat_id=message.chat.id, message_id=msg.message_id)

def process_tgid(message):
    q = message.text.strip().replace("@", "")
    try:
        r = requests.get("https://t.me/" + q)
        if "tgme_page_title" in r.text:
            title = r.text.split('og:title" content="')[1].split('"')[0]; bot.reply_to(message, "Имя: " + title)
        else: bot.reply_to(message, "Не найден")
    except: bot.reply_to(message, "Ошибка")

def process_vkid(message):
    q = message.text.strip()
    try:
        r = requests.get("https://vk.com/" + q)
        if "vk.com" in r.url: bot.reply_to(message, "VK: https://vk.com/" + q)
        else: bot.reply_to(message, "Не найден")
    except: bot.reply_to(message, "Ошибка")

def process_currency(message):
    try:
        r = requests.get("https://www.cbr-xml-daily.ru/daily_json.js"); d = r.json(); usd = d['Valute']['USD']['Value']
        bot.reply_to(message, "USD: " + str(usd))
    except: bot.reply_to(message, "Ошибка")

def process_pass(message):
    try:
        l = int(message.text); p = ''.join(random.choices(string.ascii_letters + string.digits, k=l))
        bot.reply_to(message, "Пароль: " + p)
    except: bot.reply_to(message, "Введи число")

def process_calc(message):
    try: res = eval(message.text); bot.reply_to(message, "Результат: " + str(res))
    except: bot.reply_to(message, "Ошибка")

def process_weather(message):
    try: r = requests.get("https://wttr.in/" + message.text + "?format=3"); bot.reply_to(message, r.text)
    except: bot.reply_to(message, "Ошибка")

def process_base64(message):
    text = message.text.strip()
    try: res = base64.b64decode(text).decode(); bot.reply_to(message, "Декод: " + res)
    except: res = base64.b64encode(text.encode()).decode(); bot.reply_to(message, "Энкод: " + res)

def check_admin_pin(message):
    if message.text.strip() == ADMIN_PIN: bot.send_message(message.chat.id, "Админка:", reply_markup=get_admin_menu())
    else: bot.send_message(message.chat.id, "Неверный PIN")

def process_broadcast(message):
    conn = sqlite3.connect('bot_logs.db'); c = conn.cursor(); c.execute("SELECT user_id FROM users"); users = c.fetchall(); conn.close()
    cnt = 0
    for u in users:
        try: bot.send_message(u[0], message.text); cnt += 1
        except: pass
    bot.send_message(message.chat.id, "Отправлено: " + str(cnt))

# --- КОМАНДЫ ---
@bot.message_handler(commands=['myip'])
def cmd_myip(message):
    try: bot.reply_to(message, "Твой IP: " + requests.get("https://api.ipify.org?format=json").json()['ip'])
    except: bot.reply_to(message, "Ошибка")

@bot.message_handler(commands=['geoip'])
def cmd_geoip(message):
    try:
        ip = message.text.split()[1]
        d = requests.get("http://ip-api.com/json/" + ip).json()
        bot.reply_to(message, "Гео: " + d['country'] + ", " + d.get('city', '?'))
    except: bot.reply_to(message, "Ошибка. Формат: /geoip 8.8.8.8")

@bot.message_handler(commands=['ns'])
def cmd_ns(message):
    try:
        d = message.text.split()[1]
        res = "NS " + d + ":\n"
        for ans in dns.resolver.resolve(d, 'NS'): res += str(ans) + "\n"
        bot.reply_to(message, res)
    except: bot.reply_to(message, "Ошибка")

@bot.message_handler(commands=['sha256'])
def cmd_sha256(message):
    try: bot.reply_to(message, "SHA256: " + hashlib.sha256(message.text.split(maxsplit=1)[1].encode()).hexdigest())
    except: bot.reply_to(message, "Ошибка")

@bot.message_handler(commands=['password'])
def cmd_password(message):
    try:
        length = int(message.text.split()[1]) if len(message.text.split()) > 1 else 16
        chars = string.ascii_letters + string.digits + "!@#$%^&*"
        bot.reply_to(message, "Пароль: " + ''.join(random.choices(chars, k=length)))
    except: bot.reply_to(message, "Ошибка")

@bot.message_handler(commands=['weather'])
def cmd_weather(message):
    try:
        city = message.text.split(maxsplit=1)[1]
        r = requests.get("https://wttr.in/" + city + "?format=3")
        bot.reply_to(message, r.text)
    except: bot.reply_to(message, "Ошибка")

@bot.message_handler(commands=['currency'])
def cmd_currency(message):
    try:
        r = requests.get("https://www.cbr-xml-daily.ru/daily_json.js")
        d = r.json()
        usd = d['Valute']['USD']['Value']
        eur = d['Valute']['EUR']['Value']
        bot.reply_to(message, "USD: " + str(usd) + "\nEUR: " + str(eur))
    except: bot.reply_to(message, "Ошибка")

# --- ВЕБХУК ДЛЯ RENDER ---
@app.route('/' + TOKEN, methods=['POST'])
def getMessage():
    json_string = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return "!", 200

@app.route("/")
def webhook():
    bot.remove_webhook()
    bot.set_webhook(url=URL + '/' + TOKEN)
    return "Бот запущен!", 200

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5000)))
