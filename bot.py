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

# --- КОМАНДЫ ---
@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "🕵️ OSINT Бот готов к работе!\nВведи /ip 8.8.8.8", reply_markup=get_main_menu())

@bot.message_handler(commands=['ip'])
def cmd_ip(message):
    try:
        ip = message.text.split()[1]
        d = requests.get("http://ip-api.com/json/" + ip).json()
        bot.reply_to(message, "IP: " + d['query'] + "\nСтрана: " + d['country'])
    except:
        bot.reply_to(message, "Ошибка. Формат: /ip 8.8.8.8")

@bot.message_handler(commands=['myip'])
def cmd_myip(message):
    try:
        bot.reply_to(message, "Твой IP: " + requests.get("https://api.ipify.org?format=json").json()['ip'])
    except:
        bot.reply_to(message, "Ошибка")

@bot.message_handler(commands=['password'])
def cmd_password(message):
    try:
        length = int(message.text.split()[1]) if len(message.text.split()) > 1 else 16
        chars = string.ascii_letters + string.digits + "!@#$%^&*"
        bot.reply_to(message, "Пароль: " + ''.join(random.choices(chars, k=length)))
    except:
        bot.reply_to(message, "Ошибка")

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
    bot.set_webhook(url='https://osint-panel-6r67.onrender.com/' + TOKEN)
    return "Бот запущен!", 200

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5000)))
