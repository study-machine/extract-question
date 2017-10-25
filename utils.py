# coding=utf8
from random import randint
import logging as log


class TestDB:
    """测试库表名"""
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


# 使用测试库名称
DB_NAME = TestDB

log.basicConfig(
    level=log.DEBUG,
    format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
    datefmt='%y%m%d %H:%M:%S',
    filename='question.log',
    filemode='w')


class MyLocalException(Exception):
    pass


def uni_to_u8(s):
    if isinstance(s, unicode):
        return s.encode('utf8')
    return s


def fix_six_times(c_qs, b_qs):
    """不足6的倍数，备选题补全"""
    n = len(c_qs) % 6
    if n != 0:
        for i in xrange(6 - n):
            # 随机从备选题中补足6的倍数
            c_qs.append(pop_random_question(b_qs))


def pop_random_question_by_type(qs, q_type):
    """根据类型pop随机题目"""
    type_qs = [q for q in qs if q.q_type == q_type]
    return pop_random_question(type_qs)


def pop_random_question(qs):
    """选随机题目"""
    if qs:
        return qs.pop(randint(0, len(qs) - 1))


def sort_hanzi_question(qs):
    """汉字题有排序需求，按照字音,字形,字义的顺序排列"""
    sort_value = {
        '字音': 1,
        '字形': 2,
        '字义': 3,
    }
    return sorted(qs, key=lambda q: sort_value.get(q.q_type, 4))


QUESTION_TYPE = {
    1: '字音',
    2: '字义',
    3: '字形',
    4: '听音选词',
    5: '结构',
    6: '笔顺',
    34542: '背诵题',
    34543: '朗读题',
    34544: '背诵题',
    39387: '近义词',
    39388: '反义词',
    39389: '量词',
    41729: '看图选音',
    41730: '看图辨识',
    41731: '直接背诵',
    41732: '作者/朝代',
    41733: '理解性背诵',
}


def get_question_type(id):
    """根据CategoryItemID获取CategoryID为1的题型"""
    q_type = QUESTION_TYPE.get(int(id), '')
    return q_type
