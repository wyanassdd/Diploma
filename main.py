# main.py
import os
from dotenv import load_dotenv
import telebot
from threading import Thread
from reminders import reminder_loop
from db import delete_expired_events

# Завантаження змінних із .env
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)

print("Bot is running")

# Імпорт хендлерів
from handlers.start import register_start_handlers
from handlers.tasks import register_task_handlers
from handlers.habits import register_habit_handlers
from handlers.complete import register_complete_handlers
from handlers.delete import register_delete_handlers
from handlers.list import register_list_handlers
from handlers.statistics import register_statistics_handlers
from handlers.help import register_help_handlers
from handlers.fallback import register_fallback_handlers
from handlers.edit import register_edit_handlers

# Меню
from telebot import types

def send_main_menu(chat_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("➕ Створити звичку", "📆 Додати завдання")
    markup.row("📋 Мій список", "📊 Статистика")
    markup.row("✅ Позначити виконане", "❌ Видалити")
    markup.row("✏️ Редагувати", "ℹ️ Допомога")
    bot.send_message(chat_id, "Що бажаєш зробити?", reply_markup=markup)

bot.send_main_menu = send_main_menu

# Реєстрація хендлерів
def register_all_handlers():
    register_start_handlers(bot, None)
    register_task_handlers(bot, None)
    register_habit_handlers(bot, None)
    register_complete_handlers(bot, None)
    register_delete_handlers(bot, None)
    register_list_handlers(bot, None)
    register_statistics_handlers(bot, None)
    register_help_handlers(bot, None)
    register_edit_handlers(bot, None)
    register_fallback_handlers(bot, None)

# Запуск
def start_bot():
    Thread(target=reminder_loop, args=(bot, None), daemon=True).start()
    print("Bot is running")
    bot.polling(none_stop=True)

if __name__ == '__main__':
    delete_expired_events() ######   видалити патом навєрно
    register_all_handlers()
    start_bot()
