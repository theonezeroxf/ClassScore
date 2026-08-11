"""考试批次名称、比例和成绩文件上传表单。"""

from django import forms
from grades.models import ExamBatch
class ExamImportForm(forms.Form):
 name=forms.CharField(label='批次名称'); ratio=forms.ChoiceField(choices=ExamBatch.RATIOS,label='考试:平时'); file=forms.FileField()
