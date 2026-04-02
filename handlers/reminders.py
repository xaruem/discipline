from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from utils.db import get_user, save_user
from utils.keyboards import settings_keyboard, main_menu

router = Router()

class SettingsStates(StatesGroup):
    waiting_wake = State()
    waiting_sleep = State()

@router.message(F.text == "⚙️ Настройки")
async def show_settings(message: Message):
    user = get_user(message.from_user.id)
    reminders = "✅ Вкл" if user.get("reminders_on", True) else "❌ Выкл"

    await message.answer(
        f"⚙️ *Настройки*\n\n"
        f"⏰ Подъём: *{user.get('wake_time', '07:00')}*\n"
        f"🌙 Сон: *{user.get('sleep_time', '23:00')}*\n"
        f"🔔 Напоминания: *{reminders}*\n\n"
        "Что изменить?",
        parse_mode="Markdown",
        reply_markup=settings_keyboard()
    )

@router.callback_query(F.data == "set_wake")
async def ask_wake_time(callback: CallbackQuery, state: FSMContext):
    await state.set_state(SettingsStates.waiting_wake)
    await callback.message.answer(
        "⏰ Во сколько ты просыпаешься?\n\n"
        "Напиши в формате *ЧЧ:ММ*\n"
        "Например: `07:00` или `06:30`",
        parse_mode="Markdown"
    )
    await callback.answer()

@router.message(SettingsStates.waiting_wake)
async def save_wake_time(message: Message, state: FSMContext):
    time_str = message.text.strip()
    try:
        h, m = map(int, time_str.split(":"))
        assert 0 <= h <= 23 and 0 <= m <= 59
    except:
        await message.answer("❌ Неверный формат. Попробуй ещё раз: `07:00`", parse_mode="Markdown")
        return

    user = get_user(message.from_user.id)
    user["wake_time"] = f"{h:02d}:{m:02d}"
    save_user(message.from_user.id, user)
    await state.clear()
    await message.answer(
        f"✅ Время подъёма установлено: *{user['wake_time']}*\n\n"
        "Я буду присылать утреннее приветствие в это время 🌅",
        parse_mode="Markdown",
        reply_markup=main_menu()
    )

@router.callback_query(F.data == "set_sleep")
async def ask_sleep_time(callback: CallbackQuery, state: FSMContext):
    await state.set_state(SettingsStates.waiting_sleep)
    await callback.message.answer(
        "🌙 Во сколько ты ложишься спать?\n\n"
        "Напиши в формате *ЧЧ:ММ*\n"
        "Например: `23:00` или `22:30`",
        parse_mode="Markdown"
    )
    await callback.answer()

@router.message(SettingsStates.waiting_sleep)
async def save_sleep_time(message: Message, state: FSMContext):
    time_str = message.text.strip()
    try:
        h, m = map(int, time_str.split(":"))
        assert 0 <= h <= 23 and 0 <= m <= 59
    except:
        await message.answer("❌ Неверный формат. Попробуй ещё раз: `23:00`", parse_mode="Markdown")
        return

    user = get_user(message.from_user.id)
    user["sleep_time"] = f"{h:02d}:{m:02d}"
    save_user(message.from_user.id, user)
    await state.clear()
    await message.answer(
        f"✅ Время сна установлено: *{user['sleep_time']}*\n\n"
        "Я буду напоминать тебе о сне за час до этого времени 🌙",
        parse_mode="Markdown",
        reply_markup=main_menu()
    )

@router.callback_query(F.data == "toggle_reminders")
async def toggle_reminders(callback: CallbackQuery):
    user = get_user(callback.from_user.id)
    user["reminders_on"] = not user.get("reminders_on", True)
    save_user(callback.from_user.id, user)
    status = "✅ включены" if user["reminders_on"] else "❌ выключены"
    await callback.answer(f"Напоминания {status}")
    await callback.message.edit_text(
        f"⚙️ *Настройки обновлены*\n\n"
        f"🔔 Напоминания: *{status}*",
        parse_mode="Markdown",
        reply_markup=settings_keyboard()
    )

@router.callback_query(F.data == "reset_all")
async def confirm_reset(callback: CallbackQuery):
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⚠️ Да, сбросить всё", callback_data="do_reset_all")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_reset")],
    ])
    await callback.message.edit_text(
        "⚠️ *Сбросить все данные?*\n\n"
        "Это удалит:\n• Серию дней\n• Все цели\n• Статистику\n\n"
        "Это действие *необратимо*.",
        parse_mode="Markdown",
        reply_markup=kb
    )
    await callback.answer()

@router.callback_query(F.data == "do_reset_all")
async def do_reset_all(callback: CallbackQuery):
    from utils.db import _load, _save
    data = _load()
    uid = str(callback.from_user.id)
    if uid in data:
        del data[uid]
        _save(data)
    await callback.message.edit_text(
        "🗑 Все данные удалены.\n\n"
        "Нажми /start, чтобы начать заново. 🚀"
    )
    await callback.answer()

@router.callback_query(F.data == "cancel_reset")
async def cancel_reset(callback: CallbackQuery):
    await callback.message.edit_text(
        "✅ Отмена. Данные сохранены.",
        reply_markup=settings_keyboard()
    )
    await callback.answer()
