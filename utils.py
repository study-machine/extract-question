# coding=utf8
from datetime import datetime
from random import randint
import logging as log

log.basicConfig(
    level=log.DEBUG,
    format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
    datefmt='%y-%m-%d %H:%M:%S',
    filename='log/question.log',
    filemode='w')


class MyLocalException(Exception):
    pass


def get_datetime_str():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def uni_to_u8(s):
    if isinstance(s, unicode):
        return s.encode('utf8')
    return s


def fix_six_times(c_qs, b_qs):
    """不足6的倍数，备选题补全"""
    n = len(c_qs) % 6
    if n != 0:
        if len(b_qs) < 6 - n:
            # 被选题数量并不足以补全
            c_qs = c_qs[:n * 6]
            return
        for i in xrange(6 - n):
            # 随机从备选题中补足6的倍数
            q = pop_random_question(b_qs)
            if q:
                c_qs.append(q)


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


def check_qs_none(qs):
    for q in qs:
        if q is None:
            return False
    return True
