import os
import json
import random
import asyncio
import telegram
from telegram import Bot
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

FILE = "meals.json"
ALLOWED_CHAT = int(os.getenv("CHAT_ID", "0"))


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


async def guard(update):
    # печатаем id и юзера для диагностики
    print(f"[GUARD] Chat ID: {update.effective_chat.id}, User: {update.effective_user.username}")
    return update.effective_chat.id == ALLOWED_CHAT


async def add(update, ctx):
    print(f"[ADD] from {update.effective_user.username} / {update.effective_chat.id}")
    if not await guard(update):
        print("[ADD] доступ запрещён")
        return

    text = " ".join(ctx.args)
    parts = [p.strip() for p in text.split("|")]

    name = parts[0] if parts[0] else None
    if not name:
        await update.message.reply_text("Нужно минимум название")
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

    await update.message.reply_text(f"Добавлено: {name}")
    print(f"[ADD] Добавлено: {meal}")


async def list_meals(update, ctx):
    print(f"[LIST] from {update.effective_user.username} / {update.effective_chat.id}")
    if not await guard(update):
        print("[LIST] доступ запрещён")
        return

    data = load()
    if not data:
        await update.message.reply_text("Список пуст")
        return

    line = ", ".join(f'{m["id"]} {m["name"]}' for m in data)
    await update.message.reply_text(line)
    print(f"[LIST] {line}")


async def random_meal(update, ctx):
    print(f"[RANDOM] from {update.effective_user.username} / {update.effective_chat.id}")
    if not await guard(update):
        print("[RANDOM] доступ запрещён")
        return

    data = load()

    cat = None
    ing = None

    for a in ctx.args:
        if a.startswith("cat="):
            cat = a[4:]
        if a.startswith("ing="):
            ing = a[4:]

    res = data

    if cat:
        res = [m for m in res if m["category"] == cat.lower()]

    if ing:
        need = [i.strip().lower() for i in ing.split(",")]
        res = [
            m for m in res
            if all(i in m["ingredients"] for i in need)
        ]

    if not res:
        await update.message.reply_text("Ничего не найдено")
        print("[RANDOM] ничего не найдено")
        return

    m = random.choice(res)

    txt = f"🍽 {m['name']}\nКатегория: {m['category']}"
    if m["ingredients"]:
        txt += "\nСостав: " + ", ".join(m["ingredients"])

    await update.message.reply_text(txt)
    print(f"[RANDOM] Отправлено: {txt}")


async def show_id(update, ctx):
    chat_id = update.effective_chat.id
    user = update.effective_user.username
    await update.message.reply_text(f"Chat ID: {chat_id}\nUser: {user}")
    print(f"[ID] {user} / {chat_id}")


def main():
    TOKEN = os.getenv("TOKEN")
    if not TOKEN:
        print("❌ TOKEN НЕ НАЙДЕН")
        return

    print("=== BOT STARTING ===")

    # удаляем старый webhook асинхронно
    import asyncio
    from telegram import Bot
    bot = Bot(token=TOKEN)
    try:
        asyncio.get_event_loop().run_until_complete(
            bot.delete_webhook(drop_pending_updates=True)
        )
        print("✅ Старая сессия удалена")
    except Exception as e:
        print("⚠ Не удалось удалить старую сессию:", e)

    # создаём файл meals.json если его нет
    if not os.path.exists(FILE):
        with open(FILE, "w", encoding="utf-8") as f:
            f.write("[]")

    # создаём приложение и регистрируем команды
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("add", add))
    app.add_handler(CommandHandler("list", list_meals))
    app.add_handler(CommandHandler("random", random_meal))
    app.add_handler(CommandHandler("id", show_id))

    # Блокирующий запуск polling — держит контейнер живым
    app.run_polling()


if __name__ == "__main__":
    main()
