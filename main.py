#!/usr/bin/python

import telebot
from telebot import types
from CheckRPi import MongoConnect, PGConnect, CheckRpi
from datetime import datetime

def __make_subcribe(sample):
    return f"Получение списка неработающих модулей{sample}. Ждите..."


def __change_first_element(array: list, company: str):
    if len(array) > 1:
        array[0] = f'<b>{company}:</b>'
    else:
        array = []
    return array


def __format_date(x):
    return datetime.strftime(datetime.fromtimestamp(round(datetime.timestamp(x), 0)), "%d/%m/%y %H:%M:%S")


def __ending(remainder):
    if remainder == 1:
        ending_array = ["", "ий", "ь"]
    elif (remainder > 1) and (remainder <= 3):
        ending_array = ["о", "их", "я"]
    else:
        ending_array = ["о", "их", "ей"]
    return ending_array


def get_message(array, company=""):
    subscribe = f"На данный момент{company} обнаружен, неработающ, модул".split(',')
    if len(array) > 0:
        message_array = []
        count = 20
        whole = len(array) // count
        remainder = len(array) % count
        ending_remainder = remainder % 10
        message = f"\n\r{subscribe[0] + __ending(ending_remainder)[0]} <b>{whole * count + remainder}</b>" \
                    f"{subscribe[1] + __ending(ending_remainder)[1]} " \
                    f"{subscribe[2] + __ending(ending_remainder)[2]}:\n\r"
        message_array.append(message)
        for i in range(whole):
            message = ""
            for j in range(count):
                message += f"{i * count + j + 1})    title: {array[i * count + j].get('title')}\n\r\
    floor: {array[i * count + j].get('floor')}\n\r\
    rp_id: {array[i * count + j].get('rp_id')}\n\r\
    rp_ip: {array[i * count + j].get('rp_ip')}\n\r\
    switch: {array[i * count + j].get('switch')}\n\r\
    port: {array[i * count + j].get('port')}\n\r\
    date_income: {__format_date(array[i * count + j].get('date_income'))}\n\r\n\r"
            message_array.append(message)
        message = ""
        for i in range(remainder):
            message += f"{whole * count + i + 1})    title: {array[whole * count + i].get('title')}\n\r\
    floor: {array[whole * count + i].get('floor')}\n\r\
    rp_id: {array[whole * count + i].get('rp_id')}\n\r\
    rp_ip: {array[whole * count + i].get('rp_ip')}\n\r\
    switch: {array[whole * count + i].get('switch')}\n\r\
    port: {array[whole * count + i].get('port')}\n\r\
    date_income: {__format_date(array[whole * count + i].get('date_income'))}\n\r\n\r"
        message_array.append(message)
        return message_array
    else:
        return [f"Неработающих модулей{company} не обнаружено!"]


def get_response(message, response: list, markup):
    bot.delete_message(message.chat.id, message.message_id + 1)
    bot.delete_message(message.chat.id, message.message_id + 2)
    for i in range(len(response)):
        bot.send_message(message.chat.id, response[i], parse_mode='html', reply_markup=markup)


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
    name_of_buttons = ('МГЭ', 'НИАЦ Брестская', 'НИАЦ Татарская', 'Проверить все контуры за последние сутки')
    markup = add_buttons(*name_of_buttons, count=3)
    try:
        if message.text.strip().lower() == name_of_buttons[3].lower():
            subcribe = 'Проверка неработающих модулей на всех контурах за последние сутки. Ждите...'
            bot.send_sticker(message.chat.id, open(STICKER_DIR, 'rb'), reply_markup=markup)
            bot.send_message(message.chat.id, subcribe, parse_mode='html', reply_markup=markup)
            mge = CheckRpi(MongoConnect(MGE_DIR).data)
            mge_weak = mge.get_weak(days=1)
            mge_message = get_message(mge_weak)
            niac_brest = CheckRpi(PGConnect(NIAC_BREST_DIR).data)
            niac_brest_weak = niac_brest.get_weak(days=1)
            niac_brest_message = get_message(niac_brest_weak)
            niac_tat = CheckRpi(PGConnect(NIAC_TAT_DIR).data)
            niac_tat_weak = niac_tat.get_weak(**{'6': 1, '7': 2, '8': 0}, days=1)
            niac_tat_message = get_message(niac_tat_weak)
            count = len(mge_weak) + len(niac_brest_weak) + len(niac_tat_weak)
            response = __change_first_element(mge_message, 'МосГорЭкспертиза') + \
                       __change_first_element(niac_brest_message, 'ГАУ \'НИАЦ\' ул.1-я Брестская, д.27') + \
                       __change_first_element(niac_tat_message, 'ГАУ \'НИАЦ\' ул.Б.Татарская, д.7, к.3')
            if count > 0:
                header = f'За последние сутки на всех контурах обнаружен{__ending(count % 10)[0]} <b>{count}</b> ' \
                         f'неработающ{__ending(count % 10)[1]} модул{__ending(count % 10)[2]}:'
                response.reverse()
                response.append(header)
                response.reverse()
            else:
                response = ["Неработающих модулей за последние сутки не обнаружено!"]
            get_response(message, response, markup)

        elif message.text.strip().lower() == name_of_buttons[0].lower():
            company = " в МосГорЭкспертизе"
            bot.send_sticker(message.chat.id, open(STICKER_DIR, 'rb'), reply_markup=markup)
            bot.send_message(message.chat.id, __make_subcribe(company), parse_mode='html', reply_markup=markup)
            mge = CheckRpi(MongoConnect(MGE_DIR).data)
            get_response(message, get_message(mge.get_weak(sort_1='switch', sort_2='port'), company), markup)

        elif message.text.strip().lower() == name_of_buttons[1].lower():
            company = " в ГАУ 'НИАЦ' по адресу ул. 1-я Брестская д.27"
            bot.send_sticker(message.chat.id, open(STICKER_DIR, 'rb'), reply_markup=markup)
            bot.send_message(message.chat.id, __make_subcribe(company), parse_mode='html', reply_markup=markup)
            niac_brest = CheckRpi(PGConnect(NIAC_BREST_DIR).data)
            get_response(message, get_message(niac_brest.get_weak(sort_1='switch', sort_2='port'), company), markup)

        elif message.text.strip().lower() == name_of_buttons[2].lower():
            company = " в ГАУ 'НИАЦ' по адресу ул. Б.Татарская д.7 к.3"
            bot.send_sticker(message.chat.id, open(STICKER_DIR, 'rb'), reply_markup=markup)
            bot.send_message(message.chat.id, __make_subcribe(company), parse_mode='html', reply_markup=markup)
            niac_tat = CheckRpi(PGConnect(NIAC_TAT_DIR).data)
            get_response(message, get_message(niac_tat.get_weak(**{'6': 1, '7': 2, '8': 0},
                                                                sort_1='switch', sort_2='port'), company), markup)

        else:
            response = f'Нажмите на кнопки внизу, чтобы проверить интересующие Вас контуры!'
            bot.send_message(message.chat.id, response, parse_mode='html', reply_markup=markup)

    except Exception as e:
        bot.send_message(message.chat.id, f'[ERROR] {e}', parse_mode='html', reply_markup=markup)


print("bot.polling is active")
bot.polling(none_stop=True)