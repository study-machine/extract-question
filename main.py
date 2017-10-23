# coding=utf8
import logging
from random import randint
from tiku_model import *
from category import *

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
    datefmt='%y%m%d %H:%M:%S',
    filename='extractQuestion.log',
    filemode='w')


def get_all_versions():
    logging.debug('获取所有版本')
    all_versions = JiaoCaiVersion.get_all_version()
    logging.debug(all_versions)
    for v in all_versions[:1]:
        logging.debug('开始获取版本：%s的教材' % v.name)
        get_jiaocais(v)


def get_jiaocais(version):
    logging.debug('开始获取教材：%s的课程' % version.name)
    version.get_jiaocai()
    jiaocais = version.jiaocais
    logging.debug(jiaocais)
    if not jiaocais:
        logging.warning('版本:%s无可用教材' % version.name)
        return
    for j in jiaocais[:2]:
        get_courses(j)


def get_courses(jiaocai):
    if not jiaocai:
        logging.warning('该教材%s无可用课程' % jiaocai.name)
        return
    logging.debug('开始获取教材id：%s的课程' % jiaocai.id)
    courses = jiaocai.get_courses()
    for c in courses[20:21]:
        logging.debug('%s，获取到课程' % c.name)
        get_practice(c)


def get_practice(course):
    course.get_practices()
    item_type = ''
    for practice in course.childs:
        if practice.name == '字词练习' or practice.name == '词汇':
            logging.debug('%s has %s' % (course.name, practice.name))
            get_item(practice.id, practice.name, course)


def get_item(p_id, p_name, course):
    """获取CategoryItem1 这里选字词练习和词汇"""
    items = CategoryItem.get_categoryitem_by_coursesection(p_id)
    if p_name == '字词练习':
        logging.debug('%s,开始抽取汉字问题' % course.name)
        extract_hanzi_question(items)
    elif p_name == '词汇':
        logging.debug('%s,开始抽取的词语问题' % course.name)
        extract_ciyu_question(items)


def extract_hanzi_question(items):
    """抽汉字题"""
    need_fix = 0
    confirm_questions = []  # 必须题
    back_questions = []  # 备选题
    for item in items[:1]:
        logging.debug('获取到汉字：%s' % item.name)
        qs = Question.get_question_by_item(item.id)
        # 会写字逻辑
        if item.group == '会写':
            # 字音题1道
            q = pop_random_question_by_type(qs, '字音')
            confirm_questions.append(q)
            logging.debug('%s 增加字音题%s' % (item.name, q))
            if not q:
                logging.debug('%s no 字音题，需要补充' % item.name)
                need_fix += 1
            # 字型题1道
            q = pop_random_question_by_type(qs, '字形')
            confirm_questions.append(q)
            logging.debug('%s 增加字形题%s' % (item.name, q))
            if not q:
                logging.debug('%s no 字形题，需要补充' % item.name)
                need_fix += 1
            # 字义题1道
            q = pop_random_question_by_type(qs, '字义')
            confirm_questions.append(q)
            logging.debug('%s 增加字义题 %s' % (item.name, q))
            if not q:
                logging.debug('%s no 字义题，不补充了' % item.name)
            # 必须补充的题目
            for n in xrange(need_fix):
                q = pop_random_question(qs)
                if q:
                    confirm_questions.append(q)
                    logging.debug('%s 随机补充必选题 %s' % (item.name, q))
        # 会认字逻辑
        elif item.group == '会认':
            # 字音题1道
            q = pop_random_question_by_type(qs, '字音')
            confirm_questions.append(q)
            logging.debug('%s 增加字音题%s' % (item.name, q))
            if not q:
                logging.debug('%s no 字音题' % item.name)
    # 被抽到之外机抽5道题，分组时备选
    back_questions = extract_back_questions(qs, confirm_questions)


def extract_ciyu_question(items):
    """抽词语题"""
    confirm_questions = []
    back_questions = []
    for item in items[:2]:
        logging.debug('获取到词语：%s' % item.name)
        qs = Question.get_question_by_item(item.id)
        if item.group == '近反义词练习':
            # 近义词和反义词题1道
            q = pop_random_question_by_type(qs, '近义词')
            confirm_questions.append(q)
            logging.debug('%s 增加近义词题 %s' % (item.name, q))
            if not q:
                logging.debug('%s no 近义词题，不补充了' % item.name)
                # 近义词和反义词题1道
            q = pop_random_question_by_type(qs, '反义词')
            confirm_questions.append(q)
            logging.debug('%s 增加反义词题 %s' % (item.name, q))
            if not q:
                logging.debug('%s no 反义词题，不补充了' % item.name)
    # 被抽到之外机抽5道题，分组时备选
    back_questions = extract_back_questions(qs, confirm_questions)


def extract_confirm_questions(qs, q_type, confirm_qs):
    q = pop_random_question_by_type(qs, q_type)
    if not q:
        logging.debug('%s no %s题，需要补充' % (item.name, q_type))
        return False
    confirm_qs.append(q)
    logging.debug('%s 增加%s题%s' % (item.name, q_type, q))
    return True


def extract_back_questions(qs, confirm_qs):
    """备选题，已选题之外再抽至少5道题"""
    b_qs = []
    left_qs = list(set(qs) - set(confirm_qs))
    for x in xrange(min(5, len(qs))):
        q = pop_random_question(left_qs)
        b_qs.append(q)
        logging.debug('添加备选题%s' % q)
    return b_qs


def pop_random_question_by_type(qs, q_type):
    """根据类型pop随机题目"""
    type_qs = [q for q in qs if q.q_type == q_type]
    return pop_random_question(type_qs)


def pop_random_question(qs):
    """选随机题目"""
    if qs:
        return qs.pop(randint(0, len(qs) - 1))


if __name__ == '__main__':
    get_all_versions()
