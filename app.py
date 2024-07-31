import os
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.filters import Command, BaseFilter
from aiogram.types import TelegramObject, BotCommandScopeAllPrivateChats
import asyncio
from aiogram import Bot, Dispatcher, types, F
import random
import aiosqlite
from aiogram.fsm.strategy import FSMStrategy
from handlers.user_private import user_private_router
from handlers.user_group import user_group_router


ALLOWED_UPDATES = ['message',
                   'edited_message', ]  # Проврка того, что наш бот может обрабатывать, чтобы не приходили лишнии запросы
#
# Bot.my_admin_list = []

dp = Dispatcher(fsm_strategy = FSMStrategy.USER_IN_CHAT)

from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv())

dp.include_router(user_private_router)
dp.include_router(user_group_router)


async def main():
    bot = Bot(token='7193188609:AAHnUahVmZ08SqInsCQR5CyDzu-deOSoRNY')
    await bot.delete_webhook(drop_pending_updates=True)
    await bot.delete_my_commands(scope=types.BotCommandScopeAllPrivateChats())
    await dp.start_polling(bot, allowed_updates=ALLOWED_UPDATES)

if __name__ == '__main__':
    asyncio.run(main())
