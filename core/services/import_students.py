from pathlib import Path
import pandas as pd

def _frame(upload):
 ext=Path(upload.name).suffix.lower()
 if ext not in ('.csv','.xlsx'): raise ValueError('仅支持 csv 和 xlsx 文件')
 if upload.size>10*1024*1024: raise ValueError('文件不能超过 10MB')
 return pd.read_csv(upload,dtype=str,keep_default_na=False) if ext=='.csv' else pd.read_excel(upload,dtype=str,keep_default_na=False)
def import_students(upload,class_room):
 from core.models import Student
 df=_frame(upload).rename(columns={'学号':'student_no','姓名':'name','班级':'class_name'})
 if not {'student_no','name'}<=set(df.columns): raise ValueError('文件必须包含学号和姓名列')
 result={'created':0,'updated':0,'errors':[]}
 for i,row in df.iterrows():
  no=str(row['student_no']).strip(); name=str(row['name']).strip()
  if not no or not name: result['errors'].append(f'第 {i+2} 行：学号和姓名不能为空'); continue
  _,created=Student.objects.update_or_create(class_room=class_room,student_no=no,defaults={'name':name}); result['created' if created else 'updated']+=1
 return result
