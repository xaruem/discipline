from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from utils.db import get_user, set_challenge, mark_challenge_done
from utils.challenges import get_random_challenge
from utils.keyboards import challenge_keyboard

router = Router()

@router.message(F.text == "⚡ Челлендж дня")
async def show_challenge(message: Message):
    user = get_user(message.from_user.id)
    challenge = user.get("challenge_today")
    done = user.get("challenge_done", False)

    if not challenge:
        # Выдаём случайный средний
        challenge = get_random_challenge("medium")
        set_challenge(message.from_user.id, challenge)
        user = get_user(message.from_user.id)
        done = False

    status = "✅ Выполнен!" if done else "⏳ В процессе..."

    await message.answer(
        f"⚡ *Челлендж дня*\n\n"
        f"{'✅ ' if done else '🎯 '}{challenge}\n\n"
        f"Статус: {status}\n\n"
        "Хочешь другой? Нажми *🔄 Другой*",
        parse_mode="Markdown",
        reply_markup=challenge_keyboard(done)
    )

@router.callback_query(F.data == "challenge_done")
async def complete_challenge(callback: CallbackQuery):
    mark_challenge_done(callback.from_user.id)
    user = get_user(callback.from_user.id)
    challenge = user["challenge_today"]

    await callback.message.edit_text(
        f"🏆 *Челлендж выполнен!*\n\n"
        f"✅ {challenge}\n\n"
        "Это не случайность — это характер. 💪\n"
        "Завтра будет новый вызов!",
        parse_mode="Markdown",
        reply_markup=challenge_keyboard(True)
    )
    await callback.answer("🔥 Отличная работа!")

@router.callback_query(F.data == "new_challenge")
async def new_challenge(callback: CallbackQuery):
    challenge = get_random_challenge("medium")
    set_challenge(callback.from_user.id, challenge)
    await callback.message.edit_text(
        f"⚡ *Новый челлендж дня*\n\n"
        f"🎯 {challenge}\n\n"
        "Статус: ⏳ В процессе...",
        parse_mode="Markdown",
        reply_markup=challenge_keyboard(False)
    )
    await callback.answer("🔄 Новый челлендж!")

@router.callback_query(F.data == "challenge_easy")
async def easy_challenge(callback: CallbackQuery):
    challenge = get_random_challenge("easy")
    set_challenge(callback.from_user.id, challenge)
    await callback.message.edit_text(
        f"💡 *Лёгкий челлендж*\n\n"
        f"🎯 {challenge}\n\n"
        "Статус: ⏳ В процессе...\n\n"
        "_Лёгкий сегодня — но выполни его! Привычка важнее сложности._",
        parse_mode="Markdown",
        reply_markup=challenge_keyboard(False)
    )
    await callback.answer()

@router.callback_query(F.data == "challenge_hard")
async def hard_challenge(callback: CallbackQuery):
    challenge = get_random_challenge("hard")
    set_challenge(callback.from_user.id, challenge)
    await callback.message.edit_text(
        f"🔥 *Сложный челлендж*\n\n"
        f"🎯 {challenge}\n\n"
        "Статус: ⏳ В процессе...\n\n"
        "_Это задание отделяет сильных от остальных. Ты справишься._",
        parse_mode="Markdown",
        reply_markup=challenge_keyboard(False)
    )
    await callback.answer()
