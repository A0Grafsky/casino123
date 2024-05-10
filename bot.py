import asyncio
import logging

from aiogram import Bot, Dispatcher
from config_data.config import Config, load_config
from database import database as db
from keyboards.bot_meny import set_main_meny
from handlers import start_handler, user_handler, other_handler, admin_handler


# Функция реализации БД
async def start_bot(bot: Bot):
    await db.create_users()
    await db.create_admin()
    await db.create_rate_coins()
    await db.create_old_message()
    await db.create_merch()
    await db.crete_quizzes()
    await db.create_task_table()


# Функция конфигурирования и запуска бота
async def main():
    # Конфигурируем логирование
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(filename)s:%(lineno)d #%(levelname)-8s '
               '[%(asctime)s] - %(name)s - %(message)s')

    # Инициализируем логгер
    logger = logging.getLogger(__name__)

    # Выводим в консоль информацию о начале запуска бота
    logger.info('Starting bot')

    # Загружаем конфиг в переменную config
    config: Config = load_config()

    # Инициализируем бот и диспетчер
    bot = Bot(token=config.tg_bot.token,
              parse_mode='HTML')
    dp = Dispatcher()
    # Настраиваем главное меню
    await set_main_meny(bot)

    # Регистрируем роутеры в диспетчере
    dp.include_router(start_handler.router)
    dp.include_router(admin_handler.router)
    dp.include_router(user_handler.router)
    dp.include_router(other_handler.router)

    # Инициализация БД
    dp.startup.register(start_bot)

    # Пропускаем накопившиеся апдейты и запускаем polling
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
