from aiogram import Router, F
from aiogram.types import Message
from utils.db import get_user
from utils.challenges import get_level_info
from datetime import date, timedelta

router = Router()

@router.message(F.text == "📊 Статистика")
async def show_stats(message: Message):
    user = get_user(message.from_user.id)
    streak = user["streak"]
    max_streak = user["max_streak"]
    goals = user["goals"]
    goals_done = user["goals_done"]
    lvl_emoji, lvl_name = get_level_info(streak)

    # Недельная статистика
    today = date.today()
    week_days = [(today - timedelta(days=i)).isoformat() for i in range(6, -1, -1)]

    discipline_days = sum(1 for d in week_days if d in user.get("week_discipline", []))
    challenge_days = sum(1 for d in week_days if d in user.get("week_challenges", []))

    # Процент целей
    total_goals = len(goals)
    done_goals = len(goals_done)
    goals_pct = int(done_goals / total_goals * 100) if total_goals > 0 else 0

    # Прогресс-бар для дисциплины
    disc_bar = "🟢" * discipline_days + "⬜" * (7 - discipline_days)
    chall_bar = "⚡" * challenge_days + "⬜" * (7 - challenge_days)

    # Следующий уровень
    if streak < 3:
        next_lvl = f"До уровня 🟢 Новичок: {3 - streak} дней"
    elif streak < 7:
        next_lvl = f"До уровня 🔵 Контроль: {7 - streak} дней"
    elif streak < 14:
        next_lvl = f"До уровня 🟣 Сила: {14 - streak} дней"
    elif streak < 30:
        next_lvl = f"До уровня 🔥 Дисциплина: {30 - streak} дней"
    else:
        next_lvl = "🔥 Максимальный уровень достигнут!"

    await message.answer(
        f"📊 *Твоя статистика*\n\n"
        f"━━━━━━━━━━━━━━━\n"
        f"🔥 Серия: *{streak} дней*\n"
        f"🏆 Рекорд: *{max_streak} дней*\n"
        f"{lvl_emoji} Уровень: *{lvl_name}*\n"
        f"📈 {next_lvl}\n\n"
        f"━━━━━━━━━━━━━━━\n"
        f"📅 *За последние 7 дней:*\n\n"
        f"Дисциплина: {disc_bar} {discipline_days}/7\n"
        f"Челленджи:  {chall_bar} {challenge_days}/7\n\n"
        f"━━━━━━━━━━━━━━━\n"
        f"🎯 *Цели сегодня:*\n"
        f"Выполнено: {done_goals}/{total_goals} ({goals_pct}%)\n\n"
        f"━━━━━━━━━━━━━━━\n"
        f"💡 _Каждый день без срыва — это вклад в твоё будущее_",
        parse_mode="Markdown"
    )
