from django.urls import path
from . import views
urlpatterns=[path('grades/<int:class_id>/import/',views.import_view,name='grade-import'),path('grades/batches/<int:pk>/',views.batch_detail,name='batch-detail'),path('grades/batches/<int:pk>/export/',views.export,name='batch-export')]
