import requests
import time
import os
import json
import random

TOKEN = "8151756013:AAGCtYlSTeDVgC1NR6xkBKjTA9DrewgY9Xg"
ADMIN_ID = 7817919248
API_URL = f"https://api.telegram.org/bot{TOKEN}/"

FILES_JSON = "files.json"

offset = 0

def load_files():
    if os.path.exists(FILES_JSON):
        with open(FILES_JSON, "r", encoding="utf-8") as f:
            return json.load(f)
    else:
        return {}

def save_files(files_dict):
    with open(FILES_JSON, "w", encoding="utf-8") as f:
        json.dump(files_dict, f, ensure_ascii=False, indent=2)

def get_updates(offset):
    r = requests.get(API_URL + "getUpdates", params={"offset": offset, "timeout": 100})
    return r.json()

def send_message(chat_id, text, reply_markup=None):
    data = {"chat_id": chat_id, "text": text}
    if reply_markup:
        data["reply_markup"] = json.dumps(reply_markup)
    r = requests.post(API_URL + "sendMessage", data=data)
    print(f"send_message: {r.status_code}")

def send_document_by_file_id(chat_id, file_id):
    url = API_URL + "sendDocument"
    data = {"chat_id": chat_id, "document": file_id}
    r = requests.post(url, data=data)
    print(f"send_document_by_file_id: {r.status_code}")

def get_file_info(file_id, retries=2):
    for attempt in range(retries):
        r = requests.get(API_URL + "getFile", params={"file_id": file_id})
        if r.status_code == 200:
            data = r.json()
            if "result" in data:
                return data["result"]
            else:
                print(f"getFile без result: {data}")
        else:
            print(f"getFile ошибка {r.status_code}: {r.text}")
        time.sleep(1)
    return None

def build_files_keyboard(files_dict):
    keyboard = {"inline_keyboard": []}
    for fname in files_dict:
        keyboard["inline_keyboard"].append([{"text": fname, "callback_data": f"sendfile:{fname}"}])
    return keyboard if files_dict else None

def answer_callback(callback_id, text):
    requests.post(API_URL + "answerCallbackQuery", data={"callback_query_id": callback_id, "text": text})

print("Бот запущен")

while True:
    try:
        updates = get_updates(offset)
        for update in updates.get("result", []):
            offset = update["update_id"] + 1

            if "callback_query" in update:
                cq = update["callback_query"]
                callback_id = cq["id"]
                data = cq["data"]
                chat_id = cq["message"]["chat"]["id"]
                user_id = cq["from"]["id"]

                if user_id == ADMIN_ID and data.startswith("sendfile:"):
                    filename = data.split("sendfile:")[1]
                    files = load_files()
                    if filename in files:
                        send_document_by_file_id(chat_id, files[filename])
                        answer_callback(callback_id, f"Отправляю файл {filename}")
                    else:
                        send_message(chat_id, "Файл не найден.")
                        answer_callback(callback_id, "Ошибка: файл не найден")
                else:
                    answer_callback(callback_id, "Команда не распознана или доступ запрещён.")
                continue

            if "message" not in update:
                continue

            msg = update["message"]
            chat_id = msg["chat"]["id"]
            user_id = msg["from"]["id"]
            text = msg.get("text", "")

            if text == "/start":
                if user_id == ADMIN_ID:
                    keyboard = {
                        "inline_keyboard": [
                            [{"text": "Показать сохранённые файлы", "callback_data": "show_files"}]
                        ]
                    }
                    send_message(chat_id, "Привет, админ! Отправь .apk файл или нажми кнопку.", reply_markup=keyboard)
                else:
                    keyboard = {
                        "inline_keyboard": [
                            [{"text": "Получить файл за фото", "callback_data": "get_cheat"}]
                        ]
                    }
                    send_message(chat_id, "Привет! Отправь фото, чтобы получить файл.", reply_markup=keyboard)

            elif text == "/files" and user_id == ADMIN_ID:
                files = load_files()
                keyboard = build_files_keyboard(files)
                if keyboard:
                    send_message(chat_id, "Список файлов:", reply_markup=keyboard)
                else:
                    send_message(chat_id, "Файлов пока нет.")

            elif "document" in msg and user_id == ADMIN_ID:
                doc = msg["document"]
                filename = doc["file_name"]
                file_id = doc["file_id"]

                if not filename.endswith(".apk"):
                    send_message(chat_id, "Можно загружать только .apk файлы.")
                    continue

                file_info = get_file_info(file_id)
                if not file_info:
                    send_message(chat_id, "Не удалось получить информацию о файле.")
                    continue

                file_size = file_info.get("file_size", 0)
                max_size = 130 * 1024 * 1024

                if file_size > max_size:
                    send_message(chat_id, f"Файл слишком большой ({file_size/(1024*1024):.2f} МБ). Максимум {max_size/(1024*1024)} МБ.")
                    continue

                files = load_files()
                files[filename] = file_id
                save_files(files)
                send_message(chat_id, f"Файл {filename} сохранён. Размер {file_size/(1024*1024):.2f} МБ.")

            elif "photo" in msg:
                if user_id != ADMIN_ID:
                    files = load_files()
                    if not files:
                        send_message(chat_id, "Пока нет доступных файлов.")
                    else:
                        filename = random.choice(list(files.keys()))
                        file_id = files[filename]
                        send_document_by_file_id(chat_id, file_id)
                else:
                    send_message(chat_id, "Администратору эта функция не нужна.")
    except Exception as e:
        print(f"Ошибка в основном цикле: {e}")
        time.sleep(5)
