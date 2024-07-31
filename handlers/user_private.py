import requests
from aiogram import Bot, types, F, Router
from aiogram.filters import CommandStart, Command, or_f, StateFilter
from filters.chat_types import ChatTypeFilter
from keyboads import reply
from weather import get_weather
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from datetime import datetime, timedelta
import asyncio
import pytz

user_private_router = Router()
user_private_router.message.filter(ChatTypeFilter(['private']))

class WeatherInfo(StatesGroup):
    city = State()
    question = State()
    time = State()
    change_time = State()

# Хранение задач уведомлений для каждого пользователя
user_tasks = {}

@user_private_router.message(CommandStart())
async def start_command(message: types.Message) -> None:
    await message.answer(f"Привет, {message.from_user.first_name}!", reply_markup=reply.start_kb)

@user_private_router.message(StateFilter(None), or_f(Command("/weather"), (F.text.lower() == "погода")))
async def weather(message: types.Message, state: FSMContext) -> None:
    await message.answer("Укажите город", reply_markup=types.ReplyKeyboardRemove())
    await state.set_state(WeatherInfo.city)

@user_private_router.message(WeatherInfo.city, F.text)
async def handle_city(message: types.Message, state: FSMContext) -> None:
    await state.update_data(city=message.text)
    await message.answer('Вы хотите каждый день получать уведомления о погоде? (да/нет)')
    await state.set_state(WeatherInfo.question)

@user_private_router.message(WeatherInfo.question, F.text.lower().in_(['да', 'нет']))
async def handle_question(message: types.Message, state: FSMContext) -> None:
    data = await state.get_data()
    city = data.get('city', '')

    if message.text.lower() == 'да':
        await message.answer('Введите время для получения уведомлений о погоде (в формате ЧЧ:ММ):')
        await state.set_state(WeatherInfo.time)
    elif message.text.lower() == 'нет':
        weather_data = await get_weather(city)
        if weather_data is None:
            await message.answer('Не удалось получить данные о погоде. Пожалуйста, проверьте название города и введите заново.')

            await state.set_state(WeatherInfo.city)  # Устанавливаем состояние для повторного ввода города
        else:
            await message.answer(f'Погода на данный момент в {city.capitalize()}:\n'
                                 f'{weather_data[0]}\n'
                                 f'{weather_data[1]}\n')
            await state.clear()  # Очищаем состояние после успешного получения данных
    else:
        await message.answer('Ответ должен быть "да" или "нет".')
        await WeatherInfo.question.set()

@user_private_router.message(WeatherInfo.time, F.text)
async def handle_time(message: types.Message, state: FSMContext) -> None:
    notify_time = message.text
    data = await state.get_data()
    city = data.get('city', '')

    # Запускаем фоновую задачу для отправки уведомлений
    task = asyncio.create_task(schedule_weather_notifications(message.bot, message.from_user.id, city, notify_time))

    # Сохраняем задачу в словаре
    user_tasks[message.from_user.id] = task

    await message.answer(f'Вы будете получать уведомления о погоде в {notify_time}.')

    # Сохраняем данные в состоянии
    await state.update_data(notify_time=notify_time)

    # Очищаем состояние, чтобы предотвратить конфликт с другими хэндлерами
    await state.set_state(None)  # Устанавливаем состояние в None

@user_private_router.message(StateFilter(None), or_f(Command("/change_time"), F.text.lower() == 'изменить время уведомлений'))
async def change_time_command(message: types.Message, state: FSMContext) -> None:
    data = await state.get_data()
    if 'notify_time' in data:
        # Останавливаем предыдущую задачу
        if message.from_user.id in user_tasks:
            user_tasks[message.from_user.id].cancel()
            del user_tasks[message.from_user.id]

        await message.answer("Введите новое время для получения уведомлений о погоде (в формате ЧЧ:ММ):",
                             reply_markup=types.ReplyKeyboardRemove())
        await state.set_state(WeatherInfo.change_time)
    else:
        await message.answer("Сначала установите время уведомлений.")

@user_private_router.message(WeatherInfo.change_time, F.text)
async def handle_change_time(message: types.Message, state: FSMContext) -> None:
    new_notify_time = message.text
    data = await state.get_data()
    city = data.get('city', '')

    # Проверка на корректность формата времени
    try:
        notify_hour, notify_minute = map(int, new_notify_time.split(':'))
        # Запускаем новую задачу для отправки уведомлений с новым временем
        task = asyncio.create_task(
            schedule_weather_notifications(message.bot, message.from_user.id, city, new_notify_time))

        # Сохраняем новую задачу в словаре
        user_tasks[message.from_user.id] = task

        await message.answer(f'Время уведомлений изменено на {new_notify_time}.')
        await state.update_data(notify_time=new_notify_time)
    except ValueError:
        await message.answer("Некорректный формат времени. Пожалуйста, введите время в формате ЧЧ:ММ.")

async def schedule_weather_notifications(bot: Bot, chat_id: int, city: str, notify_time: str):
    while True:
        now = datetime.now(tz=pytz.timezone('Europe/Moscow'))
        try:
            notify_hour, notify_minute = map(int, notify_time.split(':'))
        except ValueError:
            # Если notify_time некорректно, выходим из цикла
            break

        # Создаем объект времени для уведомления на сегодня
        notification_time = now.replace(hour=notify_hour, minute=notify_minute, second=0, microsecond=0)

        # Если время уведомления уже прошло, устанавливаем на завтра
        if now > notification_time:
            notification_time += timedelta(days=1)

        # Ожидаем до времени уведомления
        await asyncio.sleep((notification_time - now).total_seconds())

        # Получаем погоду и отправляем уведомление
        weather_data = await get_weather(city)
        await bot.send_message(chat_id, f'Погода на данный момент в {city.capitalize()}:\n'
                                        f'{weather_data[0]}\n'
                                        f'{weather_data[1]}\n')
