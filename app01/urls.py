from django.urls import path
from app01 import views

urlpatterns = [
    # ===== 注册 / 登录 / 退出 / 验证码 =====
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('get_code/', views.GetCodeImage.as_view(), name='get_code'),
    path('get_email_code/', views.GetEmailCode.as_view(), name='get_email_code'),
    path('change_pwd/', views.ChangePwdView.as_view(), name='change_pwd'),
    path('set_avatar/', views.SetAvatarView.as_view(), name='set_avatar'),
    # 退出登录：需要登录装饰器
    path('logout/', views.LogoutView.as_view(), name='logout'),

    # ===== 第三步：首页 / 个人站点 / 文章详情 / 点赞点踩 / 评论 =====
    path('', views.IndexView.as_view(), name='index'),
    # 个人站点 /index/<username>/
    path('index/<str:username>/', views.SiteView.as_view(), name='site'),
    # 分类   /index/<username>/category/<cid>/
    path('index/<str:username>/category/<int:cid>/', views.SiteView.as_view(), name='site_category'),
    # 标签   /index/<username>/tag/<tid>/
    path('index/<str:username>/tag/<int:tid>/', views.SiteView.as_view(), name='site_tag'),
    # 归档   /index/<username>/date/<year>-<month>/
    path('index/<str:username>/date/<int:year>-<int:month>/', views.SiteView.as_view(), name='site_date'),
    # 文章详情 /index/<username>/p/<article_id>/
    path('index/<str:username>/p/<int:article_id>/', views.ArticleDetailView.as_view(), name='article_detail'),
    # 点赞点踩 /up_down/
    path('up_down/', views.UpDownView.as_view(), name='up_down'),
    # 评论 /comment/
    path('comment/', views.CommentView.as_view(), name='comment'),

    # ===== 第四步：后台文章管理（列表 / 新增 / 编辑）=====
    # 后台首页：当前用户站点的文章列表 （GET） /backend/
    path('backend/', views.BackendView.as_view(), name='backend'),
    # 新增文章：文本框 markdown 或上传 .md 文件 （POST） /backend/add_article/
    path('backend/add_article/', views.AddArticleView.as_view(), name='add_article'),
    # 编辑文章：<article_id>，仅作者本人可编辑 （POST） /backend/edit_article/<article_id>/
    path('backend/edit_article/<int:article_id>/', views.EditArticleView.as_view(), name='edit_article'),

    # ===== 第五步：完整后台 CRUD =====
    # 删除文章（逻辑删除 + 清缓存） （POST） /backend/del_article/<article_id>/
    path('backend/del_article/', views.DelArticleView.as_view(), name='del_article'),


    # 分类管理（GET 列表 / POST 增删改 AJAX）
    path('backend/category/', views.CategoryView.as_view(), name='category'),
    # 标签管理（GET 列表 / POST 增删改 AJAX）
    path('backend/tag/', views.TagView.as_view(), name='tag'),
    # 评论管理（查看自己评论） （GET） /backend/comment/
    path('backend/comment/', views.CommentManageView.as_view(), name='comment_manage'),
    # 删除评论（逻辑删除 + 评论数-1 + 清首页缓存）
    path('backend/comment/del/', views.CommentDelView.as_view(), name='comment_del'),
    # 个人信息编辑（用户名/年龄/性别/手机号 + 站点CSS上传）
    path('backend/info/', views.InfoView.as_view(), name='info'),
]

