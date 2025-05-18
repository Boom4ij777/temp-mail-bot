import telebot
from telebot import types
import requests

TOKEN = "ВСТАВЬ_СЮДА_СВОЙ_ТОКЕН"
ADMIN_ID = 7817919248

bot = telebot.TeleBot(TOKEN)
user_data = {}

MAIL_TM_BASE = "https://api.mail.tm"


def register_mailbox():
    domain_data = requests.get(f"{MAIL_TM_BASE}/domains").json()
    domain = domain_data["hydra:member"][0]["domain"]

    from random import randint
    username = f"user{randint(10000,99999)}"
    email = f"{username}@{domain}"
    password = "P@ssw0rd123"

    acc = requests.post(f"{MAIL_TM_BASE}/accounts", json={
        "address": email,
        "password": password
    })

    if acc.status_code != 201:
        return None

    token_res = requests.post(f"{MAIL_TM_BASE}/token", json={
        "address": email,
        "password": password
    })

    if token_res.status_code != 200:
        return None

    token = token_res.json()["token"]
    return {
        "email": email,
        "password": password,
        "token": token
    }


@bot.message_handler(commands=["start"])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("Создать почту", "Мои почты")
    if message.from_user.id == ADMIN_ID:
        markup.row("Пользователи")
    bot.send_message(message.chat.id, "Привет! Выбери действие:", reply_markup=markup)


@bot.message_handler(func=lambda msg: msg.text == "Создать почту")
def handle_create_email(message):
    uid = message.from_user.id
    mailbox = register_mailbox()

    if not mailbox:
        bot.send_message(message.chat.id, "Ошибка при создании почты. Попробуй позже.")
        return

    user_data.setdefault(uid, {"username": message.from_user.username, "mails": []})
    user_data[uid]["mails"].append(mailbox)
    bot.send_message(message.chat.id, f"Создана почта: {mailbox['email']}")


@bot.message_handler(func=lambda msg: msg.text == "Мои почты")
def handle_my_emails(message):
    uid = message.from_user.id
    mails = user_data.get(uid, {}).get("mails", [])
    if not mails:
        bot.send_message(message.chat.id, "У тебя нет временных почт.")
    else:
        result = "\n".join([f"{i+1}. {m['email']}" for i, m in enumerate(mails)])
        bot.send_message(message.chat.id, f"Твои почты:\n{result}")


@bot.message_handler(func=lambda msg: msg.text == "Пользователи")
def admin_users(message):
    if message.from_user.id != ADMIN_ID:
        bot.send_message(message.chat.id, "❌ У вас нет доступа")
        return

    if not user_data:
        bot.send_message(message.chat.id, "Пользователей пока нет.")
        return

    msg = "Пользователи:\n"
    for uid, info in user_data.items():
        uname = f"@{info['username']}" if info["username"] else "без username"
        mails = "\n  • " + "\n  • ".join([m['email'] for m in info['mails']]) if info["mails"] else "  (нет почт)"
        msg += f"- {uname} (ID: {uid}){mails}\n"
    bot.send_message(message.chat.id, msg)


bot.polling()