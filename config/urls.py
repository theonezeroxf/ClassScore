from django.contrib import admin
from django.urls import include,path
urlpatterns=[path('admin/',admin.site.urls),path('accounts/',include('django.contrib.auth.urls')),path('',include('core.urls')),path('',include('attendance.urls')),path('',include('grades.urls'))]
