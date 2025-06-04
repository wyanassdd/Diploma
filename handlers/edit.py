# handlers/edit.py
import re
from telebot import types
from db import get_user_session, update_habit, update_event

DAYS_OF_WEEK = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Нд"]

user_edit_states = {}

def register_edit_handlers(bot, _):
    @bot.message_handler(func=lambda message: message.text == "✏️ Редагувати")
    def start_edit(message):
        user_id = message.from_user.id
        session = get_user_session(user_id)
        habits = session.get("habits", [])
        events = session.get("events", [])

        if not habits and not events:
            bot.send_message(message.chat.id, "У тебе ще немає що редагувати 📝")
            bot.send_main_menu(message.chat.id)
            return

        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        for habit in habits:
            markup.add(f"[Звичка] {habit['name']}")
        for event in events:
            markup.add(f"[Завдання] {event['name']}")
        markup.add("⬅️ Назад")

        bot.send_message(message.chat.id, "Оберіть, що хочете редагувати:", reply_markup=markup)
        bot.register_next_step_handler(message, process_edit_selection)

    def process_edit_selection(message):
        user_id = message.from_user.id
        text = message.text.strip()

        if text == "⬅️ Назад":
            bot.send_main_menu(message.chat.id)
            return

        if text.startswith("[Звичка] "):
            name = text.replace("[Звичка] ", "")
            user_edit_states[user_id] = {"type": "habit", "name": name}
        elif text.startswith("[Завдання] "):
            name = text.replace("[Завдання] ", "")
            user_edit_states[user_id] = {"type": "event", "name": name}
        else:
            bot.send_message(message.chat.id, "⚠️ Неправильний вибір.")
            bot.send_main_menu(message.chat.id)
            return

        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        markup.add("Назва", "Нагадування")
        if user_edit_states[user_id]["type"] == "habit":
            markup.add("Дні")
        markup.add("⬅️ Назад")

        bot.send_message(message.chat.id, "Що хочете змінити?", reply_markup=markup)
        bot.register_next_step_handler(message, process_edit_field)

    def process_edit_field(message):
        user_id = message.from_user.id
        choice = message.text.strip()

        if choice == "⬅️ Назад":
            bot.send_main_menu(message.chat.id)
            return

        if choice not in ["Назва", "Дні", "Нагадування"]:
            bot.send_message(message.chat.id, "⚠️ Неправильний вибір.")
            bot.send_main_menu(message.chat.id)
            return

        user_edit_states[user_id]["field"] = choice

        if choice == "Назва":
            bot.send_message(message.chat.id, "Введіть нову назву:")
            bot.register_next_step_handler(message, apply_edit)
        elif choice == "Дні":
            user_edit_states[user_id]["days"] = []
            send_days_reply_keyboard(message.chat.id, user_id)
            bot.register_next_step_handler(message, handle_days_selection)
        elif choice == "Нагадування":
            if user_edit_states[user_id]["type"] == "habit":
                bot.send_message(message.chat.id, "Введіть новий час нагадування у форматі ГГ:ХХ (або 'Ні' для відміни):")
            else:
                bot.send_message(message.chat.id, "Введіть нову дату та час нагадування у форматі РРРР-ММ-ДД ГГ:ХХ (або 'Ні' для відміни):")
            bot.register_next_step_handler(message, apply_edit)

    def send_days_reply_keyboard(chat_id, user_id):
        selected_days = user_edit_states[user_id].get("days", [])
        remaining_days = [d for d in DAYS_OF_WEEK if d not in selected_days]
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        for day in remaining_days:
            markup.add(day)
        if selected_days:
            markup.add("✅ Готово")
        markup.add("⬅️ Назад")
        bot.send_message(chat_id, "Оберіть дні або натисніть ✅ Готово:", reply_markup=markup)

    def handle_days_selection(message):
        user_id = message.from_user.id
        state = user_edit_states.get(user_id)
        if not state or state.get("field") != "Дні":
            bot.send_main_menu(message.chat.id)
            return

        if message.text == "⬅️ Назад":
            bot.send_main_menu(message.chat.id)
            user_edit_states.pop(user_id, None)
            return

        if message.text == "✅ Готово":
            days = user_edit_states[user_id]["days"]
            if not days:
                bot.send_message(message.chat.id, "❗ Ви не обрали жодного дня. Оберіть хоча б один.")
                send_days_reply_keyboard(message.chat.id, user_id)
                bot.register_next_step_handler(message, handle_days_selection)
                return
            update = {"days": days}
            update_habit(user_id, state["name"], update)
            bot.send_message(message.chat.id, "✅ Дні успішно оновлено!")
            user_edit_states.pop(user_id, None)
            bot.send_main_menu(message.chat.id)
            return

        if message.text in DAYS_OF_WEEK:
            if message.text not in user_edit_states[user_id]["days"]:
                user_edit_states[user_id]["days"].append(message.text)

        send_days_reply_keyboard(message.chat.id, user_id)
        bot.register_next_step_handler(message, handle_days_selection)

    def apply_edit(message):
        user_id = message.from_user.id
        new_value = message.text.strip()
        edit_data = user_edit_states.get(user_id)

        if not edit_data:
            bot.send_main_menu(message.chat.id)
            return

        item_type = edit_data["type"]
        item_name = edit_data["name"]
        field = edit_data["field"]

        if field == "Назва":
            update = {"name": new_value}
        elif field == "Нагадування":
            if new_value.lower() == "ні":
                reminder = None
            else:
                if item_type == "habit":
                    if not re.match(r'^\d{2}:\d{2}$', new_value):
                        bot.send_message(message.chat.id, "⚠️ Невірний формат часу. Спробуйте ще раз.")
                        bot.register_next_step_handler(message, apply_edit)
                        return
                    reminder = new_value
                else:
                    try:
                        from datetime import datetime
                        reminder = datetime.strptime(new_value, "%Y-%m-%d %H:%M")
                    except ValueError:
                        bot.send_message(message.chat.id, "⚠️ Невірний формат дати/часу. Спробуйте ще раз.")
                        bot.register_next_step_handler(message, apply_edit)
                        return
            update = {"reminder": reminder}

        if item_type == "habit":
            update_habit(user_id, item_name, update)
        else:
            update_event(user_id, item_name, update)

        bot.send_message(message.chat.id, "✅ Оновлено успішно!")
        user_edit_states.pop(user_id, None)
        bot.send_main_menu(message.chat.id)
