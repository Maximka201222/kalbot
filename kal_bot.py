import asyncio
import json
import os
import random

from datetime import datetime

from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart, Command

# =====================
# CONFIG
# =====================

TOKEN = "8703749908:AAFRWSOeloG7HnTj_RuNefz-3Yj6qppUdlg"

bot = Bot(token=TOKEN)
dp = Dispatcher()
active_battle_users = set()

DATA_FILE = "balances.json"
LOGS_FILE = "transactions.txt"

ADMINS = ["pilotofsu25"]

MAX_AMOUNT = 10 ** 40

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
        json.dump(
            users_balance,
            f,
            indent=4,
            ensure_ascii=False
        )

# =====================
# LOGS
# =====================

def log_transaction(username, action, amount):

    time_now = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    with open(
        LOGS_FILE,
        "a",
        encoding="utf-8"
    ) as f:

        f.write(
            f"[{time_now}] "
            f"@{username} | "
            f"{action} | "
            f"{amount} KAL\n"
        )

users_balance = load_data()

# =====================
# UTILS
# =====================

def get_user_id(user: types.User) -> str:
    return str(user.id)


def get_username(user: types.User):

    if user.username:
        return user.username.lower()

    return None


def is_admin(username: str):
    return username in ADMINS


def find_user_by_username(username: str):

    for uid, data in users_balance.items():

        if data.get("username") == username:
            return uid

    return None

# =====================
# ACTIVE GAMES
# =====================

active_crash = {}

pending_battles = {}  # battle_id -> data

# =====================
# START
# =====================

@dp.message(CommandStart())
async def start_handler(message: types.Message):

    user_id = get_user_id(message.from_user)
    username = get_username(message.from_user)

    if user_id not in users_balance:

        users_balance[user_id] = {
            "balance": 100,
            "username": username,
            "daily_last": ""
        }

        save_data()

        await message.answer(
            "🎉 Добро пожаловать в KAL Casino Bot\n\n"

            "🎁 Стартовый бонус: 100 KAL\n\n"

            "🎮 Игры:\n"
            "• /roulette amount\n"
            "• /crash amount\n"
            "• /take\n\n"

            "💰 Экономика:\n"
            "• /balance\n"
            "• /daily\n\n"

            "🍀 Удачи!"
        )

    else:

        users_balance[user_id]["username"] = username

        if "daily_last" not in users_balance[user_id]:
            users_balance[user_id]["daily_last"] = ""

        save_data()

        await message.answer(
            "👋 С возвращением!"
        )

# =====================
# BALANCE
# =====================

@dp.message(Command("balance"))
async def balance_handler(message: types.Message):

    user_id = get_user_id(message.from_user)

    if user_id not in users_balance:
        await message.answer("Используй /start")
        return

    await message.answer(
        f"💰 Баланс: "
        f"{users_balance[user_id]['balance']} KAL"
    )

# =====================
# DAILY
# =====================

@dp.message(Command("daily"))
async def daily_handler(message: types.Message):

    user_id = get_user_id(message.from_user)

    if user_id not in users_balance:
        await message.answer("Используй /start")
        return

    today = datetime.now().strftime("%Y-%m-%d")

    if users_balance[user_id]["daily_last"] == today:
        await message.answer(
            "❌ Ты уже получал награду сегодня"
        )
        return

    reward = random.randint(10, 50)

    users_balance[user_id]["balance"] += reward
    users_balance[user_id]["daily_last"] = today

    log_transaction(
        users_balance[user_id]["username"],
        "daily",
        reward
    )

    save_data()

    await message.answer(
        f"🎁 Ты получил {reward} KAL\n\n"
        f"💰 Баланс: "
        f"{users_balance[user_id]['balance']} KAL"
    )

# =====================
# ROULETTE
# =====================

@dp.message(Command("roulette"))
async def roulette_handler(message: types.Message):

    user_id = get_user_id(message.from_user)

    args = message.text.split()

    if len(args) != 2:
        await message.answer("/roulette amount")
        return

    try:
        amount = int(args[1])

    except:
        await message.answer("❌ Ошибка числа")
        return

    if amount <= 0 or amount > MAX_AMOUNT:
        return

    if users_balance[user_id]["balance"] < amount:
        await message.answer("❌ Недостаточно средств")
        return

    # списываем ставку сразу
    users_balance[user_id]["balance"] -= amount

    spin = await message.answer("🎰 Крутится.")
    await asyncio.sleep(1)

    await spin.edit_text("🎰 Крутится..")
    await asyncio.sleep(1)

    await spin.edit_text("🎰 Крутится...")
    await asyncio.sleep(1)

    # шанс победы 35%
    if random.randint(1, 100) <= 35:

        multiplier = random.choice([
            1.5,
            2,
            3,
            5
        ])

        total_win = int(amount * multiplier)

        profit = total_win - amount

        users_balance[user_id]["balance"] += total_win

        text = (
            f"🎉 ПОБЕДА\n"
            f"🚀 Множитель: x{multiplier}\n"
            f"💰 Выигрыш: +{profit} KAL"
        )

        log_transaction(
            users_balance[user_id]["username"],
            "roulette win",
            profit
        )

    else:

        text = (
            f"💀 ПРОИГРЫШ\n"
            f"-{amount} KAL"
        )

        log_transaction(
            users_balance[user_id]["username"],
            "roulette lose",
            amount
        )

    save_data()

    await spin.edit_text(
        text +
        f"\n\n💰 Баланс: "
        f"{users_balance[user_id]['balance']} KAL"
    )


# =====================
# CRASH
# =====================

@dp.message(Command("crash"))
async def crash_handler(message: types.Message):

    user_id = get_user_id(message.from_user)

    # нельзя запускать несколько игр
    if user_id in active_crash:
        await message.answer(
            "❌ У тебя уже есть активный crash"
        )
        return

    args = message.text.split()

    if len(args) != 2:
        await message.answer("/crash amount")
        return

    try:
        amount = int(args[1])

    except:
        await message.answer("❌ Ошибка числа")
        return

    if amount <= 0 or amount > MAX_AMOUNT:
        return

    if users_balance[user_id]["balance"] < amount:
        await message.answer("❌ Недостаточно средств")
        return

    # списываем ставку
    users_balance[user_id]["balance"] -= amount

    multiplier = 0.0

    active_crash[user_id] = {
        "amount": amount,
        "multiplier": multiplier
    }

    save_data()

    msg = await message.answer(
        "🚀 Запуск ракеты..."
    )

    await asyncio.sleep(1)

    # 50 шагов
    for step in range(1, 51):

        await asyncio.sleep(0.7)

        # если игрок уже забрал
        if user_id not in active_crash:
            return

        multiplier = round(step * 0.1, 1)

        active_crash[user_id]["multiplier"] = multiplier

        # шанс краша растёт каждый ход
        # x0.1 = 2%
        # x5.0 = 100%
        lose_chance = min(
            5 + step,
            85
        )

        if random.randint(1, 100) <= lose_chance:

            del active_crash[user_id]

            log_transaction(
                users_balance[user_id]["username"],
                "crash lose",
                amount
            )

            save_data()

            await msg.edit_text(
                f"💥 CRASH НА X{multiplier}\n\n"
                f"💀 Проигрыш -{amount} KAL\n\n"
                f"💰 Баланс: "
                f"{users_balance[user_id]['balance']} KAL"
            )

            return

        await msg.edit_text(
            f"🚀 Ракета летит!\n\n"
            f"📈 Множитель: X{multiplier}\n\n"
            f"💸 Забрать: "
            f"{int(amount * multiplier)} KAL\n\n"
            f"👉 /take\n"
            f"👉 /take\n"
            f"👉 /take\n"
        )

    # если дошёл до x5
    if user_id in active_crash:

        del active_crash[user_id]

        win = int(amount * 5)

        users_balance[user_id]["balance"] += win

        log_transaction(
            users_balance[user_id]["username"],
            "crash max win",
            win
        )

        save_data()

        await msg.edit_text(
            f"🏆 МАКСИМУМ X5.0\n\n"
            f"💰 Выигрыш: {win} KAL\n\n"
            f"💰 Баланс: "
            f"{users_balance[user_id]['balance']} KAL"
        )
# =====================
# TAKE
# =====================

@dp.message(Command("take"))
async def take_handler(message: types.Message):

    user_id = get_user_id(message.from_user)

    if user_id not in active_crash:
        await message.answer(
            "❌ Нет активной игры"
        )
        return

    # сразу удаляем игру
    game = active_crash.pop(user_id)

    amount = game["amount"]
    multiplier = game["multiplier"]

    win = int(amount * multiplier)

    users_balance[user_id]["balance"] += win

    log_transaction(
        users_balance[user_id]["username"],
        "crash take",
        win
    )

    save_data()

    await message.answer(
        f"✅ Ты забрал {win} KAL\n"
        f"🚀 X{multiplier:.1f}\n\n"
        f"💰 Баланс: "
        f"{users_balance[user_id]['balance']} KAL"
    )
# =====================
# ADMIN ADD
# =====================

@dp.message(Command("add"))
async def add_handler(message: types.Message):

    username = get_username(
        message.from_user
    )

    if not is_admin(username):
        await message.answer("❌ Нет прав")
        return

    args = message.text.split()

    if len(args) != 3:
        await message.answer(
            "/add @username amount"
        )
        return

    target_username = (
        args[1]
        .replace("@", "")
        .lower()
    )

    try:
        amount = int(args[2])

    except:
        await message.answer(
            "❌ Ошибка числа"
        )
        return

    target_id = find_user_by_username(
        target_username
    )

    if target_id is None:
        await message.answer(
            "❌ Пользователь не найден"
        )
        return

    users_balance[target_id]["balance"] += amount

    log_transaction(
        target_username,
        "admin add",
        amount
    )

    save_data()

    await message.answer(
        f"✅ Выдано {amount} KAL"
    )

# =====================
# STATS
# =====================

@dp.message(Command("stats"))
async def stats_handler(message: types.Message):

    username = get_username(
        message.from_user
    )

    if not is_admin(username):
        await message.answer(
            "❌ Нет прав"
        )
        return

    text = "📊 Статистика\n\n"

    total = 0

    for uid, data in users_balance.items():

        uname = data.get(
            "username",
            "unknown"
        )

        bal = data.get(
            "balance",
            0
        )

        total += bal

        text += f"@{uname} — {bal} KAL\n"

    text += (
        f"\n💰 Всего: {total} KAL"
    )

    await message.answer(text)

# =====================
# LOGS VIEW
# =====================

@dp.message(Command("logs"))
async def logs_handler(message: types.Message):

    username = get_username(
        message.from_user
    )

    if not is_admin(username):
        await message.answer(
            "❌ Нет прав"
        )
        return

    if not os.path.exists(LOGS_FILE):

        await message.answer(
            "❌ Логи пусты"
        )
        return

    with open(
        LOGS_FILE,
        "r",
        encoding="utf-8"
    ) as f:

        logs = f.readlines()

    today = datetime.now().strftime(
        "%Y-%m-%d"
    )

    today_logs = []

    for log in logs:

        if today in log:
            today_logs.append(log)

    if not today_logs:

        await message.answer(
            "❌ Сегодня транзакций нет"
        )
        return

    text = "📜 Логи за сегодня:\n\n"

    for log in today_logs[-30:]:

        text += log

    await message.answer(text)

# =====================
# MAIN
# =====================

@dp.message(Command("top"))
async def top_handler(message: types.Message):

    if not users_balance:
        await message.answer("Пока нет игроков")
        return

    sorted_users = sorted(
        users_balance.items(),
        key=lambda x: x[1].get("balance", 0),
        reverse=True
    )

    text = "🏆 ТОП 10 ИГРОКОВ\n\n"

    for i, (uid, data) in enumerate(sorted_users[:10], start=1):

        uname = data.get("username", "unknown")
        bal = data.get("balance", 0)

        text += f"{i}. @{uname} — {bal} KAL\n"

    await message.answer(text)

@dp.message(Command("battle"))
async def battle_handler(message: types.Message):

    args = message.text.split()

    if len(args) != 3:
        await message.answer("/battle @user amount")
        return

    from_user_id = get_user_id(message.from_user)
    from_username = get_username(message.from_user)

    target_username = args[1].replace("@", "").lower()

    if from_user_id in active_battle_users:
        await message.answer(
            "❌ У тебя уже есть активный battle"
        )
        return

    # нельзя вызывать себя
    if target_username == from_username:
        await message.answer(
            "❌ Нельзя вызывать самого себя"
        )
        return

    try:
        amount = int(args[2])
    except:
        await message.answer("❌ Неверная сумма")
        return

    if amount <= 0 or amount > MAX_AMOUNT:
        return

    if from_user_id not in users_balance:
        await message.answer("Используй /start")
        return

    if users_balance[from_user_id]["balance"] < amount:
        await message.answer("❌ Недостаточно средств")
        return

    target_id = find_user_by_username(target_username)

    if not target_id:
        await message.answer("❌ Игрок не найден")
        return

    battle_id = str(random.randint(100000, 999999))
    active_battle_users.add(from_user_id)
    active_battle_users.add(target_id)

    pending_battles[battle_id] = {
        "from": from_user_id,
        "to": target_id,
        "amount": amount
    }

    await message.answer(
        f"⚔️ Вызов отправлен @{target_username}\n"
        f"💰 Ставка: {amount} KAL\n"
        f"🆔 Бой ID: {battle_id}\n\n"
        f"Ожидание ответа..."
    )

    try:
        await bot.send_message(
            chat_id=int(target_id),
            text=(
                f"⚔️ Тебя вызвал @{from_username}\n\n"
                f"💰 Ставка: {amount} KAL\n"
                f"🆔 ID боя: {battle_id}\n\n"
                f"👉 /accept_battle {battle_id}"
            )
        )
    except:
        pass

@dp.message(Command("accept_battle"))
async def accept_battle(message: types.Message):

    args = message.text.split()

    if len(args) != 2:
        await message.answer("/accept_battle battle_id")
        return

    battle_id = args[1]

    if battle_id not in pending_battles:
        await message.answer("❌ Бой не найден")
        return

    battle = pending_battles[battle_id]

    user_id = get_user_id(message.from_user)

    if user_id != battle["to"]:
        await message.answer("❌ Это не твой бой")
        return

    from_id = battle["from"]
    to_id = battle["to"]
    amount = battle["amount"]

    # проверка баланса второго игрока
    if users_balance[to_id]["balance"] < amount:
        await message.answer("❌ У тебя нет денег")
        return

    # проверка баланса первого игрока
    if users_balance[from_id]["balance"] < amount:
        active_battle_users.discard(from_id)
        active_battle_users.discard(to_id)

        del pending_battles[battle_id]

        await message.answer(
            "❌ У создателя боя больше нет денег"
        )
        return

    # списываем ставки
    users_balance[from_id]["balance"] -= amount
    users_balance[to_id]["balance"] -= amount

    fight_msg = await message.answer(
        "⚔️ Бой начинается."
    )

    await asyncio.sleep(1)

    await fight_msg.edit_text(
        "⚔️ Бой начинается.."
    )

    await asyncio.sleep(1)

    await fight_msg.edit_text(
        "⚔️ Бой начинается..."
    )

    await asyncio.sleep(1)


    winner = random.choice([
        from_id,
        to_id
    ])

    pot = amount * 2

    users_balance[winner]["balance"] += pot

    from_name = users_balance[from_id]["username"]
    to_name = users_balance[to_id]["username"]
    winner_name = users_balance[winner]["username"]

    log_transaction(
        winner_name,
        "battle win",
        pot
    )
    active_battle_users.discard(from_id)
    active_battle_users.discard(to_id)

    save_data()

    del pending_battles[battle_id]

    await message.answer(
        f"⚔️ Бой завершён!\n\n"
        f"@{from_name} vs @{to_name}\n\n"
        f"🏆 Победитель: @{winner_name}\n"
        f"💰 Выигрыш: {pot} KAL"
    )

async def main():

    print("Бот запущен")

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
