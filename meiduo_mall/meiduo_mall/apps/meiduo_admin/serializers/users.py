import re

from django.utils import timezone
from rest_framework import serializers

from users.models import User


class AdminAuthSerializer(serializers.ModelSerializer):
    '''管理员登录序列化器'''
    token = serializers.CharField(label='JWT token', read_only=True)
    username = serializers.CharField(label='用户名')

    class Meta:
        model = User
        fields = ('id', 'username', 'password', 'token')

        extra_kwargs = {
            'password':{
                'write_only':True
            }
        }

    # 补充验证
    def validate(self, attrs):
        '''用户名和密码是否正确'''
        # 获取username和password
        username = attrs['username']
        password = attrs['password']

        try:
            user = User.objects.get(username=username, is_staff=True)
        except User.DoesNotExist:
            # 用户不存在
            raise serializers.ValidationError('用户名或者密码错误')
        else:
            # 校验密码
            if not user.check_password(password):
                raise serializers.ValidationError('用户名或者密码错误')

        # 在attrs中添加user
        attrs['user'] = user

        return attrs

    def create(self, validated_data):
        # 生成jwt_token，保存登录用户信息
        user = validated_data['user']

        # 更新用户登录时间
        datetime = timezone.now()
        user.last_login = datetime
        user.save()

        # 生成jwt_token
        from rest_framework_jwt.settings import api_settings

        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER

        payload = jwt_payload_handler(user)
        token = jwt_encode_handler(payload)

        # 给user对象增加属性token，保存登录用户信息
        user.token = token

        return user


class UserSerializer(serializers.ModelSerializer):
    '''用户序列化器类'''
    class Meta:
        model = User
        fields = ('id', 'username', 'mobile', 'email', 'password')

        extra_kwargs = {
            'username': {
                'min_length': 5,
                'max_length': 20,
                'error_messages': {
                    'min_length': '用户名最小长度为5',
                    'max_length': '用户名最大长度为20'
                }
            },
            'password':{
                'write_only': True,
                'min_length': 8,
                'max_length': 20,
                'error_messages': {
                    'min_length': '密码最小长度为8',
                    'max_length': '密码最大长度为20'
                }
            }
        }

    def validate_mobile(self, value):
        # 手机号格式
        if not re.match(r'^1[3-9]\d{9}$', value):
            raise serializers.ValidationError('手机号格式不正确')

        # 手机号是否注册
        count = User.objects.filter(mobile=value).count()

        if count > 0:
            raise serializers.ValidationError('手机号已注册')

        return value

    def create(self, validated_data):
        # 创建并保存新用户数据
        user = User.objects.create_user(**validated_data)

        return user
