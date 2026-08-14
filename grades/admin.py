"""在 Django 管理后台注册考试与最终成绩模型。"""

from django.contrib import admin

from .models import ExamBatch, ExamScore, FinalScore

admin.site.register([ExamBatch, ExamScore, FinalScore])
