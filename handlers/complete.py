# handlers/complete.py
from telebot import types
from db import mark_habit_completed, mark_event_completed, get_user_session, DAYS_OF_WEEK

def register_complete_handlers(bot, _):
    @bot.message_handler(func=lambda message: message.text == "✅ Позначити виконане")
    def mark_completed(message):
        user_id = message.from_user.id
        session = get_user_session(user_id)
        habits = session.get("habits", [])
        events = session.get("events", [])

        if not habits and not events:
            bot.send_message(message.chat.id, "У тебе ще немає жодної звички чи події 🗂")
            bot.send_main_menu(message.chat.id)
            return

        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        for habit in habits:
            if habit.get("status") != "виконано":
                markup.add(f"[Звичка] {habit['name']}")
        for event in events:
            if event.get("status") != "виконано":
                markup.add(f"[Завдання] {event['name']}")
        markup.add("⬅️ Назад")

        bot.send_message(message.chat.id, "Оберіть звичку або подію, яку виконано:", reply_markup=markup)
        bot.register_next_step_handler(message, process_mark_completed)

    def process_mark_completed(message):
        user_id = message.from_user.id
        text = message.text.strip()

        if text == "⬅️ Назад":
            bot.send_main_menu(message.chat.id)
            return

        updated = False

        if text.startswith("[Звичка] "):
            name = text.replace("[Звичка] ", "")
            mark_habit_completed(user_id, name)
            updated = True
        elif text.startswith("[Завдання] "):
            name = text.replace("[Завдання] ", "")
            mark_event_completed(user_id, name)
            updated = True

        if updated:
            bot.send_message(message.chat.id, "✅ Позначено як виконано!")
        else:
            bot.send_message(message.chat.id, "⚠️ Не знайдено відповідного елемента.")

        bot.send_main_menu(message.chat.id)
