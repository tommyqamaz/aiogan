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
from aiogram.types import Message, ChatActions, ReplyKeyboardMarkup, ReplyKeyboardRemove

from app.config_reader import load_config


available_artists = ["van Gogh", "Cezanne", "Hulio Perdulio"]


class GNSTStates(StatesGroup):
    """
    Generative Neural Style Transfer States
    """

    choose_painter = State()
    upload_content = State()
    run_gnst = State()


async def cmd_paint(message: Message):
    """
    Enables painting mode
    """
    await message.answer(":)")
    logging.info("cmd_paint")
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    for painter in available_artists:
        keyboard.add(painter)
    await message.answer("Choose a painter for style transfer:", reply_markup=keyboard)
    await GNSTStates.choose_painter.set()


async def cmd_choose_painter(message: Message, state: FSMContext):
    """Choose painter for further transfer"""
    if message.text not in available_artists:
        await message.answer("Choose a painter via keyboard below")
    logging.info("cmd_choose_painter")
    await state.update_data(choose_painter=message.text)

    await message.answer(
        "Upload a content image...", reply_markup=ReplyKeyboardRemove()
    )
    await GNSTStates.upload_content.set()


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
    # Prepare to run GNST
    logging.info("Painting — running CycleGAN...")
    await message.answer("Recieved!")
    await GNSTStates.run_gnst.set()
    await message.answer("Wait a bit...")
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
    users_chose = await state.get_data()

    # Instantiate GNST class
    gnst = GNST(content_path, users_chose["choose_painter"])
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
    dp.register_message_handler(cmd_paint, commands="paint", state="*")
    dp.register_message_handler(cmd_choose_painter, state=GNSTStates.choose_painter)
    dp.register_message_handler(
        cmd_upload_content,
        state=GNSTStates.upload_content,
        content_types=ContentType.ANY,
    )
