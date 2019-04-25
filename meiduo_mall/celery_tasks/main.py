# celery启动文件
from celery import Celery


# celery实例对象(生产者)
celery_app = Celery('mall')

# 加载celery配置，指定broker的位置
celery_app.config_from_object('celery_tasks.config')

# 自动注册celery任务
celery_app.autodiscover_tasks('celery_tasks.sms')

