import os
import gspread
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.types import ParseMode
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from google.oauth2.service_account import Credentials
from aiohttp import web
import logging

# --- Google Sheets Авторизация ---
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
SERVICE_ACCOUNT_FILE = 'credentials.json'  # Файл должен быть в репозитории!
credentials = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
gc = gspread.authorize(credentials)

SPREADSHEET_ID = '1hIxfnL-HlJ097v2zFWhvfsFN-eJ4-tCNwONh8t-HNAA'
SHEET_NAME = 'Лист1'
worksheet = gc.open_by_key(SPREADSHEET_ID).worksheet(SHEET_NAME)

# --- Telegram Bot ---
API_TOKEN = os.environ.get('API_TOKEN')  # Получаем токен из переменной окружения
bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# --- Меню ---
menu_keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
menu_keyboard.add("🔎 Поиск по заявителю", "🔎 Поиск по номеру заявки")

class SearchStates(StatesGroup):
    waiting_for_applicant = State()
    waiting_for_number = State()

def format_request(row):
    return (
        f"Заявка\n"
        f"от {row[0]}\n"
        f"Номер заявки: {row[1]}\n"
        f"Дата подачи заявки: {row[2]}\n"
        f"Дата закрытия заявки: {row[3]}\n"
        f"ФИО исполнителя: {row[4]}\n"
        f"Категория: {row[5]}\n"
        f"Статус: {row[6]}\n"
        f"Описание заявки: {row[8]}\n"
        f"Вложения: {row[9]}"
    )

@dp.message_handler(commands=['start', 'help'])
async def send_welcome(message: types.Message):
    await message.reply("Бот работает! Выберите действие ниже:", reply_markup=menu_keyboard)

@dp.message_handler(lambda m: m.text == "🔎 Поиск по заявителю")
async def search_by_applicant(message: types.Message):
    await message.reply("Введите ФИО заявителя для поиска:", reply_markup=menu_keyboard)
    await SearchStates.waiting_for_applicant.set()

@dp.message_handler(lambda m: m.text == "🔎 Поиск по номеру заявки")
async def search_by_number(message: types.Message):
    await message.reply("Введите номер заявки для поиска:", reply_markup=menu_keyboard)
    await SearchStates.waiting_for_number.set()

@dp.message_handler(state=SearchStates.waiting_for_applicant, content_types=types.ContentTypes.TEXT)
async def process_search_applicant(message: types.Message, state: FSMContext):
    search_text = message.text.strip().lower()
    rows = worksheet.get_all_values()
    found = False
    for row in rows[1:]:
        if search_text in row[0].lower():
            await message.answer(format_request(row), reply_markup=menu_keyboard)
            found = True
    if not found:
        await message.reply("Заявки не найдены.", reply_markup=menu_keyboard)
    await state.finish()

@dp.message_handler(state=SearchStates.waiting_for_number, content_types=types.ContentTypes.TEXT)
async def process_search_number(message: types.Message, state: FSMContext):
    search_num = message.text.strip()
    rows = worksheet.get_all_values()
    found = False
    for row in rows[1:]:
        if row[1] == search_num:
            await message.answer(format_request(row), reply_markup=menu_keyboard)
            found = True
            break
    if not found:
        await message.reply("Заявка с таким номером не найдена.", reply_markup=menu_keyboard)
    await state.finish()

@dp.message_handler()
async def write_to_sheet(message: types.Message):
    try:
        worksheet.append_row([str(message.from_user.full_name), '', '', '', '', '', '', '', message.text, ''])
        await message.reply("Сообщение записано в Google Sheets!", reply_markup=menu_keyboard)
    except Exception as e:
        await message.reply(f"Ошибка при записи в Google Sheets: {e}", reply_markup=menu_keyboard)

# --- Webhook настройки ---

async def on_start(request):
    return web.Response(text="Bot is working")

async def on_get_updates(request):
    # Ваш код обработки обновлений здесь
    return web.Response(status=200)

# Устанавливаем webhook URL
webhook_url = 'https://<your-domain>/webhook'  # Замените на ваш URL

# Подключаем webhook
app = web.Application()
app.router.add_post('/webhook', on_get_updates)

# Запуск веб-сервера
if __name__ == '__main__':
    # Ставим webhook для Telegram
    bot.set_webhook(webhook_url)

    # Запускаем сервер
    web.run_app(app, host='0.0.0.0', port=8080)  # на порт 8080 (или другой, если нужно)

    # Если вы хотите использовать polling (не рекомендую для продакшн):
    # executor.start_polling(dp, skip_updates=True)
