#!/usr/bin/python

import abc
import psycopg2
from sshtunnel import SSHTunnelForwarder
from ssh_pymongo import MongoSession
from os import path
from datetime import datetime


class IConnect(abc.ABC):

    @abc.abstractmethod
    def get_data(self) -> list:
        '''Возвращает список всех пих'''
        pass

    @classmethod
    def get_config(cls, config_directory):
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


class PGConnect(IConnect):
    def __init__(self, config_directory):
        self.__template = ('remote_host', 'remote_port', 'remote_username', 'remote_password',
                          'db_host', 'db_port', 'db_name', 'db_username', 'db_password')
        self.__params = IConnect.get_config(config_directory)
        for key in range(len(self.__template)):
            if not self.__template[key] in self.__params:
                raise Exception(f"Connection failed! Missing parameter: '{key}'")
        self.data = self.get_data()

    def __get_fields(self, cursor, table_name):
        cursor.execute(f"SELECT column_name FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = '{table_name}';")
        cls_fields = cursor.fetchall()
        fields = tuple()
        for element in range(len(cls_fields)):
            fields += cls_fields[element]
        return fields

    def __get_table(self, cursor, table_name):
        fields = self.__get_fields(cursor, table_name)
        cursor.execute(f"SELECT * FROM so.{table_name};")
        cls_data = cursor.fetchall()
        data = []
        for note in range(len(cls_data)):
            data.append(dict(zip(fields, cls_data[note])))
        return data

    def __get_stock(self, table: list, room: list):
        data = []
        for i in range(len(table)):
            floor = None
            title = None
            for j in range(len(room)):
                if table[i].get('rp_id') == room[j].get('rp_id'):
                    floor = room[j].get('floor', None)
                    title = room[j].get('title', 'unknown')
                    break
            if floor is None:
                floor = 'unknown'
            if title is None:
                title = 'unknown'
            data.append({
                'floor': floor,
                'title': title,
                'rp_id': table[i].get('rp_id'),
                'rp_ip': table[i].get('rp_ip', None),
                'switch': table[i].get('switch', None),
                'port': table[i].get('port', None),
                'date_income': table[i].get('date_income', None)
                })
        return data

    def get_data(self) -> list:
        with SSHTunnelForwarder(
                (self.__params.get('remote_host'), self.__params.get('remote_port')),
                ssh_username=self.__params.get('remote_username'),
                ssh_password=self.__params.get('remote_password'),
                remote_bind_address=(self.__params.get('db_host'), self.__params.get('db_port'))) as server:
            server.start()
            connection = psycopg2.connect(database=self.__params.get('db_name'),
                                          user=self.__params.get('db_username'),
                                          password=self.__params.get('db_password'),
                                          host='127.0.0.1',
                                          port=server.local_bind_port)

            cursor = connection.cursor()
            table = self.__get_table(cursor, 'raspberry_info')
            room = self.__get_table(cursor, 'global_room_config')
            data = self.__get_stock(table, room)
        server.stop()
        return data


class MongoConnect(IConnect):
    def __init__(self, config_directory):
        self.__template = ('remote_host', 'remote_port', 'remote_username', 'remote_password',
                          'db_host', 'db_port', 'db_name', 'db_username', 'db_password')
        self.__params = IConnect.get_config(config_directory)
        for key in range(len(self.__template)):
            if not self.__template[key] in self.__params:
                raise Exception(f"Connection failed! Missing parameter: '{key}'")
        self.data = self.get_data()

    def __get_room(self, collection:dict) -> list:
        room = list()
        floor = None
        for document in collection:
            floor = document.get('floor', None)
            if floor is not None:
                floor = int(floor)
            rooms = document.get('rooms')
            for i in range(len(rooms)):
                room.append({
                    'rp_id': rooms[i].get('rpId'),
                    'title': rooms[i].get('title', 'unknown'),
                    'floor': floor
                    })
        return room

    def __get_stock(self, collection: dict, room: list):
        data = []
        for document in collection:
            floor = None
            title = None
            for note in range(len(room)):
                if document.get('rpId') == room[note].get('rp_id'):
                    floor = room[note].get('floor', None)
                    title = room[note].get('title', 'unknown')
                    break
                else:
                    floor = 'unknown'
                    title = 'unknown'
            data.append({
                'floor': floor,
                'title': title,
                "rp_id": document.get('rpId'),
                "rp_ip": document.get('rpIp', None),
                "switch": document.get('switch', None),
                "port": document.get('port', None),
                "date_income": document.get('dateIncome', None)
                })
        return data

    def get_data(self) -> list:
        session = MongoSession(
            host=self.__params.get('remote_host'),
            port=self.__params.get('remote_port'),
            user=self.__params.get('remote_username'),
            password=self.__params.get('remote_password'),
            uri=f"mongodb://{self.__params.get('db_username')}:{self.__params.get('db_password')}@" +
                f"{self.__params.get('db_host')}:{self.__params.get('db_port')}/")

        db=session.connection[self.__params.get('db_name')]
        collection = db.sysRoomsInfo.find({})
        room = self.__get_room(collection)
        collection = db.sysConfig.find({})
        data = self.__get_stock(collection, room)
        session.stop()
        return data


class CheckRpi:
    def __init__(self, data):
        if isinstance(data, list):
            self.__data = data
        else:
            raise TypeError(f'Object "connection" must be instance of class "list"!')
        self.weak = []

    def __check_date(self) -> list:
        last_day = 1
        last_month = 1
        last_year = 2021
        date = datetime.fromtimestamp(round(datetime.timestamp(datetime.now()), 0)
                                      ).strftime("%Y,%m,%d,%H,%M").split(",")
        year = int(date[0])
        month = int(date[1])
        day = int(date[2])
        hour = int(date[3])
        minute = int(date[4])
        if (minute - 2) < 0:
            minute = 0
            if (hour - 1) < 0:
                hour = 0
            else:
                hour -= 1
        else:
            minute -= 2

        date_range = [datetime(year, month, day, hour, minute), datetime(last_year, last_month, last_day, 0, 0)]
        return date_range

    def __format_date(self, x):
        return datetime.strftime(datetime.fromtimestamp(round(datetime.timestamp(x), 0)), "%d/%m/%y %H:%M:%S")

    def __ending(self, remainder):
        if remainder == 1:
            ending_array = ["", "ий", "ь"]
        elif (remainder > 1) and (remainder <= 3):
            ending_array = ["о", "их", "я"]
        else:
            ending_array = ["о", "их", "ей"]
        return ending_array

    def __str_to_digit(self, var):
        if not isinstance(var, str) or not var.isdigit():
            return var
        else:
            digit = int(var.replace('.', ''))
            return digit

    def __sort_list(self, lst:list, key1='', key2='') -> list:
        for cnt in range(len(lst)-1, 0, -1):
            for i in range(cnt):
                current_element1 = self.__str_to_digit(lst[i].get(key1, 0))
                previous_element1 = self.__str_to_digit(lst[i + 1].get(key1, 0))
                current_element2 = self.__str_to_digit(lst[i].get(key2, 0))
                previous_element2 = self.__str_to_digit(lst[i + 1].get(key2, 0))
                if current_element1 > previous_element1:
                    lst[i], lst[i + 1] = lst[i + 1], lst[i]
                elif (current_element1 == previous_element1) and (current_element2 > previous_element2):
                    lst[i], lst[i + 1] = lst[i + 1], lst[i]
        return lst

    def get_weak(self, **kwargs) -> list:
        weak = list()
        date_range = self.__check_date()
        j = 0
        for i in range(len(self.__data)):
            if date_range[0] >= self.__data[i].get('date_income') > date_range[1]:
                weak.append(self.__data[i])
                floor = str(weak[j].get('floor', None))
                if floor is not None and len(kwargs) > 0:
                    if floor in kwargs.keys():
                        weak[j]['floor'] = kwargs.get(floor)
                j += 1
        self.weak = self.__sort_list(weak, 'switch', 'port')
        return self.weak

    def get_message(self, array, company=""):
        subscribe = f"На данный момент{company} обнаружен, неработающ, модул".split(',')
        if len(array) > 0:
            message_array = []
            count = 20
            whole = len(array) // count
            remainder = len(array) % count
            ending_remainder = remainder % 10
            message = f"\n\r{subscribe[0] + self.__ending(ending_remainder)[0]} {whole * count + remainder} " \
                      f"{subscribe[1] + self.__ending(ending_remainder)[1]} " \
                      f"{subscribe[2] + self.__ending(ending_remainder)[2]}:\n\r"
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
        date_income: {self.__format_date(array[i * count + j].get('date_income'))}\n\r\n\r"
                message_array.append(message)
            message = ""
            for i in range(remainder):
                message += f"{whole * count + i + 1})    title: {array[whole * count + i].get('title')}\n\r\
        floor: {array[whole * count + i].get('floor')}\n\r\
        rp_id: {array[whole * count + i].get('rp_id')}\n\r\
        rp_ip: {array[whole * count + i].get('rp_ip')}\n\r\
        switch: {array[whole * count + i].get('switch')}\n\r\
        port: {array[whole * count + i].get('port')}\n\r\
        date_income: {self.__format_date(array[whole * count + i].get('date_income'))}\n\r\n\r"
            message_array.append(message)
            return message_array
        else:
            return []

    def __repr__(self):
        return f'{self.__data}'


if __name__ == '__main__':
    MGE_DIR = r'c:\mge.config'
    NIAC_BREST_DIR = r'c:\niac_brest.config'
    NIAC_TAT_DIR = r'c:\niac_tat.config'

    mge = CheckRpi(MongoConnect(MGE_DIR).data)
    res = mge.get_weak(**{'3': 9, '4': 8})
    for i in range(len(res)):
        print(res[i])

