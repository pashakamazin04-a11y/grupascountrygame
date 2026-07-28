import os
import sqlite3
import telebot

BOT_TOKEN = os.environ.get("TELEGRAM_TOKEN")
if not BOT_TOKEN:
    raise ValueError("Не задан TELEGRAM_TOKEN в переменных окружения!")

bot = telebot.TeleBot(BOT_TOKEN)

OWNER_ID = 6469907589  # Твой реальный ID

def init_db():
    conn = sqlite3.connect("countries.db", check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS countries (
            user_id INTEGER PRIMARY KEY,
            name TEXT,
            flag_file_id TEXT,
            territory INTEGER,
            money INTEGER,
            resources INTEGER,
            tanks INTEGER
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS promo (
            code TEXT PRIMARY KEY,
            reward_type TEXT,
            amount INTEGER
        )
    """)
    conn.commit()

    # Дефолтная страна "Группас" для владельца (OWNER_ID)
    russia_base_territory = 17125191
    gruppas_territory = russia_base_territory * 3

    cursor.execute("SELECT user_id FROM countries WHERE user_id = ?", (OWNER_ID,))
    if not cursor.fetchone():
        cursor.execute("""
            INSERT INTO countries (user_id, name, flag_file_id, territory, money, resources, tanks)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (OWNER_ID, "Группас", "DEFAULT_GRUPPAS_FLAG", gruppas_territory, 1000000, 500000, 1000))
        conn.commit()

    conn.close()

@bot.message_handler(commands=["start"])
def start(m):
    bot.reply_to(
        m,
        "🌍 **Симулятор геополитики (Gruppas Edition)**\n\n"
        "Создай собственную страну и приведи её к победе!\n"
        "Команды:\n"
        "• `/create [название]` — создать страну (отправь вместе с фото флага)\n"
        "• `/profile` — посмотреть показатели своей страны",
        parse_mode="Markdown"
    )

@bot.message_handler(commands=["create"])
def create_country(m):
    user_id = m.from_user.id
    
    if user_id == OWNER_ID:
        bot.reply_to(m, "⚠️ У тебя уже установлена священная империя **Группас** по дефолту!", parse_mode="Markdown")
        return

    if not m.photo:
        bot.reply_to(m, "⚠️ Прикрепи фотографию флага к сообщению с командой `/create Название`!", parse_mode="Markdown")
        return

    parts = m.text.split(maxsplit=1)
    if len(parts) < 2:
        bot.reply_to(m, "⚠️ Укажи название страны. Пример: `/create Франция`", parse_mode="Markdown")
        return

    country_name = parts[1]
    flag_id = m.photo[-1].file_id

    conn = sqlite3.connect("countries.db", check_same_thread=False)
    cursor = conn.cursor()

    cursor.execute("SELECT user_id FROM countries WHERE user_id = ?", (user_id,))
    if cursor.fetchone():
        conn.close()
        bot.reply_to(m, "⚠️ У тебя уже есть страна!")
        return

    cursor.execute("""
        INSERT INTO countries (user_id, name, flag_file_id, territory, money, resources, tanks)
        VALUES (?, ?, ?, 1, 500, 200, 5)
    """, (user_id, country_name, flag_id))
    conn.commit()
    conn.close()

    bot.send_photo(
        m.chat.id,
        flag_id,
        caption=(
            f"🇦🇮 Страна **{country_name}** успешно основана!\n\n"
            "📈 Стартовые показатели:\n"
            "• Территория: 1 область\n"
            "• Бюджет: 500 монет\n"
            "• Ресурсы: 200 ед.\n"
            "• Танки: 5 ед."
        ),
        parse_mode="Markdown"
    )

@bot.message_handler(commands=["profile"])
def profile(m):
    user_id = m.from_user.id
    conn = sqlite3.connect("countries.db", check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("SELECT name, flag_file_id, territory, money, resources, tanks FROM countries WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        bot.reply_to(m, "⚠️ У тебя еще нет страны. Создай её с помощью `/create [Название]` (прикрепи фото флага).", parse_mode="Markdown")
        return

    name, flag_id, territory, money, resources, tanks = row
    text = (
        f"🏛 Государство: **{name}**\n\n"
        f"🗺 Территория: {territory:,} обл.\n"
        f"💰 Казна: {money:,} монет\n"
        f"⚙️ Ресурсы: {resources:,} ед.\n"
        f"🛡 Танки: {tanks:,} шт."
    )

    if user_id == OWNER_ID:
        text = (
            "👑 **Империя Группас (Священный дефолт)** 👑\n"
            "🎨 *Флаг: Верх — фиолетовый, Низ — пурпурный*\n\n" + text
        )
        bot.reply_to(m, text, parse_mode="Markdown")
    else:
        bot.send_photo(m.chat.id, flag_id, caption=text, parse_mode="Markdown")

if __name__ == "__main__":
    init_db()
    print("--- СИМУЛЯТОР СТРАН ЗАПУЩЕН ---")
    bot.infinity_polling(none_stop=True)
