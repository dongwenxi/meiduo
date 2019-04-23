from django.shortcuts import render, redirect
from django.views import View
from django import http
import re
from django.contrib.auth import login
from django.db import DatabaseError
from meiduo_mall.utils.response_code import RETCODE

from .models import User
import logging

logger = logging.getLogger('django') # 创建日志输出器


# Create your views here.

class RegisterView(View):
    # 注册
    def get(self, request):
        '''注册界面'''

        return render(request, 'register.html')

    def post(self, request):
        '''注册业务'''

        # 接收参数
        username = request.POST.get('username')
        password = request.POST.get('password')
        password2 = request.POST.get('password2')
        mobile = request.POST.get('mobile')
        allow = request.POST.get('allow')
        sms_code = request.POST.get('sms_code')

        # 校验
        # 校验传输的数据是否有为空
        if not all([username, password, password2, sms_code, mobile, allow]):
            return http.HttpResponseForbidden('缺少必传参数')
        # 校验前端传入数据是否符合要求
        if not re.match(r'^[a-zA-Z0-9_-]{5,20}$', username):
            return http.HttpResponseForbidden('请输入5-20位用户名')
        if not re.match(r'^[0-9A-Za-z]{8,20}$', password):
            return http.HttpResponseForbidden('请输入8-20位密码')
        if password2 != password:
            return http.HttpResponseForbidden('两次输入的密码不一致')
        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return http.HttpResponseForbidden('请正确输入手机号')

        # TODO 短信校验后期补充

        # 创建一个user
        try:
            user = User.objects.create_user(
                username=username,
                password=password, # 密码存储时需要加密
                mobile=mobile,
            )
        except DatabaseError as e:
            logger.error(e)

        # 状态保持
        login(request, user)# 存储用户的id到session中记录登录状态
        # 注册成功重定向到首页
        return redirect('/')


class UsernameCountView(View):
    '''判断用户名是否已经注册'''

    def get(self, request, username):
        count = User.objects.filter(username = username).count()

        return http.JsonResponse({'count':count, 'code':RETCODE.OK, 'errmsg': 'OK'})


