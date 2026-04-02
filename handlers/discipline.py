from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from utils.db import mark_clean_today, mark_relapse, get_user
from utils.challenges import get_level_info

router = Router()

def confirm_relapse_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="⚠️ Да, был срыв", callback_data="confirm_relapse"),
            InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_relapse"),
        ]
    ])

@router.message(F.text == "✅ Сегодня чисто")
async def clean_today(message: Message):
    result = mark_clean_today(message.from_user.id)

    if result["status"] == "already_done":
        streak = result["streak"]
        lvl_emoji, lvl_name = get_level_info(streak)
        await message.answer(
            f"✅ Ты уже отметился сегодня!\n\n"
            f"🔥 Серия: *{streak} дней* {lvl_emoji} {lvl_name}\n\n"
            "Держись до завтра! 💪",
            parse_mode="Markdown"
        )
        return

    streak = result["streak"]
    max_streak = result["max_streak"]
    lvl_emoji, lvl_name = get_level_info(streak)

    # Мотивационный текст в зависимости от серии
    if streak == 1:
        extra = "Первый день — самый важный. Завтра — второй. 🚀"
    elif streak == 3:
        extra = "3 дня! Ты преодолел первый барьер. Большинство не доходит сюда! 🟢"
    elif streak == 7:
        extra = "7 дней! Неделя чистоты. Ты уже в топ-20% людей! 🔵"
    elif streak == 14:
        extra = "14 дней! Две недели — это уже характер. 🟣"
    elif streak == 30:
        extra = "30 дней!! 🔥 Это ДИСЦИПЛИНА. Ты — другой человек."
    elif streak % 10 == 0:
        extra = f"💡 {streak} дней подряд! Серьёзный результат."
    else:
        extra = "Ты уже сильнее вчерашнего себя. Продолжай. 💪"

    await message.answer(
        f"✅ *День {streak} отмечен!*\n\n"
        f"{lvl_emoji} Уровень: *{lvl_name}*\n"
        f"🔥 Серия: *{streak} дней*\n"
        f"🏆 Рекорд: *{max_streak} дней*\n\n"
        f"{extra}",
        parse_mode="Markdown"
    )

@router.message(F.text == "💥 Срыв")
async def relapse_warning(message: Message):
    user = get_user(message.from_user.id)
    streak = user["streak"]

    if streak == 0:
        await message.answer(
            "📌 У тебя пока нет активной серии.\n"
            "Нажми *✅ Сегодня чисто*, чтобы начать! 💪",
            parse_mode="Markdown"
        )
        return

    await message.answer(
        f"⚠️ Ты уверен, что был срыв?\n\n"
        f"Твоя текущая серия: *{streak} дней*\n"
        f"После подтверждения она сбросится до 0.\n\n"
        "Подумай: *может это просто тяжёлый момент?*\n"
        "Используй кнопку 🚨 *Мне сейчас тяжело* — это не срыв!",
        parse_mode="Markdown",
        reply_markup=confirm_relapse_kb()
    )

@router.callback_query(F.data == "confirm_relapse")
async def do_relapse(callback: CallbackQuery):
    result = mark_relapse(callback.from_user.id)
    old = result["old_streak"]
    max_s = result["max_streak"]

    await callback.message.edit_text(
        f"💔 Серия сброшена.\n\n"
        f"Было: *{old} дней*\n"
        f"Рекорд остаётся: *{max_s} дней*\n\n"
        "Один провал — не конец.\n"
        "*Сдаться после него — вот это конец.*\n\n"
        "Нажми ✅ *Сегодня чисто*, чтобы начать новую серию! 🔁",
        parse_mode="Markdown"
    )
    await callback.answer()

@router.callback_query(F.data == "cancel_relapse")
async def cancel_relapse(callback: CallbackQuery):
    user = get_user(callback.from_user.id)
    await callback.message.edit_text(
        f"✅ Хорошо! Серия *{user['streak']} дней* продолжается.\n\n"
        "Если тебе тяжело — нажми 🚨 *Мне сейчас тяжело*",
        parse_mode="Markdown"
    )
    await callback.answer()
