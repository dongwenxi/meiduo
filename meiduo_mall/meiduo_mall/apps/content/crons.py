import time,os
from django.conf import settings
from django.template import loader

from .models import ContentCategory
from .utils import get_categories


def generate_static_index_html():

    # 用来装所有广告数据的字典
    contents = {}
    print('%s: generate_static_index_html' % time.ctime())

    # 获取所有广告类别数据
    contentCategory_qs = ContentCategory.objects.all()

    for category in contentCategory_qs:
        contents[category.key] = category.content_set.filter(status=True).order_by('sequence')

    context = {
        'categories': get_categories(),
        'contents': contents
    }

    # response = render(None, 'index.html', context)
    # html_text = response.content.decode()  # 获取响应体数据
    # 加载模板文件
    template = loader.get_template('index.html')
    # 渲染模板
    html_text = template.render(context)

    file_path = os.path.join(settings.STATICFILES_DIRS[0], 'index.html')
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(html_text)