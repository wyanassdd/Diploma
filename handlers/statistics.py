# handlers/statistics.py
from db import get_user_session
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from io import BytesIO

def register_statistics_handlers(bot, _):
    @bot.message_handler(func=lambda message: "статистика" in message.text.lower())
    def show_statistics(message):
        user_id = message.from_user.id
        session = get_user_session(user_id)
        habits = session.get("habits", [])
        events = session.get("events", [])

        total_habits = len(habits)
        total_events = len(events)
        completed_habits = sum(1 for h in habits if h.get("status") == "виконано")
        completed_events = sum(1 for e in events if e.get("status") == "виконано")

        text = (
            f"📊 *Твоя статистика:*\n"
            f"Звички: {completed_habits} з {total_habits} виконано\n"
            f"Завдання: {completed_events} з {total_events} виконано"
        )
        bot.send_message(message.chat.id, text, parse_mode="Markdown")

        labels = ['Виконано', 'Не виконано']
        colors = ['#76c7c0', '#e0e0e0'] 

        fig, axs = plt.subplots(1, 2, figsize=(12, 6))
        fig.suptitle('Твій прогрес', fontsize=20, fontweight='bold')

        def create_pie(ax, completed, total, title):
            ax.axis('off') 

            if total == 0:
                ax.text(0.5, 0.5, 'Немає даних', ha='center', va='center', fontsize=14, color='grey')
                ax.set_title(title, fontsize=16)
                return

            if completed == 0 or completed == total:
                color = '#76c7c0' if completed == total else '#e0e0e0'
                label = 'Виконано' if completed == total else 'Не виконано'
                percent = 100  
                wedges, texts = ax.pie(
                    [1], colors=[color],
                    startangle=90,
                    wedgeprops={'edgecolor': 'white'}
                )
                ax.text(0, 0.1, label, ha='center', va='center', fontsize=14, color='black')
                ax.text(0, -0.1, f'{percent}%', ha='center', va='center', fontsize=16, color='black')
            else:
                wedges, texts, autotexts = ax.pie(
                    [completed, total - completed],
                    labels=['Виконано', 'Не виконано'],
                    colors=['#76c7c0', '#e0e0e0'],
                    autopct='%1.1f%%',
                    startangle=90,
                    wedgeprops={'edgecolor': 'white'}
                )
                for autotext in autotexts:
                    autotext.set_color('black')
                    autotext.set_fontsize(14)

            ax.set_title(title, fontsize=16)

        create_pie(axs[0], completed_habits, total_habits, 'Звички')
        create_pie(axs[1], completed_events, total_events, 'Завдання')

        plt.tight_layout(rect=[0, 0.03, 1, 0.95])

        buf = BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight')
        buf.seek(0)
        plt.close()

        bot.send_photo(message.chat.id, buf)
        bot.send_main_menu(message.chat.id)
