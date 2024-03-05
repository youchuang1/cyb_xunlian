from django.urls import path
import app1.views

urlpatterns = [
    path('', app1.views.index),
    path('add/', app1.views.add,name='添加容器'),
    path('restar/', app1.views.restar,name='重启容器'),
    path('reset/', app1.views.reset,name='重置容器'),
    path('stop/', app1.views.stop,name='停止容器'),
]