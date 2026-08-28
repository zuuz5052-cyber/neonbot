import sqlite3
import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, WebAppInfo
import threading
import os
from flask import Flask, render_template_string

# 1. Твой токен
TOKEN = '8836477860:AAE3bN5zTLO0YZUMYleqTMbJwlXdHf1cHwI'
bot = telebot.TeleBot(TOKEN)

# --- БАЗА ДАННЫХ ДЛЯ ПРОФИЛЕЙ И БАЛАНСА ---
conn = sqlite3.connect('users.db', check_same_thread=False)
cursor = conn.cursor()

cursor.execute('''
    CREATE TABLE IF NOT EXISTS players (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        total_score INTEGER DEFAULT 0,
        games_played INTEGER DEFAULT 0
    )
''')
conn.commit()

# 2. Ссылки на игры и магазин
# Внимание: теперь лидерборд будет открываться прямо с сервера твоего бота!
# На Render вместо локального адреса будет использоваться твой публичный домен бота.
URL_SHOP = "https://shopgg.tiiny.site" 
URL_NEON_GAME = "https://neongamesnownb.tiiny.site" 
URL_TRACK_GAME = "https://trackdeathgame.tiiny.site" 
URL_WORDS_GAME = "https://worldsgame.tiiny.site" 
URL_WAVE_GAME = "https://wawegame.tiiny.site" 

def get_main_keyboard(render_url):
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    
    # Кнопка лидерборда ссылается на веб-сервер бота (/leaderboard)
    btn_leaderboard = KeyboardButton("🏆 Лидерборд", web_app=WebAppInfo(url=f"{render_url}/leaderboard"))
    btn_profile = KeyboardButton("👤 Профиль")
    btn_shop = KeyboardButton("🛒 Магазин", web_app=WebAppInfo(url=URL_SHOP))
    
    btn_neon = KeyboardButton("⚡ Неон", web_app=WebAppInfo(url=URL_NEON_GAME))
    btn_track = KeyboardButton("🏎 Трасса смерти", web_app=WebAppInfo(url=URL_TRACK_GAME))
    btn_words = KeyboardButton("💬 Игра в слова", web_app=WebAppInfo(url=URL_WORDS_GAME))
    btn_wave = KeyboardButton("🌊 Волна", web_app=WebAppInfo(url=URL_WAVE_GAME))
    
    markup.add(btn_leaderboard)
    markup.add(btn_profile, btn_shop)
    markup.add(btn_neon, btn_track, btn_words, btn_wave)
    
    return markup

# Получаем публичный URL на Render или ставим дефолт
RENDER_EXTERNAL_URL = os.environ.get("RENDER_EXTERNAL_URL", "https://neonbot-xxxx.onrender.com")

@bot.message_handler(commands=['start'])
def start_cmd(message):
    try:
        user_id = message.from_user.id
        username = message.from_user.first_name or "Игрок"
        
        cursor.execute("INSERT OR IGNORE INTO players (user_id, username, total_score, games_played) VALUES (?, ?, 0, 0)", (user_id, username))
        conn.commit()

        bot.send_message(
            message.chat.id, 
            "Привет! Игровой хаб запущен 🎮\nВыбирай раздел в меню ниже:", 
            reply_markup=get_main_keyboard(RENDER_EXTERNAL_URL)
        )
    except Exception as e:
        print(f"Ошибка в start: {e}")

# Профиль
@bot.message_handler(func=lambda message: message.text and "Профиль" in message.text)
def profile_cmd(message):
    try:
        user_id = message.from_user.id
        cursor.execute("SELECT total_score, games_played FROM players WHERE user_id = ?", (user_id,))
        user_data = cursor.fetchone()
        
        score, games = user_data if user_data else (0, 0)
            
        text = (
            f"👤 **Твой профиль:**\n\n"
            f"🆔 ID: `{user_id}`\n"
            f"🏆 Общие очки: **{score}**\n"
            f"🎮 Сыграно сессий: **{games}**\n\n"
            f"Продолжай играть и ставь новые рекорды!"
        )
        bot.send_message(message.chat.id, text, parse_mode="Markdown")
    except Exception as e:
        print(f"Ошибка в профиле: {e}")

# Перехват очков из игр
@bot.message_handler(content_types=['web_app_data'])
def receive_webapp_data(message):
    try:
        user_id = message.from_user.id
        username = message.from_user.first_name or "Игрок"
        raw_data = message.web_app_data.data
        
        try:
            earned_score = int(raw_data)
        except (ValueError, TypeError):
            earned_score = 0
            
        cursor.execute("INSERT OR IGNORE INTO players (user_id, username, total_score, games_played) VALUES (?, ?, 0, 0)", 
                       (user_id, username))
        # Также обновляем имя, если вдруг изменилось
        cursor.execute("UPDATE players SET username = ?, total_score = total_score + ?, games_played = games_played + 1 WHERE user_id = ?", 
                       (username, earned_score, user_id))
        conn.commit()
        
        bot.send_message(
            message.chat.id, 
            f"🎮 Игра окончена!\n✨ Заработано очков: **{earned_score}**\n📊 Они успешно записаны в твой профиль!", 
            parse_mode="Markdown"
        )
    except Exception as e:
        print(f"Ошибка при получении данных игры: {e}")


# --- FLASK СЕРВЕР И САЙТ ЛИДЕРБОРДА ---
app = Flask(__name__)

LEADERBOARD_HTML = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Таблица лидеров</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
        body { background-color: #0f111a; color: #ffffff; padding: 20px; display: flex; flex-direction: column; align-items: center; min-height: 100vh; }
        .container { width: 100%; max-width: 450px; }
        h1 { text-align: center; font-size: 24px; margin-bottom: 8px; color: #ffcc00; text-shadow: 0 0 10px rgba(255, 204, 0, 0.3); }
        .subtitle { text-align: center; font-size: 14px; color: #8b9bb4; margin-bottom: 25px; }
        .leaders-list { display: flex; flex-direction: column; gap: 12px; margin-bottom: 25px; }
        .leader-card { background: #1a1e29; border: 1px solid #2a324b; border-radius: 12px; padding: 14px 18px; display: flex; justify-content: space-between; align-items: center; }
        .leader-card.top-1 { border-color: #ffd700; background: linear-gradient(135deg, rgba(255, 215, 0, 0.1), #1a1e29); }
        .leader-card.top-2 { border-color: #c0c0c0; background: linear-gradient(135deg, rgba(192, 192, 192, 0.1), #1a1e29); }
        .leader-card.top-3 { border-color: #cd7f32; background: linear-gradient(135deg, rgba(205, 127, 50, 0.1), #1a1e29); }
        .player-info { display: flex; align-items: center; gap: 12px; }
        .rank { font-size: 18px; font-weight: bold; min-width: 30px; text-align: center; }
        .username { font-size: 16px; font-weight: 600; color: #f0f4f8; }
        .score-badge { background: rgba(255, 204, 0, 0.1); color: #ffcc00; padding: 6px 12px; border-radius: 20px; font-size: 14px; font-weight: bold; }
        .info-box { background: #161a25; border-left: 4px solid #ffcc00; padding: 14px; border-radius: 8px; font-size: 13px; color: #cbd5e1; text-align: center; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🏆 Топ игроков</h1>
        <p class="subtitle">В реальном времени из базы данных</p>
        <div class="leaders-list">
            {% for player in players %}
            <div class="leader-card {% if loop.index == 1 %}top-1{% elif loop.index == 2 %}top-2{% elif loop.index == 3 %}top-3{% endif %}">
                <div class="player-info">
                    <span class="rank">{% if loop.index == 1 %}🥇{% elif loop.index == 2 %}🥈{% elif loop.index == 3 %}🥉{% else %}{{ loop.index }}{% endif %}</span>
                    <span class="username">{{ player[0] }}</span>
                </div>
                <div class="score-badge">🏆 {{ player[1] }}</div>
            </div>
            {% endfor %}
        </div>
        <div class="info-box">🔥 Играй в мини-игры, зарабатывай очки и поднимайся в топ!</div>
    </div>
</body>
</html>
"""

@app.route('/leaderboard')
def leaderboard():
    # Достаем реальных топ-10 игроков из базы SQLite
    db_conn = sqlite3.connect('users.db', check_same_thread=False)
    db_cursor = db_conn.cursor()
    db_cursor.execute("SELECT username, total_score FROM players ORDER BY total_score DESC LIMIT 10")
    top_players = db_cursor.fetchall()
    db_conn.close()
    
    return render_template_string(LEADERBOARD_HTML, players=top_players)

@app.route('/')
def home():
    return "Bot is alive!"

def run_server():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

# Запускаем Flask-сервер в фоновом потоке (он же защищает от сна на Render)
threading.Thread(target=run_server, daemon=True).start()

print("Бот и веб-сервер успешно запущены!")

# Запуск Telegram-бота
while True:
    try:
        bot.polling(none_stop=True, interval=0, timeout=20)
    except Exception as e:
        print(f"Ошибка соединения: {e}")
