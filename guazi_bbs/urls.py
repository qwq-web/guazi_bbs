"""
bbs/urls.py  项目主路由配置
------------------------------------------------
  - /admin/   Django 自带后台
  - /media/   开发环境访问用户上传媒体资源
  - /static/  静态文件路由（DEBUG=False 时也生效）
  - /         后续通过 include('app01.urls') 接入业务路由
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings                       # 导入项目配置
from django.conf.urls.static import static             # 导入静态文件路由函数
from django.views.static import serve                   # 手动视图函数：用于 DEBUG=False 时服务静态/媒体文件

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('app01.urls')),
]

# —— 媒体文件路由：DEBUG=True/False 都生效 ——
# 用户上传的头像、封面、CSS 主题等，必须能通过 /media/xxx 访问
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
# 如果 DEBUG=False 时上面的 static() 不生效（它默认只在 DEBUG=True 时挂载），
# 用 serve 视图手动加一条兜底路由，确保 /media/ 下的文件始终可访问
if not settings.DEBUG:
    from django.urls import re_path
    urlpatterns += [
        re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
    ]

# —— 静态文件路由：DEBUG=False 时 Django 不自动服务静态文件 ——
# 需要手动挂载 serve 视图，让 /static/ 下的 CSS/JS/图片在非 DEBUG 模式也能访问
# （admin 后台的 CSS/JS 也走 /static/，所以这步同时修复 admin 样式丢失问题）
if not settings.DEBUG:
    from django.urls import re_path
    urlpatterns += [
        re_path(r'^static/(?P<path>.*)$', serve, {'document_root': settings.STATIC_ROOT}),
    ]

# ✅ 写在这里！主urls.py最底部
handler404 = 'app01.views._render_404'