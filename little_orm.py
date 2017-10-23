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
    @classmethod
    def get_cursor(cls):
        return cls.conn.cursor()

