"""班级维护与学生名单上传所使用的 Django 表单。"""

from django import forms
from .models import ClassRoom
class ClassRoomForm(forms.ModelForm):
 class Meta: model=ClassRoom; fields=['name','regular_base_score']
class UploadForm(forms.Form): file=forms.FileField(label='名单文件')
