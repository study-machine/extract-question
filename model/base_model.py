import pymysql

config = {
    'host': 'test.wangxiyang.com',
    'user': 'root',
    'password': 'asd123',
    'db': 'tiku',
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
