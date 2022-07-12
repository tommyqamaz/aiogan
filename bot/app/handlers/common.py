import os
import logging


from aiogram.dispatcher import FSMContext
from aiogram import Dispatcher

from aiogram.types import Message, ReplyKeyboardRemove


async def cmd_start(message: Message):
    """
    Shows the list of available commands
    """
    logging.info("cmd_start")
    await message.answer(
        "/start — View the list of available options\n"
        "/reset — Reset option\n"
        "/style — Allows you to take an image and reproduce it with a new artistic style.\n"
        "/paint — Style transfer (CycleGAN) \n"
        "/about — Information about project\n"
        "/cancel — Cancel current action"
    )


async def cmd_reset(message: Message, state: FSMContext):
    """
    Allows to reset bot state
    """
    logging.info("cmd_reset")
    await state.finish()
    for image_file in os.listdir():
        if image_file.endswith(".jpg"):
            os.remove(image_file)
    await message.answer("No problem! Try again!")


async def cmd_about(message: Message):
    """
    Shows bot info
    """
    logging.info("cmd_about")
    await message.answer("Author: @qamaz\n")


async def cmd_cancel(message: Message, state: FSMContext):
    logging.info("cmd_cancel")
    await state.finish()
    await message.answer("Action is cancelled", reply_markup=ReplyKeyboardRemove())


def register_handlers_common(dp: Dispatcher):
    dp.register_message_handler(cmd_start, commands=["start", "info"], state="*")
    dp.register_message_handler(cmd_cancel, commands="cancel", state="*")
    dp.register_message_handler(cmd_reset, commands="reset", state="*")
    dp.register_message_handler(cmd_about, commands="about", state="*")
