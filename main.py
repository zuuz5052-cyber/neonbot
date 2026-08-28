import sqlite3
import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, WebAppInfo

# 1. Твой токен
TOKEN = '8836477860:AAE3bN5zTLO0YZUMYleqTMbJwlXdHf1cHwI'
bot = telebot.TeleBot(TOKEN)

# 2. Твои ссылки на игры (замени на свои tiiny.site)
URL_NEON_GAME = "https://neongamesnownb.tiiny.site" 
URL_TRACK_GAME = "https://trackdeathgame.tiiny.site" 
URL_WORDS_GAME = "https://worldsgame.tiiny.site"  # <--- Ссылка на игру в слова

def get_main_keyboard():
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    
    btn_neon = KeyboardButton("⚡ Неон", web_app=WebAppInfo(url=URL_NEON_GAME))
    btn_track = KeyboardButton("🏎 Трасса смерти", web_app=WebAppInfo(url=URL_TRACK_GAME))
    btn_words = KeyboardButton("💬 Игра в слова", web_app=WebAppInfo(url=URL_WORDS_GAME)) # <--- Новая кнопка
    
    # Добавляем все три кнопки в клавиатуру
    markup.add(btn_neon, btn_track, btn_words)
    return markup

@bot.message_handler(commands=['start'])
def start_cmd(message):
    bot.send_message(
        message.chat.id, 
        "Привет! Игровой хаб запущен 🎮\nВыбирай игру в меню ниже:", 
        reply_markup=get_main_keyboard()
    )

print("Бот успешно запущен! Жду команд...")
bot.polling(none_stop=True)
