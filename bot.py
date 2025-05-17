import os
import telebot
import requests
import uuid

TOKEN = os.getenv("TOKEN")
ADMIN_ID = 7817919248  # Замени на свой Telegram ID

bot = telebot.TeleBot(TOKEN)

user_data = {}

def create_email():
    domain_data = requests.get("https://api.mail.tm/domains").json()
    domain = domain_data["hydra:member"][0]["domain"]

    username = str(uuid.uuid4())[:8]
    password = "Test123456!"

    payload = {
        "address": f"{username}@{domain}",
        "password": password
    }

    resp = requests.post("https://api.mail.tm/accounts", json=payload)
    if resp.status_code == 201:
        return payload["address"]
    else:
        return "Ошибка при создании почты"

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "Привет! Используй /new_email чтобы создать почту.")

@bot.message_handler(commands=['new_email'])
def new_email(message):
    email = create_email()
    uid = message.from_user.id
    user_data.setdefault(uid, {"username": message.from_user.username, "emails": []})
    user_data[uid]["emails"].append(email)
    bot.send_message(message.chat.id, f"Твоя почта: {email}")

@bot.message_handler(commands=['my_emails'])
def my_emails(message):
    uid = message.from_user.id
    emails = user_data.get(uid, {}).get("emails", [])
    if not emails:
        bot.send_message(message.chat.id, "У тебя нет почт.")
    else:
        bot.send_message(message.chat.id, "Твои почты:\n" + "\n".join(emails))

@bot.message_handler(commands=['admin_users'])
def admin_users(message):
    if message.from_user.id != ADMIN_ID:
        bot.send_message(message.chat.id, "❌ У вас нет доступа")
        return

    if not user_data:
        bot.send_message(message.chat.id, "Пока никто не использует бота.")
        return

    msg = "Пользователи бота:\n"
    for uid, info in user_data.items():
        uname = f"@{info['username']}" if info["username"] else "без username"
        emails = "\n  • " + "\n  • ".join(info["emails"]) if info["emails"] else "  (нет почт)"
        msg += f"- {uname} (ID: {uid}){emails}\n"
    bot.send_message(message.chat.id, msg)

bot.infinity_polling()
