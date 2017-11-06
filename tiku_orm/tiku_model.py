# coding=utf8
from tiku_orm.base_field import *
from tiku_orm.base_model import *
from random_questions.utils import *


class CourseSectionBase(BaseModel):
    id = 0  # SectionID
    name = ''  # SectionName
    summary = ''
    level = 0  # level
    parent_id = 0
    order_num = 0  # 顺序
    jiaocai_id = 0  # 教材_id
    assist_id = 0  # 教辅id
    grade = 0
    subject = 1  # 学科先固定1
    last = 0
    qt = 24  # CourseSection.QuestionType是api约定的🈯️值，同步练是24

    # 父节点实例
    parent_section = None

    def __init__(self, **kwargs):
        super(CourseSectionBase, self).__init__(**kwargs)
        self.section_order = 0

    def __repr__(self):
        return '<id:{},name:{},summary:{},order:{}>'.format(self.id, self.name, self.summary, self.order_num)

    def insert_new_section(self):
        self.section_order = self._cal_section_order()

        if self.write_db_type == 'zongku':
            # 总库表名和字段
            fields = dict(
                name=self.name,
                summary=self.summary,
                level=self.level,
                parent_id=self.parent_id,
                order_num=self.order_num,
                section_order=self.section_order,
                assist_id=self.assist_id,
                last=self.last,
                online_status=1,  # 同步线上库为1
                status=0  # 未删除为0
            )
            sql = """
            INSERT INTO base_course_section (name,summary,level,parent_id,
            order_num,section_order,assist_id,last,online_status,status)
            VALUES('{name}','{summary}',{level},{parent_id},
            {order_num},{section_order},{assist_id},{last},{online_status},{status})
            """.format(**fields)
        else:
            fields = dict(
                SectionName=self.name,
                Summary=self.summary,
                sLevel=self.level,
                ParentID=self.parent_id,
                OrderNum=self.order_num,
                JiaoCaiID=self.jiaocai_id,
                SectionOrder=self.section_order,
                TeachingAssistID=self.assist_id,
                Grade=self.grade,
                Subject=self.subject,
                QuestionType=self.qt,
                AddTime=get_datetime_str()
            )
            sql = """
            INSERT INTO wx_edu_coursesection (SectionName,Summary,sLevel,ParentID,
            OrderNum,JiaoCaiID,SectionOrder,TeachingAssistID,Grade,Subject,QuestionType,AddTime)
            VALUES('{SectionName}','{Summary}',{sLevel},{ParentID},
            {OrderNum},{JiaoCaiID},{SectionOrder},{TeachingAssistID},{Grade},{Subject},{QuestionType},'{AddTime}')
            """.format(**fields)
        self.id = self.insert(sql)

    def _cal_section_order(self):
        """计算SectionOrder"""
        if self.level == 0 or self.order_num == 0:
            raise MyLocalException('先确定level和order_num,再计算section_order')
        section_order = self.order_num * (1000 ** (3 - self.level))
        if self.parent_section:
            section_order += self.parent_section.section_order
        return section_order

    def get_childs_by_id(self, child_class):
        """用自身id作为parent_id找到子节点的列表"""
        if self.id == 0:
            raise MyLocalException('no id')
        sql = """
        SELECT CourseSectionID,SectionName,Summary,sLevel,ParentID,OrderNum,JiaoCaiID,
        SectionOrder,TeachingAssistID,Grade,Subject,QuestionType FROM wx_edu_coursesection
        WHERE ParentID={}
        """.format(self.id)
        res = self.select(sql)
        return [
            child_class(
                id=int(d['CourseSectionID']),
                name=uni_to_u8(d['SectionName']),
                summary=uni_to_u8(d['Summary']),
                parent_id=self.id,  # 自己的子章节
                order_num=int(d['OrderNum']),
                jiaocai_id=self.jiaocai_id,
                assist_id=self.assist_id,
                parent_section=self
            ) for d in res
        ]

    @classmethod
    def get_by_assist_type_parent_order_from_zongku(cls, a_id, q_type, p_id, order):
        sql = """
        SELECT section_id,name,summary,level,parent_id,order_num,
        section_order,assist_id FROM base_course_section
        WHERE assist_id={a_id}
        AND parent_id={p_id}
        AND order_num={order}
        """.format(a_id=a_id, q_type=q_type, p_id=p_id, order=order)
        res = cls.select(sql)
        return [
            cls(
                id=int(d['section_id']),
                name=uni_to_u8(d['name']),
                summary=uni_to_u8(d['summary']),
                parent_id=int(d['parent_id']),
                order_num=int(d['order_num']),
                assist_id=uni_to_u8(d['assist_id']),
            ) for d in res
        ]


class JiaoCaiVersion(BaseModel):
    """教材版本"""

    def __init__(self, **kwargs):
        self.id = IntegerField()
        self.name = StringField()
        self.jiaocais = []
        super(JiaoCaiVersion, self).__init__(**kwargs)

    def __repr__(self):
        return '<id:{},name:{}>'.format(self.id, self.name)

    def get_jiaocai(self):
        """获取版本的教材"""
        if self.id and not self.jiaocais:
            self.jiaocais = JiaoCai.get_jiaocai_by_version(self.id)

    @classmethod
    def get_all_version(cls):
        sql = """
        SELECT TeachingID,Name FROM wx_edu_teachingmaterial;
        """
        res = cls.select(sql)
        return [
            cls(
                id=int(d['TeachingID']),
                name=uni_to_u8(d['Name'])
            )
            for d in res
        ]

    @classmethod
    def get_version(cls, id=0, name='QQQ'):
        sql = """
        SELECT TeachingID,Name FROM wx_edu_teachingmaterial
        WHERE TeachingID={} or Name='{}';
        """.format(id, name)
        res = cls.select(sql)
        vs = [
            cls(
                id=int(d['TeachingID']),
                name=uni_to_u8(d['Name'])
            )
            for d in res
        ]
        if not vs or len(vs) > 1:
            log.error('没有找到对应id或name的版本')
            return
        return vs[0]

    @classmethod
    def get_version_from_zongku(cls, id=0, name='QQQ'):
        sql = """
        SELECT edition_id,name FROM base_edition
        WHERE edition_id={} or name='{}';
        """.format(id, name)
        res = cls.select(sql)
        vs = [
            cls(
                id=int(d['edition_id']),
                name=uni_to_u8(d['name'])
            )
            for d in res
        ]
        if not vs or len(vs) > 1:
            log.error('没有找到对应id或name的版本')
            return
        return vs[0]


class JiaoCai(BaseModel):
    """教材，含年级和分科信息"""

    def __init__(self, **kwargs):
        self.id = IntegerField()
        self.name = StringField()
        self.grade = IntegerField()
        self.subject = IntegerField(default=1)
        self.v_id = IntegerField()
        super(JiaoCai, self).__init__(**kwargs)

    def __repr__(self):
        return '<{}{}{}年级>'.format(self.id, self.name, self.grade)

    @classmethod
    def get_jiaocai_by_version(cls, v_id):
        """获取一个出版社的教材，默认语文"""
        # IsActive 为可用教材
        sql = """
        SELECT JiaoCaiID,Name,Grade,Subject FROM wx_edu_jiaocai 
        where IsActive=1 and TeachingID={} and subject=1;
        """.format(v_id)
        res = cls.select(sql)
        return [
            cls(
                id=int(d['JiaoCaiID']),
                name=uni_to_u8(d['Name']),
                grade=int(d['Grade']),
                v_id=v_id,
            ) for d in res
        ]

    @classmethod
    def get_jiaocai_by_version_from_zongku(cls, v_id):
        """获取一个出版社的教材，默认语文"""
        # IsActive 为可用教材
        sql = """
        SELECT book_id,name,grade,subject FROM base_book 
        where is_active=1 and edition_id={} and subject=1;
        """.format(v_id)
        res = cls.select(sql)
        return [
            cls(
                id=int(d['book_id']),
                name=uni_to_u8(d['name']),
                grade=int(d['grade']),
                v_id=v_id,
            ) for d in res
        ]

    def get_relate_assist(self):
        """根据教材获得教辅"""
        return JiaocaiAssist.get_assist_by_jiaocai_id(self.id)


class JiaocaiAssist(BaseModel):
    """教辅"""
    id = 0
    name = ''  # 人教版1年级语文同步练关卡题
    summary = ''
    jiaocai_id = 0  # 对应的教材id
    grade = 0  # 年级
    subject = 1  # 默认语文

    ce_id = 0  # 对应的section1册
    orderNum = 0  # 1上册2下册

    @classmethod
    def get_assist_by_jiaocai_id(cls, j_id):
        """根据教材id获得教辅，测试库的基础教辅为summary=小学语文基础"""
        sql = """
        SELECT TeachingAssistID,JiaocaiID FROM wx_edu_teachingassist
        WHERE JiaocaiID={}
        AND Summary='小学语文基础'
        """.format(j_id)
        res = cls.select(sql)
        return [
            cls(
                id=int(d['TeachingAssistID'])
            ) for d in res
        ]

    @classmethod
    def get_assist_by_jiaocai_and_type(cls, j_id, q_type):
        """根据教材id和QuestionType获得教辅"""
        sql = """
        SELECT TeachingAssistID,JiaocaiID,Name FROM wx_edu_teachingassist
        WHERE JiaocaiID={}
        AND QuestionType={}
        """.format(j_id, q_type)
        res = cls.select(sql)
        return [
            cls(
                id=int(d['TeachingAssistID']),
                name=uni_to_u8(d['Name'])
            ) for d in res
        ]

    @classmethod
    def get_assist_by_jiaocai_and_type_from_zongku(cls, j_id, q_type):
        """根据教材id和QuestionType获得教辅"""
        sql = """
        SELECT assist_id,book_id,name FROM base_assist
        WHERE book_id={}
        AND type={}
        """.format(j_id, q_type)
        res = cls.select(sql)
        return [
            cls(
                id=int(d['assist_id']),
                name=uni_to_u8(d['name'])
            ) for d in res
        ]

    def insert_new_assist(self):
        """将教辅数据写入数据库"""
        if self.write_db_type == 'zongku':
            # 总库表名和字段
            fields = dict(
                name=self.name,
                summary=self.summary,
                book_id=self.jiaocai_id,
                type=120,  # 语文同步练固定要求120
                order_num=self.orderNum,
                status=0,
                online_status=1,
            )
            sql = """
            INSERT INTO base_assist (name,summary,book_id,type,order_num,
            status,online_status)
            VALUES ('{name}','{summary}',{book_id},{type},{order_num},
            {status},{online_status})
            """.format(**fields)
        else:
            fields = dict(
                Name=self.name,
                Summary=self.summary,
                HasSection=1,
                JiaocaiID=self.jiaocai_id,
                QuestionType=120,  # 语文同步练固定要求120
                OrderNum=self.orderNum,
                Grade=self.grade,
                Subject=self.subject,
            )
            sql = """
            INSERT INTO wx_edu_teachingassist (Name,Summary,HasSection,JiaocaiID,QuestionType,OrderNum,Grade,Subject)
            VALUES ('{Name}','{Summary}',{HasSection},{JiaocaiID},{QuestionType},{OrderNum},{Grade},{Subject})
            """.format(**fields)
        self.id = self.insert(sql)

    def get_relate_ce(self):
        return SectionCe.get_ce_by_assist_id(self.id)


class SectionCe(CourseSectionBase):
    """
    册
    """
    level = 1

    def __init__(self, **kwargs):
        super(SectionCe, self).__init__(**kwargs)

    @classmethod
    def get_ce_by_assist_id(cls, assist_id):
        sql = """
        SELECT CourseSectionID,SectionName,Summary,sLevel,ParentID,OrderNum,JiaoCaiID,
        SectionOrder,TeachingAssistID,Grade,Subject,QuestionType FROM wx_edu_coursesection
        WHERE TeachingAssistID={}
        AND sLevel=1 
        """.format(assist_id)
        res = cls.select(sql)
        return [
            cls(
                id=int(d['CourseSectionID']),
                name=uni_to_u8(d['SectionName']),
                summary=uni_to_u8(d['Summary']),
                parent_id=0,
                order_num=int(d['OrderNum']),
                assist_id=uni_to_u8(d['TeachingAssistID']),
            ) for d in res
        ]

    def get_child_danyuan_list(self):
        return self.get_childs_by_id(SectionDanyuan)


class SectionDanyuan(CourseSectionBase):
    """Section单元"""
    level = 2

    def __init__(self, **kwargs):
        super(SectionDanyuan, self).__init__(**kwargs)

    def get_child_course_list(self):
        return self.get_childs_by_id(SectionRealCourse)


class SectionRealCourse(CourseSectionBase):
    """
    课程章节
    L1:上下册
    L2:单元
    L3:课程
    L4:课程练习
    """
    level = 3
    # 对应的category_items
    category_items = []
    # 课程的题目
    qs = []

    def get_child_practices(self):
        return self.get_childs_by_id(SectionPractice)


class Misson(CourseSectionBase):
    """
    课程关卡，6道题为一关(组)
    和api组确认关卡为一个CourseSection,level为3
    """
    level = 3
    last = 1

    def __init__(self, **kwargs):
        super(Misson, self).__init__(**kwargs)
        self.set_misson_name()
        self.questions = []

    def set_misson_name(self):
        """设置关卡名称"""
        if self.order_num == 0:
            raise MyLocalException('关卡order不能为0')
        self.name = '第{}关'.format(self.order_num)

    def insert_relate_section_question(self):
        if not self.id:
            raise MyLocalException('关卡没有id')
        course_section_id = self.id
        """将关卡id和questions的id写入关联表"""
        for q in self.questions:
            if not q:
                raise MyLocalException('Question为空')
            if not q.id:
                raise MyLocalException('Question没有id')

            if self.write_db_type == 'zongku':
                # 总库表名和字段
                fields = dict(
                    section_id=self.id,
                    question_id=q.id,
                    assist_id=self.assist_id,
                    status=0,
                    online_status=1
                )
                sql = """
                INSERT INTO relate_section_question (section_id,question_id,assist_id,status,online_status)
                VALUES ({section_id},{question_id},{assist_id},{status},{online_status})
                """.format(**fields)
            else:
                fields = dict(
                    CourseSectionID=self.id,
                    QuestionID=q.id,
                    TeachingAssistID=self.assist_id
                )
                sql = """
                INSERT INTO edu_relate_courseassistquestion (CourseSectionID,QuestionID,TeachingAssistID)
                VALUES ({CourseSectionID},{QuestionID},{TeachingAssistID})
                """.format(**fields)
            self.insert(sql, auto_commit=False)
            log.info('Insert new relate 关卡（{},{}）,题目（{},{}）'.format(course_section_id, self.name, q.id, q.body))
        self.conn_read.commit()

    @classmethod
    def get_missions_by_ce(cls, a_id, q_type, p_id):
        sql = """
        SELECT CourseSectionID,SectionName,Summary,sLevel,ParentID,OrderNum,JiaoCaiID,
        SectionOrder,TeachingAssistID,Grade,Subject,QuestionType FROM wx_edu_coursesection
        WHERE TeachingAssistID={a_id}
        AND QuestionType={q_type}
        AND ParentID={p_id}
        AND slevel=3
        """.format(a_id=a_id, q_type=q_type, p_id=p_id)
        res = cls.select(sql)
        return [
            cls(
                id=int(d['CourseSectionID']),
                name=uni_to_u8(d['SectionName']),
                summary=uni_to_u8(d['Summary']),
                parent_id=int(d['ParentID']),
                order_num=int(d['OrderNum']),
                assist_id=uni_to_u8(d['TeachingAssistID']),
            ) for d in res
        ]

    @classmethod
    def get_missions_by_ce_from_zongku(cls, a_id, q_type, p_id):
        sql = """
        SELECT section_id,name,summary,level,parent_id,order_num,
        section_order,assist_id FROM base_course_section
        WHERE assist_id={a_id}
        AND parent_id={p_id}
        AND level=3
        """.format(a_id=a_id, q_type=q_type, p_id=p_id)
        res = cls.select(sql)
        return [
            cls(
                id=int(d['section_id']),
                name=uni_to_u8(d['name']),
                summary=uni_to_u8(d['summary']),
                parent_id=int(d['parent_id']),
                order_num=int(d['order_num']),
                assist_id=uni_to_u8(d['assist_id']),
            ) for d in res
        ]




class SectionPractice(CourseSectionBase):
    """练习Section节点"""

    def _cal_section_order(self):
        pass


class CategoryItem(BaseModel):
    """
    选题范围，即CategoryID为1的数据
        CategoryID为2的分类，直接放入常量
    group 字符串
    """
    id = 0
    name = ''
    # 练习类型
    group = ''
    # 相关题目
    questions = []

    def __repr__(self):
        return '<id:{},name:{},group:{}>'.format(self.id, self.name, self.group)

    @classmethod
    def get_categoryitem_by_coursesection(cls, cs_id):
        """根据CourseSection找到关联的CategoryItem"""
        sql = """
        SELECT DISTINCT item.CategoryItemID,item.CategoryItem,item.Group
        FROM edu_relate_coursesectioncategory AS relate
        INNER JOIN edu_categoryitem AS item ON item.CategoryItemID = relate.CategoryItemID
        AND relate.CourseSectionID = {}
        AND item.CategoryID = 1
        INNER JOIN wx_edu_coursesection AS sec ON sec.CourseSectionID = relate.CourseSectionID
        -- INNER JOIN wx_edu_coursesection AS sec ON sec.CourseSectionID = relate.CourseSectionID
        """.format(cs_id)
        res = cls.select(sql)
        return [cls(
            id=int(d['CategoryItemID']),
            name=uni_to_u8(d['CategoryItem']),
            group=uni_to_u8(d['Group'])
        ) for d in res]


class Question(BaseModel):
    """抽的语文题目，比较特殊，有时间整合一下"""
    id = 0
    body = ''
    q_type = ''  # 这个q_type不是字段QuestionType

    def __eq__(self, other):
        if isinstance(other, Question):
            return self.id == other.id

    def __hash__(self):
        return hash(self.id)

    def __repr__(self):
        return '<id:{},body:{},q_type:{}>'.format(self.id, self.body, self.q_type)

    @classmethod
    def get_question_by_item(cls, i_id):
        """
        根据CourseSection找到关联的CategoryItem
        本次要求填空题,Question表的QuestionType=1
        """
        sql = """
        SELECT DISTINCT q.QuestionID,q.Question,relate2.CategoryItemID
        FROM edu_relate_questioncategory AS relate
        INNER JOIN wx_edu_questions_new AS q 
        ON q.QuestionID = relate.QuestionID
        AND relate.CategoryItemID = 2462 AND q.QuestionType=1 AND q.Status=0 AND relate.CategoryID=1 
        INNER JOIN edu_relate_questioncategory as relate2 
        ON q.QuestionID = relate2.QuestionID
        AND relate2.CategoryID=2
        """.format(i_id)
        res = cls.select(sql)
        return [
            cls(
                id=int(d['QuestionID']),
                body=uni_to_u8(d['Question']),
                q_type=get_question_type(d['CategoryItemID']),  # 字音、字形、字义等
            )
            for d in res
        ]


class QuestionRadio(BaseModel):
    """语文园地单选题"""
    id = 0  # QuestionID
    body = ''  # Question
    q_type = 1  # QuestionType 1为单选，语文园地都是单选
    right_answer = ''  # RightAnswer
    answer_explain = ''  # AnswerExplain 可自定义的字段
    options = 'ABC'  # Options 语文园地默认都是ABC三选项
    question_analyze = ''  # QuestionAnalyze 可自定义的字段
    subject = 1  # 语文默认1
    status = 0  # 默认0

    def __repr__(self):
        return '<id:{},body:{},right:{}>'.format(self.id, self.body, self.right_answer)

    def insert_new_question(self):
        if self.write_db_type == 'zongku':
            # 总库表名和字段
            fields = dict(
                question=self.body,
                analyse=self.question_analyze,
                show_type=self.q_type,
                right_answer=self.right_answer,
                answer_explain=self.answer_explain,
                option_count=3,
                subject=1,
                status=0,
                online_status=1
            )
            sql = """
            INSERT INTO base_question (question,analyse,show_type,right_answer,
            subject,answer_explain,option_count,status,online_status) 
            VALUES ('{question}','{analyse}',{show_type},'{right_answer}',
            {subject},'{answer_explain}',{option_count},{status},{online_status});
            """.format(**fields)
        else:
            fields = dict(
                Question=self.body,
                QuestionType=self.q_type,
                RightAnswer=self.right_answer,
                AnswerExplain=self.answer_explain,
                Options=self.options,
                QuestionAnalyze=self.question_analyze,
                Grade=0,  # question的grade都是0
                Subject=self.subject,
                Status=0,
            )
            sql = """
            INSERT INTO wx_edu_questions_new (Question,QuestionAnalyze,QuestionType,RightAnswer,
            Status,Subject,AnswerExplain,Grade,Options) 
            VALUES ('{Question}','{QuestionAnalyze}',{QuestionType},'{RightAnswer}',
            {Status},{Subject},'{AnswerExplain}',{Grade},'{Options}');
            """.format(**fields)
        self.id = self.insert(sql)

    def insert_relate_with_mission(self, section_id, a_id):
        """增补题将关卡id和questions的id写入关联表"""
        if not self.id:
            raise MyLocalException('question没有id')

        if self.write_db_type == 'zongku':
            # 总库表名和字段
            fields = dict(
                section_id=section_id,
                question_id=self.id,
                assist_id=a_id,
                status=0,
                online_status=1
            )
            sql = """
            INSERT INTO relate_section_question (section_id,question_id,assist_id,status,online_status)
            VALUES ({section_id},{question_id},{assist_id},{status},{online_status})
            """.format(**fields)
        else:
            fields = dict(
                CourseSectionID=section_id,
                QuestionID=self.id,
                TeachingAssistID=a_id
            )
            sql = """
            INSERT INTO edu_relate_courseassistquestion (CourseSectionID,QuestionID,TeachingAssistID)
            VALUES ({CourseSectionID},{QuestionID},{TeachingAssistID})
            """.format(**fields)
        self.insert(sql)
        log.info('Insert new relate 关卡:{},题目:{}'.format(section_id, self.id))


class QuestionItem(BaseModel):
    """语文园地题目选项"""
    id = 0  # QuestionItemID
    content = ''  # QuestionItem
    item_code = ''  # ItemCode 选项的字母 A,B,C
    q_id = ''  # QuestionID
    is_right = ''  # IsRight 是否正确 Y 或者 N的字符

    def __repr__(self):
        return '<id:{},code:{},content:{},q_id:{}>'.format(self.id, self.item_code, self.content, self.q_id)

    def insert_new_item(self):
        if self.write_db_type == 'zongku':
            fields = dict(
                question_item=self.content,
                item_code=self.item_code,
                question_id=self.q_id,
                status=0,
                online_status=1
            )
            sql = """
            INSERT INTO base_question_item (question_item,item_code,question_id,status,online_status) 
            VALUES ('{question_item}','{item_code}',{question_id},{status},{online_status});
            """.format(**fields)
        else:
            fields = dict(
                QuestionItem=self.content,
                ItemCode=self.item_code,
                QuestionID=self.q_id,
                IsRight=self.is_right,
            )
            sql = """
            INSERT INTO wx_edu_questionitem_new (QuestionItem,ItemCode,QuestionID,IsRight) 
            VALUES ('{QuestionItem}','{ItemCode}',{QuestionID},'{IsRight}');
            """.format(**fields)
        self.id = self.insert(sql)
