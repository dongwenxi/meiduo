from itsdangerous import TimedJSONWebSignatureSerializer as Serializer, BadData
from django.conf import settings

def generate_openid_signature(openid):
    '''加密方法'''

    serializer = Serializer(secret_key=settings.SECRET_KEY, expires_in=600)
    data = {'openid': openid}
    # 加密数据，返回byte类型
    openid_sign = serializer.dumps(data)
    return openid_sign.decode()


def check_openid_sign(openid_sign):
    '''解密，拿回数据'''

    serializer = Serializer(secret_key=settings.SECRET_KEY, expires_in=600)
    try:
        data = serializer.loads(openid_sign)
    except BadData:
        return None
    else:
        return data.get('openid')
