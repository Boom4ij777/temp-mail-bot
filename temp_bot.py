import os
import telebot
import requests
import random
import string

TOKEN = os.getenv('TOKEN')
bot = telebot.TeleBot(TOKEN)

user_mails = {}

def generate_login(length=10):
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "Привет! Команды:\n/mail — создать почту\n/list — список твоих почт\n/check [номер] — проверить почту")

@bot.message_handler(commands=['mail'])
def mail(message):
    login = generate_login()
    domain = "esiix.com"
    email = f"{login}@{domain}"
    user_mails.setdefault(message.chat.id, []).append((login, domain))
    bot.send_message(message.chat.id, f"Новая почта:\n`{email}`", parse_mode="Markdown")

@bot.message_handler(commands=['list'])
def list_mails(message):
    mails = user_mails.get(message.chat.id, [])
    if not mails:
        bot.send_message(message.chat.id, "У тебя нет сохранённых почт.")
        return
    text = "Твои почты:\n"
    for i, (login, domain) in enumerate(mails, 1):
        text += f"{i}. `{login}@{domain}`\n"
    text += "\nЧтобы проверить, введи /check 1"
    bot.send_message(message.chat.id, text, parse_mode="Markdown")

@bot.message_handler(commands=['check'])
def check_mail(message):
    try:
        index = int(message.text.split()[1]) - 1
    except:
        bot.send_message(message.chat.id, "Неверный формат. Пример: /check 1")
        return

    mails = user_mails.get(message.chat.id, [])
    if index < 0 or index >= len(mails):
        bot.send_message(message.chat.id, "Неверный номер почты.")
        return

    login, domain = mails[index]
    url = f"https://www.1secmail.com/api/v1/?action=getMessages&login={login}&domain={domain}"
    try:
        res = requests.get(url)
        if res.status_code != 200 or not res.text.strip():
            bot.send_message(message.chat.id, "Сервер не ответил или вернул пустой результат.")
            return
        msgs = res.json()
        if not msgs:
            bot.send_message(message.chat.id, "Писем нет.")
            return
        for msg in msgs:
            msg_id = msg['id']
            from_email = msg['from']
            subject = msg['subject']
            content_url = f"https://www.1secmail.com/api/v1/?action=readMessage&login={login}&domain={domain}&id={msg_id}"
            content = requests.get(content_url).json()
            body = content.get("textBody", "[пусто]")
            bot.send_message(message.chat.id, f"От: {from_email}\nТема: {subject}\n---\n{body}")
    except Exception as e:
        bot.send_message(message.chat.id, f"Ошибка при проверке: {e}")

print("Бот запущен")
bot.polling()
