from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text


async def cmd_start(message: types.Message, state: FSMContext):
    await state.finish()
    await message.answer(
        "Привет, я бот для переноса стиля!\n\
        Могу перенести стиль с одного изображения на другое\
        или изобразить твою картинку в стиле какого-нибудь художника.\n\
        Нажми (/paint) для получения нарисованной картинки\n\
        Нажми (/transfer) для переноса стиля с одной картинки на другую \n\
        Команда /cancel для отмены любого действия",
        reply_markup=types.ReplyKeyboardRemove(),
    )


async def cmd_cancel(message: types.Message, state: FSMContext):
    await state.finish()
    await message.answer("Действие отменено", reply_markup=types.ReplyKeyboardRemove())


def register_handlers_common(dp: Dispatcher):
    dp.register_message_handler(cmd_start, commands="start", state="*")
    dp.register_message_handler(cmd_cancel, commands="cancel", state="*")
    dp.register_message_handler(
        cmd_cancel, Text(equals="отмена", ignore_case=True), state="*"
    )
