"""签到、签到记录和随机抽人的 URL 路由。"""

from django.urls import path
from . import views
urlpatterns=[path('attendance/create/',views.create,name='attendance-create'),path('attendance/<int:pk>/',views.detail,name='attendance-detail'),path('attendance/<int:pk>/records/',views.records,name='attendance-records'),path('s/<uuid:token>/',views.sign,name='sign'),path('draw/<int:class_id>/',views.draw,name='draw')]
