import psycopg2
from datetime import datetime
import os
from dotenv import load_dotenv

DAYS_OF_WEEK = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Нд"]
DAY_NAME_TO_NUM = {"Пн": 0, "Вт": 1, "Ср": 2, "Чт": 3, "Пт": 4, "Сб": 5, "Нд": 6}

load_dotenv()

DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")

def get_user_session(user_id):
    init_user(user_id)
    return get_user_data(user_id)

def get_connection():
    return psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST
    )

def init_user(user_id):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("INSERT INTO users (id) VALUES (%s) ON CONFLICT DO NOTHING;", (user_id,))
            conn.commit()

def get_user_data(user_id):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT name, days, reminder, status FROM habits WHERE user_id = %s", (user_id,))
            habits = [
                {
                    "name": row[0],
                    "days": row[1],
                    "reminder": row[2].strftime("%H:%M") if row[2] else None,
                    "status": row[3]
                }
                for row in cur.fetchall()
            ]

            cur.execute("SELECT name, deadline, reminder, status, reminded FROM events WHERE user_id = %s", (user_id,))
            events = [
                {
                    "name": row[0],
                    "deadline": row[1],
                    "reminder": row[2],
                    "status": row[3],
                    "reminded": row[4]
                }
                for row in cur.fetchall()
            ]

            return {"habits": habits, "events": events}

def habit_exists(user_id, name):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM habits WHERE user_id = %s AND name = %s", (user_id, name))
            return cur.fetchone() is not None

def event_exists(user_id, name):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM events WHERE user_id = %s AND name = %s", (user_id, name))
            return cur.fetchone() is not None

def save_habit(user_id, habit):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO habits (user_id, name, days, reminder, status)
                VALUES (%s, %s, %s, %s, %s)
            """, (
                user_id,
                habit["name"],
                habit["days"],
                habit.get("reminder"),
                habit.get("status", "очікує")
            ))
            conn.commit()

def save_event(user_id, event):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO events (user_id, name, deadline, reminder, status, reminded)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                user_id,
                event["name"],
                event["deadline"],
                event.get("reminder"),
                event.get("status", "очікує"),
                event.get("reminded", False)
            ))
            conn.commit()

def mark_habit_completed(user_id, name):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE habits SET status = 'виконано'
                WHERE user_id = %s AND name = %s
            """, (user_id, name))
            conn.commit()

def mark_event_completed(user_id, name):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE events SET status = 'виконано'
                WHERE user_id = %s AND name = %s
            """, (user_id, name))
            conn.commit()

def delete_habit(user_id, name):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM habits WHERE user_id = %s AND name = %s", (user_id, name))
            conn.commit()

def delete_event(user_id, name):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM events WHERE user_id = %s AND name = %s", (user_id, name))
            conn.commit()

def get_all_user_ids():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM users")
            return [row[0] for row in cur.fetchall()]

def set_task_reminded(user_id, name):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE events SET reminded = TRUE
                WHERE user_id = %s AND name = %s
            """, (user_id, name))
            conn.commit()

def update_habit(user_id, old_name, updates):
    set_clauses = []
    values = []
    for key, value in updates.items():
        set_clauses.append(f"{key} = %s")
        values.append(value)
    set_clause = ", ".join(set_clauses)
    values.extend([user_id, old_name])

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(f"""
                UPDATE habits
                SET {set_clause}
                WHERE user_id = %s AND name = %s
            """, tuple(values))
            conn.commit()

def update_event(user_id, old_name, updates):
    set_clauses = []
    values = []
    for key, value in updates.items():
        set_clauses.append(f"{key} = %s")
        values.append(value)
    set_clause = ", ".join(set_clauses)
    values.extend([user_id, old_name])

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(f"""
                UPDATE events
                SET {set_clause}
                WHERE user_id = %s AND name = %s
            """, tuple(values))
            conn.commit()

def delete_expired_events():
    from datetime import datetime
    now = datetime.now()
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM events WHERE deadline < %s", (now,))
            conn.commit()
