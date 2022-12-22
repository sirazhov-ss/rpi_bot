#/usr/bin/python

import telebot
from telebot import types
from CheckRPi import MongoConnect, PGConnect, CheckRpi


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


def make_subcribe(sample):
    return f"Получение списка неработающих модулей{sample}. Ждите..."


def get_response(message, response, markup, company=""):
    bot.delete_message(message.chat.id, message.message_id + 1)
    bot.delete_message(message.chat.id, message.message_id + 2)
    if len(response) == 0:
        response = [f"Неработающих модулей{company} не обнаружено!"]
    for i in range(len(response)):
        bot.send_message(message.chat.id, response[i], parse_mode='html', reply_markup=markup)


TOKEN_DIR = r'c:\token'
MGE_DIR = r'c:\mge.config'
NIAC_BREST_DIR = r'c:\niac_brest.config'
NIAC_TAT_DIR = r'c:\niac_tat.config'
STICKER_DIR = r'c:\sticker.tgs'


token = open(TOKEN_DIR).read()
if token[-1:] == '\n':
    token = token[:-1]
bot = telebot.TeleBot(token)


@bot.message_handler()
def response(message):
    markup = add_buttons('НИАЦ Брестская', 'НИАЦ Татарская', 'МГЭ', count=2)
    try:
        if message.text.strip().lower() == 'мгэ':
            company = " в МосГорЭкспертизе"
            bot.send_sticker(message.chat.id, open(STICKER_DIR, 'rb'), reply_markup=markup)
            bot.send_message(message.chat.id, make_subcribe(company), parse_mode='html', reply_markup=markup)
            mge = CheckRpi(MongoConnect(MGE_DIR).data)
            get_response(message, mge.get_message(mge.get_weak(), company), markup, company)

        elif message.text.strip().lower() == 'ниац брестская':
            company = " в ГАУ 'НИАЦ' по адресу ул. 1-я Брестская д.27"
            bot.send_sticker(message.chat.id, open(STICKER_DIR, 'rb'), reply_markup=markup)
            bot.send_message(message.chat.id, make_subcribe(company), parse_mode='html', reply_markup=markup)
            niac_brest = CheckRpi(PGConnect(NIAC_BREST_DIR).data)
            get_response(message, niac_brest.get_message(niac_brest.get_weak(), company), markup, company)

        elif message.text.strip().lower() == 'ниац татарская':
            company = " в ГАУ 'НИАЦ' по адресу ул. Б.Татарская д.7 к.3"
            bot.send_sticker(message.chat.id, open(STICKER_DIR, 'rb'), reply_markup=markup)
            bot.send_message(message.chat.id, make_subcribe(company), parse_mode='html', reply_markup=markup)
            niac_tat = CheckRpi(PGConnect(NIAC_TAT_DIR).data)
            get_response(message, niac_tat.get_message(niac_tat.get_weak(**{'6': 1, '7': 2, '8': 0}), company),
                         markup, company)

        else:
            response = f'Нажмите на кнопки внизу, чтобы проверить интересующие Вас контуры!'
            bot.send_message(message.chat.id, response, parse_mode='html', reply_markup=markup)

    except Exception as e:
        bot.send_message(message.chat.id, f'[ERROR] {e}', parse_mode='html', reply_markup=markup)


print("bot.polling is active")
bot.polling(none_stop=True)