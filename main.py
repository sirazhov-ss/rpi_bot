#/usr/bin/python

import telebot
from telebot import types
from os import path
from CheckRPi import MongoConnect, PGConnect, CheckRpi

TOKEN_DIR = r'c:\token'
MGE_DIR = r'c:\mge.config'
NIAC_BREST_DIR = r'c:\niac_brest.config'
NIAC_TAT_DIR = r'c:\niac_tat.config'


def get_config(config_directory):
    if not path.isfile(config_directory):
        raise Exception(f"File not found! Check directory '{config_directory}'")
    config = {
        'remote_host': None,
        'remote_port': None,
        'remote_username': None,
        'remote_password': None,
        'db_host': None,
        'db_port': None,
        'db_name': None,
        'db_username': None,
        'db_password': None
        }
    with open(config_directory, 'r') as file:
        for line in file.readlines():
            for key in config.keys():
                if line.find(key) != -1:
                    config[key] = line.split('=')[1].strip()

    if config.get('remote_port') is not None:
        config['remote_port'] = int(config['remote_port'])

    if config.get('db_port') is not None:
        config['db_port'] = int(config['db_port'])

    return config


def add_buttons(*args, count=2):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    buttons = []
    whole = len(args) // count
    remainder = len(args) % count
    arg = 0
    for i in range(whole*count):
        buttons.append(types.KeyboardButton(args[arg]))
        arg += 1
        if (i+1) % count == 0:
            markup.row(*buttons)
            buttons = []
    if remainder > 0:
        for i in range(remainder):
            buttons.append(types.KeyboardButton(args[arg]))
            arg += 1
        markup.row(*buttons)
    return markup


token = open(TOKEN_DIR).read()
bot = telebot.TeleBot(token)


@bot.message_handler(commands=['start'])
def start(message):
    response = f'<b>{"Нажмите на кнопки внизу, чтобы проверить интересующие Вас контуры!"}</b>'
    markup = add_buttons('НИАЦ Брестская', 'НИАЦ Татарская', 'МГЭ', count=2)
    bot.send_message(message.chat.id, response, parse_mode='html', reply_markup=markup)


@bot.message_handler()
def send_weak(message):
    markup = add_buttons('НИАЦ Брестская', 'НИАЦ Татарская', 'МГЭ', count=2)
    if message.text.strip().lower() == "мгэ":
        try:
            bot.send_message(message.chat.id, "Получение списка неработающих пих в МосГорЭкспертизе. Ждите...",
                             parse_mode='html', reply_markup=markup)
            config = get_config(MGE_DIR)
            data = MongoConnect(**config).data
            subscribe = "На данный момент в МГЭ обнаружен, неработающ, модул".split(',')
            response = CheckRpi(data).get_message(subscribe)
            if len(response) == 0:
                response = ["Неработающих модулей в МГЭ не обнаружено!"]
            for i in range(len(response)):
                bot.send_message(message.chat.id, response[i], parse_mode='html', reply_markup=markup)
        except Exception as e:
            bot.send_message(message.chat.id, f'[ERROR] {e}', parse_mode='html', reply_markup=markup)
    if message.text.strip().lower() == "ниац брестская":
        try:
            bot.send_message(message.chat.id, "Получение списка неработающих пих в ГАУ 'НИАЦ' по адресу ул. 1-я "
                                              "Брестская д.27. Ждите...", parse_mode='html', reply_markup=markup)
            config = get_config(NIAC_BREST_DIR)
            data = PGConnect(**config).data
            subscribe = "На данный момент в ГАУ 'НИАЦ' по адресу ул. 1-я Брестская д.27 " \
                        "обнаружен, неработающ, модул".split(',')
            response = CheckRpi(data).get_message(subscribe)
            if len(response) == 0:
                response = ["Неработающих модулей в ГАУ 'НИАЦ' по адресу ул. 1-я Брестская д.27 не обнаружено!"]
            for i in range(len(response)):
                bot.send_message(message.chat.id, response[i], parse_mode='html', reply_markup=markup)
        except Exception as e:
            bot.send_message(message.chat.id, f'[ERROR] {e}', parse_mode='html', reply_markup=markup)
    if message.text.strip().lower() == "ниац татарская":
        try:
            bot.send_message(message.chat.id, "Получение списка неработающих пих в ГАУ 'НИАЦ' по адресу ул. Б.Татарская"
                                              " д.7 к.3. Ждите...", parse_mode='html', reply_markup=markup)
            config = get_config(NIAC_TAT_DIR)
            data = PGConnect(**config).data
            subscribe = "На данный момент в ГАУ 'НИАЦ' по адресу ул. Б.Татарская д.7 " \
                        "к.3.обнаружен, неработающ, модул".split(',')
            response = CheckRpi(data).get_message(subscribe)
            if len(response) == 0:
                response = ["Неработающих модулей в ГАУ 'НИАЦ' по адресу Б.Татарская д.7 к.3 не обнаружено!"]
            for i in range(len(response)):
                bot.send_message(message.chat.id, response[i], parse_mode='html', reply_markup=markup)
        except Exception as e:
            bot.send_message(message.chat.id, f'[ERROR] {e}', parse_mode='html', reply_markup=markup)


print ("bot.polling is active")
bot.polling(none_stop=True)