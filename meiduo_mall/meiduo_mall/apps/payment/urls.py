from django.conf.urls import url, include
from django.contrib import admin

from . import views


urlpatterns = [
    # 支付宝链接页面
    url(r'^payment/(?P<order_id>\d+)/$', views.PaymentView.as_view()),
    # 支付成功之后状态修改
    url(r'^payment/status/$', views.PaymentStatusView.as_view())
   ]