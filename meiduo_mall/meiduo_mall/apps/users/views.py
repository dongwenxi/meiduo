from django.shortcuts import render, redirect
from django.views import View
from django import http
import re
from django.contrib.auth import login
from django.db import DatabaseError
from meiduo_mall.utils.response_code import RETCODE
from django_redis import get_redis_connection
from django.contrib.auth import authenticate

from .models import User
import logging

logger = logging.getLogger('django')  # 创建日志输出器


# Create your views here.

class RegisterView(View):

    # 注册
    def get(self, request):
        """注册界面"""

        return render(request, 'register.html')

    def post(self, request):
        """注册业务"""

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

        # 短信校验
        # 创建redis连接,获取redis中的随机验证码/一定要解码
        redis_conn = get_redis_connection('verify_code')
        sms_code_server = redis_conn.get('sms_%' % mobile).decode()
        # 校验
        if sms_code_server is None:
            return http.HttpResponseForbidden('短信验证码已失效')
        if sms_code_server != sms_code:
            return http.HttpResponseForbidden('输入的短信验证码有误')

        # 创建一个user
        try:
            user = User.objects.create_user(
                username=username,
                password=password,  # 密码存储时需要加密
                mobile=mobile,
            )
        except DatabaseError as e:
            logger.error(e)

        # 状态保持
        login(request, user)  # 存储用户的id到session中记录登录状态
        # 注册成功重定向到首页
        return redirect('')


class UsernameCountView(View):
    '''判断用户名是否已经注册'''

    def get(self, request, username):
        count = User.objects.filter(username=username).count()

        return http.JsonResponse({'count': count, 'code': RETCODE.OK, 'errmsg': 'OK'})


class MobileCountView(View):
    '''判断手机号是否重复'''

    def get(self, request, mobile):
        count = User.objects.filter(mobile=mobile).count()

        return http.JsonResponse({'count': count, 'code': RETCODE.OK, 'errmsg': 'OK'})


class LoginView(View):

    def get(self, request):
        # 登录界面
        return render(request, 'login.html')

    def post(self, request):
        # 获取表单账号，密码
        username = request.POST.get('username')
        password = request.POST.get('password')
        remembered = request.POST.get('remembered')
        # 校验
        # 根据表单提交用户名获取数据库中本条user信息,基本逻辑代码
        # user = User.objects.get(username= username)
        # user.check_password(password)
        # 实现手机号或其他多账号登录
        # 通过自定义用户认证后端实现
        # django中auth自带认证方法
        user = authenticate(username=username, password=password)
        # 根据是否勾选记住密码保持状态
        login(request, user)
        if remembered != 'on':
            return request.session.set_expiry(0)
        else:
            return request.session.set_expiry(None)
        # 响应结果
        return redirect('/')
