from fdfs_client.client import Fdfs_client

# 创建对象
client = Fdfs_client('./client.conf')
# 上传
ret = client.upload_by_filename('/home/python/Desktop/02-其他资料/upload_Images/kk01.jpeg')

print(ret)
