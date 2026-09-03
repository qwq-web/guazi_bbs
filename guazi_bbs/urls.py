"""
bbs/urls.py  项目主路由配置
------------------------------------------------
  - /admin/   Django 自带后台
  - /media/   开发环境访问用户上传媒体资源
  - /         后续通过 include('app01.urls') 接入业务路由
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings # 导入项目配置
from django.conf.urls.static import static # 导入静态文件路由函数

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('app01.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) # 配置媒体文件路由

# ✅ 写在这里！主urls.py最底部
handler404 = 'app01.views._render_404'