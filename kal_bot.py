import asyncio
import json
import os
import random
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart, Command

TOKEN = "8380218047:AAGB6Wo2-v0mqUFpmQv4Ol00l_Mse5NwT2w"

bot = Bot(token=TOKEN)
dp = Dispatcher()

DATA_FILE = "balances.json"

ADMINS = ["pilotofsu25", "olenalipun"]

MAX_AMOUNT = 10**40
MAX_BALANCE = 10**40


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
        if uid == "roulette_bank":
            continue
        if data.get("username") == username:
            return uid
    return None


# =====================
# INIT ROULETTE BANK
# =====================

if "roulette_bank" not in users_balance:
    users_balance["roulette_bank"] = {"balance": 0}
    save_data()


# =====================
# START
# =====================

@dp.message(CommandStart())
async def start_handler(message: types.Message):
    user_id = get_user_id(message.from_user)
    username = get_username(message.from_user)

    if user_id not in users_balance:
        users_balance[user_id] = {"balance": 0, "username": username}
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

    extra_message = args[3] if len(args) >= 4 else ""

    users_balance[sender_id]["balance"] -= amount
    users_balance[target_id]["balance"] += amount
    save_data()

    await message.answer(f"✅ Отправлено {amount} KAL @{target_username}")

    try:
        text = f"💰 Тебе пришло {amount} KAL\n👤 От: @{get_username(message.from_user)}\n💳 Баланс: {users_balance[target_id]['balance']} KAL"
        if extra_message:
            text += f"\n\n💬 Сообщение:\n{extra_message}"
        await bot.send_message(int(target_id), text)
    except:
        pass


# =====================
# ADD / REMOVE (ADMIN)
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
        await bot.send_message(int(target_id), f"💰 Тебе начислено {amount} KAL\n👤 Администратор: @{admin_username}\n💳 Баланс: {new_balance} KAL")
    except:
        pass


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
        await bot.send_message(int(target_id), f"❌ У тебя забрали {amount} KAL\n👤 Администратор: @{admin_username}\n💳 Баланс: {users_balance[target_id]['balance']} KAL")
    except:
        pass


# =====================
# ROULETTE
# =====================

@dp.message(Command("roulette"))
async def roulette_handler(message: types.Message):
    user_id = get_user_id(message.from_user)

    if user_id not in users_balance:
        await message.answer("Сначала используй /start")
        return

    args = message.text.split()
    if len(args) != 2:
        await message.answer("Использование:\n/roulette amount")
        return

    try:
        amount = int(args[1])
    except:
        await message.answer("Ставка должна быть числом")
        return

    if amount <= 0 or amount > MAX_AMOUNT:
        await message.answer("Некорректная ставка")
        return

    user_balance = users_balance[user_id]["balance"]
    bank_balance = users_balance["roulette_bank"]["balance"]

    if amount > user_balance:
        await message.answer("Недостаточно средств")
        return

    max_bet = users_balance["roulette_bank"]["balance"] // 2  # 50% от банка

    if amount > max_bet:
        await message.answer(
            f"🏦 Максимальная ставка: {max_bet} KAL"
        )
        return

    spin = await message.answer("🎰 Крутится...")
    await asyncio.sleep(1)
    await spin.edit_text("🎰 Крутится..")
    await asyncio.sleep(1)
    await spin.edit_text("🎰 Крутится.")
    await asyncio.sleep(1)

    win_chance = 40
    roll = random.randint(1, 100)

    if roll <= win_chance:
        users_balance[user_id]["balance"] += amount
        users_balance["roulette_bank"]["balance"] -= amount
        result = f"🎉 ВЫИГРЫШ!\n+{amount} KAL\n\n💰 Баланс: {users_balance[user_id]['balance']} KAL"
    else:
        users_balance[user_id]["balance"] -= amount
        users_balance["roulette_bank"]["balance"] += amount
        result = f"💀 ПРОИГРЫШ\n-{amount} KAL\n\n💰 Баланс: {users_balance[user_id]['balance']} KAL"

    save_data()
    await spin.edit_text(result)


# =====================
# ROULETTE BANK ADMIN
# =====================

@dp.message(Command("radd"))
async def radd_handler(message: types.Message):
    admin_username = get_username(message.from_user)
    if not is_admin(admin_username):
        await message.answer("Нет прав")
        return

    args = message.text.split()
    if len(args) != 2:
        await message.answer("/radd amount")
        return

    try:
        amount = int(args[1])
    except:
        await message.answer("Ошибка числа")
        return

    if amount <= 0:
        await message.answer("Некорректная сумма")
        return

    users_balance["roulette_bank"]["balance"] += amount
    save_data()
    await message.answer(f"🏦 Банк пополнен на {amount} KAL\n💰 Сейчас в банке: {users_balance['roulette_bank']['balance']} KAL")


@dp.message(Command("rremove"))
async def rremove_handler(message: types.Message):
    admin_username = get_username(message.from_user)
    if not is_admin(admin_username):
        await message.answer("Нет прав")
        return

    args = message.text.split()
    if len(args) != 2:
        await message.answer("/rremove amount")
        return

    try:
        amount = int(args[1])
    except:
        await message.answer("Ошибка числа")
        return

    if amount <= 0:
        await message.answer("Некорректная сумма")
        return

    if users_balance["roulette_bank"]["balance"] < amount:
        await message.answer("Недостаточно средств в банке")
        return

    users_balance["roulette_bank"]["balance"] -= amount
    save_data()
    await message.answer(f"💸 Из банка забрано {amount} KAL\n💰 Сейчас в банке: {users_balance['roulette_bank']['balance']} KAL")


# =====================
# STATS (ADMIN)
# =====================

@dp.message(Command("stats"))
async def stats_handler(message: types.Message):
    username = get_username(message.from_user)
    if not is_admin(username):
        await message.answer("Нет прав")
        return

    total = sum(user["balance"] for uid, user in users_balance.items() if uid != "roulette_bank")
    text = "📊 Статистика:\n\n"

    for uid, data in users_balance.items():
        if uid == "roulette_bank":
            continue
        uname = data.get("username", "unknown")
        bal = data.get("balance", 0)
        text += f"@{uname} — {bal} KAL\n"

    text += f"\n🏦 Банк рулетки: {users_balance['roulette_bank']['balance']} KAL"
    text += f"\n💰 Всего у пользователей: {total} KAL"

    await message.answer(text)


# =====================
# MAIN
# =====================

async def main():
    print("Бот запущен")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
