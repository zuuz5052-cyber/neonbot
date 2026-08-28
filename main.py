import sqlite3
import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, WebAppInfo
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import os

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

# 2. Твои ссылки на игры
URL_NEON_GAME = "https://neongamesnownb.tiiny.site" 
URL_TRACK_GAME = "https://trackdeathgame.tiiny.site" 
URL_WORDS_GAME = "https://worldsgame.tiiny.site" 
URL_WAVE_GAME = "https://wawegame.tiiny.site" 

def get_main_keyboard():
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    
    # Кнопки профиля и магазина рядом на первой строчке
    btn_profile = KeyboardButton("👤 Профиль")
    btn_shop = KeyboardButton("🛒 Магазин")
    
    btn_neon = KeyboardButton("⚡ Неон", web_app=WebAppInfo(url=URL_NEON_GAME))
    btn_track = KeyboardButton("🏎 Трасса смерти", web_app=WebAppInfo(url=URL_TRACK_GAME))
    btn_words = KeyboardButton("💬 Игра в слова", web_app=WebAppInfo(url=URL_WORDS_GAME))
    btn_wave = KeyboardButton("🌊 Волна", web_app=WebAppInfo(url=URL_WAVE_GAME))
    
    markup.add(btn_profile, btn_shop)
    markup.add(btn_neon, btn_track, btn_words, btn_wave)
    
    return markup

@bot.message_handler(commands=['start'])
def start_cmd(message):
    try:
        user_id = message.from_user.id
        username = message.from_user.first_name or "Игрок"
        
        cursor.execute("INSERT OR IGNORE INTO players (user_id, username, total_score, games_played) VALUES (?, ?, 0, 0)", (user_id, username))
        conn.commit()

        bot.send_message(
            message.chat.id, 
            "Привет! Игровой хаб запущен 🎮\nВыбирай игру, открой профиль или загляни в магазин:", 
            reply_markup=get_main_keyboard()
        )
    except Exception as e:
        print(f"Ошибка в start: {e}")

# Точный обработчик для команды /help
@bot.message_handler(commands=['help'])
def help_cmd(message):
    try:
        help_text = (
            "🆘 **Помощь по боту:**\n\n"
            "🎮 Играй в мини-игры, зарабатывай очки и трать их в магазине!\n"
            "🛒 Нажми кнопку «🛒 Магазин», чтобы посмотреть доступные призы.\n\n"
            "💬 По всем вопросам и для получения призов пиши создателю: **@zews_zuuz**"
        )
        bot.send_message(message.chat.id, help_text, parse_mode="Markdown")
    except Exception as e:
        print(f"Ошибка в help: {e}")

# Обработка нажатия на кнопку "👤 Профиль"
@bot.message_handler(func=lambda message: message.text and "Профиль" in message.text)
def profile_cmd(message):
    try:
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
    except Exception as e:
        print(f"Ошибка в профиле: {e}")

# Точный обработчик для кнопки "🛒 Магазин"
@bot.message_handler(func=lambda message: message.text == "🛒 Магазин")
def shop_cmd(message):
    try:
        shop_text = (
            "🛒 **Магазин призов за очки:**\n\n"
            "1️⃣ **Игра в боте по вашему пожеланию**\n"
            "   💰 Цена: **2 000 очков**\n\n"
            "2️⃣ **Рандомный скин КС (от 50 до 200 руб.)**\n"
            "   💰 Цена: **7 777 очков**\n\n"
            "3️⃣ **Прокачка на кейс батле на 50 рублей**\n"
            "   💰 Цена: **10 000 очков**\n\n"
            "👇 Накопил нужное количество очков? Сделай скриншот профиля и пиши создателю: **@zews_zuuz**"
        )
        bot.send_message(message.chat.id, shop_text, parse_mode="Markdown")
    except Exception as e:
        print(f"Ошибка в магазине: {e}")

# ПЕРЕХВАТ ОЧКОВ ИЗ ИГРЫ Web App
@bot.message_handler(content_types=['web_app_data'])
def receive_webapp_data(message):
    try:
        user_id = message.from_user.id
        raw_data = message.web_app_data.data
        
        try:
            earned_score = int(raw_data)
        except (ValueError, TypeError):
            earned_score = 0
            
        cursor.execute("INSERT OR IGNORE INTO players (user_id, username, total_score, games_played) VALUES (?, ?, 0, 0)", 
                       (user_id, message.from_user.first_name or "Игрок"))
        
        cursor.execute("UPDATE players SET total_score = total_score + ?, games_played = games_played + 1 WHERE user_id = ?", 
                       (earned_score, user_id))
        conn.commit()
        
        bot.send_message(
            message.chat.id, 
            f"🎮 Игра окончена!\n✨ Заработано очков: **{earned_score}**\n📊 Они успешно записаны в твой профиль!", 
            parse_mode="Markdown"
        )
    except Exception as e:
        print(f"Ошибка при получении данных игры: {e}")

print("Бот успешно запущен! Жду команд...")

# Веб-сервер для Render (анти-сон)
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

# Авто-переподключение 24/7
while True:
    try:
        bot.polling(none_stop=True, interval=0, timeout=20)
    except Exception as e:
        print(f"Ошибка соединения: {e}")
