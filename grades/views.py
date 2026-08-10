import io
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404,redirect,render
from django.db.models import Sum
from openpyxl import Workbook
from core.models import ClassRoom
from .forms import ExamImportForm
from .models import ExamBatch,FinalScore
from .services.import_exam import import_exam
from .services.score_adjustment import build_scores
def generate(batch):
 items=[]
 for score in batch.exam_scores.select_related('student'):
  bonus=score.student.draw_records.aggregate(s=Sum('score_delta'))['s'] or 0; items.append({'student_id':score.student_id,'exam_score':float(score.exam_score),'original_regular_score':min(100,float(batch.class_room.regular_base_score)+bonus)})
 for row in build_scores(items,batch.ratio): FinalScore.objects.update_or_create(batch=batch,student_id=row.pop('student_id'),defaults=row)
@login_required
def import_view(request,class_id):
 room=get_object_or_404(ClassRoom,pk=class_id,teacher=request.user); form=ExamImportForm(request.POST or None,request.FILES or None); result=None
 if request.method=='POST' and form.is_valid():
  batch=ExamBatch.objects.create(class_room=room,name=form.cleaned_data['name'],ratio=form.cleaned_data['ratio'],created_by=request.user)
  try: result=import_exam(form.cleaned_data['file'],batch); generate(batch); return redirect('batch-detail',batch.pk)
  except ValueError as e: batch.delete(); form.add_error('file',str(e))
 return render(request,'grades/import.html',{'form':form,'classroom':room,'result':result})
@login_required
def batch_detail(request,pk):
 batch=get_object_or_404(ExamBatch,pk=pk,class_room__teacher=request.user)
 if request.method=='POST':
  fs=get_object_or_404(FinalScore,pk=request.POST.get('score_id'),batch=batch); fs.adjusted_regular_score=max(0,min(100,float(request.POST.get('adjusted_regular_score')))); ew=float(batch.ratio[0])/10; fs.final_score=round(ew*float(fs.exam_score)+(1-ew)*float(fs.adjusted_regular_score),1); fs.adjust_reason='教师手动修正'; fs.save(); return redirect('batch-detail',pk)
 return render(request,'grades/detail.html',{'batch':batch})
@login_required
def export(request,pk):
 batch=get_object_or_404(ExamBatch,pk=pk,class_room__teacher=request.user); wb=Workbook(); ws=wb.active; ws.append(['班级','学号','姓名','考试成绩','原始平时分','修正平时分','最终成绩','是否平时分异常','修正原因','正态性检验 p 值'])
 for x in batch.final_scores.select_related('student'): ws.append([batch.class_room.name,x.student.student_no,x.student.name,float(x.exam_score),float(x.original_regular_score),float(x.adjusted_regular_score),float(x.final_score),'是' if x.is_regular_outlier else '否',x.adjust_reason,x.normality_p_value])
 buf=io.BytesIO(); wb.save(buf); response=HttpResponse(buf.getvalue(),content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'); response['Content-Disposition']=f'attachment; filename="scores_{batch.pk}.xlsx"'; return response
