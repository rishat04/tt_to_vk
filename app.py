import telebot
import config
import schedule
import threading
import time

from db import DB

from keyboards import main_keyboard, project_keyboard, get_projects, tiktok_keyboard
from utils import get_vk_group_id, get_tiktok_username

from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

from utils import proccess


bot = telebot.TeleBot(config.tg_token)

project = {}
task = {}

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, """\
Привет, давай рубить бабосики на перезаливах!\
""", reply_markup=main_keyboard())

@bot.message_handler(func=lambda message: message.text == 'Создать проект')
def create_project(message):
    bot.send_message(message.chat.id, 'Введите название проекта:')
    bot.register_next_step_handler(message, save_project_name)

def save_project_name(message):
    project_name = message.text
    project['project_name'] = project_name
    bot.send_message(message.chat.id, 'Отправьте ссылку на группу ВК:')
    bot.register_next_step_handler(message, save_vk_id)

def save_vk_id(message):
    vk_group_url = message.text
    vk_group_id = get_vk_group_id(vk_group_url)
    project['vk_group_id'] = vk_group_id
    bot.send_message(message.chat.id, 'Отправьте ссылки на страницы ТикТок:')
    bot.register_next_step_handler(message, save_tiktok_pages)

def save_tiktok_pages(message):
    tiktok_pages = message.text.split('\n')
    project['tiktok_channels'] = []
    for tiktok_page in tiktok_pages:
        project['tiktok_channels'].append({
            'channel_name': get_tiktok_username(tiktok_page),
            'last_video_time': 0
        })
    
    bot.send_message(message.chat.id, 'Отправьте описание и тэги к видео:')
    bot.register_next_step_handler(message, save_description)

def save_description(message):
    description = message.text
    project['description'] = description

    db = DB()

    db.set_project(project)
    db.save()

    bot.send_message(message.chat.id, 'Проект успешно создан 🫶🏻')


@bot.message_handler(func=lambda message: message.text == 'Редактировать проект')
def create_project(message):
    db = DB()
    projects = db.get_projects()

    if not projects:
        bot.send_message(message.chat.id, 'У вас нет действующих проектов(')
        return

    bot.send_message(message.chat.id, 'Выберите проект:', reply_markup=get_projects(projects))

@bot.message_handler(func=lambda message: 'tiktok.com' in message.text)
def add_tiktok(message):
    if not task['add']:
        return
    
    db = DB()

    vk_group_id = task['add']['vk_group_id']
    message_id = task['add']['message_id']
    project = db.get_project(vk_group_id)

    for tiktok_channel in message.text.split('\n'):
        tiktok_channel = get_tiktok_username(tiktok_channel)
        db.set_tiktok_account(vk_group_id, tiktok_channel)
        db.save()

    bot.delete_message(message.chat.id, message_id+1)
    bot.edit_message_text('Выберите действие:',
                          message.chat.id,
                          message_id,
                          reply_markup=project_keyboard(project))
    
@bot.message_handler()
def add_tiktok(message):
    if not task['edit']:
        return
    
    db = DB()
    
    vk_group_id = task['edit']['vk_group_id']
    message_id = task['edit']['message_id']
    project = db.get_project(vk_group_id)

    desc_and_tags = message.text
    db.set_description(vk_group_id, desc_and_tags)
    db.save()

    bot.delete_message(message.chat.id, message_id+1)
    bot.edit_message_text('Выберите действие:',
                          message.chat.id,
                          message_id,
                          reply_markup=project_keyboard(project))

@bot.callback_query_handler(func=lambda call: True)
def callback_project_query(call):
    db = DB()
    projects = db.get_projects()
    
    for project in projects:
        vk_group_id = project['vk_group_id']

        if call.data == f'add_tiktok_{vk_group_id}':
            bot.edit_message_text('Введите ТТ аккаунт(ы):',
                                    call.message.chat.id,
                                    call.message.id)   
            task['add'] = {
                'vk_group_id': vk_group_id,
                'message_id': call.message.id,
            }         

        if call.data == f'show_description_{project["vk_group_id"]}':
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton('Редактировать', callback_data=f'edit_description_{project["vk_group_id"]}'),
                       InlineKeyboardButton('<<<', callback_data=f'show_project_{vk_group_id}'))
            
            bot.edit_message_text(f'Текущее описание и тэги: \n\n {project["description"]}',
                                    call.message.chat.id,
                                    call.message.id,
                                    reply_markup=markup) 

        if call.data == f'edit_description_{project["vk_group_id"]}':
            bot.edit_message_text('Введите описание и тэги:',
                                    call.message.chat.id,
                                    call.message.id)   
            task['edit'] = {
                'vk_group_id': vk_group_id,
                'message_id': call.message.id,
            } 

        if call.data == f'show_project_{vk_group_id}':
            bot.edit_message_text('Выберите действие:', 
                                    call.message.chat.id,
                                    call.message.id,
                                    reply_markup=project_keyboard(project))
            
        if call.data == f'delete_project_{vk_group_id}':
            db.delete_project(vk_group_id)
            db.save()
            bot.edit_message_text('Проект удален!', 
                                call.message.chat.id,
                                call.message.id)
        
        tiktok_channels = project['tiktok_channels']

        for tiktok_channel in tiktok_channels:
            tiktok_id = tiktok_channel['channel_name']
            
            if call.data == f'show_tiktok_{tiktok_id}':
                bot.edit_message_text('Выберите действие:', 
                                    call.message.chat.id,
                                    call.message.id,
                                    reply_markup=tiktok_keyboard(vk_group_id, tiktok_id))

            if call.data == f'delete_tiktok_{tiktok_id}':
                db.delete_tiktok_from_project(vk_group_id, tiktok_id)
                db.save()

                bot.edit_message_text('Выберите действие:', 
                                    call.message.chat.id,
                                    call.message.id,
                                    reply_markup=project_keyboard(project))
                
    if call.data == 'cmd_project_keyboard':            
        bot.edit_message_text('Выберите проект:', 
                                call.message.chat.id,
                                call.message.id,
                                reply_markup=get_projects(projects))
        

def run_scheduler():
    while True:
        schedule.run_pending()
        time.sleep(1)


if __name__ == '__main__':
    schedule.every(2).hours.do(proccess)
    scheduler_thread = threading.Thread(target=run_scheduler)
    scheduler_thread.daemon = True
    scheduler_thread.start()
    
    bot.infinity_polling()