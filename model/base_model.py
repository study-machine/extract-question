# coding=utf-8
import pymysql
from utils import MyLocalException

config = {
    # 'host': 'test.wangxiyang.com',
    'host': '10.10.228.163',
    # 'user': 'root',
    'user': 'test',
    'port': 3301,
    # 'password': 'asd123',
    'password': 'OnlyKf!@#',
    'db': 'tiku',
    # 'db': 'tiku-dev',
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor,
}


class BaseModel(object):
    conn = pymysql.connect(**config)

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

    @classmethod
    def get_cursor(cls):
        return cls.conn.cursor()

    @classmethod
    def select(cls, sql):
        cursor = cls.get_cursor()
        cursor.execute(sql)
        return cursor.fetchall()

    @classmethod
    def insert(cls, sql, auto_commit=True):
        cursor = cls.get_cursor()
        cursor.execute(sql)
        if auto_commit:
            cls.commit()
        return cursor.lastrowid

    @classmethod
    def commit(cls):
        cls.conn.commit()
