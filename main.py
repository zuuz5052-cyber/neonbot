import sqlite3
import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, WebAppInfo
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import os

# 1. Твой токен
TOKEN = '8836477860:AAE3bN5zTLO0YZUMYleqTMbJwlXdHf1cHwI'
bot = telebot.TeleBot(TOKEN)

# --- БАЗА ДАННЫХ ДЛЯ ПРОФИЛЕЙ ---
conn = sqlite3.connect('users.db', check_same_thread=False)
cursor = conn.cursor()

# Создаем таблицу игроков, если её еще нет
cursor.execute('''
    CREATE TABLE IF NOT EXISTS players (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        total_score INTEGER DEFAULT 0,
        games_played INTEGER DEFAULT 0
    )
''')
conn.commit()
# ---------------------------------

# 2. Твои ссылки на игры
URL_NEON_GAME = "https://neongamesnownb.tiiny.site" 
URL_TRACK_GAME = "https://trackdeathgame.tiiny.site" 
URL_WORDS_GAME = "https://worldsgame.tiiny.site" 
URL_WAVE_GAME = "https://wawegame.tiiny.site" 

def get_main_keyboard():
    # row_width=2 делает так, что следующие кнопки будут выстраиваться по 2 в ряд
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    
    # 1. Создаем кнопки
    btn_profile = KeyboardButton("👤 Профиль")
    btn_neon = KeyboardButton("⚡ Неон", web_app=WebAppInfo(url=URL_NEON_GAME))
    btn_track = KeyboardButton("🏎 Трасса смерти", web_app=WebAppInfo(url=URL_TRACK_GAME))
    btn_words = KeyboardButton("💬 Игра в слова", web_app=WebAppInfo(url=URL_WORDS_GAME))
    btn_wave = KeyboardButton("🌊 Волна", web_app=WebAppInfo(url=URL_WAVE_GAME))
    
    # 2. Сначала добавляем Профиль (он будет один на первой строчке во всю ширину)
    markup.add(btn_profile)
    
    # 3. Затем добавляем игры (они автоматически встанут сеткой по 2 в ряд: 1-2 и 3-4)
    markup.add(btn_neon, btn_track, btn_words, btn_wave)
    
    return markup

@bot.message_handler(commands=['start'])
def start_cmd(message):
    user_id = message.from_user.id
    username = message.from_user.first_name or "Игрок"
    
    cursor.execute("INSERT OR IGNORE INTO players (user_id, username, total_score, games_played) VALUES (?, ?, 0, 0)", (user_id, username))
    conn.commit()

    bot.send_message(
        message.chat.id, 
        "Привет! Игровой хаб запущен 🎮\nВыбирай игру или открой профиль в меню ниже:", 
        reply_markup=get_main_keyboard()
    )

# Обработка нажатия на кнопку "👤 Профиль"
@bot.message_handler(func=lambda message: message.text == "👤 Профиль")
def profile_cmd(message):
    user_id = message.from_user.id
    
    cursor.execute("SELECT total_score, games_played FROM players WHERE user_id = ?", (user_id,))
    user_data = cursor.fetchone()
    
    if user_data:
        score, games = user_data
    else:
        score, games = 0, 0
        
    text = (
        f"👤 **Твой профиль:**\n\n"
        f"🆔 ID: `{user_id}`\n"
        f"🏆 Общие очки: **{score}**\n"
        f"🎮 Сыграно сессий: **{games}**\n\n"
        f"Продолжай играть и ставь новые рекорды!"
    )
    bot.send_message(message.chat.id, text, parse_mode="Markdown")

print("Бот успешно запущен! Жду команд...")

# Веб-сервер для Render
class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is alive!")

def run_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), SimpleHandler)
    server.serve_forever()

threading.Thread(target=run_server, daemon=True).start()

bot.polling(none_stop=True)
