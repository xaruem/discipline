import asyncio
from datetime import datetime, timedelta
from aiogram import Bot
from utils.db import get_all_users, get_user
from utils.motivation import MORNING_MESSAGES, EVENING_MESSAGES, WATER_REMINDERS, PHONE_REMINDERS
import random

async def send_reminders(bot: Bot):
    """Отправка напоминаний по расписанию."""
    while True:
        now = datetime.now()
        current_time = now.strftime("%H:%M")
        current_hour = now.hour
        current_minute = now.minute

        try:
            all_users = get_all_users()
            for uid in all_users:
                user = get_user(int(uid))
                if not user.get("reminders_on", True):
                    continue

                wake = user.get("wake_time", "07:00")
                sleep = user.get("sleep_time", "23:00")

                # ── Утреннее приветствие ──────────────────────────────────
                if current_time == wake:
                    await bot.send_message(uid, random.choice(MORNING_MESSAGES))

                # ── Вечерний отчёт (за 1 час до сна) ────────────────────
                sleep_h, sleep_m = map(int, sleep.split(":"))
                evening_h = sleep_h - 1
                if current_hour == evening_h and current_minute == 0:
                    await bot.send_message(uid, random.choice(EVENING_MESSAGES))

                # ── Напоминание про воду каждые 2 часа (с 9 до 21) ──────
                if 9 <= current_hour <= 21 and current_minute == 0 and current_hour % 2 == 0:
                    await bot.send_message(uid, random.choice(WATER_REMINDERS))

                # ── Антителефон в 18:00 ───────────────────────────────────
                if current_hour == 18 and current_minute == 0:
                    await bot.send_message(uid, random.choice(PHONE_REMINDERS))

                # ── Напоминания о еде ─────────────────────────────────────
                await check_meal_reminders(bot, uid, user, current_time, current_hour, current_minute)

        except Exception as e:
            print(f"Scheduler error: {e}")

        await asyncio.sleep(60 - datetime.now().second)


async def check_meal_reminders(bot: Bot, uid: str, user: dict, current_time: str, hour: int, minute: int):
    """Умные напоминания о питании."""
    mode = user.get("meal_mode")
    if not mode:
        return

    eaten = user.get("meals_eaten_today", [])

    # ── ФИКСИРОВАННЫЙ режим ───────────────────────────────────────────────────
    if mode == "fixed":
        times = user.get("meal_times", [])
        names = user.get("meal_names", [])

        for i, meal_time in enumerate(times):
            meal_h, meal_m = map(int, meal_time.split(":"))

            # За 5 минут до приёма — напомни
            remind_dt = datetime.now().replace(hour=meal_h, minute=meal_m, second=0) - timedelta(minutes=5)
            remind_time = remind_dt.strftime("%H:%M")
            if current_time == remind_time and i not in eaten:
                name = names[i] if i < len(names) else f"Приём {i+1}"
                await bot.send_message(
                    uid,
                    f"🍽 Через 5 минут *{name}* ({meal_time})\n\n"
                    f"Приготовься поесть! 🥗",
                    parse_mode="Markdown"
                )

            # Через 15 минут после — проверь, поел ли
            check_dt = datetime.now().replace(hour=meal_h, minute=meal_m, second=0) + timedelta(minutes=15)
            check_time = check_dt.strftime("%H:%M")
            if current_time == check_time and i not in eaten:
                name = names[i] if i < len(names) else f"Приём {i+1}"
                from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
                kb = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="✅ Да, поел", callback_data=f"meal_eat:{i}")],
                    [InlineKeyboardButton(text="⏭ Пропускаю", callback_data=f"meal_skip:{i}")],
                ])
                await bot.send_message(
                    uid,
                    f"🤔 *{name}* должен был быть в {meal_time}.\n\n"
                    f"Ты поел? 👇",
                    parse_mode="Markdown",
                    reply_markup=kb
                )

    # ── ИНТЕРВАЛЬНЫЙ режим ────────────────────────────────────────────────────
    elif mode == "interval":
        interval_h = user.get("meal_interval_hours", 4)
        first_time = user.get("meal_times", ["08:00"])[0]
        first_h, first_m = map(int, first_time.split(":"))

        # Вычисляем все времена приёмов на сегодня
        base = datetime.now().replace(hour=first_h, minute=first_m, second=0, microsecond=0)
        sleep_h, sleep_m = map(int, user.get("sleep_time", "23:00").split(":"))
        sleep_dt = datetime.now().replace(hour=sleep_h, minute=sleep_m, second=0)

        meal_index = 0
        t = base
        while t < sleep_dt:
            remind_time = (t - timedelta(minutes=5)).strftime("%H:%M")
            if current_time == remind_time:
                count_today = len(eaten)
                await bot.send_message(
                    uid,
                    f"🍽 Пора поесть! Приём #{meal_index + 1}\n\n"
                    f"Сегодня уже было: {count_today} раз(а) 🥗\n"
                    f"Открой раздел *🍽 Питание* и отметь!",
                    parse_mode="Markdown"
                )
            t += timedelta(hours=interval_h)
            meal_index += 1


async def start_scheduler(bot: Bot):
    asyncio.create_task(send_reminders(bot))

