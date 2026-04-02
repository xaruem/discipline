import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from config import BOT_TOKEN
from handlers import start, discipline, goals, challenges, reminders, stats, motivation, meals
from utils.scheduler import start_scheduler

logging.basicConfig(level=logging.INFO)

async def main():
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())

    # Register routers
    dp.include_router(start.router)
    dp.include_router(discipline.router)
    dp.include_router(goals.router)
    dp.include_router(challenges.router)
    dp.include_router(reminders.router)
    dp.include_router(stats.router)
    dp.include_router(motivation.router)
    dp.include_router(meals.router)

    # Start scheduler for reminders
    await start_scheduler(bot)

    print("🤖 Discipline Bot запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
