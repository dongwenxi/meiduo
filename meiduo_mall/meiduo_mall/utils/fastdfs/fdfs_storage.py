from django.core.files.storage import Storage
from fdfs_client.client import Fdfs_client
from django.conf import settings


class FastDFSStorage(Storage):
    """自定义文件存储类"""

    # def _open(self, name, mode='rb'):
    #     """
    #     用于打开文件
    #     :param name: 要打开的文件名
    #     :param mode: 打开文件模式
    #     """
    #     pass
    def __init__(self, client_conf=None, base_url=None):
        if client_conf is None:
            client_conf = settings.FDFS_CLIENT_CONF

        self.client_conf = client_conf

        if base_url is None:
            base_url = settings.FDFS_BASE_URL

        self.base_url = base_url


    def _save(self, name, content):
        """
        文件上传时会调用此方法
        :param name: 要上传的文件名
        :param content: 要上传的文件对象
        :return: file_id
        """
        # 创建对象
        client = Fdfs_client(self.client_conf)

        # 上传文件到FDFS系统
        res = client.upload_by_buffer(content.read())

        if res.get('Status') != 'Upload successed.':
            raise Exception('上传文件到FDFS系统失败')

        # 获取file_id
        file_id = res.get('Remote file_id')
        return file_id

    def exists(self, name):
        '''判断上传文件的名称和文件系统中原有的文件名是否冲突'''

        return False


    def url(self, name):
        """
        当使用image字段.url属性时就会来调用此方法获取到要访问的图片绝对路径
        :param name: file_id
        :return: http://192.168.103.210:8888 + file_id
        """
        # return 'http://192.168.103.210:8888/' + name
        return self.base_url + name
