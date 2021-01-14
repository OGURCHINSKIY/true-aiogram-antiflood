from datetime import datetime, timedelta
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

    @singledispatchmethod
    def get(self, chat: typing.Union[str, int, None] = None, user: typing.Union[str, int, None] = None):
        ttl = self.cache.get(chat, {}).get(user, self.default)
        if datetime.now() < ttl:
            return True
        self.cache.get(chat, {}).pop(user, None)
        return False

    @get.register
    def get(self, message: types.Message):
        return self.get(message.chat.id, message.from_user.id)

    def set(self, message: types.Message, **ttl):
        delta_ttl = ttl or self.ttl
        if not delta_ttl:
            raise Exception("where ttl?????")
        time = datetime.now() + timedelta(**delta_ttl)
        self.cache.setdefault(message.chat.id, {})[message.from_user.id] = time

    def left(self, message: types.Message) -> timedelta:
        if self.get(message):
            return self.cache.get(message.chat.id).get(message.from_user.id) - datetime.now()
        else:
            return timedelta()


cache = AiogramTTLCache(seconds=5)


class ThrottleMiddleware(BaseMiddleware):
    async def on_process_message(self, message: types.Message, data: dict):
        if not cache.get(message):
            cache.set(message)
            return
        else:
            #cache.set(message, seconds=int(cache.left(message).total_seconds() * 2))
            await message.answer(f"flood control wait {cache.left(message)} sec.")
            raise CancelHandler


@dp.message_handler(commands=["start"])
async def photo_with_musk(message: types.Message, state: FSMContext):
    await message.answer(message.text)

if __name__ == '__main__':
    dp.setup_middleware(ThrottleMiddleware())
    executor.start_polling(dp, skip_updates=True)
