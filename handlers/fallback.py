# handlers/fallback.py
from db import get_user_session


def register_fallback_handlers(bot, user_sessions):
    @bot.message_handler(func=lambda message: True)
    def fallback(message):
        user_id = message.from_user.id
        session = get_user_session(user_id)

        # Не реагувати, якщо користувач у процесі створення звички
        if "new_habit" in session:
            return

        bot.send_main_menu(message.chat.id)