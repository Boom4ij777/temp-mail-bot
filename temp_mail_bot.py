
import asyncio
import random
import string
import aiohttp
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message
import os

TOKEN = os.getenv("BOT_TOKEN")  # Получай токен через переменную окружения
bot = Bot(token=TOKEN)
dp = Dispatcher()

API_DOMAIN = "1secmail.com"
API_BASE = f"https://{API_DOMAIN}/api/v1/"

# Генерация случайного email
def generate_email():
    login = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
    domain = random.choice(["1secmail.com", "1secmail.net", "1secmail.org"])
    return login, domain

user_emails = {}  # Временное хранилище email'ов пользователей

@dp.message(Command("start"))
async def cmd_start(message: Message):
    login, domain = generate_email()
    user_emails[message.from_user.id] = (login, domain)
    email = f"{login}@{domain}"
    await message.answer(f"Твоя временная почта:\n**{email}**", parse_mode="Markdown")
    await message.answer("Напиши /inbox чтобы проверить входящие.")

@dp.message(Command("inbox"))
async def cmd_inbox(message: Message):
    user_data = user_emails.get(message.from_user.id)
    if not user_data:
        await message.answer("Сначала используй /start")
        return

    login, domain = user_data
    params = {
        "action": "getMessages",
        "login": login,
        "domain": domain
    }
    async with aiohttp.ClientSession() as session:
        async with session.get(API_BASE, params=params) as resp:
            data = await resp.json()
            if not data:
                await message.answer("Писем нет.")
                return

            response = "Входящие письма:\n"
            for letter in data:
                response += f"\nID: {letter['id']}, От: {letter['from']}, Тема: {letter['subject']}"
            response += "\n\nЧтобы прочитать, напиши /read ID_письма"
            await message.answer(response)

@dp.message(Command("read"))
async def cmd_read(message: Message):
    args = message.text.strip().split()
    if len(args) != 2 or not args[1].isdigit():
        await message.answer("Формат: /read ID_письма")
        return

    mail_id = args[1]
    user_data = user_emails.get(message.from_user.id)
    if not user_data:
        await message.answer("Сначала используй /start")
        return

    login, domain = user_data
    params = {
        "action": "readMessage",
        "login": login,
        "domain": domain,
        "id": mail_id
    }
    async with aiohttp.ClientSession() as session:
        async with session.get(API_BASE, params=params) as resp:
            data = await resp.json()
            await message.answer(f"**От:** {data['from']}\n**Тема:** {data['subject']}\n\n{data['textBody']}", parse_mode="Markdown")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
