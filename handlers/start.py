# handlers/start.py
from telebot import types
from db import get_user_session

def register_start_handlers(bot, user_sessions):
    @bot.message_handler(commands=['start'])
    def start(message):
        user_id = message.from_user.id
        get_user_session(user_id)  # Ініціалізуємо сесію
        send_main_menu(message.chat.id)

    def send_main_menu(chat_id):
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.row("➕ Створити звичку", "📆 Додати завдання")
        markup.row("📋 Мій список", "📊 Статистика")
        markup.row("✅ Позначити виконане", "❌ Видалити")
        # markup.row("ℹ️ Допомога")
        markup.row("✏️ Редагувати", "ℹ️ Допомога")
        bot.send_message(chat_id, "Що бажаєш зробити?", reply_markup=markup)

    bot.send_main_menu = send_main_menu