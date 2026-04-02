from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

def main_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="✅ Сегодня чисто"), KeyboardButton(text="💥 Срыв")],
            [KeyboardButton(text="🎯 Мои цели"), KeyboardButton(text="⚡ Челлендж дня")],
            [KeyboardButton(text="🍽 Питание"), KeyboardButton(text="📊 Статистика")],
            [KeyboardButton(text="💬 Мотивация"), KeyboardButton(text="🚨 Мне сейчас тяжело")],
            [KeyboardButton(text="⚙️ Настройки")],
        ],
        resize_keyboard=True
    )

def goals_keyboard(goals: list, goals_done: list) -> InlineKeyboardMarkup:
    buttons = []
    for i, goal in enumerate(goals):
        check = "✅" if i in goals_done else "⬜"
        buttons.append([
            InlineKeyboardButton(text=f"{check} {goal}", callback_data=f"toggle_goal:{i}"),
            InlineKeyboardButton(text="🗑", callback_data=f"delete_goal:{i}")
        ])
    buttons.append([InlineKeyboardButton(text="➕ Добавить цель", callback_data="add_goal")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def challenge_keyboard(done: bool) -> InlineKeyboardMarkup:
    buttons = []
    if not done:
        buttons.append([InlineKeyboardButton(text="✅ Выполнил!", callback_data="challenge_done")])
    buttons.append([InlineKeyboardButton(text="🔄 Другой челлендж", callback_data="new_challenge")])
    buttons.append([InlineKeyboardButton(text="💪 Лёгкий", callback_data="challenge_easy"),
                    InlineKeyboardButton(text="🔥 Сложный", callback_data="challenge_hard")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def danger_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏃 Выйти на улицу", callback_data="action_walk")],
        [InlineKeyboardButton(text="💪 Сделать отжимания", callback_data="action_pushups")],
        [InlineKeyboardButton(text="🚿 Холодный душ", callback_data="action_shower")],
        [InlineKeyboardButton(text="📖 Открыть книгу", callback_data="action_book")],
    ])

def settings_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⏰ Время пробуждения", callback_data="set_wake")],
        [InlineKeyboardButton(text="🌙 Время сна", callback_data="set_sleep")],
        [InlineKeyboardButton(text="🔔 Напоминания вкл/выкл", callback_data="toggle_reminders")],
        [InlineKeyboardButton(text="🔄 Сбросить всё", callback_data="reset_all")],
    ])
