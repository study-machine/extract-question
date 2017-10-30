# coding=utf-8
import pymysql
from config import *
from utils import MyLocalException


class BaseModel(object):
    # 读库的连接
    conn_read = pymysql.connect(**db_config_read)
    # 写库的连接
    conn_write = pymysql.connect(**db_config_write)

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

    @classmethod
    def get_read_cursor(cls):
        return cls.conn_read.cursor()

    @classmethod
    def get_write_cursor(cls):
        return cls.conn_write.cursor()

    @classmethod
    def select(cls, sql):
        cursor = cls.get_read_cursor()
        cursor.execute(sql)
        return cursor.fetchall()

    @classmethod
    def insert(cls, sql, auto_commit=True):
        cursor = cls.get_write_cursor()
        cursor.execute(sql)
        if auto_commit:
            cls.commit()
        return cursor.lastrowid

    @classmethod
    def commit(cls):
        cls.conn_write.commit()
