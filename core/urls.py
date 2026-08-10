from django.urls import path
from . import views
urlpatterns=[path('',views.dashboard,name='dashboard'),path('classes/',views.class_list,name='class-list'),path('classes/create/',views.class_create,name='class-create'),path('classes/<int:pk>/',views.class_detail,name='class-detail'),path('classes/<int:pk>/students/import/',views.student_import,name='student-import')]
