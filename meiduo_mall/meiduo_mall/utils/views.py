from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View

class LoginRequiredView(LoginRequiredMixin, View):
    '''判断是否登录类视图基类'''
    pass
