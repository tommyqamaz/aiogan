import aiogram.utils.markdown as md
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import ParseMode
from aiogram.utils import executor

from io import BytesIO
from PIL import Image

import asyncio
import concurrent.futures
from functools import partial


import sys
sys.path.insert(0, "./gan_model")
sys.path.insert(0, "./nst_model")
from nst import NST
from gan import GAN

API_TOKEN = None
with open(".env", "r") as dotenvfile:
    API_TOKEN = dotenvfile.read().split('"')[1]

loop = asyncio.get_event_loop()
bot = Bot(token=API_TOKEN, loop=loop)

storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

valid_model_names = ["NST", "GAN"]


class Form(StatesGroup):
    choose_model = State()
    send_content = State()
    send_style = State()


@dp.message_handler(commands="start")
async def start(message: types.Message):
    """
    Conversation's entry point
    """
    # Set state
    await Form.choose_model.set()
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add(*valid_model_names)
    await message.reply("Hi! Choose a model!", reply_markup=markup)


@dp.message_handler(state="*", commands="cancel")
@dp.message_handler(Text(equals="cancel", ignore_case=True), state="*")
async def cancel(message: types.Message, state: FSMContext):
    """
    Allow user to cancel any action
    """
    current_state = await state.get_state()
    if current_state is None:
        return
    # Cancel state and inform user about it
    await state.finish()
    # And remove keyboard (just in case)
    await message.reply("Cancelled.", reply_markup=types.ReplyKeyboardRemove())


@dp.message_handler(
    lambda message: message.text not in valid_model_names, state=Form.choose_model
)
async def invalid_choose_model(message: types.Message, state: FSMContext):
    return await message.reply("Incorrect model name, try again.")


@dp.message_handler(state=Form.choose_model)
async def choose_model(message: types.Message, state: FSMContext):
    await Form.next()
    await state.update_data(requested_model=message.text)
    await message.reply("Send the content picture.")


@dp.message_handler(state=Form.send_content, content_types=["photo"])
async def send_content(message: types.Message, state: FSMContext):
    content_bytes = await bot.download_file_by_id(message.photo[-1].file_id)
    content_bytes.seek(0)
    content_image = Image.open(content_bytes)
    await state.update_data(content_image=content_image)
    async with state.proxy() as data:
        if data["requested_model"] == "GAN":
            
            await message.reply("GAN is running, please be patient.")
            print('someone has started GAN')
            async with state.proxy() as data:
                
                GAN_partial = partial(
                    GAN,
                    input_image=data["content_image"],
                    max_size=256
                )
                
                with concurrent.futures.ThreadPoolExecutor() as pool:
                    result_image = await loop.run_in_executor(pool, GAN_partial)
            result_bytes = BytesIO()
            result_image.save(result_bytes, format="PNG")
            # send the result
            result_bytes.seek(0)
            result_message = await message.reply_photo(result_bytes)
            await Form.choose_model.set()
            await result_message.reply("I hope you liked it.")


        elif data["requested_model"] == "NST":
            await Form.send_style.set()
            await message.reply("Send the style picture.")
    # await message.reply_photo(message.photo[-1].file_id)
    # await bot.send_photo(message.chat.id, bytes)

@dp.message_handler(state=Form.send_style, content_types=["photo"])
async def send_style(message: types.Message, state: FSMContext):

    # download the style photo and save it to state
    style_bytes = await bot.download_file_by_id(message.photo[-1].file_id)
    style_bytes.seek(0)
    style_image = Image.open(style_bytes)
    await state.update_data(style_image=style_image)

    # send the message to notify user that NST has started
    header = "NST is running, please be patient."
    progress_message = await message.reply(header)
    print('someone has started NST')
    # run NST and save result to bytes; update the progress_message to show progress bar
    async with state.proxy() as data:
        
        NST_partial = partial(
            NST,
            content=data["content_image"],
            style=data["style_image"],
            num_epochs=2000,
            max_size=256
        )
        
        with concurrent.futures.ThreadPoolExecutor() as pool:
            result_image = await loop.run_in_executor(pool, NST_partial)
    result_bytes = BytesIO()
    result_image.save(result_bytes, format="PNG")

    # send the result
    result_bytes.seek(0)
    result_message = await message.reply_photo(result_bytes)

    await Form.choose_model.set()
    await result_message.reply("I hope you liked it.")


import time

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)