import json
import random
import os
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
    return update.effective_chat.id == ALLOWED_CHAT


async def add(update, ctx):
    if not await guard(update):
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


async def list_meals(update, ctx):
    if not await guard(update):
        return

    data = load()
    if not data:
        await update.message.reply_text("Список пуст")
        return

    line = ", ".join(f'{m["id"]} {m["name"]}' for m in data)
    await update.message.reply_text(line)


async def random_meal(update, ctx):
    if not await guard(update):
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
        return

    m = random.choice(res)

    txt = f"🍽 {m['name']}\nКатегория: {m['category']}"
    if m["ingredients"]:
        txt += "\nСостав: " + ", ".join(m["ingredients"])

    await update.message.reply_text(txt)


def main():
    TOKEN = os.getenv("TOKEN")

    if not TOKEN:
        print("❌ TOKEN НЕ НАЙДЕН")
        return

    print("=== BOT STARTING ===")

    bot = telegram.Bot(token=TOKEN)
    try:
        bot.delete_webhook(drop_pending_updates=True)
        print("✅ Старая сессия удалена")
    except Exception as e:
        print("⚠ Не удалось удалить старую сессию:", e)

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("add", add))
    app.add_handler(CommandHandler("list", list_meals))
    app.add_handler(CommandHandler("random", random_meal))

    app.run_polling()


if __name__ == "__main__":
    main()
