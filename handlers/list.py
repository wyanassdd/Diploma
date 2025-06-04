# handlers/list.py
from db import get_user_session

def register_list_handlers(bot, _):
    @bot.message_handler(func=lambda message: message.text == "📋 Мій список")
    def show_user_list(message):
        user_id = message.from_user.id
        session = get_user_session(user_id)
        habits = session.get("habits", [])
        events = session.get("events", [])

        status_map = {
            "очікує": "очікує⏳",
            "виконано": "виконано✅"
        }

        if not habits and not events:
            bot.send_message(message.chat.id, "📭 У тебе ще немає звичок чи завдань.\nСпробуй створити одну з них!")
            bot.send_main_menu(message.chat.id)
            return

        if habits:
            bot.send_message(message.chat.id, "📌 *Твої звички:*", parse_mode="Markdown")
            for i, habit in enumerate(habits, 1):
                status = status_map.get(habit.get("status", "очікує"), "очікує⏳")
                text = (
                    f"*{i}. {habit['name']}*\n"
                    f"📆 Дні: {', '.join(habit['days'])}\n"
                    f"⏱ {'Нагадування о ' + habit['reminder'] if habit['reminder'] else 'Без нагадування'}\n"
                    f"🔄 Статус: {status}"
                )
                bot.send_message(message.chat.id, text, parse_mode="Markdown")

        if events:
            bot.send_message(message.chat.id, "📌 *Твої завдання:*", parse_mode="Markdown")
            for i, event in enumerate(events, 1):
                deadline = event["deadline"].strftime("%Y-%m-%d %H:%M")
                reminder = event.get("reminder")
                reminder_str = reminder.strftime("%Y-%m-%d %H:%M") if reminder else "без нагадування"
                status = status_map.get(event.get("status", "очікує"), "очікує⏳")
                text = (
                    f"*{i}. {event['name']}*\n"
                    f"📅 Дедлайн: {deadline}\n"
                    f"⏱ Нагадування: {reminder_str}\n"
                    f"🔄 Статус: {status}"
                )
                bot.send_message(message.chat.id, text, parse_mode="Markdown")

        bot.send_main_menu(message.chat.id)
