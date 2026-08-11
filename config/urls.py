"""项目总路由：把请求分发给管理后台、认证系统和三个业务应用。"""

from django.contrib import admin
from django.urls import include,path
urlpatterns=[path('admin/',admin.site.urls),path('accounts/',include('django.contrib.auth.urls')),path('',include('core.urls')),path('',include('attendance.urls')),path('',include('grades.urls'))]
