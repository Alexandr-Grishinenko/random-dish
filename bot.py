import os
import json
import random
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message

logging.basicConfig(level=logging.INFO)

TOKEN = os.getenv("TOKEN")
ALLOWED_CHAT = int(os.getenv("CHAT_ID", "0"))
FILE = "meals.json"

bot = Bot(token=TOKEN)
dp = Dispatcher()


# --------------------- Работа с файлами ---------------------
def load():
    try:
        with open(FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return []


def save(data):
    with open(FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def next_id(data):
    return max([m["id"] for m in data], default=0) + 1


def is_allowed(chat_id):
    return chat_id == ALLOWED_CHAT


# --------------------- Команды ---------------------
@dp.message(Command(commands=["add"]))
async def add(msg: Message):
    print(f"ALLOWED_CHAT: {ALLOWED_CHAT}")
    print(f"msg.chat.id: {msg.chat.id}")
    if not is_allowed(msg.chat.id):
        logging.info(f"[ADD] доступ запрещён: {msg.from_user.username}")
        return

    # аргументы после команды через split
    args = msg.text.split()[1:]
    text = " ".join(args)
    parts = [p.strip() for p in text.split("|")]

    name = parts[0] if parts[0] else None
    if not name:
        await msg.answer("Нужно минимум название")
        return

    category = parts[1] if len(parts) > 1 and parts[1] else "Без категории"

    if len(parts) > 2 and parts[2]:
        ing = [i.strip().lower() for i in parts[2].split(",")]
    else:
        ing = []

    data = load()
    meal = {
        "id": next_id(data),
        "name": name,
        "category": category.lower(),
        "ingredients": ing
    }
    data.append(meal)
    save(data)

    await msg.answer(f"Добавлено: {name}")
    logging.info(f"[ADD] Добавлено: {meal}")


@dp.message(Command(commands=["list"]))
async def list_meals(msg: Message):
    if not is_allowed(msg.chat.id):
        logging.info(f"[LIST] доступ запрещён: {msg.from_user.username}")
        return

    data = load()
    if not data:
        await msg.answer("Список пуст")
        return

    line = ", ".join(f'{m["id"]} {m["name"]}' for m in data)
    await msg.answer(line)
    logging.info(f"[LIST] {line}")


@dp.message(Command(commands=["random"]))
async def random_meal(msg: Message):
    if not is_allowed(msg.chat.id):
        logging.info(f"[RANDOM] доступ запрещён: {msg.from_user.username}")
        return

    data = load()

    # аргументы через split
    args = msg.text.split()[1:]
    cat = None
    ing = None
    for a in args:
        if a.startswith("cat="):
            cat = a[4:]
        if a.startswith("ing="):
            ing = a[4:]

    res = data
    if cat:
        res = [m for m in res if m["category"] == cat.lower()]
    if ing:
        need = [i.strip().lower() for i in ing.split(",")]
        res = [m for m in res if all(i in m["ingredients"] for i in need)]

    if not res:
        await msg.answer("Ничего не найдено")
        logging.info("[RANDOM] ничего не найдено")
        return

    m = random.choice(res)
    txt = f"🍽 {m['name']}\nКатегория: {m['category']}"
    if m["ingredients"]:
        txt += "\nСостав: " + ", ".join(m["ingredients"])

    await msg.answer(txt)
    logging.info(f"[RANDOM] Отправлено: {txt}")


@dp.message(Command(commands=["id"]))
async def show_id(msg: Message):
    chat_id = msg.chat.id
    user = msg.from_user.username
    await msg.answer(f"Chat ID: {chat_id}\nUser: {user}")
    logging.info(f"[ID] {user} / {chat_id}")


# --------------------- Запуск ---------------------
async def main():
    if not os.path.exists(FILE):
        with open(FILE, "w", encoding="utf-8") as f:
            f.write("[]")

    logging.info("=== BOT STARTING ===")
    # удаляем старый webhook, чтобы не было конфликтов
    await bot.delete_webhook(drop_pending_updates=True)
    logging.info("✅ Старая сессия Telegram очищена")
    await dp.start_polling(bot)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
