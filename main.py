import sqlite3
import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, WebAppInfo
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import os

# 1. Твой токен
TOKEN = '8836477860:AAE3bN5zTLO0YZUMYleqTMbJwlXdHf1cHwI'
bot = telebot.TeleBot(TOKEN)

# 2. Твои ссылки на игры
URL_NEON_GAME = "https://neongamesnownb.tiiny.site" 
URL_TRACK_GAME = "https://trackdeathgame.tiiny.site" 
URL_WORDS_GAME = "https://worldsgame.tiiny.site" 
URL_WAVE_GAME = "https://wawegame.tiiny.site"  # <--- Ссылка на игру "Волна"

def get_main_keyboard():
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    
    btn_neon = KeyboardButton("⚡ Неон", web_app=WebAppInfo(url=URL_NEON_GAME))
    btn_track = KeyboardButton("🏎 Трасса смерти", web_app=WebAppInfo(url=URL_TRACK_GAME))
    btn_words = KeyboardButton("💬 Игра в слова", web_app=WebAppInfo(url=URL_WORDS_GAME))
    btn_wave = KeyboardButton("🌊 Волна", web_app=WebAppInfo(url=URL_WAVE_GAME))
    
    # Добавляем все четыре кнопки в клавиатуру
    markup.add(btn_neon, btn_track, btn_words, btn_wave)
    return markup

@bot.message_handler(commands=['start'])
def start_cmd(message):
    bot.send_message(
        message.chat.id, 
        "Привет! Игровой хаб запущен 🎮\nВыбирай игру в меню ниже:", 
        reply_markup=get_main_keyboard()
    )

print("Бот успешно запущен! Жду команд...")

# Веб-сервер для предотвращения засыпания бота на Render
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
