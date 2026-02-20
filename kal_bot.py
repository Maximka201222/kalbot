import asyncio
import json
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart, Command

TOKEN = "8380218047:AAGB6Wo2-v0mqUFpmQv4Ol00l_Mse5NwT2w"

bot = Bot(token=TOKEN)
dp = Dispatcher()

DATA_FILE = "balances.json"

ADMINS = ["pilotofsu25", "olenalipun"]

MAX_AMOUNT = 1_000_000_000_000_000_000_000_000_000_000_000_000_000_000_000
MAX_BALANCE = 1_000_000_000_000_000_000_000_000_000_000_000_000_000_000_000


# =====================
# FILE FUNCTIONS
# =====================

def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_data():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(users_balance, f, indent=4, ensure_ascii=False)


users_balance = load_data()


# =====================
# UTILS
# =====================

def get_user_id(user: types.User) -> str:
    return str(user.id)


def get_username(user: types.User) -> str:
    return user.username.lower() if user.username else None


def is_admin(username: str) -> bool:
    return username in ADMINS


def find_user_by_username(username: str):
    for uid, data in users_balance.items():
        if data.get("username") == username:
            return uid
    return None


# =====================
# START
# =====================

@dp.message(CommandStart())
async def start_handler(message: types.Message):

    user_id = get_user_id(message.from_user)
    username = get_username(message.from_user)

    if user_id not in users_balance:

        users_balance[user_id] = {
            "balance": 0,
            "username": username
        }

        save_data()

        await message.answer("✅ Ты зарегистрирован в системе KAL")

    else:
        await message.answer("Ты уже зарегистрирован")

    if username:
        users_balance[user_id]["username"] = username
        save_data()


# =====================
# BALANCE
# =====================

@dp.message(Command("balance"))
async def balance_handler(message: types.Message):

    user_id = get_user_id(message.from_user)

    if user_id not in users_balance:
        await message.answer("Сначала используй /start")
        return

    balance = users_balance[user_id]["balance"]

    await message.answer(f"💰 Баланс: {balance} KAL")


# =====================
# SEND WITH MESSAGE
# =====================

@dp.message(Command("send"))
async def send_handler(message: types.Message):

    sender_id = get_user_id(message.from_user)

    if sender_id not in users_balance:
        await message.answer("Сначала используй /start")
        return

    args = message.text.split(maxsplit=3)

    if len(args) < 3:
        await message.answer(
            "Использование:\n"
            "/send @username amount сообщение\n\n"
            "Пример:\n"
            "/send @ivan 100 Спасибо"
        )
        return

    target_username = args[1].replace("@", "").lower()

    try:
        amount = int(args[2])
    except:
        await message.answer("Количество должно быть числом")
        return

    if amount <= 0 or amount > MAX_AMOUNT:
        await message.answer("Некорректное количество")
        return

    if users_balance[sender_id]["balance"] < amount:
        await message.answer("Недостаточно средств")
        return

    target_id = find_user_by_username(target_username)

    if target_id is None:
        await message.answer("Пользователь не найден")
        return

    # сообщение (необязательно)
    extra_message = ""

    if len(args) >= 4:
        extra_message = args[3]

    # перевод
    users_balance[sender_id]["balance"] -= amount
    users_balance[target_id]["balance"] += amount

    save_data()

    await message.answer(
        f"✅ Отправлено {amount} KAL @{target_username}"
    )

    # уведомление получателю
    try:

        text = (
            f"💰 Тебе пришло {amount} KAL\n"
            f"👤 От: @{get_username(message.from_user)}\n"
            f"💳 Баланс: {users_balance[target_id]['balance']} KAL"
        )

        if extra_message:
            text += f"\n\n💬 Сообщение:\n{extra_message}"

        await bot.send_message(int(target_id), text)

    except:
        pass


# =====================
# ADD (ADMIN)
# =====================

@dp.message(Command("add"))
async def add_handler(message: types.Message):

    admin_username = get_username(message.from_user)

    if not is_admin(admin_username):
        await message.answer("Нет прав")
        return

    args = message.text.split()

    if len(args) != 3:
        await message.answer("/add @username amount")
        return

    target_username = args[1].replace("@", "").lower()

    try:
        amount = int(args[2])
    except:
        await message.answer("Ошибка числа")
        return

    if amount <= 0 or amount > MAX_AMOUNT:
        await message.answer("Некорректное количество")
        return

    target_id = find_user_by_username(target_username)

    if target_id is None:
        await message.answer("Пользователь не найден")
        return

    new_balance = users_balance[target_id]["balance"] + amount

    if new_balance > MAX_BALANCE:
        await message.answer("Превышен лимит баланса")
        return

    users_balance[target_id]["balance"] = new_balance

    save_data()

    await message.answer(f"✅ Начислено {amount} KAL @{target_username}")

    try:
        await bot.send_message(
            int(target_id),
            f"💰 Тебе начислено {amount} KAL\n"
            f"👤 Администратор: @{admin_username}\n"
            f"💳 Баланс: {new_balance} KAL"
        )
    except:
        pass


# =====================
# REMOVE (ADMIN)
# =====================

@dp.message(Command("remove"))
async def remove_handler(message: types.Message):

    admin_username = get_username(message.from_user)

    if not is_admin(admin_username):
        await message.answer("Нет прав")
        return

    args = message.text.split()

    if len(args) != 3:
        await message.answer("/remove @username amount")
        return

    target_username = args[1].replace("@", "").lower()

    try:
        amount = int(args[2])
    except:
        await message.answer("Ошибка числа")
        return

    if amount <= 0 or amount > MAX_AMOUNT:
        await message.answer("Некорректное количество")
        return

    target_id = find_user_by_username(target_username)

    if target_id is None:
        await message.answer("Пользователь не найден")
        return

    if users_balance[target_id]["balance"] < amount:
        await message.answer("Недостаточно средств у пользователя")
        return

    users_balance[target_id]["balance"] -= amount

    save_data()

    await message.answer(f"❌ Забрано {amount} KAL у @{target_username}")

    try:
        await bot.send_message(
            int(target_id),
            f"❌ У тебя забрали {amount} KAL\n"
            f"👤 Администратор: @{admin_username}\n"
            f"💳 Баланс: {users_balance[target_id]['balance']} KAL"
        )
    except:
        pass


# =====================
# STATS (ADMIN)
# =====================

@dp.message(Command("stats"))
async def stats_handler(message: types.Message):

    username = get_username(message.from_user)

    if not is_admin(username):
        await message.answer("Нет прав")
        return

    args = message.text.split()

    total = sum(user["balance"] for user in users_balance.values())

    if len(args) == 2 and args[1].lower() == "общая":

        await message.answer(
            f"💰 Всего в обороте: {total} KAL"
        )

        return

    text = "📊 Статистика:\n\n"

    for data in users_balance.values():

        uname = data.get("username", "unknown")
        bal = data.get("balance", 0)

        text += f"@{uname} — {bal} KAL\n"

    text += f"\n💰 Всего: {total} KAL"

    await message.answer(text)


# =====================
# MAIN
# =====================

async def main():

    print("Бот запущен")

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())