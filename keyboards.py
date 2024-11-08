import json
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from telebot.types import ReplyKeyboardMarkup, KeyboardButton

def main_keyboard():
    markup = ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    markup.add(KeyboardButton(text="Создать проект"), KeyboardButton(text="Редактировать проект"))
    return markup

def project_keyboard(project):
    markup = {'inline_keyboard': []}
    
    tiktok_channels = project['tiktok_channels']

    for tiktok_channel in tiktok_channels:
        tiktok_id = tiktok_channel['channel_name']
        
        markup['inline_keyboard'].append([{
            'text': tiktok_id,
            'callback_data': f'show_tiktok_{tiktok_id}'
        }])

    markup['inline_keyboard'].append([
        {
            'text': 'Добавить ТТ аккаунт',
            'callback_data': f'add_tiktok_{project["vk_group_id"]}'
        }
    ])

    markup['inline_keyboard'].append([
        {
            'text': 'Описание и тэги',
            'callback_data': f'show_description_{project["vk_group_id"]}'
        }
    ])

    markup['inline_keyboard'].append([
        {
            'text': 'Удалить проект',
            'callback_data': f'delete_project_{project["vk_group_id"]}'
        },
        {
            'text': '<<<',
            'callback_data': 'cmd_project_keyboard'
        }
    ])
    return json.dumps(markup)

def get_projects(projects):
    markup = InlineKeyboardMarkup(row_width=1)
    for project in projects:
        markup.add(InlineKeyboardButton(text=project['project_name'], callback_data=f"show_project_{project['vk_group_id']}"))
    return markup

def tiktok_keyboard(vk_group_id, tiktok_id):
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton('Удалить', callback_data=f'delete_tiktok_{tiktok_id}'),
               InlineKeyboardButton('<<<', callback_data=f'show_project_{vk_group_id}'))
    return markup