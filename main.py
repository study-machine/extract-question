# coding=utf8
from random import shuffle
from model.tiku_model import *
from utils import *

# 版本、册、年级的限定
# key为上线版本ID，value为15为一年级上下册，二年级上；True,False是否新版
LIMIT_VERSIONS = {
    1: 15,  # 人教版
    100: 15,  # 苏教版
    75: 15,  # 北师大版
    10449: 30,  # 人教(新版)
    10450: 30,  # 苏教(新版)
    10453: 30,  # 北师大(新版)
}


def get_all_versions():
    log.info('开始')
    all_versions = JiaoCaiVersion.get_all_version()

    # 限定的版本
    target_versions = {k for k in LIMIT_VERSIONS.keys()}
    versions = [v for v in all_versions if v.id in target_versions]
    if not versions:
        log.error('没有找到限定要求版本的')
        return
    log.info('处理的版本:{}'.format(versions))

    for v in versions:
        log.info('开始获取版本：%s的教材' % v.name)
        get_jiaocais(v)


def get_jiaocais(version):
    log.info('开始获取教材：%s的课程' % version.name)
    version.get_jiaocai()
    jiaocais = version.jiaocais
    log.info(jiaocais)

    # 限定年级
    if LIMIT_VERSIONS.get(version.id, 0) == 15:
        jiaocais = [j for j in jiaocais if j.grade in [2, 3]]   # 旧版教材以三年级上下，二年级只要下册
    elif LIMIT_VERSIONS.get(version.id, 0) == 30:
        jiaocais = [j for j in jiaocais if j.grade in [1, 2]]   # 新版教材以一年级上下，二年级只要上册
    log.info('获得的教材:{}'.format(jiaocais))
    if not jiaocais:
        log.error('版本:%s无可用教材' % version.name)
        return

    for j in jiaocais:
        get_basic_assist(j, version)


def get_basic_assist(jiaocai, version):
    # 基础教辅
    basic_assists = jiaocai.get_relate_assist()
    if not basic_assists:
        log.error('教材:{}无可用教辅'.format(jiaocai.name))
        return

    # 创建新教辅
    new_assist = JiaocaiAssist(
        name='{vname}{grade}年级语文同步练关卡题'.format(vname=version.name, grade=jiaocai.grade),
        summary='练习题',
        jiaocai_id=jiaocai.id,
        grade=jiaocai.grade,
        subject=1,
        orderNum=1,
    )
    new_assist.insert_new_assist()
    log.info('Insert new 教辅id:{},name:{}'.format(new_assist.id, new_assist.name))

    get_ce(basic_assists[0], new_assist, jiaocai)


def get_ce(assist, new_assist, jiaocai):
    # 基础册，上册
    basic_ces = assist.get_relate_ce()

    if LIMIT_VERSIONS.get(jiaocai.id, 0) == 30 and jiaocai.grade == 2:  # 新版教材二年级只要上册
        basic_ces = [c for c in basic_ces if c.order_num == 1]
    if LIMIT_VERSIONS.get(jiaocai.id, 0) == 15 and jiaocai.grade == 2:  # 旧版教材二年级只要下册
        basic_ces = [c for c in basic_ces if c.order_num == 2]

    for basic_ce in basic_ces:
        new_ce = SectionCe(
            name=basic_ce.name,
            summary=basic_ce.summary,
            parent_id=0,
            order_num=1,
            assist_id=new_assist.id,
            jiaocai_id=new_assist.jiaocai_id,
            grade=new_assist.grade,
            subject=1
        )
        new_ce.insert_new_section()
        log.info('Insert new 册id:{},name:{}'.format(new_ce.id, new_ce.name))

        get_danyuan(basic_ce, new_ce)


def get_danyuan(ce, new_ce):
    danyuans = ce.get_child_danyuan_list()
    for i, danyuan in enumerate(danyuans):
        mg = MissionGroupGenerator(danyuan)
        # 一个单元最多45个关卡
        if len(mg.missions) > 45:
            mg.missions = mg.missions[:45]

        new_danyuan = SectionDanyuan(
            name='第{}单元'.format(i + 1),
            summary='语文同步练',
            parent_id=new_ce.id,
            parent_section=new_ce,
            order_num=i + 1,
            assist_id=new_ce.assist_id,
            jiaocai_id=new_ce.jiaocai_id,
            grade=new_ce.grade,
            subject=1,
        )
        new_danyuan.insert_new_section()
        log.info('Insert new 单元id:{},name:{}'.format(new_danyuan.id, new_danyuan.name))

        for m in mg.missions:
            m.parent_id = new_danyuan.id
            m.parent_section = new_danyuan
            m.assist_id = new_ce.assist_id
            m.jiaocai_id = new_ce.jiaocai_id
            m.grade = new_ce.grade
            m.subject = 1
            m.insert_new_section()
            log.info('Insert new 关卡id:{},name:{}'.format(m.id, m.name))
            m.insert_relate_section_question()
            print m


class MissionGroupGenerator(object):
    def __init__(self, danyuan):
        self.danyuan = danyuan
        self.mission_order = 1  # 一个单元的关卡序号从1开始
        self.missions = []

        self.get_courses()

    def get_courses(self):
        courses = self.danyuan.get_child_course_list()
        for c in courses:
            log.info('=' * 30)
            log.info('课程《%s》,id:%s' % (c.name, c.id))
            log.info('=' * 30)
            self.get_practice(c)

    def get_practice(self, course):
        """获取字或词的练习"""
        practices = course.get_child_practices()

        for practice in practices:
            if practice.name == '字词练习' or practice.name == '词汇':
                log.info('%s has %s' % (course.name, practice.name))

                # 找到确定添加的题
                qe = QuestionsExtractor(practice, course)
                confirm_questions = qe.confirm_qs
                # 一个课程的汉字或词语题目数量
                n = len(confirm_questions)
                if n < 6:
                    log.error('课程%s的%s题目低于6道，无法组成关卡' % (course.name, practice.name))
                    continue
                log.info('课程%s有%s题%d道' % (course.name, practice.name, n))

                for i in xrange(n / 6):
                    # 创建Misson
                    mission = Misson(
                        summary=course.name,
                        order_num=self.mission_order
                    )
                    self.mission_order += 1
                    mission.questions = confirm_questions[i * 6:i * 6 + 6]
                    log.info('课程%s 添加关卡%d' % (course.name, self.mission_order))
                    log.info(mission.questions)
                    self.missions.append(mission)


class QuestionsExtractor(object):
    def __init__(self, practice, course):
        self.practice = practice
        self.course = course
        self.confirm_qs = []

        self.too_many = False
        self.r = 1

        self.get_item()

    def get_item(self):
        """获取CategoryItem1 这里选字词练习和词汇"""
        items = CategoryItem.get_categoryitem_by_coursesection(self.practice.id)
        # 如果一个课程的字或词数量过多，取题逻辑微调
        if len(items) > 20:
            self.too_many = True
            self.r = randint(0, 1)

        if self.practice.name == '字词练习':
            log.debug('%s,开始抽取汉字问题' % self.course.name)
            c_qs, b_qs = self.extract_hanzi_question(items)

            # 汉字题需要排序
            c_qs = sort_hanzi_question(c_qs)
            # 如果不是6的倍数补全
            fix_six_times(c_qs, b_qs)

        elif self.practice.name == '词汇':
            log.debug('%s,开始抽取的词语问题' % self.course.name)
            c_qs, b_qs = self.extract_ciyu_question(items)
            # 如果不是6的倍数补全
            fix_six_times(c_qs, b_qs)
            # 打乱词语题的排序
            shuffle(c_qs)
        # 返回确定的题组
        if None in c_qs:
            raise MyLocalException('题目有空值')
        self.confirm_qs = c_qs

    def extract_hanzi_question(self, items):
        """抽汉字题"""
        confirm_questions = []  # 必须题
        back_questions = []  # 备选题
        for item in items:
            qs = Question.get_question_by_item(item.id)
            # 会写字逻辑
            if item.group == '会写':
                need_fix = 0  # 必须题补充数
                log.debug('<会写字>：{},{}'.format(item.id, item.name))
                # 字音题1道
                if not self.extract_confirm_questions(qs, '字音', confirm_questions, item.name):
                    if not self.too_many:
                        log.debug('%s no 字音题，需要补充' % item.name)
                        need_fix += 1
                # 字型题1道
                if not self.extract_confirm_questions(qs, '字形', confirm_questions, item.name):
                    if not self.too_many:
                        log.debug('%s no 字形题，需要补充' % item.name)
                        need_fix += 1
                # 字义题1道
                if not self.extract_confirm_questions(qs, '字义', confirm_questions, item.name):
                    log.debug('%s no 字义题，不补充了' % item.name)
                # 必须补充的题目
                if need_fix:
                    for n in xrange(need_fix):
                        q = pop_random_question(qs)
                        # 还有题，而且不是重复题
                        if q and q not in confirm_questions:
                            confirm_questions.append(q)
                            log.debug('%s 随机补充必选题 %s' % (item.name, q))
            # 会认字逻辑
            elif item.group == '会认':
                log.debug('<会认字>：{},{}'.format(item.id, item.name))
                # 字音题1道
                if not self.extract_confirm_questions(qs, '字音', confirm_questions, item.name):
                    log.debug('%s no 字音题，不补充了' % item.name)
            # 被抽到之外机抽1道题，分组时备选
            back_questions += self.extract_back_questions(qs, confirm_questions, 5)

        confirm_questions = list(set(confirm_questions))
        # 被选题不能和必选题冲突
        back_questions = list(set(back_questions) - set(confirm_questions))
        return confirm_questions, back_questions

    def extract_ciyu_question(self, items):
        """抽词语题"""
        confirm_questions = []
        back_questions = []
        for item in items:
            log.debug('获取到词语：%s' % item.name)
            qs = Question.get_question_by_item(item.id)
            if item.group == '近反义词练习':
                # 近义词和反义词题各1道
                if self.r and not self.extract_confirm_questions(qs, '近义词', confirm_questions, item.name):
                    log.debug('%s no 近义词题，不补充了' % item.name)
                if not self.r and not self.extract_confirm_questions(qs, '反义词', confirm_questions, item.name):
                    log.debug('%s no 反义词题，不补充了' % item.name)
            else:
                log.debug('%s has no 反义词题' % item.name)
            # 被抽到之外机抽1道题，分组时备选
            back_questions += self.extract_back_questions(qs, confirm_questions, 5)
        confirm_questions = list(set(confirm_questions))
        back_questions = list(set(back_questions) - set(confirm_questions))
        if not check_qs_none(confirm_questions):
            raise MyLocalException('题目有空值')
        return confirm_questions, back_questions

    def extract_confirm_questions(self, qs, q_type, confirm_qs, i_name=''):
        """根据类型抽取必选题"""
        q = pop_random_question_by_type(qs, q_type)
        if not q or q.id in {q.id for q in confirm_qs}:
            log.debug('%s no %s题型' % (i_name, q_type))
            return False
        confirm_qs.append(q)
        log.debug('%s 增加%s题%s' % (i_name, q_type, q))
        return True

    def extract_back_questions(self, qs, confirm_qs, n):
        """备选题，已选题之外再抽至少n道题"""
        b_qs = []
        left_qs = list(set(qs) - set(confirm_qs))
        for x in xrange(min(n, len(qs))):
            q = pop_random_question(left_qs)
            if not q:
                return []
            if q.id in {q.id for q in confirm_qs}:
                continue
            b_qs.append(q)
            log.debug('添加备选题%s' % q)
        return b_qs


if __name__ == '__main__':
    get_all_versions()
