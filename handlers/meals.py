from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from utils.db import (
    get_user, save_user,
    setup_meals_fixed, setup_meals_interval,
    mark_meal_eaten, get_meal_schedule_text
)
from utils.keyboards import main_menu

router = Router()

# ─── FSM состояния ────────────────────────────────────────────────────────────

class MealSetup(StatesGroup):
    choose_mode = State()
    # Fixed mode
    fixed_count = State()
    fixed_times = State()
    fixed_names = State()
    # Interval mode
    interval_hours = State()
    interval_start = State()

# ─── Клавиатуры ──────────────────────────────────────────────────────────────

def meal_mode_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🕐 Фиксированное время (завтрак, обед, ужин)", callback_data="meal_mode_fixed")],
        [InlineKeyboardButton(text="⏱ Интервалы (каждые N часов)", callback_data="meal_mode_interval")],
    ])

def meal_main_kb(user: dict) -> InlineKeyboardMarkup:
    """Клавиатура с кнопками для каждого приёма пищи."""
    mode = user.get("meal_mode")
    eaten = user.get("meals_eaten_today", [])
    buttons = []

    if mode == "fixed":
        times = user.get("meal_times", [])
        names = user.get("meal_names", [])
        for i, t in enumerate(times):
            name = names[i] if i < len(names) else f"Приём {i+1}"
            check = "✅" if i in eaten else "🍽"
            buttons.append([InlineKeyboardButton(
                text=f"{check} {t} — {name}",
                callback_data=f"meal_eat:{i}"
            )])
    elif mode == "interval":
        # Показываем сколько раз поел сегодня
        count = len(eaten)
        buttons.append([InlineKeyboardButton(
            text=f"✅ Поел сейчас (всего сегодня: {count})",
            callback_data="meal_eat_now"
        )])

    buttons.append([InlineKeyboardButton(text="⚙️ Изменить график", callback_data="meal_setup")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# ─── Главное меню питания ─────────────────────────────────────────────────────

@router.message(F.text == "🍽 Питание")
async def show_meals(message: Message):
    user = get_user(message.from_user.id)
    mode = user.get("meal_mode")

    if not mode:
        await message.answer(
            "🍽 *График питания*\n\n"
            "У тебя ещё не настроен график еды.\n\n"
            "Выбери режим:",
            parse_mode="Markdown",
            reply_markup=meal_mode_kb()
        )
        return

    eaten = user.get("meals_eaten_today", [])
    schedule_text = get_meal_schedule_text(user)

    if mode == "fixed":
        total = len(user.get("meal_times", []))
        done = len(eaten)
        skips = len(user.get("meal_skips_week", []))
        pct = int(done / total * 100) if total else 0
        bar = "█" * (pct // 10) + "░" * (10 - pct // 10)

        await message.answer(
            f"🍽 *График питания*\n\n"
            f"{schedule_text}\n\n"
            f"[{bar}] {pct}% — {done}/{total} сегодня\n"
            f"⚠️ Пропусков за неделю: {skips}\n\n"
            "Нажми на приём, чтобы отметить ✅",
            parse_mode="Markdown",
            reply_markup=meal_main_kb(user)
        )
    else:
        hours = user.get("meal_interval_hours", 4)
        count = len(eaten)
        await message.answer(
            f"🍽 *График питания*\n\n"
            f"⏱ Режим: каждые *{hours} часов*\n"
            f"✅ Приёмов пищи сегодня: *{count}*\n\n"
            "Нажми кнопку когда поел 👇",
            parse_mode="Markdown",
            reply_markup=meal_main_kb(user)
        )

# ─── Настройка режима ─────────────────────────────────────────────────────────

@router.callback_query(F.data == "meal_setup")
async def start_meal_setup(callback: CallbackQuery):
    await callback.message.edit_text(
        "⚙️ *Настройка графика питания*\n\n"
        "Выбери режим:",
        parse_mode="Markdown",
        reply_markup=meal_mode_kb()
    )
    await callback.answer()

# ── FIXED MODE ────────────────────────────────────────────────────────────────

@router.callback_query(F.data == "meal_mode_fixed")
async def fixed_mode_start(callback: CallbackQuery, state: FSMContext):
    await state.set_state(MealSetup.fixed_count)
    await callback.message.edit_text(
        "🕐 *Фиксированное расписание*\n\n"
        "Сколько приёмов пищи в день?\n\n"
        "Напиши цифру: `2`, `3` или `4`",
        parse_mode="Markdown"
    )
    await callback.answer()

@router.message(MealSetup.fixed_count)
async def fixed_get_count(message: Message, state: FSMContext):
    try:
        count = int(message.text.strip())
        assert 1 <= count <= 6
    except:
        await message.answer("❌ Введи число от 1 до 6")
        return

    await state.update_data(count=count, times=[], names=[])
    await state.set_state(MealSetup.fixed_times)
    await message.answer(
        f"✅ {count} приёма(ов) пищи.\n\n"
        f"Теперь введи время через запятую:\n\n"
        f"Например для {count} приёмов:\n"
        f"`{'  ,  '.join(['08:00', '13:00', '19:00'][:count])}`\n\n"
        f"_Формат: ЧЧ:ММ через запятую_",
        parse_mode="Markdown"
    )

@router.message(MealSetup.fixed_times)
async def fixed_get_times(message: Message, state: FSMContext):
    data = await state.get_data()
    count = data["count"]
    raw = message.text.strip()

    try:
        parts = [t.strip() for t in raw.split(",")]
        assert len(parts) == count
        for t in parts:
            h, m = map(int, t.split(":"))
            assert 0 <= h <= 23 and 0 <= m <= 59
    except:
        await message.answer(
            f"❌ Неверный формат. Нужно {count} значений через запятую.\n"
            f"Пример: `08:00, 13:00, 19:00`",
            parse_mode="Markdown"
        )
        return

    times = [t.strip() for t in raw.split(",")]
    await state.update_data(times=times)
    await state.set_state(MealSetup.fixed_names)

    examples = ["Завтрак", "Обед", "Ужин", "Перекус"]
    example_str = ", ".join(examples[:count])
    await message.answer(
        f"✅ Время установлено: {', '.join(times)}\n\n"
        f"Теперь дай названия приёмам через запятую:\n\n"
        f"Например: `{example_str}`\n\n"
        f"_Или напиши_ `авто` _и я назову сам_",
        parse_mode="Markdown"
    )

@router.message(MealSetup.fixed_names)
async def fixed_get_names(message: Message, state: FSMContext):
    data = await state.get_data()
    count = data["count"]
    times = data["times"]
    raw = message.text.strip()

    if raw.lower() == "авто":
        auto_names = ["Завтрак", "2-й завтрак", "Обед", "Полдник", "Ужин", "Поздний ужин"]
        names = auto_names[:count]
    else:
        names = [n.strip() for n in raw.split(",")]
        if len(names) != count:
            await message.answer(
                f"❌ Нужно {count} названий через запятую.\n"
                f"Или напиши `авто`",
                parse_mode="Markdown"
            )
            return

    setup_meals_fixed(message.from_user.id, times, names)
    await state.clear()

    schedule = "\n".join([f"🍽 {t} — {n}" for t, n in zip(times, names)])
    await message.answer(
        f"✅ *График питания настроен!*\n\n"
        f"{schedule}\n\n"
        f"Я буду напоминать тебе за 5 минут до каждого приёма пищи.\n"
        f"И спрошу — поел ли ты, если ты не отметил. 🔔",
        parse_mode="Markdown",
        reply_markup=main_menu()
    )

# ── INTERVAL MODE ─────────────────────────────────────────────────────────────

@router.callback_query(F.data == "meal_mode_interval")
async def interval_mode_start(callback: CallbackQuery, state: FSMContext):
    await state.set_state(MealSetup.interval_hours)
    await callback.message.edit_text(
        "⏱ *Интервальный режим*\n\n"
        "Каждые сколько часов ты ешь?\n\n"
        "Напиши число: `3`, `4` или `5`",
        parse_mode="Markdown"
    )
    await callback.answer()

@router.message(MealSetup.interval_hours)
async def interval_get_hours(message: Message, state: FSMContext):
    try:
        hours = int(message.text.strip())
        assert 1 <= hours <= 12
    except:
        await message.answer("❌ Введи число от 1 до 12")
        return

    await state.update_data(hours=hours)
    await state.set_state(MealSetup.interval_start)
    await message.answer(
        f"✅ Каждые {hours} ч.\n\n"
        f"В какое время первый приём пищи?\n\n"
        f"Пример: `08:00`",
        parse_mode="Markdown"
    )

@router.message(MealSetup.interval_start)
async def interval_get_start(message: Message, state: FSMContext):
    raw = message.text.strip()
    try:
        h, m = map(int, raw.split(":"))
        assert 0 <= h <= 23 and 0 <= m <= 59
    except:
        await message.answer("❌ Неверный формат. Пример: `08:00`", parse_mode="Markdown")
        return

    data = await state.get_data()
    hours = data["hours"]
    first = f"{h:02d}:{m:02d}"

    setup_meals_interval(message.from_user.id, hours, first)
    await state.clear()

    # Показываем примерное расписание
    from datetime import datetime, timedelta
    start_dt = datetime.strptime(first, "%H:%M")
    schedule_lines = []
    t = start_dt
    while t.hour < 22:
        schedule_lines.append(f"🍽 {t.strftime('%H:%M')}")
        t += timedelta(hours=hours)

    schedule = "\n".join(schedule_lines[:6])

    await message.answer(
        f"✅ *Интервальный режим настроен!*\n\n"
        f"Первый приём: *{first}*\n"
        f"Каждые: *{hours} часов*\n\n"
        f"Примерное расписание сегодня:\n{schedule}\n\n"
        f"Я буду напоминать тебе в каждый интервал 🔔",
        parse_mode="Markdown",
        reply_markup=main_menu()
    )

# ─── Отметить приём пищи ─────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("meal_eat:"))
async def meal_eat_fixed(callback: CallbackQuery):
    index = int(callback.data.split(":")[1])
    result = mark_meal_eaten(callback.from_user.id, index)
    user = get_user(callback.from_user.id)

    names = user.get("meal_names", [])
    name = names[index] if index < len(names) else f"Приём {index+1}"
    eaten = result["eaten"]
    total = result["total"]

    if eaten == total:
        msg = f"🏆 Все {total} приёма пищи выполнены! Отличный день!"
    else:
        msg = f"✅ {name} отмечен! Выполнено {eaten}/{total}"

    await callback.answer(msg, show_alert=(eaten == total))

    # Обновляем сообщение
    schedule_text = get_meal_schedule_text(user)
    pct = int(eaten / total * 100) if total else 0
    bar = "█" * (pct // 10) + "░" * (10 - pct // 10)
    skips = len(user.get("meal_skips_week", []))

    await callback.message.edit_text(
        f"🍽 *График питания*\n\n"
        f"{schedule_text}\n\n"
        f"[{bar}] {pct}% — {eaten}/{total} сегодня\n"
        f"⚠️ Пропусков за неделю: {skips}\n\n"
        "Нажми на приём, чтобы отметить ✅",
        parse_mode="Markdown",
        reply_markup=meal_main_kb(user)
    )

@router.callback_query(F.data == "meal_eat_now")
async def meal_eat_interval(callback: CallbackQuery):
    from datetime import datetime
    user = get_user(callback.from_user.id)
    eaten_list = user.get("meals_eaten_today", [])
    now_ts = int(datetime.now().timestamp())
    eaten_list.append(now_ts)
    user["meals_eaten_today"] = eaten_list
    from utils.db import save_user
    save_user(callback.from_user.id, user)

    count = len(eaten_list)
    hours = user.get("meal_interval_hours", 4)

    phrases = ["Отлично!", "Хорошо, так держать!", "Молодец, питание под контролем!"]
    import random
    phrase = random.choice(phrases)

    await callback.answer(f"✅ Приём #{count} отмечен! {phrase}", show_alert=False)
    await callback.message.edit_text(
        f"🍽 *График питания*\n\n"
        f"⏱ Режим: каждые *{hours} часов*\n"
        f"✅ Приёмов пищи сегодня: *{count}*\n"
        f"🕐 Последний: {datetime.now().strftime('%H:%M')}\n\n"
        f"Следующий примерно в {_next_meal_time(hours)}\n\n"
        "Нажми кнопку когда поел 👇",
        parse_mode="Markdown",
        reply_markup=meal_main_kb(user)
    )

def _next_meal_time(hours: int) -> str:
    from datetime import datetime, timedelta
    t = datetime.now() + timedelta(hours=hours)
    return t.strftime("%H:%M")

@router.callback_query(F.data.startswith("meal_skip:"))
async def meal_skip(callback: CallbackQuery):
    index = int(callback.data.split(":")[1])
    user = get_user(callback.from_user.id)
    names = user.get("meal_names", [])
    name = names[index] if index < len(names) else f"Приём {index+1}"
    await callback.message.edit_text(
        f"⏭ *{name}* пропущен.\n\n"
        "Старайся не пропускать еду — это влияет на энергию и самоконтроль.\n"
        "Поешь при первой возможности! 🍽",
        parse_mode="Markdown"
    )
    await callback.answer()
