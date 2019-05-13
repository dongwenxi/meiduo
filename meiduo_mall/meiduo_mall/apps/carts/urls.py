from django.conf.urls import url
from . import views


urlpatterns = [
    # 购物车的增删改查
    url(r'^carts/$', views.CartsView.as_view()),
    # 购物车的全选
    url(r'^carts/selection/$', views.CartsSetectView.as_view()),
    # 简单购物车数据展示
    url(r'^carts/simple/$', views.CartsSimpleView.as_view()),
]