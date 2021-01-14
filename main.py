from datetime import datetime, timedelta

import typing
from aiogram import Bot, Dispatcher, executor, types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.handler import CancelHandler
from aiogram.dispatcher.middlewares import BaseMiddleware

API_TOKEN = ''

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)


class AiogramTTLCache:
    def __init__(self, **ttl):
        self.ttl = ttl
        self.cache = {}
        self.default = datetime(2000, 1, 1)

    def get(self, *,
            message: types.Message = None,
            chat: typing.Union[str, int] = None,
            user: typing.Union[str, int] = None):
        if message is not None:
            chat, user = message.chat.id, message.from_user.id
        chat, user = self.check_input(chat=chat, user=user)
        ttl = self.cache.get(chat, {}).get(user, self.default)
        if datetime.now() < ttl:
            return True
        self.cache.get(chat, {}).pop(user, None)
        return False

    def set(self, *,
            message: types.Message = None,
            chat: typing.Union[str, int] = None,
            user: typing.Union[str, int] = None, **ttl):
        if message is not None:
            chat, user = message.chat.id, message.from_user.id
        chat, user = self.check_input(chat=chat, user=user)
        delta_ttl = ttl or self.ttl
        if not delta_ttl:
            raise Exception("where ttl?????")
        time = datetime.now() + timedelta(**delta_ttl)
        self.cache.setdefault(chat, {}).setdefault(user, time)

    def left(self, *,
             message: types.Message = None,
             chat: typing.Union[str, int] = None,
             user: typing.Union[str, int] = None) -> timedelta:
        if message is not None:
            chat, user = message.chat.id, message.from_user.id
        chat, user = self.check_input(chat=chat, user=user)
        if self.get(chat=chat, user=user):
            return self.cache.get(chat).get(user) - datetime.now()
        else:
            return timedelta()

    @staticmethod
    def check_input(chat: typing.Union[str, int], user: typing.Union[str, int]):
        if chat is None and user is None:
            raise ValueError('`user` or `chat` parameter is required but no one is provided!')

        if user is None and chat is not None:
            user = chat
        elif user is not None and chat is None:
            chat = user
        return str(chat), str(user)


cache = AiogramTTLCache(seconds=5)


class ThrottleMiddleware(BaseMiddleware):
    @staticmethod
    async def on_process_message(message: types.Message, data: dict):
        if not cache.get(message=message):
            cache.set(message=message)
            return
        else:
            # cache.set(message, seconds=int(cache.left(message).total_seconds() * 2))
            await message.answer(f"flood control wait {cache.left(message=message)} sec.")
            raise CancelHandler


@dp.message_handler(commands=["start"])
async def photo_with_musk(message: types.Message, state: FSMContext):
    await message.answer(message.text)


if __name__ == '__main__':
    dp.setup_middleware(ThrottleMiddleware())
    executor.start_polling(dp, skip_updates=True)
