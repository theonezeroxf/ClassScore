"""考试批次、原始考试成绩和最终成绩快照模型。"""

from django.conf import settings
from django.db import models
from django.core.validators import MinValueValidator,MaxValueValidator
from core.models import ClassRoom,Student
class ExamBatch(models.Model):
 """某班级的一次考试成绩导入批次。"""
 RATIOS=[('7:3','七三'),('6:4','六四'),('5:5','五五')]
 class_room=models.ForeignKey(ClassRoom,on_delete=models.CASCADE,related_name='exam_batches'); name=models.CharField(max_length=150); ratio=models.CharField(max_length=3,choices=RATIOS); created_by=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE); created_at=models.DateTimeField(auto_now_add=True)
class ExamScore(models.Model):
 """批次内学生的原始考试成绩。"""
 batch=models.ForeignKey(ExamBatch,on_delete=models.CASCADE,related_name='exam_scores'); student=models.ForeignKey(Student,on_delete=models.CASCADE); exam_score=models.DecimalField(max_digits=5,decimal_places=1,validators=[MinValueValidator(0),MaxValueValidator(100)]); created_at=models.DateTimeField(auto_now_add=True)
 class Meta: constraints=[models.UniqueConstraint(fields=['batch','student'],name='unique_batch_exam_student')]
class FinalScore(models.Model):
 """保留原始、修正平时分及最终分的可追溯快照。"""
 batch=models.ForeignKey(ExamBatch,on_delete=models.CASCADE,related_name='final_scores'); student=models.ForeignKey(Student,on_delete=models.CASCADE); exam_score=models.DecimalField(max_digits=5,decimal_places=1); original_regular_score=models.DecimalField(max_digits=5,decimal_places=1); adjusted_regular_score=models.DecimalField(max_digits=5,decimal_places=1); final_score=models.DecimalField(max_digits=5,decimal_places=1); is_regular_outlier=models.BooleanField(default=False); adjust_reason=models.TextField(blank=True); normality_p_value=models.FloatField(null=True,blank=True); created_at=models.DateTimeField(auto_now_add=True)
 class Meta: constraints=[models.UniqueConstraint(fields=['batch','student'],name='unique_batch_final_student')]
