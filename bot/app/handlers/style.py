import os
import gc
import asyncio
import logging
import threading
from io import BytesIO

from stylization_mode.test import *
from stylization_mode.style_menu import *

from aiogram.dispatcher import FSMContext
from aiogram.types.message import ContentType
from aiogram import Bot, Dispatcher
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import Message, ChatActions, CallbackQuery, InputMediaPhoto

from app.config_reader import load_config

"""author: https://github.com/tensorush"""


class FNSTStates(StatesGroup):
    """
    Fast Neural Style Transfer States
    """

    style_menu = State()
    upload_content = State()
    run_fnst = State()


async def cmd_style(message: Message, state: FSMContext):
    """
    Enables style mode
    """
    await message.answer("You've chosen stylization")

    logging.info("Stylization — selecting style...")

    await FNSTStates.style_menu.set()
    async with state.proxy() as data:
        data["style_path"] = "bot/stylization_mode/style_images/oil_painting.jpg"
        await message.answer_photo(
            open(data["style_path"], "rb"),
            caption="1️⃣ Select one of 21 styles...",
            reply_markup=select_style_1,
        )


# @dp.callback_query_handler(select_style_callback.filter(), state=FNSTStates.style_menu)
async def select_style(call: CallbackQuery, callback_data: dict, state: FSMContext):
    """
    Navigates the 21 style options
    """
    name = callback_data.get("name")
    await call.message.edit_media(
        InputMediaPhoto(open(f"bot/stylization_mode/style_images/{name}.jpg", "rb")),
        reply_markup=style_menu[name],
    )
    async with state.proxy() as data:
        data["style_path"] = f"bot/stylization_mode/style_images/{name}.jpg"


async def ignore_style(call: CallbackQuery):
    """
    Ignores button input for the selected style
    """
    logging.info("Style ignored...")

    await call.answer()


async def accept_style(call: CallbackQuery):
    """
    Accepts the chosen style
    """
    await call.answer()
    await call.message.answer("OMG")

    logging.info("Stylization — uploading content...")

    await FNSTStates.upload_content.set()
    await call.message.answer("Upload a content image...")


async def upload_content(message: Message, state: FSMContext):
    """
    Downloads content image and executes FNST in another thread
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
    await message.answer("Nice pic! \n")
    # Prepare to run FNST

    logging.info("Stylization — running FNST...")

    await FNSTStates.run_fnst.set()
    await message.answer("Be patient — wait a second or maybe more...")
    # Signal typing
    await ChatActions.typing()
    # Get style path
    input_data = await state.get_data()
    style_path = input_data["style_path"]
    # Run FNST in a separate thread
    thread = threading.Thread(
        target=lambda message, state, content_path, style_path: asyncio.run(
            run_fnst(message, state, content_path, style_path)
        ),
        args=(message, state, content_path, style_path),
    )
    thread.start()


async def run_fnst(message: Message, state: FSMContext, content_path, style_path):
    """
    Runs Fast Neural Style Transfer with MSG-Net
    """
    # Instantiate FNST class
    fnst = FNST(content_path, style_path)
    # Run FNST
    stylized_image, time_passed = fnst.transfer_style()
    # Send stylized image
    bytes = BytesIO()
    bytes.name = "stylized_image.jpg"
    stylized_image.save(bytes, "JPEG")
    bytes.seek(0)
    config = load_config("bot/app/config/bot.ini")
    bot_fnst = Bot(token=config.tg_bot.token)
    await bot_fnst.send_photo(
        message.chat.id,
        photo=bytes,
        caption=f"Stylization took only {time_passed} seconds ⏰",
    )
    await bot_fnst.close()
    # Clear memory storage
    os.remove(content_path)
    del fnst
    gc.collect()
    # End FNST state
    logging.info("Stylization — FNST completed!")
    await state.finish()


def register_handlers_style(dp: Dispatcher):
    dp.register_message_handler(cmd_style, commands="style", state=None),
    dp.register_callback_query_handler(
        select_style, select_style_callback.filter(), state=FNSTStates.style_menu
    ),

    dp.register_callback_query_handler(
        ignore_style, text="ignore_style", state=FNSTStates.style_menu
    )
    dp.register_callback_query_handler(
        accept_style, text="accept_style", state=FNSTStates.style_menu
    )
    dp.register_message_handler(
        upload_content, state=FNSTStates.upload_content, content_types=ContentType.ANY
    )
