# coding=utf-8
import pymysql
from tiku_orm.tiku_model import QuestionRadio, QuestionItem, JiaoCaiVersion, JiaoCai, JiaocaiAssist, CourseSectionBase, \
    Misson
from random_questions.utils import uni_to_u8
from random_questions.utils import log, MyLocalException


def raw_questions_generator():
    local_db = {
        'host': 'test.wangxiyang.com',
        'user': 'root',
        'port': 3306,
        'password': 'asd123',
        'db': 'mytest',
        'charset': 'utf8mb4',
        'cursorclass': pymysql.cursors.DictCursor,
    }
    conn = pymysql.connect(**local_db)
    cursor = conn.cursor()
    sql = """
    select * from raw_questions;
    """
    cursor.execute(sql)
    for n in xrange(cursor.rowcount):
        yield cursor.fetchone()


def trans_question_body(body):
    """转化question的json格式"""
    body = body.strip()
    body = body.replace('（）', '（ ）')

    wrapper = """#{"type":"para_begin","style":"chinese_text"}#%s#{"type":"para_end"}#"""
    return wrapper % body


def trans_right_answer(answer):
    """转化RightAnswer的json格式"""
    answer = answer.strip()
    wrapper = """[{"blank_id":1,"choice":"%s"}]"""
    return wrapper % answer


def check_no_or_too_many(l, name1, name2):
    if not l:
        log.error('{}没有{}'.format(name1, name2))
        return False
    elif len(l) > 1:
        log.error('{}下的{}超过1个'.format(name1, name2))
        return True
    return True


class ParsedRawQuestion(object):
    def __init__(self, raw_question):
        self.raw_question = raw_question
        self.mission_num = raw_question['mission']
        self.danyuan_num = raw_question['danyuan']
        self.grade = raw_question['grade']
        self.version_name = raw_question['version_name']
        self.summary = raw_question['summary']

        # 获取所属版本、教材、教辅、册、单元
        self.version = None
        self.jiaocai = None
        self.assist = None
        self.ce = None
        self.danyuan = None
        self.mission = None
        self.question = None

        self.get_version()
        if not self.version:
            return
        self.get_jiaocai()
        if not self.jiaocai:
            return
        self.get_assist()
        if not self.assist:
            return
        self.get_ce()
        if not self.ce:
            return
        self.get_danyuan()
        if not self.danyuan:
            return

        self.cal_mission_order_num()

        # 题目和选项
        self.right_option = raw_question['right_option']
        self.create_question()
        self.create_item_group()

    def create_question(self):
        """创建question_obj并插入获取id"""
        body = trans_question_body(self.raw_question['body'])
        right_answer = trans_right_answer(self.raw_question['right_option'])
        question_obj = QuestionRadio(
            body=body,
            q_type=1,  # 单选
            right_answer=right_answer,
            answer_explain='同步练增补题',
            options='ABC',
            question_analyze='同步练增补题',
            subject=1,
            status=0
        )
        question_obj.insert_new_question()
        if not question_obj.id:
            raise MyLocalException('question没有id')
        self.question = question_obj

    def create_item_group(self):
        """创建并插入问题选项"""
        for option in ['A', 'B', 'C']:
            item = QuestionItem(
                content=self.raw_question[option],
                item_code=option,
                q_id=self.question.id,
                is_right='Y' if self.right_option == option else 'N'
            )
            item.insert_new_item()

    def get_version(self):
        self.version = JiaoCaiVersion.get_version_from_zongku(name=self.raw_question['version_name'])
        if self.version:
            log.debug('获取到题目所属版本{}'.format(self.version))

    def get_jiaocai(self):
        jiaocais = JiaoCai.get_jiaocai_by_version_from_zongku(self.version.id)
        jiaocais = [j for j in jiaocais if j.grade == self.grade]
        if check_no_or_too_many(jiaocais, '版本：{}的{}年级'.format(self.version.name, self.grade), '教材'):
            self.jiaocai = jiaocais[0]
            log.debug('获取到题目所属教材{}'.format(self.jiaocai))

    def get_assist(self):
        # 120为语文同步练教辅
        assists = JiaocaiAssist.get_assist_by_jiaocai_and_type_from_zongku(self.jiaocai.id, 120)
        if check_no_or_too_many(assists, '教材：{}'.format(self.jiaocai.name), '教辅'):
            self.assist = assists[0]
            log.debug('获取到题目所属教辅{}'.format(self.assist))

    def get_ce(self):
        ces = CourseSectionBase.get_by_assist_type_parent_order_from_zongku(
            a_id=self.assist.id,
            q_type=24,
            p_id=0,  # 册的ParentID为0
            order=1  # 本次只要上册
        )
        if check_no_or_too_many(ces, '教辅:{}'.format(self.assist.name), '册'):
            self.ce = ces[0]
            log.debug('获取到题目所属册{}'.format(self.ce))

    def get_danyuan(self):
        danyuans = CourseSectionBase.get_by_assist_type_parent_order_from_zongku(
            a_id=self.assist.id,
            q_type=24,
            p_id=self.ce.id,
            order=self.danyuan_num
        )
        if check_no_or_too_many(danyuans, '册:{}'.format(self.ce.name), '单元'):
            self.danyuan = danyuans[0]
            log.debug('获取到题目所属单元{}'.format(self.danyuan))

    def cal_mission_order_num(self):
        """关卡的序号放在这里计算"""
        if not self.danyuan:
            raise MyLocalException('没有单元，没法计算序号')
        missions = Misson.get_missions_by_ce_from_zongku(
            a_id=self.assist.id,
            q_type=24,
            p_id=self.danyuan.id
        )
        self.mission_order_num = missions[-1].order_num + self.mission_num


def start():
    log.info('开始')
    raw_qs = raw_questions_generator()
    # 新的关卡
    new_mission = None
    for i, rq in enumerate(raw_qs):
        rq = {uni_to_u8(k): uni_to_u8(v) for k, v in rq.items()}
        log.info('读取表格题目:{}'.format(rq['body']))
        # 解析raw_question
        pq = ParsedRawQuestion(rq)

        # 没有单元,说明没找到从属关系
        if not pq.danyuan:
            continue
        # 每六道题一个关卡
        if i % 6 == 0:
            new_mission = Misson(
                summary=pq.summary,
                order_num=pq.mission_order_num,
                parent_id=pq.danyuan.id,
                jiaocai_id=pq.jiaocai.id,
                assist_id=pq.assist.id,
                grade=pq.grade,
                subject=1,
                qt=24
            )
            new_mission.parent_section = pq.danyuan
            new_mission.insert_new_section()
        pq.question.insert_relate_with_mission(section_id=new_mission.id, a_id=pq.assist.id)
        print 'insert relate for 题目:{},关卡{}'.format(pq.question.id, new_mission.id)
    log.info('结束')
