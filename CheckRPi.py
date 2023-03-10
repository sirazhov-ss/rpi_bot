#!/usr/bin/python

import abc
import psycopg2
from sshtunnel import SSHTunnelForwarder
from ssh_pymongo import MongoSession
from os import path
from datetime import datetime, timedelta


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

    def __get_room(self, collection: dict) -> list:
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
        self.weak = self.get_weak()

    def __str_to_digit(self, var):
        if not isinstance(var, str) or not var.isdigit():
            return var
        else:
            digit = int(var.replace('.', ''))
            return digit

    def __sort_list(self, lst: list, key1='', key2='') -> list:
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

    def get_weak(self, days=365, sort_1='date_income', sort_2='', **kwargs) -> list:
        date = datetime.now() - timedelta(minutes=3)
        date_range = [date, date - timedelta(days=days)]
        self.weak = []
        j = 0
        for i in range(len(self.__data)):
            if date_range[0] >= self.__data[i].get('date_income') > date_range[1]:
                self.weak.append(self.__data[i])
                floor = str(self.weak[j].get('floor', None))
                if floor is not None and len(kwargs) > 0:
                    if floor in kwargs.keys():
                        self.weak[j]['floor'] = kwargs.get(floor)
                j += 1
        return self.__sort_list(self.weak, sort_1, sort_2)

    def __repr__(self):
        return f'{self.__data}'


if __name__ == '__main__':
    MGE_DIR = r'c:\mge.config'
    NIAC_BREST_DIR = r'c:\niac_brest.config'
    NIAC_TAT_DIR = r'c:\niac_tat.config'

    mge = CheckRpi(MongoConnect(MGE_DIR).data)
#    res = mge.get_weak(**{'3': 9, '4': 8}, days=30)
    res = mge.get_weak(sort_1='switch', sort_2='port')
    for i in range(len(res)):
        print(res[i])

