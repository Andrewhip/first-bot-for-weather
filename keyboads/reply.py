from aiogram.types import KeyboardButtonPollType, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.utils.keyboard import ReplyKeyboardBuilder


start_kb = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="Погода"),
            KeyboardButton(text="Изменить время уведомлений"),
        ],
    ],
    resize_keyboard=True,
    input_field_placeholder='Что Вас интересует?'
)

del_kbd = ReplyKeyboardRemove() #Для удаления клавиатуры после нажатия кнопки


