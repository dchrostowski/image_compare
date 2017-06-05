from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$',views.index,name="index"),
    url(r'^upload-success\/?', views.upload_success,name="upload_success")
]
