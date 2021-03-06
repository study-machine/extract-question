# coding=utf-8
import pymysql


class DatabaseConfig(object):
    local_db = {
        'host': 'test.wangxiyang.com',
        'user': 'root',
        'port': 3306,
        'password': 'asd123',
        'db': 'tiku2',
        'charset': 'utf8mb4',
        'cursorclass': pymysql.cursors.DictCursor,
    }

    dev_db = {
        'host': '10.10.228.163',
        'user': 'test',
        'port': 3301,
        'password': 'OnlyKf!@#',
        'db': 'tiku',
        'charset': 'utf8mb4',
        'cursorclass': pymysql.cursors.DictCursor,
    }

    QA_db = {
        'host': '10.9.35.226',
        'user': 'test',
        'port': 3329,
        'password': 'qaOnly!@#',
        'db': 'tiku',
        'charset': 'utf8mb4',
        'cursorclass': pymysql.cursors.DictCursor,
    }

    # 本地开发速算盒子总库
    dev_susuan_db = {
        'host': 'test.wangxiyang.com',
        'user': 'root',
        'port': 3306,
        'password': 'asd123',
        'db': 'knowboxstore4',
        'charset': 'utf8mb4',
        'cursorclass': pymysql.cursors.DictCursor,
    }
    # 速算题库总库线上库
    online_susuan_db = {
        'host': '10.19.141.31',
        'user': 'wangxy',
        'port': 3306,
        'password': 'wangxy112',
        'db': 'knowboxstore',
        'charset': 'utf8mb4',
        'cursorclass': pymysql.cursors.DictCursor,
    }
    # 线上从库
    online_slave_db = {
        'host': '10.215.48.111',
        'user': 'liyj',
        'port': 3306,
        'password': 'liyj123',
        'db': 'tiku',
        'charset': 'utf8mb4',
        'cursorclass': pymysql.cursors.DictCursor,
    }


db_config_read = DatabaseConfig.online_susuan_db
db_config_write = DatabaseConfig.online_susuan_db


class DevDB(object):
    """开发库表名"""
    # 版本表
    T_VERSION = 'wx_edu_teachingmaterial'
    # 教材表
    T_JIAOCAI = 'wx_edu_jiaocai'
    # 教辅表
    T_ASSIST = 'wx_edu_teachingassist'
    # 章节表
    T_SECTION = 'wx_edu_coursesection'
    # CategoryItem表
    T_ITEM = 'edu_categoryitem'
    # 题目表
    T_QUESTION = 'wx_edu_questions_new'
    # 章节和Item关联表
    R_SECTION_ITEM = 'edu_relate_coursesectioncategory'
    # 题目和Item关联表
    R_QUESTION_ITEM = 'edu_relate_questioncategory'


class SusuanDB(object):
    """速算总库表名"""
    # 版本表
    T_VERSION = 'base_edition'
    # 教材表
    T_JIAOCAI = 'base_book'
    # 教辅表
    T_ASSIST = 'base_assist'
    # 章节表
    T_SECTION = 'bass_course_section'
    # CategoryItem表,速算总库没有
    T_ITEM = ''
    # 题目表
    T_QUESTION = 'base_question'
    # 章节和Item关联表
    R_SECTION_ITEM = 'relate_section_question'
    # 题目和Item关联表,速算总库没有
    R_QUESTION_ITEM = ''
