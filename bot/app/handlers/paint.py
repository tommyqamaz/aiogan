from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

from io import BytesIO
from PIL import Image

available_paiters_names = ["kekus jopus", "hulio perdulio", "sun' hui'v'chai"]


class PaintParams(StatesGroup):
    painter_selection = State()
    image = State()
    processing = State()


async def gan_start(message: types.Message):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for painter in available_paiters_names:
        keyboard.add(painter)
    await message.answer("Выберете художника из представленных:", reply_markup=keyboard)
    await PaintParams.painter_selection.set()


async def chose_style(message: types.Message, state: FSMContext):
    if message.text.lower() not in available_paiters_names:
        await message.answer(
            "Пожалуйста, выберите художника, стиль которого будет применён к Вашей картинке,\
             используя клавиатуру ниже."
        )
        return
    await state.update_data(chosen_painter=message.text.lower())
    await PaintParams.next()
    await message.answer(
        "Отправьте одну картинку.", reply_markup=types.ReplyKeyboardRemove()
    )


async def get_image(message: types.Message, state: FSMContext):
    data = await state.get_data()
    print(data)
    await message.answer(
        "Стиль этого художника будет применён:", data.get("chosen_painter")
    )
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)

    for c in ["Ok", "/cancel"]:
        keyboard.add(c)

    await message.answer("Начинаем трансформацию?!", reply_markup=keyboard)


async def confirm(message: types.Message, state: FSMContext):
    pass


def register_handlers_paint(dp: Dispatcher):
    dp.register_message_handler(gan_start, commands="paint", state="*")
    dp.register_message_handler(chose_style, state=PaintParams.painter_selection)
    dp.register_message_handler(
        get_image,
        content_types=["photo"],
        state=PaintParams.image,
    )
