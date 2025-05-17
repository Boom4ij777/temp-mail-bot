import os
import telebot
from telebot import types
import requests
import random
import string

TOKEN = os.getenv("TOKEN")
bot = telebot.TeleBot(TOKEN)
user_data = {}

def generate_login(length=10):
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))

@bot.message_handler(commands=["start"])
def start(message):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("Создать почту", callback_data="create"))
    markup.add(types.InlineKeyboardButton("Мои почты", callback_data="list"))
    bot.send_message(message.chat.id, "Добро пожаловать! Выберите действие:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    chat_id = call.message.chat.id

    if call.data == "create":
        login = generate_login()
        domain = "esiix.com"
        email = f"{login}@{domain}"
        user_data.setdefault(chat_id, []).append((login, domain))
        bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id,
                              text=f"Новая почта создана:\n`{email}`", parse_mode="Markdown")
    elif call.data == "list":
        mails = user_data.get(chat_id, [])
        if not mails:
            return bot.answer_callback_query(call.id, "У вас нет сохранённых почт.")
        markup = types.InlineKeyboardMarkup()
        for i, (login, domain) in enumerate(mails):
            markup.add(types.InlineKeyboardButton(f"{i+1}. {login}@{domain}", callback_data=f"mail_{i}"))
        markup.add(types.InlineKeyboardButton("Назад", callback_data="back"))
        bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id,
                              text="Ваши почты:", reply_markup=markup)
    elif call.data.startswith("mail_"):
        index = int(call.data.split("_")[1])
        try:
            login, domain = user_data[chat_id][index]
        except IndexError:
            return bot.answer_callback_query(call.id, "Почта не найдена.")
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("Проверить", callback_data=f"check_{index}"))
        markup.add(types.InlineKeyboardButton("Удалить", callback_data=f"delete_{index}"))
        markup.add(types.InlineKeyboardButton("Назад", callback_data="list"))
        bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id,
                              text=f"`{login}@{domain}`", parse_mode="Markdown", reply_markup=markup)
    elif call.data.startswith("check_"):
        index = int(call.data.split("_")[1])
        login, domain = user_data[chat_id][index]
        url = f"https://www.1secmail.com/api/v1/?action=getMessages&login={login}&domain={domain}"
        try:
            msgs = requests.get(url).json()
            if not msgs:
                return bot.answer_callback_query(call.id, "Писем пока нет.")
            for msg in msgs[:1]:
                msg_id = msg["id"]
                content_url = f"https://www.1secmail.com/api/v1/?action=readMessage&login={login}&domain={domain}&id={msg_id}"
                content = requests.get(content_url).json()
                body = content.get("textBody", "Нет текста")
                bot.send_message(chat_id, f"Тема: {msg['subject']}\nОт: {msg['from']}\n\n{body}")
        except Exception as e:
            bot.send_message(chat_id, f"Ошибка при проверке: {e}")
    elif call.data.startswith("delete_"):
        index = int(call.data.split("_")[1])
        try:
            user_data[chat_id].pop(index)
            bot.answer_callback_query(call.id, "Почта удалена.")
        except IndexError:
            bot.answer_callback_query(call.id, "Ошибка удаления.")
        bot.edit_message_reply_markup(chat_id=chat_id, message_id=call.message.message_id, reply_markup=None)
    elif call.data == "back":
        start(call.message)

print("Бот запущен")
bot.polling()