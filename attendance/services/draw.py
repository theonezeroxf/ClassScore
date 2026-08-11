"""根据签到情况构建候选池并随机抽取学生。"""

import random
def candidates(class_room,session=None):
 qs=session.records.filter(status='valid').values_list('student_id',flat=True) if session else class_room.students.values_list('id',flat=True)
 if session: qs=qs.exclude(student_id__in=session.draw_records.values_list('student_id',flat=True))
 return class_room.students.filter(id__in=qs)
def draw_student(class_room,session=None):
 pool=list(candidates(class_room,session)); return random.choice(pool) if pool else None
