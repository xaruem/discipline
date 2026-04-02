from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from utils.motivation import get_motivation, get_danger_action
from utils.keyboards import danger_keyboard

router = Router()

@router.message(F.text == "💬 Мотивация")
async def show_motivation(message: Message):
    msg = get_motivation("hold")
    await message.answer(
        f"💬 *Слово дня*\n\n{msg}\n\n"
        "_Сохрани этот настрой до конца дня._",
        parse_mode="Markdown"
    )

@router.message(F.text == "🚨 Мне сейчас тяжело")
async def danger_mode(message: Message):
    msg = get_motivation("danger")
    action = get_danger_action()

    await message.answer(
        f"🚨 *СТОП. ЧИТАЙ.*\n\n"
        f"{msg}\n\n"
        f"━━━━━━━━━━━━━━━\n"
        f"⚡ *Сделай прямо сейчас:*\n\n"
        f"{action}\n\n"
        f"━━━━━━━━━━━━━━━\n"
        "Или выбери действие ниже 👇",
        parse_mode="Markdown",
        reply_markup=danger_keyboard()
    )

@router.callback_query(F.data == "action_walk")
async def action_walk(callback: CallbackQuery):
    await callback.message.edit_text(
        "🏃 *Выйди на улицу прямо сейчас*\n\n"
        "Не думай — просто оденься и выйди.\n"
        "Даже 5 минут на улице переключат твой мозг.\n\n"
        "Поставь таймер на 10 минут и просто иди. 🚶",
        parse_mode="Markdown"
    )
    await callback.answer("Иди! 🏃")

@router.callback_query(F.data == "action_pushups")
async def action_pushups(callback: CallbackQuery):
    await callback.message.edit_text(
        "💪 *25 отжиманий — прямо сейчас*\n\n"
        "Ложись на пол. Начинай считать.\n\n"
        "1... 2... 3...\n\n"
        "После 10 отжиманий ты уже забудешь о проблеме.\n"
        "После 25 — почувствуешь силу. 🔥",
        parse_mode="Markdown"
    )
    await callback.answer("Давай! 💪")

@router.callback_query(F.data == "action_shower")
async def action_shower(callback: CallbackQuery):
    await callback.message.edit_text(
        "🚿 *Холодный душ — лучшее лекарство*\n\n"
        "Иди в ванную прямо сейчас.\n"
        "Включи холодную воду. Встань под неё.\n\n"
        "Первые 10 секунд — сложно.\n"
        "После 30 секунд — эйфория и ясность.\n\n"
        "Это работает. Проверено. 🧊",
        parse_mode="Markdown"
    )
    await callback.answer("В душ! 🚿")

@router.callback_query(F.data == "action_book")
async def action_book(callback: CallbackQuery):
    await callback.message.edit_text(
        "📖 *Открой книгу — прямо сейчас*\n\n"
        "Не важно, какую. Возьми любую.\n"
        "Прочитай хотя бы одну страницу.\n\n"
        "Это переключит твой мозг на другой режим.\n"
        "10 страниц — и ты уже в другом состоянии. 📚",
        parse_mode="Markdown"
    )
    await callback.answer("Читай! 📖")
