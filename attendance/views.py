import base64,hashlib,io
import qrcode
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.http import JsonResponse
from django.shortcuts import get_object_or_404,redirect,render
from django.utils import timezone
from core.models import ClassRoom
from .forms import AttendanceSessionForm,SignForm
from .models import AttendanceRecord,AttendanceSession,QuestionDrawRecord
from .services.draw import candidates,draw_student
from .services.geo import haversine_m
@login_required
def create(request):
 form=AttendanceSessionForm(request.POST or None,user=request.user)
 if request.method=='POST' and form.is_valid(): obj=form.save(commit=False); obj.created_by=request.user; obj.save(); return redirect('attendance-detail',obj.pk)
 return render(request,'generic_form.html',{'form':form,'title':'创建签到','geolocation':True})
@login_required
def detail(request,pk):
 s=get_object_or_404(AttendanceSession,pk=pk,class_room__teacher=request.user); link=request.build_absolute_uri(f'/s/{s.token}/'); img=qrcode.make(link); buf=io.BytesIO(); img.save(buf,format='PNG'); qr=base64.b64encode(buf.getvalue()).decode()
 return render(request,'attendance/detail.html',{'session':s,'link':link,'qr':qr})
@login_required
def records(request,pk): return render(request,'attendance/records.html',{'session':get_object_or_404(AttendanceSession,pk=pk,class_room__teacher=request.user)})
def sign(request,token):
 s=get_object_or_404(AttendanceSession,token=token)
 if request.method=='POST':
  form=SignForm(request.POST)
  if form.is_valid():
   d=form.cleaned_data; now=timezone.now()
   if not s.is_active or now<s.start_time or now>s.end_time: form.add_error(None,'签到不在有效时间内')
   else:
    student=s.class_room.students.filter(student_no=d['student_no'],name=d['name']).first()
    if not student: form.add_error(None,'学号或姓名不匹配')
    else:
     distance=haversine_m(s.center_lat,s.center_lng,d['lat'],d['lng']); ua=request.META.get('HTTP_USER_AGENT',''); device_hash=hashlib.sha256(f'{s.token}{d["device_id"]}{ua}'.encode()).hexdigest()
     if distance>s.radius_m: form.add_error(None,f'距离签到点 {distance:.0f} 米，超出允许范围')
     else:
      try: AttendanceRecord.objects.create(session=s,student=student,student_no_snapshot=student.student_no,student_name_snapshot=student.name,lat=d['lat'],lng=d['lng'],distance_m=distance,device_hash=device_hash,ip_address=request.META.get('REMOTE_ADDR'),user_agent=ua); return render(request,'attendance/sign.html',{'session':s,'success':True})
      except IntegrityError: form.add_error(None,'该学生或设备已经签到')
 else: form=SignForm()
 return render(request,'attendance/sign.html',{'session':s,'form':form})
@login_required
def draw(request,class_id):
 room=get_object_or_404(ClassRoom,pk=class_id,teacher=request.user); sid=request.GET.get('session'); session=get_object_or_404(AttendanceSession,pk=sid,class_room=room) if sid else None
 if request.method=='POST':
  data=request.POST; student=room.students.filter(pk=data.get('student_id')).first()
  if student and data.get('score_delta') in ('1','2','3'): QuestionDrawRecord.objects.create(class_room=room,attendance_session=session,student=student,score_delta=int(data['score_delta']),remark=data.get('remark',''),created_by=request.user); return redirect(request.get_full_path())
  student=draw_student(room,session)
  return JsonResponse({'id':student.id,'student_no':student.student_no,'name':student.name} if student else {'error':'没有可抽取学生'},status=200 if student else 400)
 return render(request,'attendance/draw.html',{'classroom':room,'session':session,'student_nos':list(candidates(room,session).values_list('student_no',flat=True)),'drawn':session.draw_records.all() if session else []})
