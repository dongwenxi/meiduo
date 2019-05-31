from django.conf.urls import url
from rest_framework.routers import DefaultRouter

from .views import users, statistical, channels, skus, spus


urlpatterns = [
    # 用户登录
    url(r'^authorizations/$', users.AdminAuthView.as_view()),
    # 统计用户数量
    url(r'^statistical/total_count/$', statistical.UserTotalCountView.as_view()),
    # 获取日增用户数量
    url(r'^statistical/day_increment/$', statistical.UserDayIncrementView.as_view()),
    # 获取日活用户
    url(r'^statistical/day_active/$', statistical.UserDayActiveView.as_view()),
    # 获取日下单用户数量
    url(r'^statistical/day_orders/$', statistical.UserDayOrderView.as_view()),
    # 获取30天新增用户数量
    url(r'^statistical/month_increment/$', statistical.UserMouthIncrementView.as_view()),
    # 获取日分类商品访问数据
    url(r'^statistical/goods_day_views/$', statistical.GoodsDayViewsView.as_view()),

    # 用户管理
    url(r'^users/$', users.UserInfoView.as_view()),

    # 频道管理
    url(r'^goods/channel_types/$', channels.ChannelTypesView.as_view()),
    url(r'^goods/categories/$', channels.ChannelCategoryView.as_view()),

    # SKU图片管理
    url(r'^skus/simple/$', skus.SKUSimpleView.as_view()),

    # SKU商品管理
    url(r'^goods/simple/$', spus.SPUSimpleView.as_view()),
]

# 创建路由对象
router = DefaultRouter()
# 注册视图集
router.register('goods/channels', channels.ChannelViewSet, base_name='channels')
# 将生成url配置项列表添加到urlpatterns中
urlpatterns += router.urls

# SKU图片管理
router = DefaultRouter()
router.register('skus/images', skus.SKUImageViewSet, base_name='images')
urlpatterns += router.urls

# SKU商品管理
router = DefaultRouter()
router.register('skus', skus.SKUViewSet, base_name='skus')
urlpatterns += router.urls
