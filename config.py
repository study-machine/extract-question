# coding=utf-8
import pymysql


class DatabaseConfig(object):
    local_db = {
        'host': 'test.wangxiyang.com',
        'user': 'root',
        'port': 3306,
        'password': 'asd123',
        'db': 'tiku-dev',
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
