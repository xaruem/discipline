from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from utils.db import get_user, add_goal, remove_goal, toggle_goal_done
from utils.keyboards import goals_keyboard

router = Router()

class GoalStates(StatesGroup):
    waiting_for_goal = State()

@router.message(F.text == "🎯 Мои цели")
async def show_goals(message: Message):
    user = get_user(message.from_user.id)
    goals = user["goals"]
    goals_done = user["goals_done"]

    if not goals:
        await message.answer(
            "🎯 *Твои цели на день*\n\n"
            "У тебя пока нет целей.\nДобавь первую цель! 👇",
            parse_mode="Markdown",
            reply_markup=goals_keyboard([], [])
        )
        return

    done_count = len(goals_done)
    total = len(goals)
    percent = int(done_count / total * 100) if total > 0 else 0
    progress_bar = "█" * (percent // 10) + "░" * (10 - percent // 10)

    await message.answer(
        f"🎯 *Цели на сегодня*\n\n"
        f"[{progress_bar}] {percent}%\n"
        f"Выполнено: {done_count}/{total}\n\n"
        "Нажми на цель, чтобы отметить ✅",
        parse_mode="Markdown",
        reply_markup=goals_keyboard(goals, goals_done)
    )

@router.callback_query(F.data.startswith("toggle_goal:"))
async def toggle_goal(callback: CallbackQuery):
    index = int(callback.data.split(":")[1])
    done = toggle_goal_done(callback.from_user.id, index)
    user = get_user(callback.from_user.id)
    goals = user["goals"]
    goals_done = user["goals_done"]

    done_count = len(goals_done)
    total = len(goals)
    percent = int(done_count / total * 100) if total > 0 else 0
    progress_bar = "█" * (percent // 10) + "░" * (10 - percent // 10)

    status = "✅ Выполнено!" if done else "⬜ Снято"
    await callback.answer(status)

    await callback.message.edit_text(
        f"🎯 *Цели на сегодня*\n\n"
        f"[{progress_bar}] {percent}%\n"
        f"Выполнено: {done_count}/{total}\n\n"
        "Нажми на цель, чтобы отметить ✅",
        parse_mode="Markdown",
        reply_markup=goals_keyboard(goals, goals_done)
    )

@router.callback_query(F.data.startswith("delete_goal:"))
async def delete_goal(callback: CallbackQuery):
    index = int(callback.data.split(":")[1])
    remove_goal(callback.from_user.id, index)
    user = get_user(callback.from_user.id)
    await callback.answer("🗑 Цель удалена")
    await callback.message.edit_text(
        "🎯 *Твои цели на день*\n\nНажми на цель для отметки ✅",
        parse_mode="Markdown",
        reply_markup=goals_keyboard(user["goals"], user["goals_done"])
    )

@router.callback_query(F.data == "add_goal")
async def prompt_add_goal(callback: CallbackQuery, state: FSMContext):
    await state.set_state(GoalStates.waiting_for_goal)
    await callback.message.answer(
        "✍️ Напиши свою цель на сегодня:\n\n"
        "Примеры:\n"
        "• Сделать сайт\n"
        "• Спорт 30 минут\n"
        "• Прочитать 10 страниц"
    )
    await callback.answer()

@router.message(GoalStates.waiting_for_goal)
async def save_new_goal(message: Message, state: FSMContext):
    goal_text = message.text.strip()
    if len(goal_text) > 100:
        await message.answer("❌ Слишком длинно! Максимум 100 символов.")
        return

    add_goal(message.from_user.id, goal_text)
    await state.clear()

    user = get_user(message.from_user.id)
    await message.answer(
        f"✅ Цель добавлена: *{goal_text}*\n\n"
        f"Всего целей: {len(user['goals'])}",
        parse_mode="Markdown",
        reply_markup=goals_keyboard(user["goals"], user["goals_done"])
    )
