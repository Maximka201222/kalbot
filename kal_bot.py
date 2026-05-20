import asyncio
import json
import os
import random

from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart, Command
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext

# =====================
# CONFIG
# =====================

TOKEN = "8668174547:AAFe89tyKePuJLMaOkb78vKK8xNLelLnm5U"

bot = Bot(token=TOKEN)
dp = Dispatcher()

DATA_FILE = "balances.json"

ADMINS = ["pilotofsu25", "olenalipun"]

MAX_AMOUNT = 10 ** 40
MAX_BALANCE = 10 ** 40

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


def get_username(user: types.User):
    return user.username.lower() if user.username else None


def is_admin(username: str):
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
    users_balance["roulette_bank"] = {
        "balance": 0
    }
    save_data()

# =====================
# FSM STATES
# =====================

class SendMoney(StatesGroup):
    user = State()
    amount = State()
    message = State()


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

        await message.answer("✅ Ты зарегистрирован")
    else:
        users_balance[user_id]["username"] = username
        save_data()

        await message.answer("👋 Ты уже зарегистрирован")


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
# SEND FSM
# =====================

@dp.message(Command("send"))
async def send_start(message: types.Message, state: FSMContext):
    sender_id = get_user_id(message.from_user)

    if sender_id not in users_balance:
        await message.answer("Сначала используй /start")
        return

    await state.set_state(SendMoney.user)

    await message.answer("👤 Кому отправить? Напиши @username")


# STEP 1 USER

@dp.message(SendMoney.user)
async def send_user(message: types.Message, state: FSMContext):
    username = message.text.replace("@", "").lower()

    target_id = find_user_by_username(username)

    if target_id is None:
        await message.answer("❌ Пользователь не найден")
        return

    await state.update_data(
        target_id=target_id,
        username=username
    )

    await state.set_state(SendMoney.amount)

    await message.answer("💰 Сколько отправить?")


# STEP 2 AMOUNT

@dp.message(SendMoney.amount)
async def send_amount(message: types.Message, state: FSMContext):
    try:
        amount = int(message.text)
    except:
        await message.answer("❌ Введи число")
        return

    if amount <= 0 or amount > MAX_AMOUNT:
        await message.answer("❌ Некорректная сумма")
        return

    await state.update_data(amount=amount)

    await state.set_state(SendMoney.message)

    await message.answer("💬 Напиши сообщение или /skip")


# STEP 3 MESSAGE

@dp.message(SendMoney.message)
async def send_finish(message: types.Message, state: FSMContext):
    data = await state.get_data()

    sender_id = get_user_id(message.from_user)

    target_id = data["target_id"]
    username = data["username"]
    amount = data["amount"]

    extra_message = message.text

    if extra_message == "/skip":
        extra_message = ""

    if users_balance[sender_id]["balance"] < amount:
        await message.answer("❌ Недостаточно средств")
        await state.clear()
        return

    # SEND MONEY

    users_balance[sender_id]["balance"] -= amount
    users_balance[target_id]["balance"] += amount

    save_data()

    await message.answer(
        f"✅ Отправлено {amount} KAL пользователю @{username}"
    )

    # SEND NOTIFICATION

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

    await state.clear()


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
        await message.answer("❌ Ставка должна быть числом")
        return

    if amount <= 0 or amount > MAX_AMOUNT:
        await message.answer("❌ Некорректная ставка")
        return

    if users_balance[user_id]["balance"] < amount:
        await message.answer("❌ Недостаточно средств")
        return

    max_bet = users_balance["roulette_bank"]["balance"] // 2

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

    roll = random.randint(1, 100)

    # 40% win chance

    if roll <= 40:
        users_balance[user_id]["balance"] += amount
        users_balance["roulette_bank"]["balance"] -= amount

        result = (
            f"🎉 ВЫИГРЫШ\n"
            f"+{amount} KAL\n\n"
            f"💰 Баланс: {users_balance[user_id]['balance']} KAL"
        )

    else:
        users_balance[user_id]["balance"] -= amount
        users_balance["roulette_bank"]["balance"] += amount

        result = (
            f"💀 ПРОИГРЫШ\n"
            f"-{amount} KAL\n\n"
            f"💰 Баланс: {users_balance[user_id]['balance']} KAL"
        )

    save_data()

    await spin.edit_text(result)


# =====================
# ADMIN ADD
# =====================

@dp.message(Command("add"))
async def add_handler(message: types.Message):
    username = get_username(message.from_user)

    if not is_admin(username):
        await message.answer("❌ Нет прав")
        return

    args = message.text.split()

    if len(args) != 3:
        await message.answer("/add @username amount")
        return

    target_username = args[1].replace("@", "").lower()

    try:
        amount = int(args[2])
    except:
        await message.answer("❌ Ошибка числа")
        return

    target_id = find_user_by_username(target_username)

    if target_id is None:
        await message.answer("❌ Пользователь не найден")
        return

    users_balance[target_id]["balance"] += amount

    save_data()

    await message.answer(
        f"✅ Начислено {amount} KAL @{target_username}"
    )


# =====================
# ADMIN REMOVE
# =====================

@dp.message(Command("remove"))
async def remove_handler(message: types.Message):
    username = get_username(message.from_user)

    if not is_admin(username):
        await message.answer("❌ Нет прав")
        return

    args = message.text.split()

    if len(args) != 3:
        await message.answer("/remove @username amount")
        return

    target_username = args[1].replace("@", "").lower()

    try:
        amount = int(args[2])
    except:
        await message.answer("❌ Ошибка числа")
        return

    target_id = find_user_by_username(target_username)

    if target_id is None:
        await message.answer("❌ Пользователь не найден")
        return

    if users_balance[target_id]["balance"] < amount:
        await message.answer("❌ Недостаточно средств")
        return

    users_balance[target_id]["balance"] -= amount

    save_data()

    await message.answer(
        f"❌ Забрано {amount} KAL у @{target_username}"
    )


# =====================
# ROULETTE BANK ADMIN
# =====================

@dp.message(Command("radd"))
async def radd_handler(message: types.Message):
    username = get_username(message.from_user)

    if not is_admin(username):
        await message.answer("❌ Нет прав")
        return

    args = message.text.split()

    if len(args) != 2:
        await message.answer("/radd amount")
        return

    try:
        amount = int(args[1])
    except:
        await message.answer("❌ Ошибка числа")
        return

    users_balance["roulette_bank"]["balance"] += amount

    save_data()

    await message.answer(
        f"🏦 Банк пополнен на {amount} KAL"
    )


@dp.message(Command("rremove"))
async def rremove_handler(message: types.Message):
    username = get_username(message.from_user)

    if not is_admin(username):
        await message.answer("❌ Нет прав")
        return

    args = message.text.split()

    if len(args) != 2:
        await message.answer("/rremove amount")
        return

    try:
        amount = int(args[1])
    except:
        await message.answer("❌ Ошибка числа")
        return

    if users_balance["roulette_bank"]["balance"] < amount:
        await message.answer("❌ Недостаточно средств")
        return

    users_balance["roulette_bank"]["balance"] -= amount

    save_data()

    await message.answer(
        f"💸 Из банка забрано {amount} KAL"
    )


# =====================
# STATS
# =====================

@dp.message(Command("stats"))
async def stats_handler(message: types.Message):
    username = get_username(message.from_user)

    if not is_admin(username):
        await message.answer("❌ Нет прав")
        return

    text = "📊 Статистика:\n\n"

    total = 0

    for uid, data in users_balance.items():

        if uid == "roulette_bank":
            continue

        uname = data.get("username", "unknown")
        bal = data.get("balance", 0)

        total += bal

        text += f"@{uname} — {bal} KAL\n"

    text += (
        f"\n🏦 Банк рулетки: {users_balance['roulette_bank']['balance']} KAL"
    )

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
