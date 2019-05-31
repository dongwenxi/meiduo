from rest_framework.generics import CreateAPIView, ListCreateAPIView
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from meiduo_admin.serializers.users import AdminAuthSerializer, UserSerializer
from users.models import User


class AdminAuthView(CreateAPIView):
    # 指定视图所使用的序列化器类
    serializer_class = AdminAuthSerializer
    # POST /meiduo_admin/authorizations/
    # class AdminAuthView(APIView):
    # def post(self, request):
    #     """
    #     管理员登录:
    #     1. 获取参数并进行校验
    #     2. 服务器签发jwt token数据
    #     3. 返回应答
    #     """
        # 1. 获取参数并进行校验
        # serializer = AdminAuthSerializer(data=request.data)
        # serializer.is_valid(raise_exception=True)

        # 2. 服务器签发jwt token数据(create)
        # serializer.save()

        # 3. 返回应答
        # return Response(serializer.data, status=status.HTTP_201_CREATED)


class UserInfoView(ListCreateAPIView):
    '''查询用户详细信息'''
    serializer_class = UserSerializer

    def get_queryset(self):
        '''重写GenericAPIView中的get_queryset'''
        # self.request:请求request对象
        keyword =self.request.query_params.get('keyword') # None

        if keyword:
            # 1.1如果keyword不为空，根据用户名搜索普通用户
            users = User.objects.filter(username__contains=keyword, is_staff=False)
        else:
            # 否则获取所有普通用户的数据
            users = User.objects.filter(is_staff= False)

        return users

    # def post(self, reqeust):
    #     return self.create(request)

    # def post(self, request):
    #     '''网站用户数据新增'''
    #     serializer = self.get_serializer(data=request.data)
    #     serializer.is_valid(raise_exception=True)

    #     serializer.save()
    #     return Response(serializer.data, status=status.HTTP_201_CREATED)

    # def get(self, request):
    #     '''网站用户数据获取'''
    #     users = self.get_queryset()

    #     serializer = self.get_serializer(users, many=True)
    #     return Response(serializer.data)

    # def get(self, request):
    #     return self.list(reuqest)
