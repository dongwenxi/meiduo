from django.db import models
from django.contrib.auth.models import AbstractUser

from meiduo_mall.utils.models import BaseModel

# Create your models here.

class User(AbstractUser):
    # 自定义用户模型类
    mobile = models.CharField(max_length=11, unique=True, verbose_name='手机号')
    # 给已经存在表的模型添加字段，新字段必须给默认值，或者为None，否则迁移会报错
    email_active = models.BooleanField(default=False, verbose_name='邮箱激活状态')
    default_address = models.ForeignKey('Address', related_name='users', null=True,
                                        blank=True, on_delete=models.SET_NULL, verbose_name='默认地址')

    class Meta:
        db_table = 'tb_users'
        verbose_name = '用户'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.username


class Address(BaseModel):
    '''用户地址'''
    user =models.ForeignKey(User, on_delete=models.CASCADE, related_name='addresser', verbose_name='用户')
    title = models.CharField(max_length=20, verbose_name='地址名称')
    receiver = models.CharField(max_length=20, verbose_name='收货人')
    province = models.ForeignKey('area.Area', on_delete=models.PROTECT, related_name='province_addresses', verbose_name='省')
    city = models.ForeignKey('area.Area', on_delete=models.PROTECT, related_name='city_addresses', verbose_name='市')
    district = models.ForeignKey('area.Area', on_delete=models.PROTECT, related_name='district_addresses', verbose_name='区')
    place = models.CharField(max_length=50, verbose_name='地址')
    mobile = models.CharField(max_length=11, verbose_name='手机')
    tel = models.CharField(max_length=20, null=True, blank=True, default='', verbose_name='固定电话')
    email = models.CharField(max_length=30, null=True, blank=True, default='', verbose_name='电子邮箱')
    is_deleted = models.BooleanField(default=False, verbose_name='逻辑删除')

    class Meta:
        db_table = 'tb_address'
        verbose_name = '用户地址'
        verbose_name_plural = verbose_name
        ordering = ['-update_times']
