import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand
from aiogram.contrib.fsm_storage.memory import MemoryStorage

from app.config_reader import load_config
from app.handlers.common import register_handlers_common
from app.handlers.paint import register_handlers_paint
from app.handlers.style import register_handlers_style


logger = logging.getLogger(__name__)
# register telegram interface commands
async def set_commands(bot: Bot):
    commands = [
        BotCommand(command="/start", description="List of available options"),
        BotCommand(
            command="/reset", description="Reset, if you've uploaded the wrong images"
        ),
        BotCommand(
            command="/paint",
            description="Transfer style of your photo to given painter domain",
        ),
        BotCommand(
            command="/style",
            description="Neural style transfer between two pictures",
        ),
        BotCommand(command="/about", description="If u r a curious one"),
    ]
    await bot.set_my_commands(commands)


async def main():
    # logging to stdout
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    )
    logger.error("Starting bot")

    # parcing the config file
    logger.error("Loading config")
    config = load_config("bot/app/config/bot.ini")
    # initialization of the bot and dispatcher
    bot = Bot(token=config.tg_bot.token)
    dp = Dispatcher(bot, storage=MemoryStorage())

    # handlers registration
    register_handlers_common(dp)
    register_handlers_paint(dp)
    register_handlers_style(dp)
    # set bot's commands
    await set_commands(bot)

    await dp.skip_updates()
    await dp.start_polling()


if __name__ == "__main__":
    asyncio.run(main())
