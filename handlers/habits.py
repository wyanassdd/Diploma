# handlers/habits.py
import re
from telebot import types
from db import save_habit, init_user, DAYS_OF_WEEK, habit_exists

def register_habit_handlers(bot, _):
    user_states = {}

    @bot.message_handler(func=lambda message: message.text == "➕ Створити звичку")
    def ask_habit_name(message):
        user_id = message.from_user.id
        init_user(user_id)
        user_states[user_id] = {"name": None, "days": [], "reminder": None}
        bot.send_message(message.chat.id, "Введи назву звички:", reply_markup=types.ReplyKeyboardRemove())
        bot.register_next_step_handler(message, process_habit_name)

    def process_habit_name(message):
        user_id = message.from_user.id
        name = message.text.strip()

        if habit_exists(user_id, name):
            bot.send_message(message.chat.id, "⚠️ Така звичка вже існує. Вибери іншу назву.")
            bot.register_next_step_handler(message, process_habit_name)
            return

        user_states[user_id]["name"] = name
        send_days_reply_keyboard(message.chat.id, user_states[user_id]["days"])

    def send_days_reply_keyboard(chat_id, selected_days):
        remaining_days = [d for d in DAYS_OF_WEEK if d not in selected_days]
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        for day in remaining_days:
            markup.add(day)
        if selected_days:
            markup.add("✅ Готово")
        bot.send_message(chat_id, "Обери дні або натисни ✅ Готово:", reply_markup=markup)

    @bot.message_handler(func=lambda message: message.text in DAYS_OF_WEEK or message.text == "✅ Готово")
    def handle_day_reply(message):
        user_id = message.from_user.id
        habit = user_states.get(user_id)
        if not habit:
            bot.send_main_menu(message.chat.id)
            return

        if message.text == "✅ Готово":
            if habit["days"]:
                ask_reminder_yes_no(message)
            else:
                bot.send_message(message.chat.id, "Ти ще не вибрав жодного дня 🙂")
                send_days_reply_keyboard(message.chat.id, habit["days"])
            return
        elif message.text in DAYS_OF_WEEK and message.text not in habit["days"]:
            habit["days"].append(message.text)
            send_days_reply_keyboard(message.chat.id, habit["days"])

    def ask_reminder_yes_no(message):
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        markup.row("Так", "Ні")
        bot.send_message(message.chat.id, "Потрібно нагадування про звичку?", reply_markup=markup)
        bot.register_next_step_handler(message, handle_reminder_answer)

    def handle_reminder_answer(message):
        user_id = message.from_user.id
        if message.text == "Ні":
            save(user_id, message.chat.id)
        elif message.text == "Так":
            bot.send_message(message.chat.id, "Вкажи час у форматі ГГ:ХХ (наприклад, 08:30):")
            bot.register_next_step_handler(message, process_reminder_time)
        else:
            ask_reminder_yes_no(message)

    def process_reminder_time(message):
        user_id = message.from_user.id
        time_text = message.text.strip()
        if re.match(r'^\d{2}:\d{2}$', time_text):
            hours, minutes = map(int, time_text.split(":"))
            if 0 <= hours <= 23 and 0 <= minutes <= 59:
                user_states[user_id]["reminder"] = time_text
                save(user_id, message.chat.id)
                return
        bot.send_message(message.chat.id, "Неправильний формат. Спробуй ще раз (ГГ:ХХ):")
        bot.register_next_step_handler(message, process_reminder_time)

    def save(user_id, chat_id):
        habit = user_states.pop(user_id)
        save_habit(user_id, habit)
        summary = f"Створено звичку: *{habit['name']}*\nДні: {', '.join(habit['days'])}"
        if habit["reminder"]:
            summary += f"\n⏰ Нагадування: {habit['reminder']}"
        summary += f"\n🔄 Статус: очікує⏳"
        bot.send_message(chat_id, summary, parse_mode='Markdown')
        bot.send_main_menu(chat_id)
