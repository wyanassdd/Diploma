import time
from datetime import datetime, timedelta
from db import get_all_user_ids, get_user_data, set_task_reminded, DAY_NAME_TO_NUM, delete_expired_events

def reminder_loop(bot, _):
    last_cleanup_date = None

    while True:
        now = datetime.now()

        # Видалення прострочених подій раз на добу
        if last_cleanup_date != now.date():
            delete_expired_events()
            last_cleanup_date = now.date()

        user_ids = get_all_user_ids()
        for user_id in user_ids:
            session = get_user_data(user_id)

            # ===== Нагадування про завдання =====
            for task in session.get("events", []):
                if task.get("reminder") and not task.get("reminded"):
                    if now >= task["reminder"]:
                        try:
                            bot.send_message(user_id, f"⏰ Нагадування про завдання: *{task['name']}*", parse_mode='Markdown')
                            set_task_reminded(user_id, task["name"])
                        except Exception as e:
                            print(f"[ERROR] Нагадування про завдання: {e}")

            # ===== Нагадування про звички =====
            for habit in session.get("habits", []):
                reminder_time_str = habit.get("reminder")
                if reminder_time_str:
                    try:
                        reminder_time = datetime.strptime(reminder_time_str, "%H:%M").time()
                        today_weekday = now.weekday()
                        valid_days = [DAY_NAME_TO_NUM.get(d) for d in habit.get("days", [])]
                        if today_weekday in valid_days:
                            reminder_dt = datetime.combine(now.date(), reminder_time)
                            if reminder_dt <= now <= reminder_dt + timedelta(minutes=1):
                                bot.send_message(user_id, f"🔔 Нагадування про звичку: *{habit['name']}*", parse_mode='Markdown')
                    except Exception as e:
                        print(f"[ERROR] Нагадування про звичку: {e}")

        time.sleep(60)
