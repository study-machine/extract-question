# coding=utf8
from model.tiku_model import *
from utils import *


def get_all_versions():
    log.info('获取所有版本')
    all_versions = JiaoCaiVersion.get_all_version()
    log.info(all_versions)
    for v in all_versions:
        log.info('开始获取版本：%s的教材' % v.name)
        get_jiaocais(v)


def get_jiaocais(version):
    log.info('开始获取教材：%s的课程' % version.name)
    version.get_jiaocai()
    jiaocais = version.jiaocais
    log.info(jiaocais)
    if not jiaocais:
        log.warning('版本:%s无可用教材' % version.name)
        return
    for j in jiaocais[1:]:
        get_basic_assist(j)


def get_basic_assist(jiaocai):
    assists = jiaocai.get_relate_assist()
    get_ce(assists[0])


def get_ce(assist):
    ces = assist.get_relate_ce()
    get_danyuan(ces[0])


def get_danyuan(ce):
    danyuans = ce.get_child_danyuan_list()
    for danyuan in danyuans:
        get_courses(danyuan)


class MissionGenerator(object):
    def __init__(self, danyuan):
        self.danyuan = danyuan



def get_courses(danyuan):
    courses = danyuan.get_child_course_list()
    for c in courses:
        log.info('=' * 30)
        log.info('课程《%s》,id:%s' % (c.name, c.id))
        log.info('=' * 30)
        get_practice(c)


def get_practice(course):
    """获取字或词的练习"""
    practices = course.get_child_practices()

    misson_group_order = 0

    for practice in practices:
        if practice.name == '字词练习' or practice.name == '词汇':
            log.info('%s has %s' % (course.name, practice.name))

            # 找到确定添加的题
            confirm_questions = get_item(practice.id, practice.name, course)
            # 一个课程的汉字或词语题目数量
            n = len(confirm_questions)
            if n < 6:
                log.error('课程%s的%s题目低于6道，无法组成关卡' % (course.name, practice.name))
                continue
            log.info('课程%s有%s题%d道' % (course.name, practice.name, n))
            for i in xrange(n / 6):
                misson_group_order += 1
                # 创建MissonGroup
                mg = MissonGroup(id=course.id, summary=practice.name, order_num=misson_group_order)
                mg.questions = confirm_questions[i * 6:i * 6 + 6]
                log.info('课程%s 添加关卡%d' % (course.name, misson_group_order))
                log.info(mg.questions)
                print mg





def get_item(practice_id, practice_name, course):
    """获取CategoryItem1 这里选字词练习和词汇"""
    items = CategoryItem.get_categoryitem_by_coursesection(practice_id)
    if practice_name == '字词练习':
        log.debug('%s,开始抽取汉字问题' % course.name)
        c_qs, b_qs = extract_hanzi_question(items)
        # 汉字题需要排序
        c_qs = sort_hanzi_question(c_qs)
        # 如果不是6的倍数补全
        fix_six_times(c_qs, b_qs)

    elif practice_name == '词汇':
        log.debug('%s,开始抽取的词语问题' % course.name)
        c_qs, b_qs = extract_ciyu_question(items)
        # 如果不是6的倍数补全
        fix_six_times(c_qs, b_qs)
    # 返回确定的题组
    return c_qs


def extract_hanzi_question(items):
    """抽汉字题"""
    confirm_questions = []  # 必须题
    back_questions = []  # 备选题
    for item in items:
        qs = Question.get_question_by_item(item.id)
        # 会写字逻辑
        if item.group == '会写':
            need_fix = 0  # 必须题补充数
            log.debug('<会写字>：%s' % item.name)
            # 字音题1道
            if not extract_confirm_questions(qs, '字音', confirm_questions, item.name):
                log.debug('%s no 字音题，需要补充' % item.name)
                need_fix += 1
            # 字型题1道
            if not extract_confirm_questions(qs, '字形', confirm_questions, item.name):
                log.debug('%s no 字形题，需要补充' % item.name)
                need_fix += 1
            # 字义题1道
            if not extract_confirm_questions(qs, '字义', confirm_questions, item.name):
                log.debug('%s no 字义题，不补充了' % item.name)
            # 必须补充的题目
            if need_fix:
                for n in xrange(need_fix):
                    q = pop_random_question(qs)
                    if q:
                        confirm_questions.append(q)
                        log.debug('%s 随机补充必选题 %s' % (item.name, q))
        # 会认字逻辑
        elif item.group == '会认':
            log.debug('<会认字>：%s' % item.name)
            # 字音题1道
            if not extract_confirm_questions(qs, '字音', confirm_questions, item.name):
                log.debug('%s no 字音题，不补充了' % item.name)
        # 被抽到之外机抽1道题，分组时备选
        back_questions += extract_back_questions(qs, confirm_questions, 1)
    return confirm_questions, back_questions


def extract_ciyu_question(items):
    """抽词语题"""
    confirm_questions = []
    back_questions = []
    for item in items:
        log.debug('获取到词语：%s' % item.name)
        qs = Question.get_question_by_item(item.id)
        if item.group == '近反义词练习':
            # 近义词和反义词题各1道
            if not extract_confirm_questions(qs, '近义词', confirm_questions, item.name):
                log.debug('%s no 近义词题，不补充了' % item.name)
            if not extract_confirm_questions(qs, '反义词', confirm_questions, item.name):
                log.debug('%s no 反义词题，不补充了' % item.name)
        else:
            log.debug('%s has no 反义词题' % item.name)
        # 被抽到之外机抽1道题，分组时备选
        back_questions += extract_back_questions(qs, confirm_questions, 1)
    return confirm_questions, back_questions


def extract_confirm_questions(qs, q_type, confirm_qs, i_name=''):
    """根据类型抽取必选题"""
    q = pop_random_question_by_type(qs, q_type)
    if not q:
        log.debug('%s no %s题型' % (i_name, q_type))
        return False
    confirm_qs.append(q)
    log.debug('%s 增加%s题%s' % (i_name, q_type, q))
    return True


def extract_back_questions(qs, confirm_qs, n):
    """备选题，已选题之外再抽至少n道题"""
    b_qs = []
    left_qs = list(set(qs) - set(confirm_qs))
    for x in xrange(min(n, len(qs))):
        q = pop_random_question(left_qs)
        b_qs.append(q)
        log.debug('添加备选题%s' % q)
    return b_qs


if __name__ == '__main__':
    get_all_versions()
