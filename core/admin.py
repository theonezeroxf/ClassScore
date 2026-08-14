"""在 Django 管理后台注册班级和学生模型。"""

from django.contrib import admin

from .models import ClassRoom, Student

admin.site.register([ClassRoom, Student])
