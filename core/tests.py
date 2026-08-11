"""学生名单导入规则的自动化测试。"""

import io
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from openpyxl import Workbook
from .models import ClassRoom,Student
from .services.import_students import import_students
class StudentImportTests(TestCase):
 def setUp(self): self.room=ClassRoom.objects.create(name='一班',teacher=User.objects.create_user('t'))
 def test_csv_create_update_and_leading_zero(self):
  r=import_students(SimpleUploadedFile('a.csv','学号,姓名\n001,张三\n'.encode()),self.room); self.assertEqual(r['created'],1); self.assertTrue(Student.objects.filter(student_no='001').exists())
  r=import_students(SimpleUploadedFile('a.csv','学号,姓名\n001,李三\n'.encode()),self.room); self.assertEqual(r['updated'],1); self.assertEqual(Student.objects.get().name,'李三')
 def test_xlsx_and_invalid_row(self):
  wb=Workbook(); ws=wb.active; ws.append(['学号','姓名']); ws.append(['002','李四']); ws.append(['','无号']); b=io.BytesIO(); wb.save(b)
  r=import_students(SimpleUploadedFile('a.xlsx',b.getvalue()),self.room); self.assertEqual((r['created'],len(r['errors'])),(1,1))
