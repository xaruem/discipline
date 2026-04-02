from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message
from utils.keyboards import main_menu
from utils.db import get_user

router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message):
    user = get_user(message.from_user.id)
    name = message.from_user.first_name

    await message.answer(
        f"👋 Привет, *{name}*!\n\n"
        "Я твой *Discipline Bot* — личный инструмент контроля.\n\n"
        "Я помогу тебе:\n"
        "✅ Держать серию дней без срывов\n"
        "🎯 Выполнять ежедневные цели\n"
        "⚡ Проходить челленджи\n"
        "📊 Видеть прогресс\n"
        "🚨 Не сдаваться в тяжёлые моменты\n\n"
        "Выбери действие в меню ниже 👇",
        parse_mode="Markdown",
        reply_markup=main_menu()
    )
