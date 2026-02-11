import os
import json
import random
from iogram import Bot, Dispatcher, types
from iogram.contrib.middlewares.logging import LoggingMiddleware
from iogram.types import ParseMode

TOKEN = os.getenv("TOKEN")
ALLOWED_CHAT = int(os.getenv("CHAT_ID", "0"))
FILE = "meals.json"

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)
dp.middleware.setup(LoggingMiddleware())

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
@dp.message("/add")
async def add(msg: types.Message, args: list[str]):
    print(f"[ADD] from {msg.from_user.username} / {msg.chat.id}")
    if not is_allowed(msg.chat.id):
        print("[ADD] доступ запрещён")
        return

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
    print(f"[ADD] Добавлено: {meal}")

@dp.message("/list")
async def list_meals(msg: types.Message):
    print(f"[LIST] from {msg.from_user.username} / {msg.chat.id}")
    if not is_allowed(msg.chat.id):
        print("[LIST] доступ запрещён")
        return

    data = load()
    if not data:
        await msg.answer("Список пуст")
        return

    line = ", ".join(f'{m["id"]} {m["name"]}' for m in data)
    await msg.answer(line)
    print(f"[LIST] {line}")

@dp.message("/random")
async def random_meal(msg: types.Message, args: list[str]):
    print(f"[RANDOM] from {msg.from_user.username} / {msg.chat.id}")
    if not is_allowed(msg.chat.id):
        print("[RANDOM] доступ запрещён")
        return

    data = load()
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
        print("[RANDOM] ничего не найдено")
        return

    m = random.choice(res)
    txt = f"🍽 {m['name']}\nКатегория: {m['category']}"
    if m["ingredients"]:
        txt += "\nСостав: " + ", ".join(m["ingredients"])

    await msg.answer(txt)
    print(f"[RANDOM] Отправлено: {txt}")

@dp.message("/id")
async def show_id(msg: types.Message):
    chat_id = msg.chat.id
    user = msg.from_user.username
    await msg.answer(f"Chat ID: {chat_id}\nUser: {user}")
    print(f"[ID] {user} / {chat_id}")

# --------------------- Запуск ---------------------
async def main():
    # создаём файл meals.json если его нет
    if not os.path.exists(FILE):
        with open(FILE, "w", encoding="utf-8") as f:
            f.write("[]")

    print("=== BOT STARTING ===")
    await bot.delete_webhook(drop_pending_updates=True)
    print("✅ Старая сессия Telegram очищена")
    await dp.start_polling()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
