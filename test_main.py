#coding=utf8
from tiku_model import *
from category import get_question_type

av = JiaoCaiVersion.get_all_version()
for v in av[:1]:
    v.get_jiaocai()
    print v.name,v.jiaocais
    courses = v.jiaocais[1].get_courses()
    for c in courses[20:21]:
        print c
        c.get_practices()
        print c.childs
        for p in c.childs:
            if p.name=='字词练习':
                print c.name,'has 字词练习'

            elif p.name =='词汇':
                print c.name,'has 词汇'

print CategoryItem.get_categoryitem_by_coursesection(335249)

for x in Question.get_question_by_item(1206):
    print x