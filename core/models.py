"""核心数据模型：教师拥有班级，班级包含学生。"""

from django.contrib.auth.models import User
from django.db import models
class ClassRoom(models.Model):
 """教师创建的教学班级。"""
 name=models.CharField('班级名称',max_length=100); teacher=models.ForeignKey(User,on_delete=models.CASCADE,related_name='classrooms'); regular_base_score=models.DecimalField(max_digits=5,decimal_places=1,default=60); created_at=models.DateTimeField(auto_now_add=True); updated_at=models.DateTimeField(auto_now=True)
 def __str__(self): return self.name
class Student(models.Model):
 """学生档案；学号仅要求在所属班级内唯一。"""
 class_room=models.ForeignKey(ClassRoom,on_delete=models.CASCADE,related_name='students'); student_no=models.CharField(max_length=50); name=models.CharField(max_length=100); created_at=models.DateTimeField(auto_now_add=True); updated_at=models.DateTimeField(auto_now=True)
 class Meta: constraints=[models.UniqueConstraint(fields=['class_room','student_no'],name='unique_class_student_no')]; ordering=['student_no']
 def __str__(self): return f'{self.student_no} {self.name}'
