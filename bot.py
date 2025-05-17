import telebot
import requests
import json

TOKEN = "YOUR_BOT_TOKEN"
ADMIN_ID = 7817919248  # Твой Telegram ID

bot = telebot.TeleBot(TOKEN)

user_data = {}

def create_email():
    domain = requests.get("https://api.mail.tm/domains").json()["hydra:member"][0]["domain"]
    username = requests.get("https://api.mail.tm/accounts").json()
    return f"{username['address']}@{domain}"

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
        bot.send_message(message.chat.id, "Твои почты:
" + "
".join(emails))

@bot.message_handler(commands=['admin_users'])
def admin_users(message):
    if message.from_user.id != ADMIN_ID:
        bot.send_message(message.chat.id, "❌ У вас нет доступа")
        return

    if not user_data:
        bot.send_message(message.chat.id, "Пока никто не использует бота.")
        return

    msg = "Пользователи бота:
"
    for uid, info in user_data.items():
        uname = f"@{info['username']}" if info["username"] else "без username"
        emails = "\n  • " + "\n  • ".join(info["emails"]) if info["emails"] else "  (нет почт)"
        msg += f"- {uname} (ID: {uid}){emails}\n"
    bot.send_message(message.chat.id, msg)

bot.polling()