from django.shortcuts import render, redirect, reverse
from django.views import View
from django import http
from django.contrib.auth import login, logout, mixins
from django.db import DatabaseError
from django_redis import get_redis_connection
from django.contrib.auth import authenticate
import json, re
from django.conf import settings
from django.core.paginator import Paginator
import logging
from random import randint
from itsdangerous import TimedJSONWebSignatureSerializer as TOKEN

from .models import User, Address
from meiduo_mall.utils.views import LoginRequiredView
from .utils import check_token_to_user, generate_verify_email_url
from celery_tasks.email.tasks import send_verify_email
from celery_tasks.sms.tasks import send_sms_code
from meiduo_mall.utils.response_code import RETCODE
from goods.models import SKU
from carts.utils import merge_cart_cookie_to_redis
from orders.models import OrderInfo

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
        sms_code_server = redis_conn.get('sms_%s' % mobile).decode()
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
            return render(request, 'register.html', {'register_errmsg': '用户注册失败'})

        # 状态保持
        login(request, user)  # 存储用户的id到session中记录它的登录状态
        response = redirect('/')  # 创建好响应对象
        response.set_cookie('username', user.username, max_age=settings.SESSION_COOKIE_AGE)

        # 响应结果重定向到首页
        return response


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
        if user is None:
            return render(request, 'login.html', {'account_errmsg': '用户名或密码错误'})
        # 根据是否勾选记住密码保持状态
        login(request, user)
        if remembered != 'on':
            request.session.set_expiry(0)
        else:
            request.session.set_expiry(None)

        # 在首页显示用户名
        response = redirect(request.GET.get('next', '/'))  # 创建好响应对象
        response.set_cookie('username', user.username, max_age=settings.SESSION_COOKIE_AGE if remembered == 'on' else None)


        # 登录成功那一刻合并购物车
        merge_cart_cookie_to_redis(request, user, response)
        # 响应结果重定向到首页
        return response


class LogoutView(View):
    '''退出登录'''

    def get(self, request):
        # 清除session中的状态保持数据
        logout(request)

        # 清除cookie中的username
        response = redirect(reverse('users:login'))
        response.delete_cookie('username')

        return response


class UserInfoView(mixins.LoginRequiredMixin, View):
    '''用户中心界面'''

    def get(self, request):

        return render(request, 'user_center_info.html')


class EmailView(mixins.LoginRequiredMixin, View):
    '''添加用户邮箱'''

    def put(self, request):
        # 接收请求体email数据

        json_dict = json.loads(request.body.decode())
        email =json_dict.get('email')

        # 校验
        if all([email]) is None:
            return http.HttpResponseForbidden('清输入邮箱')

        if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
            return http.HttpResponseForbidden('邮箱格式错误')

        # 获取user
        user = request.user
        # 设置user.email字段
        user.email = email
        # 用save保存
        user.save()

        # 发送验证邮件，用celery
        verify_url = generate_verify_email_url(user) # 生成激活链接
        send_verify_email.delay(email,verify_url)

        # 响应
        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK'})


class VerifyEmailView(View):
    '''激活邮箱'''

    def get(self, request):
        # 获取token
        token = request.GET.get('token')

        # 解密并获取user
        user = check_token_to_user(token)
        if user is None:
            return http.HttpResponseForbidden('token无效')

        # 修改当前user.email_active
        user.email_active = True
        user.save()

        # 响应
        return redirect('/info/')


class AddressView(mixins.LoginRequiredMixin, View):
    '''用户收获地址'''
    def get(self, request):
        '''显示用户收货地址界面'''
        user = request.user
        # 获取当前用户所有的收货地址
        address_qs = Address.objects.filter(is_deleted=False, user=user)

        address_list = []
        for address in address_qs:
            address_dict = {
                'id': address.id,
                'title': address.title,
                'receiver': address.receiver,
                'province_id': address.province_id,
                'province': address.province.name,
                'city_id': address.city_id,
                'city': address.city.name,
                'district_id': address.district_id,
                'district': address.district.name,
                'place': address.place,
                'mobile': address.mobile,
                'tel': address.tel,
                'email': address.email,
            }
            address_list.append(address_dict)

        context = {
            'addresses': address_list,
            'default_address_id': user.default_address_id
        }
        return render(request, 'user_center_site.html', context)


class CreateAddressView(LoginRequiredView):
    '''新增收货地址'''

    def post(self, request):
        user = request.user
        # 判断用户收货地址数据，大于20个提前响应
        count = Address.objects.filter(user=user, is_deleted=False).count()
        if count > 20:
            return http.HttpResponseForbidden('用户收货地址上限')
        # 接收请求数据
        json_dict = json.loads(request.body.decode())
        title = json_dict.get('title')
        receiver = json_dict.get('receiver')
        province_id = json_dict.get('province_id')
        city_id = json_dict.get('city_id')
        district_id = json_dict.get('district_id')
        place = json_dict.get('place')
        mobile = json_dict.get('mobile')
        tel = json_dict.get('tel')
        email = json_dict.get('email')
        # 校验
        if all([title, receiver, province_id, city_id, district_id, place, mobile]) is False:
            return http.HttpResponseForbidden('缺少必传参数')

        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return http.HttpResponseForbidden('参数mobile有误')
        if tel:
            if not re.match(r'^(0[0-9]{2,3}-)?([2-9][0-9]{6,7})+(-[0-9]{1,4})?$', tel):
                return http.HttpResponseForbidden('参数tel有误')
        if email:
            if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
                return http.HttpResponseForbidden('参数email有误')

        # 新增
        try:
            address = Address.objects.create(
                user=user,
                title=title,
                receiver=receiver,
                province_id=province_id,
                city_id=city_id,
                district_id=district_id,
                place=place,
                mobile=mobile,
                tel=tel,
                email=email
            )
            if user.default_address is None:
                user.default_address = address
                user.save()
        except Exception:
            return http.HttpResponseForbidden('保存地址失败')

        # 将新增的地址响应到首页
        address_dict = {
            'id': address.id,
            'title': address.title,
            'receiver': address.receiver,
            'province_id': address.province_id,
            'province': address.province.name,
            'city_id': address.city_id,
            'city': address.city.name,
            'district_id': address.district_id,
            'district': address.district.name,
            'place': address.place,
            'mobile': address.mobile,
            'tel': address.tel,
            'email': address.email,
        }
        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK', 'address': address_dict})


class UpdateDestroyAddressView(LoginRequiredView):
    """修改和删除"""

    def put(self, request, address_id):
        """修改地址逻辑"""
        # 查询要修改的地址对象
        try:
            address = Address.objects.get(id=address_id)
        except Address.DoesNotExist:
            return http.HttpResponseForbidden('要修改的地址不存在')

        # 接收
        json_dict = json.loads(request.body.decode())
        title = json_dict.get('title')
        receiver = json_dict.get('receiver')
        province_id = json_dict.get('province_id')
        city_id = json_dict.get('city_id')
        district_id = json_dict.get('district_id')
        place = json_dict.get('place')
        mobile = json_dict.get('mobile')
        tel = json_dict.get('tel')
        email = json_dict.get('email')

        # 校验
        if all([title, receiver, province_id, city_id, district_id, place, mobile]) is False:
            return http.HttpResponseForbidden('缺少必传参数')

        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return http.HttpResponseForbidden('参数mobile有误')
        if tel:
            if not re.match(r'^(0[0-9]{2,3}-)?([2-9][0-9]{6,7})+(-[0-9]{1,4})?$', tel):
                return http.HttpResponseForbidden('参数tel有误')
        if email:
            if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
                return http.HttpResponseForbidden('参数email有误')

        # 修改
        Address.objects.filter(id=address_id).update(
            title=title,
            receiver=receiver,
            province_id=province_id,
            city_id=city_id,
            district_id=district_id,
            place=place,
            mobile=mobile,
            tel=tel,
            email=email
        )
        address = Address.objects.get(id=address_id)  # 要重新查询一次新数据
        # 把新增的地址数据响应回去
        address_dict = {
            'id': address.id,
            'title': address.title,
            'receiver': address.receiver,
            'province_id': address.province_id,
            'province': address.province.name,
            'city_id': address.city_id,
            'city': address.city.name,
            'district_id': address.district_id,
            'district': address.district.name,
            'place': address.place,
            'mobile': address.mobile,
            'tel': address.tel,
            'email': address.email,
        }
        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK', 'address': address_dict})
        # 响应

    def delete(self, request, address_id):
        """对收货地址逻辑删除"""
        try:
            address = Address.objects.get(id=address_id)
        except Address.DoesNotExist:
            return http.HttpResponseForbidden('要删除的地址不存在')

        address.is_deleted = True
        # address.delete()
        address.save()

        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK'})


class DefaultAddressView(LoginRequiredView):
    """设置默认地址"""

    def put(self, request, address_id):
        """实现默认地址"""
        try:
            address = Address.objects.get(id=address_id)
        except Address.DoesNotExist:
            return http.HttpResponseForbidden('要修改的地址不存在')

        user = request.user
        user.default_address = address
        user.save()

        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK'})


class UpdateTitleAddressView(LoginRequiredView):
    """修改用户收货地址标题"""

    def put(self, request, address_id):
        try:
            address = Address.objects.get(id=address_id)
        except Address.DoesNotExist:
            return http.HttpResponseForbidden('要修改的地址不存在')

        json_dict = json.loads(request.body.decode())
        title = json_dict.get('title')
        address.title = title
        address.save()

        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK'})


class ChangePasswordView(LoginRequiredView):
    """修改密码"""

    def get(self, request):
        return render(request, 'user_center_pass.html')


    def post(self, request):
        # 获取表单数据
        old_pwd = request.POST.get('old_pwd')
        new_pwd = request.POST.get('new_pwd')
        new_cpwd = request.POST.get('new_cpwd')
        # 获取用户旧密码
        user = request.user
        # 校验
        if not all([old_pwd, new_cpwd, new_pwd]):
            return http.HttpResponseForbidden('缺少必传参数')
        if not user.check_password(old_pwd):
            return http.HttpResponseForbidden('密码输入有误')
        if new_pwd != new_cpwd:
            return http.HttpResponseForbidden('两次密码输入不一致')

        # 保存新密码
        user.set_password(new_pwd)
        user.save()

        logout(request)
        response = redirect('/login/')
        response.delete_cookie('username')

        return response


class UserBrowseHistory(LoginRequiredView):
    '''记录商品浏览记录'''

    def post(self, request):
        # 获取请求体中的sku_id
        json_dict = json.loads(request.body.decode())
        sku_id = json_dict.get('sku_id')
        user = request.user
        # 校验sku_id
        try:
            sku = SKU.objects.get(id = sku_id)
        except SKU.DoesNotExist:
            return http.HttpResponseForbidden('商品不存在')

        # 创建redis连接对象，存储数据
        redis_conn = get_redis_connection('history')
        pl = redis_conn.pipeline()

        key = 'history_%s' % user.id

        # 去重
        pl.lrem(key, 0, sku_id)
        # 存储到开头
        pl.lpush(key, sku_id)
        # 截取前五个
        pl.ltrim(key, 0, 4)
        pl.execute()

        # 响应
        return http.JsonResponse({'code' : RETCODE.OK, 'errmsg': 'OK'})


    def get(self, request):
        # 创建redis连接
        redis_conn =  get_redis_connection('history')
        # 截取数据库中的数据
        sku_list  = redis_conn.lrange('history_%s' % request.user.id, 0, -1)

        skus =[]
        # 遍历sku_list
        for sku_id in sku_list:
            sku = SKU.objects.get(id=sku_id)
            sku_dict = {
                'id': sku.id,
                'name': sku.name,
                'default_image_url': sku.default_image.url,
                'price': sku.price,
            }
            skus.append(sku_dict)

        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK', 'skus': skus})


class UserOrderInfoView(LoginRequiredView):

    def get(self, request, page_num):
        user = request.user
        # 查询当前登录用户的所有订单
        order_qs = OrderInfo.objects.filter(user=user).order_by('-create_times')
        for order_model in order_qs:
            # 给每个订单多定义两个属性-订单支付方式中文名-订单状态中文名
            order_model.pay_method_name = OrderInfo.PAY_METHOD_CHOICES[order_model.pay_method - 1][1]
            order_model.status_name = OrderInfo.ORDER_STATUS_CHOICES[order_model.status - 1][1]
            # 再给订单模型对象定义sku_list属性，用它来包装订单中的所有商品
            order_model.sku_list = []

            # 获取订单中的所有商品
            order_goods_qs = order_model.skus.all()
            # 遍历订单中所有商品查询集
            for good_model in order_goods_qs:
                sku = good_model.sku
                sku.count = good_model.count
                sku.amount = sku.price * sku.count
                # 把sku添加到订单sku_list列表中
                order_model.sku_list.append(sku)

        # 创建分页器
        paginator = Paginator(order_qs, 2)
        # 获取指定页的所有数据
        page_orders = paginator.page(page_num)
        # 获取总页数
        total_page = paginator.num_pages

        context = {
            'page_orders': page_orders,
            'page_num': page_num,
            'total': total_page
        }
        return render(request, 'user_center_order.html', context)


class FindPasswordView(View):
    '''找回密码'''

    def get(self, request):
        '''渲染找回密码界面'''

        return render(request, 'find_password.html')


class UsernameExistView(View):
    '''验证用户名是否存在'''

    def get(self, request, username):
        # 获取参数
        image_code_cli = request.GET.get('text')
        uuid = request.GET.get('image_code_id')
        # 校验
        # 校验用户名是否已存在
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return http.JsonResponse({'code': RETCODE.USERERR, 'errmsg': '用户名不存在'}, status=404)
        # 创建redis连接对象
        redis_conn = get_redis_connection('verify_code')
        # 提取图像验证码
        img_code = redis_conn.get('img_%s' % uuid)
        # 提取完毕之后删除图形验证码，防止恶意刷短信
        redis_conn.delete('img_%s' % uuid)
        # get数据如果为空，会报错，所以要先验证图形验证码是否失效
        if img_code is None:
            return http.JsonResponse({'code': RETCODE.NECESSARYPARAMERR, 'errmsg': '图形验证码失效'})
        # 对比图形验证码
        # 注意：从服务器提取的图形验证码一定要解码
        if image_code_cli.lower() != img_code.decode().lower():
            return http.JsonResponse({'code': RETCODE.IMAGECODEERR, 'errmsg': '图形验证码有误'}, status=400)
        # 根据用户名获取手机号
        mobile = user.mobile
        # 创建token对象
        token = TOKEN(settings.SECRET_KEY, 300)
        access_token = token.dumps({'mobile': mobile})
        access_token = access_token.decode()
        # 存储access_token进redis
        redis_conn.setex('token_%s' % user.id, 300, access_token)
        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK', 'mobile': mobile, 'access_token': access_token})


class GenerateSmsCodeView(View):
    '''发送短信验证码'''
    def get(self, request):
        # 解析token，获取mobile
        access_token = request.GET.get('access_token')
        # 创建token对象
        token = TOKEN(settings.SECRET_KEY, 300)
        mobile = token.loads(access_token)['mobile']
        # 生成短信验证码
        sms_code = '%06d' % randint(0, 999999)
        logger.info(sms_code)
        # 创建redis管道对象来用于保存数据，能提高代码运行效率
        redis_conn = get_redis_connection('verify_code')
        pl = redis_conn.pipeline()
        # 保存短信验证码
        pl.setex('sms_%s' % mobile, 60 * 3, sms_code)
        # 手机号发过短信后在redis中存储一个标记
        # redis_conn.setex('send_flag_%s' % mobile, 60, 1)
        pl.setex('send_flag_%s' % mobile, 60, 1)
        # 执行管道
        pl.execute()

        # 发送短信验证码 (后面参数信息为 手机号，[验证码， 有效时间单位分钟]， 短信模板ID)
        # CCP().send_template_sms(mobile, [sms_code, constants.SMS_CODE_EXPIRE // 60], constants.SMS_TEMPLATE_ID)
        # 将需要执行的任务列表存储在broker
        send_sms_code.delay(mobile, sms_code)
        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': '短信发送成功'})


class SMSVerifyView(View):
    '''验证短信验证码'''
    def get(self, request, username):
        # 获取参数信息
        sms_code = request.GET.get('sms_code')
        user = User.objects.get(username=username)
        mobile = user.mobile
        # 短信校验
        # 创建redis连接,获取redis中的随机验证码/一定要解码
        redis_conn = get_redis_connection('verify_code')
        sms_code_server = redis_conn.get('sms_%s' % mobile).decode()
        # 校验
        if sms_code_server is None:
            return http.JsonResponse({'errmsg': '手机号有误'}, status=404)
        if sms_code_server != sms_code:
            return http.JsonResponse({'errmsg': '输入的短信验证码有误'}, status=400)

        user_id = user.id
        access_token = redis_conn.get('token_%s' % user_id)
        access_token = access_token.decode()
        return http.JsonResponse({'user_id': user_id, 'access_token': access_token})


class InputPasswordView(View):
    '''覆盖原密码'''
    def post(self, request, user_id):
        # 获取用户
        user = User.objects.get(id= user_id)
        # 获取表单密码
        pwd = request.POST.get('password')
        cpwd = request.POST.get('password2')
        access_token = request.POST.get('access_token')

        # 校验
        if all([pwd, cpwd, access_token]) is False:
            return http.JsonResponse({'code': RETCODE.PARAMERR, 'message': '缺少必传参数'})

        if pwd != cpwd:
            return http.JsonResponse({'message': '两次输入密码不一致', 'code': RETCODE.CPWDERR})

        # 创建reis链接
        redis_conn = get_redis_connection('verify_code')
        # 获取server中的token
        access_token_server = redis_conn.get('token_%s' % user_id)
        # 校验token
        if access_token != access_token_server:
            return http.JsonResponse({'message': '数据有误'}, status=400)

        # 保存新密码
        user.set_password(pwd)
        user.save()

        return http.JsonResponse({'code': RETCODE.OK, 'message': '修改成功'})
