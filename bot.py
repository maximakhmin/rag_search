from model import Model
from ragSearch import RagSearch
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from tokens import TOKEN
from download import is_download_link, get_file_name
import os
import requests

model_names = ["gemma3:12b", "llama3.1"]
model = Model("bge-m3:567m", model_names)
ragDB = {}

bot = telebot.TeleBot(TOKEN)

prev_messages = {}

keyboard = InlineKeyboardMarkup()  
keyboard.add(InlineKeyboardButton("Присласть источник", callback_data="file"), InlineKeyboardButton("Поменять модель LLM", callback_data="change_llm"))
keyboard.add(InlineKeyboardButton("Посмотреть источники", callback_data="db"), InlineKeyboardButton("Очистить источники", callback_data="clear"))
keyboard.add(InlineKeyboardButton("Задать вопрос", callback_data="question"))

model_name_keyboard = InlineKeyboardMarkup()
num_lines = len(model_names)//2
for i in range(num_lines):
    model_name_keyboard.add(InlineKeyboardButton(model_names[i*2], callback_data=model_names[i*2]),
                            InlineKeyboardButton(model_names[i*2+1], callback_data=model_names[i*2+1]))
if (len(model_names)%2==1):
    model_name_keyboard.add(InlineKeyboardButton(model_names[-1], callback_data=model_names[-1]))    




start_text = """Привет 👋  
Я — AI-ассистент, использующий RAG (Retrieval-Augmented Generation) поиск.

Я умею:
📄 Читать и анализировать файлы (pdf, txt, mp3, mp4)
💬 Отвечать на вопросы по содержимому документов
🔍 Искать нужную информацию по смыслу, а не по ключевым словам"""


@bot.message_handler(commands=['start'])
def start(message):
    if not message.chat.id in ragDB.keys():
        ragDB[message.chat.id] = RagSearch(message.chat.id, model)
    m = bot.send_message(message.chat.id, start_text, reply_markup=keyboard)
    prev_messages[message.chat.id] = m


@bot.callback_query_handler(func=lambda x: x.data == "change_llm")
def change_llm(call):
    message = call.message
    bot.edit_message_reply_markup(message.chat.id, prev_messages[message.chat.id].message_id, reply_markup=None)
    m = bot.send_message(message.chat.id, f"Выберете модель. Текущая модель: {ragDB[message.chat.id].get_model_name()}", reply_markup=model_name_keyboard)
    prev_messages[message.chat.id] = m

@bot.callback_query_handler(func=lambda x: x.data in model_names)
def set_llm(call):
    message = call.message
    bot.edit_message_reply_markup(message.chat.id, prev_messages[message.chat.id].message_id, reply_markup=None)
    ragDB[message.chat.id].set_model_name(call.data)
    m = bot.send_message(message.chat.id, f"Новая модель: {ragDB[message.chat.id].get_model_name()}", reply_markup=keyboard)
    prev_messages[message.chat.id] = m

@bot.callback_query_handler(func=lambda x: x.data == "question")
def question(call):
    message = call.message
    bot.edit_message_reply_markup(message.chat.id, prev_messages[message.chat.id].message_id, reply_markup=None)
    
    if len(ragDB[message.chat.id].get_files())==0:
        m = bot.send_message(message.chat.id, "Сначала загрузите источники", reply_markup=keyboard)
        prev_messages[message.chat.id] = m
    else:       
        bot.send_message(message.chat.id, "Напишите свой вопрос")
        bot.register_next_step_handler(message, question_text)
        
def question_text(message):
    sent = bot.send_message(message.chat.id, "Обработка вопроса...")
    answer = ragDB[message.chat.id].find(message.text)
    bot.delete_message(message.chat.id, sent.message_id)
    m = bot.send_message(message.chat.id, answer, reply_markup=keyboard)
    prev_messages[message.chat.id] = m    


def is_valid_attachment(message):
    size = 52428800 # 50MB
    return message.audio and message.audio.file_size<size or \
           message.document and message.document.file_size<size or \
           message.video and message.video.file_size<size
       



@bot.callback_query_handler(func=lambda x: x.data == "file")
def add_file(call):
    message = call.message

    bot.edit_message_reply_markup(message.chat.id, prev_messages[message.chat.id].message_id, reply_markup=None)
    bot.send_message(message.chat.id, "Пришлите источник в виде файла .pdf, .txt, mp3 или mp4 размером до 50MB. Так же можно прислать ссылку на скачивание")
    bot.register_next_step_handler(message, file)

def file(message):
    sent = bot.send_message(message.chat.id, "Cкачивание файла...")

    if (message.text and is_download_link(message.text)):
        response = requests.get(message.text)
        if response.status_code == 200:
            downloaded_file = response.content
            file_name = get_file_name(message.text)
            if not file_name:
                downloaded_file = None
        else:
            downloaded_file = None


    elif (is_valid_attachment(message)):
        if (message.audio):
            file_info = bot.get_file(message.audio.file_id)
            file_name = message.audio.file_name
        elif (message.document):
            file_info = bot.get_file(message.document.file_id)
            file_name = message.document.file_name
        elif (message.video):
            file_info = bot.get_file(message.video.file_id)
            file_name = message.video.file_name
 
        downloaded_file = bot.download_file(file_info.file_path)

    else:
        downloaded_file = None


    if (downloaded_file):

        bot.edit_message_text("Обработка файла...", message.chat.id, sent.message_id)

        with open(file_name, 'wb') as new_file:
            new_file.write(downloaded_file)

        b = ragDB[message.chat.id].load_file(file_name)
        os.remove(file_name)
    else:
        b = False

    bot.delete_message(message.chat.id, sent.message_id)    
    if b:    
        answer = "Файл загружен успешно"
    else:
        answer = "Ошибка загрузки файла"

    m = bot.send_message(message.chat.id, answer, reply_markup=keyboard)
    prev_messages[message.chat.id] = m    

    

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


