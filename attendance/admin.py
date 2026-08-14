"""在 Django 管理后台注册签到和抽取模型。"""

from django.contrib import admin

from .models import AttendanceRecord, AttendanceSession, QuestionDrawRecord

admin.site.register([AttendanceSession, AttendanceRecord, QuestionDrawRecord])
