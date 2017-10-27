# coding=utf-8
import pymysql
from config import *
from utils import MyLocalException

config = DatabaseConfig.local_db


# config = DatabaseConfig.dev_db

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
