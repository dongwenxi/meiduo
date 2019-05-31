from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone

from goods.models import GoodsVisitCount
from meiduo_admin.serializers.statistical import GoodsVisitCountSerializer
from users.models import User


# get  /meiduo_admin/statistical/total_count/
class UserTotalCountView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        # 获取网站用户总数
        # 统计网站用户总数量
        count = User.objects.count()
        # 返回响应
        now_date = timezone.now()

        response_data = {
            'date': now_date.date(),
            'count': count,
        }

        return Response(response_data)


# get /meiduo_admin/statistical/day_increment/
class UserDayIncrementView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        # 统计网站日新增用户数量
        now_date = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        count = User.objects.filter(date_joined__gte=now_date).count()

        # 返回响应
        response_data = {
            'date': now_date.date(),
            'count': count
        }

        return Response(response_data)


# get  meiduo_admin/statistical/day_active/
class UserDayActiveView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        # 统计网站当日活跃用户数量
        now_date = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        count = User.objects.filter(last_login__gte=now_date).count()

        # 响应
        response_date = {
            'count': count,
            'date': now_date.date()
        }

        return Response(response_date)


class UserDayOrderView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        # 统计网站日下单用户数量
        now_date = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        count = User.objects.filter(orders__create_times__gte=now_date).count()

        # 响应
        response_date = {
            'count': count,
            'date': now_date.date()
        }

        return Response(response_date)


class UserMouthIncrementView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        # 统计一个月新增用户的数量
        now_date = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        # 起始日期
        begin_date = now_date - timezone.timedelta(days=29)
        # 统计数量列表
        count_list = []

        for i in range(30):
            # 当天日期
            cur_date = begin_date + timezone.timedelta(days=i)
            # 次日日期
            next_date = cur_date + timezone.timedelta(days=1)

            # 统计当天网站新增用户的数量
            count = User.objects.filter(date_joined__gte=cur_date, date_joined__lt=next_date).count()

            count_list.append({
                'date': cur_date,
                'count': count
            })

        return Response(count_list)


# get   /meiduo_admin/statistical/goods_day_views/
class GoodsDayViewsView(APIView):
    '''获取当天日分类商品的访问量'''
    permission_classes = [IsAdminUser]

    def get(self, request):
        # 获取当天日分类商品访问量数据
        now_date = timezone.now().date()
        good_visits = GoodsVisitCount.objects.filter(date=now_date)

        # 将数据序列化并返回
        serializer = GoodsVisitCountSerializer(good_visits, many=True)
        return Response(serializer.data)
