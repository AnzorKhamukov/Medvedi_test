from aiogram import Bot, Dispatcher, types
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import ParseMode
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.utils import executor
from aiogram.types import Message
import requests
import os
from dotenv import load_dotenv

load_dotenv()

API_TOKEN = os.getenv('TOKEN')
BACKEND_URL = os.getenv('BACKEND_URL_LOCAL')

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())


class Product_search(StatesGroup):
    nm_id = State()


@dp.message_handler(commands=['start'])
async def sent_welcome(message: types.Message):
    await message.reply("Привет! Введите ID товара.")


@dp.message_handler(commands=['search'])
async def search_product(message: types.Message):
    await Product_search.nm_id.set()
    await message.reply("Введите ID товара")


@dp.message_handler(state=Product_search.nm_id)
async def handle_nm_id(message: types.Message, state: FSMContext):
    cleaned_text = message.text.strip()

    if not cleaned_text.isdigit():
        await message.reply("Введите ID товара числом!")
        return

    try:
        nm_id = int(cleaned_text)
        await state.update_data(nm_id=nm_id)

        response = requests.get(f"{BACKEND_URL}/{nm_id}")
        response.raise_for_status()
        product_data = response.json()

        text = f"""
        Товар: {product_data['nm_id']}
        Цена: {product_data['current_price']}
        Общий остаток: {product_data['sum_quantity']}
        Остатки по размерам:
        {product_data['quantity_by_sizes']}
        """

        if product_data.get('image_url'):
            await message.reply_photo(photo=product_data['image_url'], caption=text)
        else:
            await message.reply(text)

        await state.finish()

    except ValueError:
        await message.reply("Введенный ID товара не является числом!")
    except requests.exceptions.RequestException as e:
        await message.reply(f"Произошла ошибка при запросе данных: {e}")
    except KeyError as e:
        await message.reply(f"Произошла ошибка: {e}")

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
