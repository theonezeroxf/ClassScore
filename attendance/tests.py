from datetime import timedelta
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from core.models import ClassRoom,Student
from .models import AttendanceSession,AttendanceRecord,QuestionDrawRecord
from .services.geo import haversine_m
class AttendanceTests(TestCase):
 def setUp(self):
  self.user=User.objects.create_user('t'); self.room=ClassRoom.objects.create(name='一班',teacher=self.user); self.a=Student.objects.create(class_room=self.room,student_no='1',name='甲'); self.b=Student.objects.create(class_room=self.room,student_no='2',name='乙'); now=timezone.now(); self.s=AttendanceSession.objects.create(class_room=self.room,title='课',center_lat=30,center_lng=120,start_time=now-timedelta(minutes=1),end_time=now+timedelta(minutes=10),created_by=self.user)
 def post(self,student,device='d',lat=30): return self.client.post(reverse('sign',args=[self.s.token]),{'student_no':student.student_no,'name':student.name,'lat':lat,'lng':120,'device_id':device},HTTP_USER_AGENT='ua')
 def test_haversine_and_sign_rules(self):
  self.assertLess(haversine_m(30,120,30,120),.1); self.assertContains(self.post(self.a),'签到成功'); self.assertContains(self.post(self.a),'已经签到'); self.assertContains(self.post(self.b),'已经签到'); self.assertContains(self.post(self.b,'x',31),'超出允许范围')
 def test_identity_and_expired(self):
  r=self.client.post(reverse('sign',args=[self.s.token]),{'student_no':'1','name':'错','lat':30,'lng':120,'device_id':'x'}); self.assertContains(r,'不匹配'); self.s.end_time=timezone.now()-timedelta(seconds=1); self.s.save(); self.assertContains(self.post(self.a),'有效时间')
 def test_draw_candidates_and_scores(self):
  AttendanceRecord.objects.create(session=self.s,student=self.a,student_no_snapshot='1',student_name_snapshot='甲',lat=30,lng=120,distance_m=0,device_hash='x'); self.client.force_login(self.user); url=reverse('draw',args=[self.room.pk])+'?session='+str(self.s.pk); data=self.client.post(url).json(); self.assertEqual(data['id'],self.a.id); QuestionDrawRecord.objects.create(class_room=self.room,attendance_session=self.s,student=self.a,score_delta=3,created_by=self.user); self.assertEqual(self.a.draw_records.aggregate(s=__import__('django').db.models.Sum('score_delta'))['s'],3); self.assertEqual(self.client.post(url).status_code,400)
