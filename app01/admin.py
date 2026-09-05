from django.contrib import admin
from app01.models import *
# 注册模型到管理员界面

# 标准注册,并且对模版进行额外配置
@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    """用户模型后台管理配置"""
    # 列表页展示的字段
    list_display = ['id', 'username', 'age', 'gender', 'phone', 'email', 'blog', 'is_delete']
    # 过滤器：右侧筛选栏
    list_filter = ['gender', 'is_delete']
    # 搜索框，可以按用户名、手机号、邮箱搜索
    search_fields = ['username', 'phone', 'email']


@admin.register(Blog)
class BlogAdmin(admin.ModelAdmin):
    """个人站点模型后台管理配置"""
    list_display = ['id', 'site_name', 'site_title', 'site_theme', 'is_delete']
    search_fields = ['site_name', 'site_title']


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    """标签模型后台管理配置"""
    list_display = ['id', 'name', 'blog', 'is_delete']
    list_filter = ['blog']
    search_fields = ['name']


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """分类模型后台管理配置"""
    list_display = ['id', 'name', 'blog', 'is_delete']
    list_filter = ['blog']
    search_fields = ['name']


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    """文章模型后台管理配置"""
    list_display = ['id', 'title', 'blog', 'category', 'cover', 'up_num', 'down_num', 'comment_num', 'is_delete']
    list_filter = ['blog', 'category', 'is_delete']
    search_fields = ['title', 'content']


@admin.register(UpAndDown)
class UpAndDownAdmin(admin.ModelAdmin):
    """点赞点踩记录表后台管理配置"""
    list_display = ['id', 'user', 'article', 'is_up', 'create_time']
    list_filter = ['is_up']


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    """评论模型后台管理配置"""
    list_display = ['id', 'user', 'article', 'parent', 'reply_to', 'create_time', 'is_delete']
    list_filter = ['is_delete']
    search_fields = ['content']