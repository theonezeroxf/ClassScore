"""成绩导入、优化边界和 XLSX 导出的自动化测试。"""

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from core.models import ClassRoom,Student
from .models import ExamBatch
from .services.import_exam import import_exam
from .services.score_adjustment import build_scores
class GradeTests(TestCase):
 def setUp(self): self.user=User.objects.create_user('t'); self.room=ClassRoom.objects.create(name='一班',teacher=self.user); self.students=[Student.objects.create(class_room=self.room,student_no=str(i),name=f'学生{i}') for i in range(5)]; self.batch=ExamBatch.objects.create(class_room=self.room,name='期末',ratio='7:3',created_by=self.user)
 def test_import_calculation_outlier_bounds_and_export(self):
  body='学号,姓名,考试成绩\n'+'\n'.join(f'{i},学生{i},{60+i*5}' for i in range(5)); r=import_exam(SimpleUploadedFile('x.csv',body.encode()),self.batch); self.assertEqual(r['created'],5)
  items=[{'student_id':s.id,'exam_score':60+i*5,'original_regular_score':v} for i,(s,v) in enumerate(zip(self.students,[60,61,62,63,100]))]; rows=build_scores(items,'7:3'); self.assertEqual(len(rows),5); self.assertTrue(all(0<=x['adjusted_regular_score']<=100 and 0<=x['final_score']<=100 for x in rows)); self.assertTrue(rows[-1]['is_regular_outlier'])
  from grades.views import generate
  generate(self.batch); self.client.force_login(self.user); response=self.client.get(reverse('batch-export',args=[self.batch.pk])); self.assertEqual(response.status_code,200); self.assertIn(b'PK',response.content[:4])
