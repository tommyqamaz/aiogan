import os
import logging


from aiogram.dispatcher import FSMContext
from aiogram import Dispatcher

from aiogram.types import Message, ReplyKeyboardRemove


async def cmd_start(message: Message):
    """
    Shows the list of available commands
    """
    logging.info("Helping...cmd_start")
    await message.answer(
        "/start — View the list of available options ❓\n"
        "/reset — Reset, if you've uploaded the wrong images 🔄\n"
        "/style — Select a style to transfer onto your image 🌈\n"
        "/paint — Upload your image to turn it into a painting 🎨\n"
        "/about — Check out the source code, if you're curious 🤓\n"
        "/cancel — CANCEL!!! fuck off"
    )


async def cmd_reset(message: Message, state: FSMContext):
    """
    Allows to reset bot state
    """
    logging.info("Resetting...cmd_reset")
    await state.finish()
    for image_file in os.listdir():
        if image_file.endswith(".jpg"):
            os.remove(image_file)
    await message.answer("Changed your mind? Alright, let's start over 🙄")


async def cmd_about(message: Message):
    """
    Shows bot info
    """
    logging.info("About...cmd_about")
    await message.answer("Author: @qamaz\n")


async def cmd_cancel(message: Message, state: FSMContext):
    logging.info("Cancelled...cmd_cancel")
    await state.finish()
    await message.answer("Action is cancelled", reply_markup=ReplyKeyboardRemove())


def register_handlers_common(dp: Dispatcher):
    dp.register_message_handler(cmd_start, commands=["start", "info"], state="*")
    dp.register_message_handler(cmd_cancel, commands="cancel", state="*")
    dp.register_message_handler(cmd_reset, commands="reset", state="*")
    dp.register_message_handler(cmd_about, commands="about", state="*")
