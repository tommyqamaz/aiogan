import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand
from aiogram.contrib.fsm_storage.memory import MemoryStorage

from app.config_reader import load_config
from app.handlers.common import register_handlers_common
from app.handlers.paint import register_handlers_paint

logger = logging.getLogger(__name__)
# Регистрация команд, отображаемых в интерфейсе Telegram
async def set_commands(bot: Bot):
    commands = [
        BotCommand(command="/cancel", description="Отменить текущее действие"),
        BotCommand(command="/info", description="Информация о боте и технологиях"),
        BotCommand(
            command="/paint", description="Преобразование картинки в стиле художника"
        ),
        BotCommand(
            command="/transfer", description="Перенести стиль одной картинки на другую"
        ),
    ]
    await bot.set_my_commands(commands)


async def main():
    # Настройка логирования в stdout
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    )
    logger.error("Starting bot")

    # Парсинг файла конфигурации
    config = load_config("bot/app/config/bot.ini")

    # Объявление и инициализация объектов бота и диспетчера
    bot = Bot(token=config.tg_bot.token)
    dp = Dispatcher(bot, storage=MemoryStorage())

    # Регистрация хэндлеров
    register_handlers_common(dp)
    register_handlers_paint(dp)
    # Установка команд бота
    await set_commands(bot)

    # пропуск накопившихся апдейтов (необязательно)
    await dp.skip_updates()
    # Запуск поллинга
    await dp.start_polling()


if __name__ == "__main__":
    asyncio.run(main())
