# handlers/delete.py
from telebot import types
from db import delete_habit, delete_event, get_user_session

def register_delete_handlers(bot, _):
    @bot.message_handler(func=lambda message: "Видалити" in message.text)
    def start_deletion(message):
        user_id = message.from_user.id
        session = get_user_session(user_id)
        habits = session.get("habits", [])
        events = session.get("events", [])

        if not habits and not events:
            bot.send_message(message.chat.id, "У тебе ще немає що видаляти 🗑")
            bot.send_main_menu(message.chat.id)
            return

        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        for habit in habits:
            markup.add(f"[Звичка] {habit['name']}")
        for event in events:
            markup.add(f"[Завдання] {event['name']}")
        markup.add("⬅️ Назад")

        bot.send_message(message.chat.id, "Оберіть, що хочеш видалити:", reply_markup=markup)
        bot.register_next_step_handler(message, process_deletion)

    def process_deletion(message):
        user_id = message.from_user.id
        text = message.text.strip()

        if text == "⬅️ Назад":
            bot.send_main_menu(message.chat.id)
            return

        deleted = False

        if text.startswith("[Звичка] "):
            name = text.replace("[Звичка] ", "")
            delete_habit(user_id, name)
            deleted = True
        elif text.startswith("[Завдання] "):
            name = text.replace("[Завдання] ", "")
            delete_event(user_id, name)
            deleted = True

        if deleted:
            bot.send_message(message.chat.id, "🗑 Успішно видалено!")
        else:
            bot.send_message(message.chat.id, "⚠️ Не вдалося знайти для видалення.")

        bot.send_main_menu(message.chat.id)
