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
