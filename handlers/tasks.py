# handlers/tasks.py
from datetime import datetime
from telebot import types
from db import save_event, init_user, event_exists
from google_calendar import add_event_to_calendar


def register_task_handlers(bot, _):
    user_states = {}

    @bot.message_handler(func=lambda message: message.text == "📆 Додати завдання")
    def add_task_start(message):
        user_id = message.from_user.id
        init_user(user_id)
        bot.send_message(message.chat.id, "Введи назву завдання:")
        bot.register_next_step_handler(message, process_task_name)

    def process_task_name(message):
        user_id = message.from_user.id
        name = message.text.strip()
        
        if event_exists(user_id, name):
            bot.send_message(message.chat.id, "⚠️ Таке завдання вже існує. Вибери іншу назву.")
            bot.register_next_step_handler(message, process_task_name)
            return

        user_states[user_id] = {"name": name}
        bot.send_message(message.chat.id, "Введи дедлайн у форматі РРРР-ММ-ДД ГГ:ХХ")
        bot.register_next_step_handler(message, process_task_deadline)
        
    def process_task_deadline(message):
        user_id = message.from_user.id
        try:
            deadline = datetime.strptime(message.text.strip(), "%Y-%m-%d %H:%M")
            if deadline < datetime.now():
                bot.send_message(message.chat.id, "⛔ Дата/час дедлайну не може бути в минулому. Спробуй ще раз.")
                bot.register_next_step_handler(message, process_task_deadline)
                return
            user_states[user_id]["deadline"] = deadline
            ask_task_reminder(message)
        except ValueError:
            bot.send_message(message.chat.id, "⚠️ Невірний формат. Використай РРРР-ММ-ДД ГГ:ХХ")
            bot.register_next_step_handler(message, process_task_deadline)

    def ask_task_reminder(message):
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        markup.row("Так", "Ні")
        bot.send_message(message.chat.id, "Потрібне нагадування для цього завдання?", reply_markup=markup)
        bot.register_next_step_handler(message, process_task_reminder_choice)

    def process_task_reminder_choice(message):
        user_id = message.from_user.id
        if message.text == "Ні":
            ask_add_to_calendar(message)
        elif message.text == "Так":
            bot.send_message(message.chat.id, "Введи дату та час нагадування у форматі РРРР-ММ-ДД ГГ:ХХ")
            bot.register_next_step_handler(message, process_task_reminder_time)
        else:
            ask_task_reminder(message)

    def process_task_reminder_time(message):
        user_id = message.from_user.id
        try:
            reminder_time = datetime.strptime(message.text.strip(), "%Y-%m-%d %H:%M")
            deadline = user_states[user_id]["deadline"]
            if reminder_time < datetime.now():
                bot.send_message(message.chat.id, "⛔ Нагадування не може бути в минулому. Спробуй ще раз.")
                bot.register_next_step_handler(message, process_task_reminder_time)
                return
            if reminder_time > deadline:
                bot.send_message(message.chat.id, "⛔ Нагадування не може бути пізніше дедлайну. Спробуй ще раз.")
                bot.register_next_step_handler(message, process_task_reminder_time)
                return
            user_states[user_id]["reminder"] = reminder_time
            ask_add_to_calendar(message)
        except ValueError:
            bot.send_message(message.chat.id, "⚠️ Невірний формат. Використай РРРР-ММ-ДД ГГ:ХХ")
            bot.register_next_step_handler(message, process_task_reminder_time)

    def ask_add_to_calendar(message):
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        markup.row("Так", "Ні")
        bot.send_message(message.chat.id, "Додати завдання до Google Calendar?", reply_markup=markup)
        bot.register_next_step_handler(message, process_add_to_calendar)

    def process_add_to_calendar(message):
        user_id = message.from_user.id
        choice = message.text.strip().lower()
        if choice == "так":
            user_states[user_id]["add_to_calendar"] = True
        else:
            user_states[user_id]["add_to_calendar"] = False
        save(user_id, message.chat.id)

    def save(user_id, chat_id):
        event = user_states.pop(user_id)
        event["status"] = "очікує"
        event["reminded"] = False
        save_event(user_id, event)

        from google_calendar import add_event_to_calendar
        from datetime import timedelta

        if event.get("add_to_calendar"):
            try:
                event_link = add_event_to_calendar(
                    user_id, 
                    summary=event["name"],
                    description="Завдання з Telegram-бота @Rhythm_of_lifeBot",
                    start_time=event["deadline"] - timedelta(minutes=60),
                    end_time=event["deadline"]
                )
                bot.send_message(chat_id, f"📅 Подія додана в Google Calendar: {event_link}")
            except Exception as e:
                bot.send_message(chat_id, f"⚠️ Не вдалося додати подію в Google Calendar: {e}")

        deadline_str = event["deadline"].strftime("%Y-%m-%d %H:%M")
        summary = f"Створено завдання: *{event['name']}*\n📅 Дедлайн: {deadline_str}"
        if "reminder" in event:
            reminder_str = event["reminder"].strftime("%Y-%m-%d %H:%M")
            summary += f"\n⏰ Нагадування: {reminder_str}"
        summary += f"\n🔄 Статус: {event['status']}"

        bot.send_message(chat_id, summary, parse_mode='Markdown')
        bot.send_main_menu(chat_id)
