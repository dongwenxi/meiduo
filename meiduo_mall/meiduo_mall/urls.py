"""meiduo_mall URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url, include
from django.contrib import admin

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    # 用户模块
    url(r'^', include('users.urls', namespace='users')),
    # 首页模块
    url(r'^', include('content.urls', namespace='contents')),
    # 验证模块
    url(r'^', include('verifications.urls', namespace='verifications')),
    # qq模块
    url(r'^', include('oauth.urls', namespace='oauth')),
    # 收货地址
    url(r'^', include('area.urls', namespace='area')),
    # 商品模块
    url(r'^', include('goods.urls', namespace='goods')),
    # 搜索模块
    url(r'^search/', include('haystack.urls')),
    # 购物车模块
    url(r'^', include('carts.urls')),
    # 购物车模块
    url(r'^', include('orders.urls')),
    # 支付模块
    url(r'^', include('payment.urls')),
    # 后台管理
    url(r'^meiduo_admin/', include('meiduo_admin.urls')),
]
