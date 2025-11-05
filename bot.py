from model import Model
from ragSearch import RagSearch
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from tokens import TOKEN
import os

model = Model("bge-m3:567m", "gemma3:4b")
ragDB = {}

bot = telebot.TeleBot(TOKEN)

prev_messages = {}

keyboard = InlineKeyboardMarkup()  
keyboard.add(InlineKeyboardButton("Присласть источник", callback_data="file"), InlineKeyboardButton("Задать вопрос", callback_data="question"))
keyboard.add(InlineKeyboardButton("Посмотреть источники", callback_data="db"), InlineKeyboardButton("Очистить источники", callback_data="clear"))

start_text = """Привет 👋  
Я — AI-ассистент, использующий RAG (Retrieval-Augmented Generation) поиск.

Я умею:
📄 Читать и анализировать файлы (PDF или txt)
💬 Отвечать на вопросы по содержимому документов
🔍 Искать нужную информацию по смыслу, а не по ключевым словам"""


@bot.message_handler(commands=['start'])
def start(message):
    if not message.chat.id in ragDB.keys():
        ragDB[message.chat.id] = RagSearch(message.chat.id, model)
    m = bot.send_message(message.chat.id, start_text, reply_markup=keyboard)
    prev_messages[message.chat.id] = m



@bot.callback_query_handler(func=lambda x: x.data == "question")
def question(call):
    message = call.message

    bot.edit_message_reply_markup(message.chat.id, prev_messages[message.chat.id].message_id, reply_markup=None)
    bot.send_message(message.chat.id, "Напишите свой вопрос")
    bot.register_next_step_handler(message, question_text)
        
def question_text(message):
    sent = bot.send_message(message.chat.id, "Обработка вопроса...")
    answer = ragDB[message.chat.id].find(message.text)
    bot.delete_message(message.chat.id, sent.message_id)
    m = bot.send_message(message.chat.id, answer, reply_markup=keyboard)
    prev_messages[message.chat.id] = m    



@bot.callback_query_handler(func=lambda x: x.data == "file")
def add_file(call):
    message = call.message

    bot.edit_message_reply_markup(message.chat.id, prev_messages[message.chat.id].message_id, reply_markup=None)
    bot.send_message(message.chat.id, "Пришлите источник в виде файла .pdf или .txt")
    bot.register_next_step_handler(message, file)

def file(message):
    sent = bot.send_message(message.chat.id, "Обработка файла...")

    file_info = bot.get_file(message.document.file_id)
    downloaded_file = bot.download_file(file_info.file_path)

    file_name = message.document.file_name
    with open(file_name, 'wb') as new_file:
        new_file.write(downloaded_file)

    b = ragDB[message.chat.id].load_file(file_name)
    bot.delete_message(message.chat.id, sent.message_id)
    if b:    
        answer = "Файл загружен успешно"
    else:
        answer = "Ошибка обработки файла"

    m = bot.send_message(message.chat.id, answer, reply_markup=keyboard)
    prev_messages[message.chat.id] = m    

    os.remove(file_name)

    

@bot.callback_query_handler(func=lambda x: x.data == "clear")
def clear(call):
    message = call.message

    bot.edit_message_reply_markup(message.chat.id, prev_messages[message.chat.id].message_id, reply_markup=None)
    ragDB[message.chat.id].clear()
    m = bot.send_message(message.chat.id, "Хранилище источников очищено", reply_markup=keyboard)
    prev_messages[message.chat.id] = m    



@bot.callback_query_handler(func=lambda x: x.data == "db")
def db(call):
    message = call.message

    bot.edit_message_reply_markup(message.chat.id, prev_messages[message.chat.id].message_id, reply_markup=None)

    if len(ragDB[message.chat.id].get_files())==0:
        answer = "Нет загруженных источников"
    else:   
        answer = "Загруженные источники:"
        for file_name in ragDB[message.chat.id].get_files():
            answer += f"\n{file_name}"

    m = bot.send_message(message.chat.id, answer, reply_markup=keyboard)
    prev_messages[message.chat.id] = m    


bot.infinity_polling()


