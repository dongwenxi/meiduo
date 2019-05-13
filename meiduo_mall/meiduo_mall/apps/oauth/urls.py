from django.conf.urls import url
from . import views


urlpatterns = [
    # qq登录界面
    url(r'^qq/authorization/$', views.OAuthURLview.as_view()),
    # qq回调界面
    url(r'^oauth_callback/$', views.OAuthUserView.as_view()),
]