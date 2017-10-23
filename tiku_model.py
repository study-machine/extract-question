# coding=utf8
from utils import uni_to_u8
from little_orm import BaseModel
from category import get_question_type


class JiaoCaiVersion(BaseModel):
    """教材版本"""

    def __init__(self, id, name):
        self.id = id
        self.name = name
        self.jiaocais = []

    def __repr__(self):
        return '<id:{},name:{}>'.format(self.id, self.name)

    def get_jiaocai(self):
        if not self.jiaocais:
            self.jiaocais = JiaoCai.get_jiaocai_by_version(self.id)

    @classmethod
    def get_all_version(cls):
        cursor = cls.get_cursor()
        sql = """
		SELECT TeachingID,Name FROM wx_edu_teachingmaterial;
		"""
        cursor.execute(sql)
        return [cls(int(d['TeachingID']), d['Name'].encode('utf8')) for d in cursor.fetchall()]


class JiaoCai(BaseModel):
    """教材，含年级和分科信息"""

    def __init__(self, id, grade, subject=1, v_id=0):
        self.id = id
        self.grade = grade
        self.subject = subject
        self.v_id = v_id

    def __repr__(self):
        return '<id:{},grade:{}>'.format(self.id, self.grade)

    def get_courses(self):
        return CourseSection.get_real_courses_by_jiaocai(self.id)

    @classmethod
    def get_jiaocai_by_version(cls, v_id, subject=1):
        """获取一个出版社的教材，默认语文"""
        cursor = cls.get_cursor()
        # IsActive 为可用教材
        sql = """
        SELECT JiaoCaiID,Grade,Subject FROM wx_edu_jiaocai 
        where IsActive=1 and TeachingID={} and subject={};
        """.format(v_id, subject)
        cursor.execute(sql)
        return [cls(int(d['JiaoCaiID']), int(d['Grade'])) for d in cursor.fetchall()]


class CourseSection(BaseModel):
    """课程章节"""

    def __init__(self, id, name, parent_id=-1, level=3, jiaocai_id=-1):
        self.id = int(id)
        self.name = uni_to_u8(name)
        self.level = int(level)  # 3课程，4练习
        self.parent_id = parent_id
        # 子章节
        self.childs = []
        # 拥有的category_items
        self.category_items = []

    def __repr__(self):
        return '<id:{},name:{}>'.format(self.id, self.name)

    def get_practices(self):
        """获取课程里的练习分类，slevel=4为课程练习的section"""
        cursor = self.get_cursor()
        sql = """
        SELECT CourseSectionID,SectionName,ParentID FROM wx_edu_coursesection 
        where ParentID={} and IsDelete=0;
        """.format(self.id)
        cursor.execute(sql)
        # print cursor.fetchall()
        self.childs = [CourseSection(
            d['CourseSectionID'], d['SectionName'], d['ParentID']) for d in cursor.fetchall()]
        # return [cls(int(d['CourseSectionID']), d['SectionName'].encode('utf8'), int(d['ParentID'])) for d in cursor.fetchall()]

    @classmethod
    def get_real_courses_by_jiaocai(cls, j_id):
        """获取教材的课程，真实生活意义上的课程是slevel为3的CourseSection"""
        cursor = cls.get_cursor()
        sql = """
        SELECT CourseSectionID,SectionName,ParentID FROM wx_edu_coursesection 
        where JiaoCaiID={} and IsDelete=0 and sLevel=3;
        """.format(j_id)
        cursor.execute(sql)
        return [cls(int(d['CourseSectionID']), d['SectionName'].encode('utf8'), int(d['ParentID'])) for d in cursor.fetchall()]


class CategoryItem(BaseModel):
    """
    选题范围，即CategoryID为1的数据
        CategoryID为2的分类，直接放入常量
    group 字符串
    """

    def __init__(self, id, name, group=''):
        super(CategoryItem, self).__init__()
        self.id = int(id)
        self.name = uni_to_u8(name)
        self.group = uni_to_u8(group)
        # 相关题目
        self.questions = []

    def __repr__(self):
        return '<id:{},name:{},group:{}>'.format(self.id, self.name, self.group)

    @classmethod
    def get_categoryitem_by_coursesection(cls, cs_id):
        """根据CourseSection找到关联的CategoryItem"""
        cursor = cls.get_cursor()

        sql = """
        SELECT DISTINCT item.CategoryItemID,item.CategoryItem,item.Group
        FROM edu_relate_coursesectioncategory AS relate
        INNER JOIN edu_categoryitem AS item ON item.CategoryItemID = relate.CategoryItemID
        AND relate.CourseSectionID = {}
        AND item.CategoryID = 1
        INNER JOIN wx_edu_coursesection AS sec ON sec.CourseSectionID = relate.CourseSectionID
        -- INNER JOIN wx_edu_coursesection AS sec ON sec.CourseSectionID = relate.CourseSectionID
        """.format(cs_id)
        cursor.execute(sql)
        return [cls(d['CategoryItemID'], d['CategoryItem'], d['Group']) for d in cursor.fetchall()]


class Question(BaseModel):
    """题目"""

    def __init__(self, id, body, q_type):
        self.id = int(id)
        self.body = uni_to_u8(body)
        self.q_type = uni_to_u8(q_type)
        self.q_tuple = self.to_tuple()

    def __repr__(self):
        return '<id:{},body:{},q_type:{}>'.format(self.id, self.body, self.q_type)

    def to_tuple(self):
    	return (self.id,self.q_type)


    @classmethod
    def get_question_by_item(cls, i_id):
        """根据CourseSection找到关联的CategoryItem"""
        cursor = cls.get_cursor()

        sql = """
        SELECT q.QuestionID,q.Question,relate2.CategoryItemID
        FROM edu_relate_questioncategory AS relate
        INNER JOIN wx_edu_questions_new AS q 
        ON q.QuestionID = relate.QuestionID
        AND relate.CategoryItemID = {}
        INNER JOIN edu_relate_questioncategory as relate2 
        ON q.QuestionID = relate2.QuestionID
		AND relate2.CategoryID=2
        """.format(i_id)
        cursor.execute(sql)
        return [
            cls(d['QuestionID'],
                d['Question'],
                get_question_type(d['CategoryItemID']),
                )
            for d in cursor.fetchall()
        ]
