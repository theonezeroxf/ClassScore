from django.contrib import admin
from .models import AttendanceSession,AttendanceRecord,QuestionDrawRecord
admin.site.register([AttendanceSession,AttendanceRecord,QuestionDrawRecord])
