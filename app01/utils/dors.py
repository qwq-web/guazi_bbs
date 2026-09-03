"""
app01/utils/dors.py  登录校验装饰器
------------------------------------------------------
  - 未登录：返回 JSON {"code":400,"msg":"请先登录"}（前端 AJAX 友好）
  - 已登录：直接执行原方法
  - is_login_method  配合 @method_decorator 用在类视图方法上
  - is_login_func    直接用在函数视图上
"""
from django.http import JsonResponse, HttpResponse

# 登录校验装饰器 Class 中的方法
def is_login_method(func):
    """
        类视图需要多传递一个 self 参数 , 或者在 method_decorator 中使用 partial 绑定 self 参数。
   """
    def wrapper(self,request, *args, **kwargs):
        user = request.user  # 获取 session 中的用户信息
        # 判断是否登录成功
        if not user.is_authenticated:
            return HttpResponse('请先登录')

        return func(self,request, *args, **kwargs)
    return wrapper

# 常规函数视图方法
def is_logout_func(func):
    def wrapper(request, *args, **kwargs):
        user = request.user  # 获取 session 中的用户信息

        # 判断是否登录成功
        if not user.is_authenticated:
            return HttpResponse('请先登录')

        return func(request, *args, **kwargs)
    return  wrapper()

