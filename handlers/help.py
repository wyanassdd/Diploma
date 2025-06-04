# handlers/help.py

def register_help_handlers(bot, user_sessions):
    @bot.message_handler(func=lambda message: "Допомога" in message.text)
    def show_help(message):
        text = (
            "ℹ️ *Допомога з використанням бота:*\n"
            "• ➕ Створити звичку — додай регулярну дію з днями та нагадуванням\n"
            "• 📆 Додати завдання — одноразова подія з дедлайном\n"
            "• 📋 Мій список — переглянь усі свої звички та завдання\n"
            "• ✅ Позначити виконане — відміть, що ти виконав звичку або завдання\n"
            "• 📊 Статистика — переглянь свій прогрес\n"
            "• ❌ Видалити — можеш прибрати звичку або завдання\n"
            # "• ✏️ Редагувати — змінити назву, дні або нагадування для звички чи завдання"
        )
        bot.send_message(message.chat.id, text, parse_mode="Markdown")
        bot.send_main_menu(message.chat.id)
