import os
import gc
import asyncio
import logging
import threading
from io import BytesIO

from painting_mode.test import *

from aiogram.dispatcher import FSMContext
from aiogram.types.message import ContentType
from aiogram import Bot, Dispatcher
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import Message, ChatActions

from app.config_reader import load_config


class GNSTStates(StatesGroup):
    """
    Generative Neural Style Transfer States
    """

    upload_content = State()
    run_gnst = State()


async def cmd_paint(message: Message):
    """
    Enables painting mode
    """
    await message.answer("You've chosen painting 🎨")
    logging.info("Painting — uploading content...")
    await GNSTStates.upload_content.set()
    await message.answer("1️⃣ Upload a content image...")


async def cmd_upload_content(message: Message, state: FSMContext):
    """
    Downloads content image and executes GNST in another thread
    """
    # Check if the message contains a photo
    if not message.photo:
        return await message.reply(
            "Please try again - just send a compressed JPEG or PNG 🖼"
        )
    # Get content path
    content_path = str(message.from_user.id) + "_content.jpg"
    # Download content image
    await message.photo[-1].download(content_path)
    await message.answer("Brilliant! 💎\n")
    # Prepare to run GNST
    logging.info("Painting — running CycleGAN...")
    await GNSTStates.run_gnst.set()
    await message.answer("2️⃣ Be patient — it'll take half a minute at most ⏳")
    # Signal typing
    await ChatActions.typing()
    # Run GNST in a separate thread
    thread = threading.Thread(
        target=lambda message, state, content_path: asyncio.run(
            run_cyclegan(message, state, content_path)
        ),
        args=(message, state, content_path),
    )
    thread.start()


async def run_cyclegan(message: Message, state: FSMContext, content_path):
    """
    Runs Generative Neural Style Transfer with CycleGAN
    """
    # Instantiate GNST class
    gnst = GNST(content_path)
    # Run GNST
    painted_image, time_passed = gnst.transfer_style()
    # Send stylized image
    bytes = BytesIO()
    bytes.name = "painted_image.jpg"
    painted_image.save(bytes, "JPEG")
    bytes.seek(0)
    config = load_config("bot/app/config/bot.ini")
    bot_gnst = Bot(token=config.tg_bot.token)
    await bot_gnst.send_photo(
        message.chat.id,
        photo=bytes,
        caption=f"Stylization took only {time_passed} seconds ⏰",
    )
    await bot_gnst.close()
    # Clear memory storage
    os.remove(content_path)
    del gnst
    gc.collect()
    # End GNST state
    logging.info("Stylization — GNST completed!")
    await state.finish()


def register_handlers_paint(dp: Dispatcher):
    dp.register_message_handler(cmd_paint, commands="paint", state=None)
    dp.register_message_handler(
        cmd_upload_content,
        state=GNSTStates.upload_content,
        content_types=ContentType.ANY,
    )
