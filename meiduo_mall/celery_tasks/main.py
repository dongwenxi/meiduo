# celery启动文件
from celery import Celery
import os

# 告诉celery，调用的django配置文件路径
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'meiduo_mall.setting.dev')

# celery实例对象(生产者)
celery_app = Celery('meiduo')

# 加载celery配置，指定broker的位置
celery_app.config_from_object('celery_tasks.config')

# 自动注册celery任务
celery_app.autodiscover_tasks(['celery_tasks.sms', 'celery_tasks.email'])
