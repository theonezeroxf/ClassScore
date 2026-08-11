"""教师仪表盘、班级 CRUD 和学生导入视图。"""

from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404,redirect,render
from .forms import ClassRoomForm,UploadForm
from .models import ClassRoom
from .services.import_students import import_students
@login_required
def dashboard(request): return render(request,'core/dashboard.html',{'classes':request.user.classrooms.all()})
@login_required
def class_list(request): return render(request,'core/class_list.html',{'classes':request.user.classrooms.all()})
@login_required
def class_create(request):
 form=ClassRoomForm(request.POST or None)
 if request.method=='POST' and form.is_valid(): obj=form.save(commit=False); obj.teacher=request.user; obj.save(); return redirect('class-detail',obj.pk)
 return render(request,'generic_form.html',{'form':form,'title':'新建班级'})
@login_required
def class_detail(request,pk): return render(request,'core/class_detail.html',{'classroom':get_object_or_404(ClassRoom,pk=pk,teacher=request.user)})
@login_required
def student_import(request,pk):
 room=get_object_or_404(ClassRoom,pk=pk,teacher=request.user); form=UploadForm(request.POST or None,request.FILES or None); result=None
 if request.method=='POST' and form.is_valid():
  try: result=import_students(form.cleaned_data['file'],room)
  except ValueError as e: form.add_error('file',str(e))
 return render(request,'core/import.html',{'form':form,'classroom':room,'result':result})
