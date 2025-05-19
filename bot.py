
import os
import zipfile
import itertools
import string
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, ContextTypes, filters

TOKEN = os.getenv("BOT_TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Пришли мне ZIP-файл, и я попробую подобрать к нему пароль.")

def generate_passwords(max_length=4):
    chars = string.ascii_lowercase + string.digits
    for length in range(1, max_length + 1):
        for pwd_tuple in itertools.product(chars, repeat=length):
            yield ''.join(pwd_tuple)

async def handle_zip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    file = update.message.document
    if not file.file_name.endswith('.zip'):
        await update.message.reply_text("Отправь именно ZIP-файл.")
        return

    await update.message.reply_text("Начинаю подбор пароля...")

    os.makedirs("temp", exist_ok=True)
    file_path = f"temp/{file.file_name}"
    zip_file = await file.get_file()
    await zip_file.download_to_drive(file_path)

    try:
        with zipfile.ZipFile(file_path) as zf:
            for pwd in generate_passwords(4):
                try:
                    zf.extractall("temp/unzipped", pwd=pwd.encode())
                    await update.message.reply_text(f"Пароль найден: `{pwd}`", parse_mode="Markdown")
                    return
                except:
                    continue
            await update.message.reply_text("Пароль не найден (до 4 символов, a-z, 0-9).")
    except zipfile.BadZipFile:
        await update.message.reply_text("Файл повреждён или не ZIP.")
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)

async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Я тебя не понял. Пришли ZIP-файл.")

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.Document.ALL, handle_zip))
app.add_handler(MessageHandler(filters.COMMAND, unknown))

if __name__ == "__main__":
    app.run_polling()
