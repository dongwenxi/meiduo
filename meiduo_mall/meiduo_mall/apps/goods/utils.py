def get_breadcrumb(category):
    """面包屑导航"""
    cat1 = category.parent.parent
    cat1.url = cat1.goodschannel_set.all()[0].url
    breadcrumb = {
        'cat1': cat1,
        'cat2': category.parent,
        'cat3': category
    }

    return breadcrumb