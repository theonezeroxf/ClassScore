"""创建签到和学生签到的输入校验表单。"""

from django import forms
from .models import AttendanceSession
class AttendanceSessionForm(forms.ModelForm):
 class Meta:
  model=AttendanceSession; fields=['class_room','title','start_time','end_time','center_lat','center_lng','radius_m']; widgets={'start_time':forms.DateTimeInput(attrs={'type':'datetime-local'}),'end_time':forms.DateTimeInput(attrs={'type':'datetime-local'})}
 def __init__(self,*a,user=None,**kw):
  super().__init__(*a,**kw)
  if user:self.fields['class_room'].queryset=user.classrooms.all()
 def clean(self):
  d=super().clean()
  if d.get('start_time') and d.get('end_time') and d['end_time']<=d['start_time']: self.add_error('end_time','结束时间必须晚于开始时间')
  return d
class SignForm(forms.Form):
 student_no=forms.CharField(); name=forms.CharField(); lat=forms.DecimalField(); lng=forms.DecimalField(); device_id=forms.CharField(max_length=200)
