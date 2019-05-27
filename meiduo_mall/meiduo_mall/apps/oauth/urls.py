from django.conf.urls import url
from . import views


urlpatterns = [
    # qq登录界面
    url(r'^qq/authorization/$', views.OAuthURLview.as_view()),
    # qq回调界面
    url(r'^oauth_callback/$', views.OAuthUserView.as_view()),
    # 微博登录界面
    url(r'^weibo/authorization/$', views.SinaURLView.as_view()),
    # 微博登录成功后的回调处理
    url(r'^sina_callback/$', views.OAuthWeiboView.as_view()),
    #
    url(r'^oauth/sina/user/$', views.OAuthWeiboView.as_view()),
]