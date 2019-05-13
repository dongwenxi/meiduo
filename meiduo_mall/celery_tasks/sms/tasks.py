# 编写异步任务代码
from celery_tasks.sms.yuntongxun.sms import CCP
from celery_tasks.main import celery_app

# 导包失败，celery是脱离django框架运行的，必须在main文件中指定django配置文件路径
from meiduo_mall.apps.verifications import constants


# 此装饰器作为是让下面的函数真正的成功celery的任务
@celery_app.task(name='send_sms_code')
def send_sms_code(mobile, sms_code):
    # 定义发短信的方法
    """
    利用celery异步发送短信
    :param mobile: 要收到短信的手机号
    :param sms_code: 短信验证码
    """
    CCP().send_template_sms(mobile, [sms_code, constants.SMS_CODE_EXPIRE // 60], constants.SMS_TEMPLATE_ID)
