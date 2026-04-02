import json
import os
from datetime import date, datetime
from typing import Optional

DATA_FILE = "data/users.json"

def _load() -> dict:
    if not os.path.exists(DATA_FILE):
        os.makedirs("data", exist_ok=True)
        return {}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def _save(data: dict):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_user(user_id: int) -> dict:
    data = _load()
    uid = str(user_id)
    if uid not in data:
        data[uid] = {
            "streak": 0,
            "max_streak": 0,
            "last_check": None,
            "goals": [],
            "goals_done": [],
            "challenge_today": None,
            "challenge_done": False,
            "week_discipline": [],   # список дат "чисто"
            "week_challenges": [],   # список дат выполненных челленджей
            "wake_time": "07:00",
            "sleep_time": "23:00",
            "reminders_on": True,
            "joined": str(date.today()),
            # Питание
            "meal_mode": None,          # "fixed" или "interval"
            "meal_times": [],           # ["08:00", "13:00", "19:00"] для fixed
            "meal_interval_hours": 4,   # для interval
            "meal_names": [],           # ["Завтрак", "Обед", "Ужин"]
            "meals_eaten_today": [],    # индексы съеденных приёмов (fixed) или timestamps (interval)
            "meal_skips_week": [],      # даты с пропущенными приёмами
        }
        _save(data)
    return data[uid]

def save_user(user_id: int, user_data: dict):
    data = _load()
    data[str(user_id)] = user_data
    _save(data)

def mark_clean_today(user_id: int) -> dict:
    """Отметить 'сегодня чисто'. Возвращает обновлённые данные."""
    user = get_user(user_id)
    today = str(date.today())

    if user["last_check"] == today:
        return {"status": "already_done", "streak": user["streak"]}

    # Проверяем непрерывность
    from datetime import timedelta
    yesterday = str(date.today() - timedelta(days=1))
    if user["last_check"] == yesterday:
        user["streak"] += 1
    else:
        user["streak"] = 1  # начать заново

    user["last_check"] = today
    if user["streak"] > user["max_streak"]:
        user["max_streak"] = user["streak"]

    # Записываем в статистику недели
    if today not in user["week_discipline"]:
        user["week_discipline"].append(today)
    # Оставляем только последние 7 дней
    user["week_discipline"] = user["week_discipline"][-7:]

    save_user(user_id, user)
    return {"status": "ok", "streak": user["streak"], "max_streak": user["max_streak"]}

def mark_relapse(user_id: int) -> dict:
    """Сброс — срыв."""
    user = get_user(user_id)
    old_streak = user["streak"]
    user["streak"] = 0
    user["last_check"] = None
    save_user(user_id, user)
    return {"old_streak": old_streak, "max_streak": user["max_streak"]}

def add_goal(user_id: int, goal: str):
    user = get_user(user_id)
    user["goals"].append(goal)
    save_user(user_id, user)

def remove_goal(user_id: int, index: int):
    user = get_user(user_id)
    if 0 <= index < len(user["goals"]):
        user["goals"].pop(index)
        if index in user["goals_done"]:
            user["goals_done"].remove(index)
    save_user(user_id, user)

def toggle_goal_done(user_id: int, index: int) -> bool:
    user = get_user(user_id)
    if index in user["goals_done"]:
        user["goals_done"].remove(index)
        done = False
    else:
        user["goals_done"].append(index)
        done = True
    save_user(user_id, user)
    return done

def reset_daily(user_id: int):
    """Сбросить ежедневные цели (вызывается раз в сутки)."""
    user = get_user(user_id)
    user["goals_done"] = []
    user["challenge_today"] = None
    user["challenge_done"] = False
    save_user(user_id, user)

def set_challenge(user_id: int, challenge: str):
    user = get_user(user_id)
    user["challenge_today"] = challenge
    user["challenge_done"] = False
    save_user(user_id, user)

def mark_challenge_done(user_id: int):
    user = get_user(user_id)
    user["challenge_done"] = True
    today = str(date.today())
    if today not in user["week_challenges"]:
        user["week_challenges"].append(today)
    user["week_challenges"] = user["week_challenges"][-7:]
    save_user(user_id, user)

def get_all_users() -> list:
    data = _load()
    return list(data.keys())

# ─── ПИТАНИЕ ────────────────────────────────────────────────────────────────

def setup_meals_fixed(user_id: int, times: list, names: list):
    """Настроить фиксированное расписание еды."""
    user = get_user(user_id)
    user["meal_mode"] = "fixed"
    user["meal_times"] = times        # ["08:00", "13:00", "19:00"]
    user["meal_names"] = names        # ["Завтрак", "Обед", "Ужин"]
    user["meals_eaten_today"] = []
    save_user(user_id, user)

def setup_meals_interval(user_id: int, interval_hours: int, first_time: str):
    """Настроить интервальный режим питания."""
    user = get_user(user_id)
    user["meal_mode"] = "interval"
    user["meal_interval_hours"] = interval_hours
    user["meal_times"] = [first_time]   # время первого приёма
    user["meal_names"] = []
    user["meals_eaten_today"] = []
    save_user(user_id, user)

def mark_meal_eaten(user_id: int, meal_index: int) -> dict:
    """Отметить приём пищи как выполненный."""
    user = get_user(user_id)
    today = str(date.today())
    if meal_index not in user["meals_eaten_today"]:
        user["meals_eaten_today"].append(meal_index)
    total = len(user["meal_times"])
    eaten = len(user["meals_eaten_today"])
    save_user(user_id, user)
    return {"eaten": eaten, "total": total}

def reset_meals_daily(user_id: int):
    """Сброс еды на новый день + фиксация пропусков."""
    user = get_user(user_id)
    today = str(date.today())
    if user.get("meal_mode") == "fixed":
        total = len(user.get("meal_times", []))
        eaten = len(user.get("meals_eaten_today", []))
        if total > 0 and eaten < total:
            skips = user.get("meal_skips_week", [])
            skips.append(today)
            user["meal_skips_week"] = skips[-7:]
    user["meals_eaten_today"] = []
    save_user(user_id, user)

def get_meal_schedule_text(user: dict) -> str:
    """Сформировать текст расписания питания."""
    mode = user.get("meal_mode")
    if not mode:
        return "❌ График питания не настроен"
    if mode == "fixed":
        times = user.get("meal_times", [])
        names = user.get("meal_names", [])
        eaten = user.get("meals_eaten_today", [])
        lines = []
        for i, t in enumerate(times):
            name = names[i] if i < len(names) else f"Приём {i+1}"
            check = "✅" if i in eaten else "🍽"
            lines.append(f"{check} {t} — {name}")
        return "\n".join(lines) if lines else "Нет приёмов"
    elif mode == "interval":
        hours = user.get("meal_interval_hours", 4)
        first = user.get("meal_times", ["08:00"])[0]
        return f"⏱ Каждые {hours} ч, начиная с {first}"

