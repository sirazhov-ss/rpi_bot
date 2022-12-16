#/usr/bin/python

import telebot
from telebot import types
from os import path
from CheckRPi.main import MongoConnect, PGConnect, CheckRpi

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

    return config


print (get_config(r'c:\mge.config'))
print (get_config(r'c:\niac_brest.config'))
print (get_config(r'c:\niac_tat.config'))

bot=telebot.TeleBot(open(r'c:\token'))


#

# @bot.message_handler()
# def send_weak(message):
#     if message.text.strip().lower() == "мгэ":
#         response = button_message(weak_mge, "МГЭ")
#     elif message.text.strip().lower() == "ниац брестская":
#         stock_niac_brest = get_stock_postgres(REMOTE_HOST_NIAC_BREST, REMOTE_PORT_NIAC_BREST, REMOTE_BIND_ADDRESS_NIAC_BREST, USERNAME_NIAC_BREST, "NIAC_BREST")
#         weak_niac_brest = get_weak(stock_niac_brest,+3)
#         response = button_message(weak_niac_brest, "ГАУ \"НИАЦ\" по адресу 1-я Брестская д.27", 0)
#     elif message.text.strip().lower() == "ниац татарская":
#         stock_niac_tat = get_stock_postgres(REMOTE_HOST_NIAC_TAT, REMOTE_PORT_NIAC_TAT, REMOTE_BIND_ADDRESS_NIAC_TAT, USERNAME_NIAC_TAT, "NIAC_TAT")
#         weak_niac_tat = get_weak(stock_niac_tat,+3)
#         response = button_message(weak_niac_tat, "ГАУ \"НИАЦ\" по адресу Б.Татарская д.7 к.3", 0)
#     elif message.text.strip().lower() == "старт":
#         return start(message)
#     elif message.text.strip().lower() == "стоп":
#         return stop(message)
#     elif message.text.strip().lower() == "помощь":
#         return help(message)
#     else:
#         response = ["Привет! Чтобы ознакомиться с тем, что я умею, наберите /help или напишите <b><u>помощь</u></b>."]
#     for i in range(len(response)):
#         bot.send_message(message.chat.id, response[i], parse_mode='html')
#
#
# print ("bot.polling is active")
bot.polling(none_stop=True)