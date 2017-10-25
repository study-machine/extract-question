# coding=utf8
from utils import *
from model.base_model import *


class TestDB:
    """测试库表名"""
    # 版本表
    T_VERSION = 'wx_edu_teachingmaterial'
    # 教材表
    T_JIAOCAI = 'wx_edu_jiaocai'
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


class JiaoCaiVersion(BaseModel):
    """教材版本"""
    id = 0
    name = ''
    jiaocais = []

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


class JiaoCai(BaseModel):
    """教材，含年级和分科信息"""

    id = 0
    grade = 0
    subject = 1

    def __repr__(self):
        return '<id:{},grade:{}>'.format(self.id, self.grade)

    def get_courses(self):
        return CourseSection.get_real_courses_by_jiaocai(self.id)

    @classmethod
    def get_jiaocai_by_version(cls, v_id, subject=1):
        """获取一个出版社的教材，默认语文"""
        # IsActive 为可用教材
        sql = """
        SELECT JiaoCaiID,Grade,Subject FROM wx_edu_jiaocai 
        where IsActive=1 and TeachingID={} and subject=1;
        """.format(v_id)
        res = cls.select(sql)
        return [
            cls(
                id=int(d['JiaoCaiID']),
                grade=int(d['Grade'])
            ) for d in res
        ]


class CourseSection(BaseModel):
    """
    课程章节
    L1:上下册
    L2:单元
    L3:课程
    L4:课程练习
    """

    id = 0
    name = ''
    level = 0
    parent_id = 0
    # 子Section
    childs = []
    # 对应的category_items
    category_items = []

    def __repr__(self):
        return '<id:{},name:{}>'.format(self.id, self.name)

    def get_practices(self):
        if self.level != 3:
            raise StandardError('slevel != 3 ,不会有slevel4的childs ')
        """获取课程里的练习分类，slevel=4为课程练习的section"""
        sql = """
        SELECT CourseSectionID,SectionName,ParentID FROM wx_edu_coursesection 
        where ParentID={} and IsDelete=0;
        """.format(self.id)
        res = self.select(sql)
        self.childs = [
            self.__class__(
                id=int(d['CourseSectionID']),
                name=uni_to_u8(d['SectionName']),
                parent_id=int(d['ParentID'])
            ) for d in res
        ]

    @classmethod
    def get_real_courses_by_jiaocai(cls, j_id):
        """获取教材的课程，真实生活意义上的课程是slevel为3的CourseSection"""
        sql = """
        SELECT CourseSectionID,SectionName,ParentID FROM wx_edu_coursesection 
        where JiaoCaiID={} and IsDelete=0 and sLevel=3;
        """.format(j_id)
        res = cls.select(sql)
        return [
            cls(
                id=int(d['CourseSectionID']),
                name=uni_to_u8(d['SectionName']),
                parent_id=int(d['ParentID']),
                level=3
            ) for d in res
        ]


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
    """题目"""

    id = 0
    body = ''
    q_type = ''

    def __repr__(self):
        return '<id:{},body:{},q_type:{}>'.format(self.id, self.body, self.q_type)

    @classmethod
    def get_question_by_item(cls, i_id):
        """
        根据CourseSection找到关联的CategoryItem
        本次要求填空题,Question表的QuestionType=1
        """
        sql = """
        SELECT q.QuestionID,q.Question,relate2.CategoryItemID
        FROM edu_relate_questioncategory AS relate
        INNER JOIN wx_edu_questions_new AS q 
        ON q.QuestionID = relate.QuestionID
        AND relate.CategoryItemID = {}
        AND q.QuestionType=1
        INNER JOIN edu_relate_questioncategory as relate2 
        ON q.QuestionID = relate2.QuestionID
        AND relate2.CategoryID=2
        """.format(i_id)
        res = cls.select(sql)
        return [
            cls(
                id=int(d['QuestionID']),
                body=uni_to_u8(d['Question']),
                type=get_question_type(d['CategoryItemID']),
            )
            for d in res
        ]


class MissonGroup(object):
    """
    课程关卡，6道题为一关(组)
    和王立阳确认关卡为一个CourseSection,level为3
    挂载到单元下面
    """

    def __init__(self, course_id, zici, order):
        self.course_id = course_id
        self.zici = zici
        self.order = order
        self.questions = []

    def __repr__(self):
        return '<course_id:{},zici:{},order:{}>'.format(self.course_id, self.zici, self.order)

    def write_mission_to_db(self):
        """将关卡作为section写入数据库"""
        sql = """
        
        """
        pass

    def write_question_relate_to_db(self):
        """将关卡和questions的id写入section_question为level2的关联表"""
        pass
