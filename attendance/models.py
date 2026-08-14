"""签到场次、签到明细与课堂抽人加分的数据模型。"""

import uuid

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from core.models import ClassRoom, Student


class AttendanceSession(models.Model):
    """一次有时间和地理范围限制的课堂签到。"""

    class_room = models.ForeignKey(
        ClassRoom, on_delete=models.CASCADE, related_name="attendance_sessions"
    )
    title = models.CharField(max_length=150)
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    center_lat = models.DecimalField(max_digits=9, decimal_places=6)
    center_lng = models.DecimalField(max_digits=9, decimal_places=6)
    radius_m = models.PositiveIntegerField(default=200)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)


class AttendanceRecord(models.Model):
    """学生的一次有效签到及其审计信息。"""

    STATUS = [
        ("valid", "有效"),
        ("duplicate_student", "学生重复"),
        ("duplicate_device", "设备重复"),
        ("out_of_range", "超出范围"),
        ("expired", "已过期"),
    ]
    session = models.ForeignKey(
        AttendanceSession, on_delete=models.CASCADE, related_name="records"
    )
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    student_no_snapshot = models.CharField(max_length=50)
    student_name_snapshot = models.CharField(max_length=100)
    lat = models.DecimalField(max_digits=9, decimal_places=6)
    lng = models.DecimalField(max_digits=9, decimal_places=6)
    distance_m = models.FloatField()
    device_hash = models.CharField(max_length=64)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    status = models.CharField(max_length=30, choices=STATUS, default="valid")
    signed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["session", "student"], name="unique_session_student"
            ),
            models.UniqueConstraint(
                fields=["session", "device_hash"], name="unique_session_device"
            ),
        ]


class QuestionDrawRecord(models.Model):
    """随机抽中学生后登记的课堂回答加分。"""

    class_room = models.ForeignKey(
        ClassRoom, on_delete=models.CASCADE, related_name="draw_records"
    )
    attendance_session = models.ForeignKey(
        AttendanceSession,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="draw_records",
    )
    student = models.ForeignKey(
        Student, on_delete=models.CASCADE, related_name="draw_records"
    )
    score_delta = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(3)]
    )
    remark = models.CharField(max_length=255, blank=True)
    drawn_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
