"""
app01/views.py  全部业务视图（20 个类视图）
------------------------------------------------------
第1步：RegisterView / GetCodeImage / GetEmailCode / LoginView / LogoutView
       ChangePwdView / SetAvatarView
第2步：IndexView / SiteView / ArticleDetailView / UpDownView / CommentView
第3步：BackendView / AddArticleView / EditArticleView
第4步：DelArticleView / CategoryView / TagView / CommentManageView /
       CommentDelView / InfoView

缓存约定（全部通过 django.core.cache，禁止直接操作 redis）：
  code:{随机串}              图形验证码，60s
  email_code:{username}      邮箱验证码，300s
  home_article_list          首页文章列表，300s
  site_sidebar:{blog_id}     个人站点侧边栏，300s

AJAX 接口统一返回：
  成功 {"code":200,"msg":"...","url":"..."}
  失败 {"code":400,"msg":{字段:错误信息} 或 "错误字符串"}
"""
from django.shortcuts import render
from django.views import View
from django.core.paginator import Paginator  # 首页文章分页

# 注册相关模块
from django.http import JsonResponse
from app01.forms.user_forms import MyRegisterForm
from app01.models import *
import markdown

# ===== 注册 ====
# 允许上传的头像后缀
ALLOW_AVATAR_EXT = {'.jpg', '.jpeg', '.png', '.gif', '.bmp'}
class RegisterView(View):
    def get(self, request):
        return render(request, 'register.html')
    def post(self, request):
        """
        业务整体思路：
        GET请求：仅仅渲染注册页面给浏览器用户填写表单
        POST请求：接收前端AJAX提交的FormData表单数据（普通文本 + 头像文件）
        执行流程：表单校验 → 头像文件校验 → 先创建个人Blog站点对象 → 创建User用户对象并绑定Blog → 返回JSON结果跳转登录页
        """
        # --------------------------
        # 1：服务端表单校验（文本字段）
        form = MyRegisterForm(request.POST)
        # 单独获取头像文件，文件不经过Form校验，手动写校验逻辑
        avatar = request.FILES.get('avatar')

        if not form.is_valid():
            errors = {k: v[0] for k, v in form.errors.items()}
            return JsonResponse({'code': 400, 'msg': errors})

        if not avatar:
            return JsonResponse({'code': 400, 'msg': {'avatar': '请上传头像'}})

        # 提取文件后缀，全部转为小写，判断是否属于允许的图片后缀集合 ALLOW_AVATAR_EXT
        ext = '.' + avatar.name.rsplit('.', 1)[-1].lower() if '.' in avatar.name else ''
        if ext not in ALLOW_AVATAR_EXT:
            return JsonResponse({'code': 400, 'msg': {'avatar': '头像仅支持 jpg/png/gif/bmp'}})

        # 2. 创建个人Blog站点对象
        data = form.cleaned_data
        blog = Blog.objects.create(
            site_name=data['username'],
            site_title=data['site_title'],
        )
        blog.save()

        # 创建用户对象并自动添加密码
        user = User.objects.create_user(
            username=data['username'],
            password=data['password'],
            email=data['email'],
            avatar=avatar,
            blog=blog,
        )
        user.save()


        # 返回数据
        return JsonResponse({"code":200,"msg":"注册成功","url":"/login/"})


from app01.utils.code import get_code_image
from django.core.cache import cache
from django.http import HttpResponse

# ===== 验证码 ====
class GetCodeImage(View):
    """
    图形验证码图片接口：
      前端在 URL 上带 ?key=xxx，后端生成验证码文本，
      存入 Redis：code:{key}，过期 60 秒，并返回 PNG 图片二进制。
      前端登录提交时把 key + 用户输入的 code 一起传回校验。
    """
    def get(self, request):
        # 生成验证码字符串 + 图片二进制
        code, buf = get_code_image()
        key = request.GET.get('key') #前端传递的key
        # 存入缓存
        cache.set(f'code:{key}', code, 60)
        # 这里需要注意 不能返回 json , 因为 json 是文本格式，图片二进制不能直接返回
        return HttpResponse(buf, content_type='image/png') # 返回图片格式二进制


from app01.utils.email_util import generate_email_code, send_email_code

# ===== 邮箱验证码 ====
class GetEmailCode(View):
    """
       获取邮箱验证码：POST username
         校验用户存在 → 生成 6 位数字 → 存 Redis(email_code:{username}, 300s) → 发邮件
       """
    def post(self, request):
        username = (request.POST.get('username') or '').strip()
        # 校验用户名是否存在
        if not username:
            return JsonResponse({'code': 400, 'msg': '请输入用户名'})
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return JsonResponse({'code': 400, 'msg': '该用户名不存在，请先注册'})
        if not user.email:
            return JsonResponse({'code': 400, 'msg': '该账号未绑定邮箱'})

        code = generate_email_code(6) # 6位数字验证码
        print('邮箱验证码:', code)  # 学习阶段方便调试
        # 存入缓存(email_code:{username}, 300s)
        cache.set(f'email_code:{username}', code, 300)

        # 发送邮件
        ok = send_email_code(user.email, code)
        if not ok:
            return JsonResponse({'code': 400, 'msg': '邮件发送失败，请稍后重试'})
        return JsonResponse({'code': 200, 'msg': '验证码已发送至邮箱，5 分钟内有效'})


from django.contrib import auth
# ===== 登录 ====
class LoginView(View):
    """
   三重校验登录：
     1) 图形验证码（Redis code:{key}）
     2) 用户名 + 密码（auth.authenticate）
     3) 邮箱验证码（Redis email_code:{username}）
   全部通过 → auth.login；校验成功后立即删除缓存 key，防止被复用。
   """
    def get(self, request):
        return render(request, 'login.html')
    def post(self, request):
        username = (request.POST.get('username') or '').strip()
        password = request.POST.get('password') or ''
        code = (request.POST.get('code') or '').strip()
        code_key = (request.POST.get('code_key') or '').strip()
        email_code = (request.POST.get('email_code') or '').strip()

        # 1) 图形验证码校验
        cached_code = cache.get(f'code:{code_key}')
        if not cached_code or cached_code.lower() != code.lower():
            return JsonResponse({'code': 400, 'msg': {'code': '图形验证码错误或已过期'}})
        # 校验通过删除缓存 key
        cache.delete(f'code:{code_key}')

        # 2) 用户名密码
        user = auth.authenticate(request, username=username, password=password)
        if not user:
            return JsonResponse({'code': 400, 'msg': {'password': '用户名或密码错误'}})

        # 3) 邮箱验证码
        cached_email = cache.get(f'email_code:{username}')
        if not cached_email or cached_email != email_code:
            return JsonResponse({'code': 400, 'msg': {'email_code': '邮箱验证码错误或已过期'}})
        # 校验通过删除缓存 key
        cache.delete(f'email_code:{username}')

        # 全部通过：写 session（会落到 Redis）
        auth.login(request, user)
        return JsonResponse({'code': 200, 'msg': '登录成功', 'url': '/'})


from app01.utils.dors import is_login_method
# ===== 修改密码 ====
class ChangePwdView(View):
    """修改密码（导航栏模态框 AJAX）。"""
    @is_login_method
    def post(self, request):
        old_pwd = request.POST.get('old_pwd') or ''
        new_pwd = request.POST.get('new_pwd') or ''
        confirm_pwd = request.POST.get('confirm_pwd') or ''

        user = request.user
        if not user.check_password(old_pwd):
            return JsonResponse({'code': 400, 'msg': {'old_pwd': '旧密码错误'}})
        if old_pwd == new_pwd:
            return JsonResponse({'code': 400, 'msg': {'new_pwd': '新密码不能与旧密码相同'}})
        if new_pwd != confirm_pwd:
            return JsonResponse({'code': 400, 'msg': {'confirm_pwd': '两次新密码不一致'}})

        user.set_password(new_pwd)   # 自动哈希加密
        user.save()
        return JsonResponse({'code': 200, 'msg': '密码修改成功，请重新登录', 'url': '/login/'})

# ===== 设置头像 ====
class SetAvatarView(View):
    """修改头像：GET 预览页 / POST AJAX 上传。"""
    @is_login_method
    def get(self, request):
        return render(request, 'set_avatar.html')

    @is_login_method
    def post(self, request):
        avatar = request.FILES.get('avatar')
        if not avatar:
            return JsonResponse({'code': 400, 'msg': {'avatar': '请选择头像图片'}})
        ext = '.' + avatar.name.rsplit('.', 1)[-1].lower() if '.' in avatar.name else ''
        if ext not in ALLOW_AVATAR_EXT:
            return JsonResponse({'code': 400, 'msg': {'avatar': '头像仅支持 jpg/png/gif/bmp'}})

        user = request.user
        user.avatar = avatar
        user.save()
        return JsonResponse({'code': 200, 'msg': '头像修改成功', 'url': '/set_avatar/'})

# 首页文章列表缓存 key
HOME_ARTICLE_CACHE_KEY = 'home_article_list'
# 个人站点侧边栏缓存 key 前缀
SITE_SIDEBAR_KEY_PREFIX = 'site_sidebar'
from django.db.models import Count, Q
from django.utils import timezone # 用于计算近10天热榜时间范围
from datetime import timedelta # 用于计算近10天热榜时间范围
class IndexView(View):
    """
    瓜子BBS首页视图
    请求参数:
        type: 筛选类型
            cat    - 按分类筛选，搭配 id 参数
            my_up  - 我赞过的文章（需登录）
            my_comment - 我评论过的文章（需登录）
            search - 标题搜索，搭配 q 参数
        id: 分类ID(type=cat时生效)
        q: 搜索关键词(type=search时生效)

    缓存规则：
        只有【默认全部文章】走Redis缓存，过期300秒；
        分类/我的/搜索筛选，全部实时查询数据库，不走缓存。

    模板上下文：
        articles    主列表文章数据
        categories  全站分类(带每类有效文章数量)
        latest      右侧最新6篇
        hot         右侧近10天热榜6篇
        filter_type 当前筛选标记 all/cat/my_up/my_comment/search
        filter_id   当前选中分类ID
        filter_name 页面面板头部显示文字
        now_user    当前登录用户request.user
    """

    def get(self, request):
        ftype = request.GET.get('type', '').strip() # 文章类型
        cid = request.GET.get('id', '').strip() # 分类ID
        filter_type, filter_id, filter_name = 'all', None, '' # 默认全部文章

        # 分类筛选
        if ftype == 'cat' and cid.isdigit():
            cat = Category.objects.filter(id=int(cid)).first()
            if cat:
                articles = list(
                    Article.objects.filter(is_delete=False, category=cat)
                    .select_related('blog__user').order_by('-create_time')
                )
                filter_type, filter_id, filter_name = 'cat', cat.id, cat.name
            else:
                articles = []
                filter_type, filter_id, filter_name = 'cat', int(cid), '(分类不存在)'
        elif ftype == 'my_up':
            if request.user.is_authenticated:
                articles = list(
                    Article.objects.filter(
                        is_delete=False,
                        updowns__user=request.user, updowns__is_up=True,
                    ).distinct().select_related('blog__user').order_by('-create_time')
                )
            else:
                articles = []
            filter_type, filter_name = 'my_up', '我赞过'
        elif ftype == 'search':
            q = request.GET.get('q', '').strip()
            if q:
                articles = list(
                    Article.objects.filter(is_delete=False, title__icontains=q)
                    .select_related('blog__user').order_by('-create_time')
                )
                filter_name = '搜索：%s' % q
            else:
                articles = cache.get(HOME_ARTICLE_CACHE_KEY) or None
                if articles is None:
                    articles = list(
                        Article.objects.filter(is_delete=False)
                        .select_related('blog__user').order_by('-create_time')
                    )
                    cache.set(HOME_ARTICLE_CACHE_KEY, articles, 300)
                filter_name = '全部文章'
            filter_type = 'search'
        elif ftype == 'my_comment':
            if request.user.is_authenticated:
                articles = list(
                    Article.objects.filter(
                        is_delete=False,
                        comments__user=request.user, comments__is_delete=False,
                    ).distinct().select_related('blog__user').order_by('-create_time')
                )
            else:
                articles = []
            filter_type, filter_name = 'my_comment', '我评论过'
        else:
            # 默认全部：走缓存（仅默认视图缓存，筛选视图实时查）
            articles = cache.get(HOME_ARTICLE_CACHE_KEY) or None
            if articles is None:
                articles = list(
                    Article.objects.filter(is_delete=False)
                    .select_related('blog__user').order_by('-create_time')
                )
                cache.set(HOME_ARTICLE_CACHE_KEY, articles, 300)

        # 左侧：全站分类 + 各分类文章数
        categories = list(
            # 统计每个分类的有效文章数
            Category.objects.annotate(
                count=Count('articles', filter=Q(articles__is_delete=False))
            ).values('id', 'name', 'count').order_by('-count')
        )

        # 右侧：最新 6 篇 + 近 10 天点赞最多 6 篇
        latest = list(
            Article.objects.filter(is_delete=False)
            .select_related('blog__user').order_by('-create_time')[:4]
        )
        # 近10天热榜6篇
        # 计算近10天前的时间点 timezone.now() Django 带时区的当前时间（推荐用这个，不要用 `datetime.now()`，否则时区会乱），获取服务器当前时刻，带时区信息。
        #  timedelta(days=10) 创建一个10天的时间差 , 现在的时间 **减去 10 天** → 得到**10 天前的那个时间点**。
        ten_days_ago = timezone.now() - timedelta(days=10)
        hot = list(
            Article.objects.filter(is_delete=False, create_time__gte=ten_days_ago)
            .select_related('blog__user').order_by('-up_num')[:5]
        )

        # —— 首页文章分页：每页 10 篇 ——
        # 从查询参数获取当前页码，默认第 1 页
        page_num = request.GET.get('page', '1')
        paginator = Paginator(articles, 10)  # 每页 10 篇文章
        # page_obj 当前页对象，包含该页的文章列表和分页信息
        page_obj = paginator.get_page(page_num)
        # page_range 用于模板渲染分页导航条
        page_range = paginator.page_range

        return render(request, 'index.html',locals())


from django.shortcuts import  redirect

# 退出登录
class LogoutView(View):
    """退出登录：auth.logout 清 session，跳转首页。"""
    @is_login_method
    def get(self, request):
        auth.logout(request)
        return redirect('/')

# ============================================================
# 第三步：首页 / 个人站点 / 文章详情 / 点赞点踩 / 评论
# ============================================================
def _render_404(request,exception):
    """统一 404 页面。"""
    return render(request, 'error404.html', status=404)


class SiteView(View):
    """
       个人站点：/index/<username>/
         按 category/tag/date 三种筛选。
   """
    def get(self, request, username, cid=None, tid=None, year=None, month=None):
        user = User.objects.filter(username=username).first()
        if not user or not user.blog_id:
            return _render_404(request)
        blog = user.blog  # 获取用户博客

        # 获取用户博客的文章列表,并关联用户信息
        articles = Article.objects.filter(
            blog=blog, is_delete=False
        ).select_related('blog__user')

        if cid:
            articles = articles.filter(category_id=cid)
        if tid:
            articles = articles.filter(tags=tid)
        if year and month:
            articles = articles.filter(
                create_time__year=year, create_time__month=month
            )
        articles = articles.order_by('-create_time')

        # 1. 分类 + 文章数（反向关系 Article→Category 的 related_name='articles'）
        #    filter=Q(articles__is_delete=False) 只统计未逻辑删除的文章
        category_list = list(
            Category.objects.filter(blog=blog, is_delete=False)
            .annotate(article_count=Count('articles', filter=Q(articles__is_delete=False)))
            .values('id', 'name', 'article_count')
        )

        # 2. 标签 + 文章数（反向关系 Article→Tag 的 related_name='articles'）
        tag_list = list(
            Tag.objects.filter(blog=blog, is_delete=False)
            .annotate(article_count=Count('articles', filter=Q(articles__is_delete=False)))
            .values('id', 'name', 'article_count')
        )

        # 3. 日期归档：按 年-月 分组统计文章数
        #    用 MySQL 原生 date_format 最稳，避免跨库时间函数语法差异
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT DATE_FORMAT(create_time,'%%Y-%%m') AS ym, COUNT(*) "
                "FROM bbs_article "
                "WHERE blog_id=%s AND is_delete=0 "
                "GROUP BY ym ORDER BY ym DESC",
                [blog.id],
            )
            rows = cursor.fetchall()
        date_list = [{'date': r[0], 'article_count': r[1]} for r in rows]


        return render(request, 'site.html',locals())

class ArticleDetailView(View):
    def get(self, request, username, article_id):
        # 获取用户信息
        user = User.objects.filter(username=username).first()
        if not user or not user.blog_id:
            return _render_404(request)
        # 获取文章详情
        article = Article.objects.filter(
            id=article_id, blog=user.blog, is_delete=False
        ).select_related('blog__user').first()

        if not article:
            return _render_404(request)

        # content_html = article.content

        content_html = markdown.markdown(
            article.content, extensions=['extra', 'fenced_code', 'toc']
        )

        # 作者最新 6 篇（排除当前文章）
        latest = list(
            Article.objects.filter(blog=article.blog, is_delete=False)
            .exclude(id=article.id)
            .select_related('blog__user').order_by('-create_time')[:6]
        )

        # 评论树：根评论 + 每个根评论下的子回复
        # select_related('user') 关联查询评论用户；select_related('reply_to') 关联查询@回复目标用户
        comments = list(Comment.objects.filter(
            article=article, parent__isnull=True, is_delete=False
        ).select_related('user', 'reply_to'))
        for root in comments:
            root.subs = list(Comment.objects.filter(
                parent=root, is_delete=False
            ).select_related('user', 'reply_to'))

        return render(request, 'article_detail.html',locals())


from django.db.models import F

class CommentView(View):
    """
       发表评论（需登录）：
         - 支持根评论（parent_id 为空）与子回复（parent_id 非空）
         - 评论成功后：article.comment_num +1；删除首页缓存
         - 提交后前端刷新页面以展示新评论（评论展示由服务端渲染）
    """
    @is_login_method
    def post(self, request):
        article_id = request.POST.get('article_id')
        content = (request.POST.get('content') or '').strip()
        parent_id = request.POST.get('parent_id') or ''
        # 回复目标用户名：前端点击"回复"时传入被回复用户的 username
        reply_user = request.POST.get("reply_user", "")

        article = Article.objects.filter(id=article_id, is_delete=False).first() # 获取文章详情
        if not article:
            return JsonResponse({'code': 400, 'msg': '文章不存在'})
        if not content:
            return JsonResponse({'code': 400, 'msg': '评论内容不能为空'})

        # 父评论校验：必须存在且属于同一篇文章
        parent = None
        if parent_id:
            parent = Comment.objects.filter(
                id=parent_id, article=article, is_delete=False
            ).first()
            if not parent:
                return JsonResponse({'code': 400, 'msg': '父评论不存在'})

        # 回复目标用户校验：通过 username 查找被回复的用户对象
        # 如果是根评论（无 parent），reply_to 为 None；子回复时根据 reply_user 查找
        reply_to_user = None
        if reply_user:
            reply_to_user = User.objects.filter(username=reply_user).first()

        # @功能：自己回复自己时不添加 @前缀；回复别人时在内容前自动加上 "@用户名 "
        # reply_to_user 存在且不是当前登录用户时才加 @前缀
        if reply_to_user and reply_to_user.id != request.user.id:
            # 在评论内容前拼接 "@用户名 "，前端渲染时用特殊颜色标记
            content = '@{} {}'.format(reply_to_user.username, content)

        # 创建评论，保存 reply_to 关系（@功能核心）
        Comment.objects.create(
            user=request.user, article=article,
            content=content, parent=parent,
            reply_to=reply_to_user if (reply_to_user and reply_to_user.id != request.user.id) else None,
        )

        # 评论计数 +1（用 F 表达式避免并发覆盖）
        Article.objects.filter(id=article.id).update(comment_num=F('comment_num') + 1)

        # 写操作完成：删除首页缓存
        cache.delete(HOME_ARTICLE_CACHE_KEY)

        return JsonResponse({'code': 200, 'msg': '评论成功'})



class UpDownView(View):
    @is_login_method
    def post(self, request):
        article_id = request.POST.get('article_id')
        # is_up 前端传字符串 'true'/'false'
        is_up = request.POST.get('is_up') == 'true'

        article = Article.objects.filter(id=article_id, is_delete=False).first()
        if not article:
            return JsonResponse({'code': 400, 'msg': '文章不存在'})

        # 禁止给自己文章点赞点踩
        # 说明：User↔Blog 的外键建在 User 上（related_name='user'），
        #       所以站点主人是 article.blog.user，而不是 blog.user_id。
        if article.blog.user.id == request.user.id:
            return JsonResponse({'code': 400, 'msg': '不能对自己的文章点赞点踩'})

        # 查当前用户对该文章的既有态度
        existing = UpAndDown.objects.filter(
            user=request.user, article=article
        ).first()

        if not existing:
            # 没有记录：新建态度
            UpAndDown.objects.create(user=request.user, article=article, is_up=is_up)
            article.up_num += 1 if is_up else 0
            article.down_num += 0 if is_up else 1

        elif existing.is_up == is_up:
            # 重复点击，取消态度
            existing.delete()
            article.up_num -= 1 if is_up else 0
            article.down_num -= 0 if is_up else 1

        else:
            # 切换赞↔踩
            existing.is_up = is_up
            existing.save()
            if is_up:
                article.up_num += 1
                article.down_num -= 1
            else:
                article.down_num += 1
                article.up_num -= 1

        article.save()
        cache.delete(HOME_ARTICLE_CACHE_KEY)

        return JsonResponse({
            'code': 200, 'msg': '操作成功',
            'up_num': article.up_num, 'down_num': article.down_num,
        })




# ====================================================================
# 第四步：后台文章管理 —— 列表 / 新增 / 编辑（Markdown 增强）
# ====================================================================
# 主页：文章列表
class BackendView(View):
    """
    后台首页：展示当前登录用户站点的全部文章（含逻辑删除的也展示，方便管理）。
    提供新增/编辑入口；删除在第五步实现（含缓存清理）。
    """

    @is_login_method
    def get(self, request):
        blog = request.user.blog
        # 文章列表（含已逻辑删除，便于后台看到全部）
        articles = Article.objects.filter(blog=blog).order_by('-create_time')
        return render(request, 'backend/backend.html', {
            'articles': articles, 'blog': blog,
        })

# 清空缓存
def _clear_article_caches(blog_id):
    """发布/编辑文章后清除首页与该站点侧边栏缓存"""
    cache.delete(HOME_ARTICLE_CACHE_KEY)
    cache.delete(f'{SITE_SIDEBAR_KEY_PREFIX}:{blog_id}')

# 新增文章
class AddArticleView(View):
    @is_login_method
    def get(self, request):
        blog = request.user.blog
        # 分类、标签用于下拉/多选
        categories = Category.objects.filter(blog=blog)
        tags = Tag.objects.filter(blog=blog)
        return render(request, 'backend/add_article.html', {
            'categories': categories, 'tags': tags,
        })
    def post(self, request):
        blog = request.user.blog
        title = (request.POST.get('title') or '').strip()
        content = request.POST.get('content') or ''
        category_id = request.POST.get('category') or ''
        tag_ids = request.POST.getlist('tags')
        md_file = request.FILES.get('md_file')
        # 封面图片文件：可选上传，不上传时为 None，前端回退用作者头像
        cover_file = request.FILES.get('cover')

        #读取文件内容
        if md_file:
            content = md_file.read().decode('utf-8')

        # 基本校验
        if not title:
            return JsonResponse({'code': 400, 'msg': '标题不能为空'})
        if not content or not content.strip():
            return JsonResponse({'code': 400, 'msg': '内容不能为空'})

        # 创建文章（content 存原始 markdown 文本）
        # 封面：如果用户上传了封面图片就传入，否则用模型默认值（空字符串）
        article = Article.objects.create(
            blog=blog, title=title, content=content,
            category_id=category_id or None,
            cover=cover_file if cover_file else '',
        )

        # 多对多标签
        if tag_ids:
            article.tags.set(tag_ids)

            # 清缓存：首页 + 该站点侧边栏
        _clear_article_caches(blog.id)
        return JsonResponse({'code': 200, 'msg': '发布成功', 'url': '/backend/'})

# 文章编辑
class EditArticleView(View):
    @is_login_method
    def get(self, request, article_id):
        # 获取站点
        blog = request.user.blog
        article = Article.objects.filter(id=article_id, blog=blog).first() # 根据站点查询文章
        if not article:
            return _render_404(request)
        categories = Category.objects.filter(blog=blog) # 获取当前站点的所有分类
        tags = Tag.objects.filter(blog=blog) # 获取当前站点的所有标签
        # 当前已选标签 id 集合，用于多选回显
        selected_tag_ids = list(article.tags.values_list('id', flat=True))

        return render(request, 'backend/edit_article.html', {
            'article': article, 'categories': categories, 'tags': tags,
            'selected_tag_ids': selected_tag_ids,
        })

    @is_login_method
    def post(self, request, article_id):
        blog = request.user.blog
        # 限定作者本人文章
        article = Article.objects.filter(id=article_id, blog=blog).first()
        if not article:
            return JsonResponse({'code': 400, 'msg': '文章不存在或无权操作'})

        title = (request.POST.get('title') or '').strip()
        content = request.POST.get('content') or ''
        category_id = request.POST.get('category') or ''
        tag_ids = request.POST.getlist('tags')
        md_file = request.FILES.get('md_file')
        # 封面图片文件：可选上传；上传则替换旧封面，不上传则保留原封面
        cover_file = request.FILES.get('cover')

        # 读取文件内容
        if md_file:
            content = md_file.read().decode('utf-8')

        if not title:
            return JsonResponse({'code': 400, 'msg': '标题不能为空'})
        if not content or not content.strip():
            return JsonResponse({'code': 400, 'msg': '内容不能为空'})

        article.title = title
        article.content = content
        article.category_id = category_id or None
        # 封面：仅当用户上传了新封面时才覆盖，不上传则保留旧值
        if cover_file:
            article.cover = cover_file
        # 编辑保存时自动恢复删除状态：如果文章之前被逻辑删除，编辑后恢复为正常
        article.is_delete = False
        article.save()
        # 标签：先清后设
        article.tags.set(tag_ids)

        _clear_article_caches(blog.id)
        return JsonResponse({'code': 200, 'msg': '修改成功', 'url': '/backend/'})

# ==================== 16. 删除文章 DelArticleView ====================
class DelArticleView(View):
    """
    删除文章（两阶段删除）：
      - 第一次删除：逻辑删除 is_delete=True，后台仍可见，可编辑恢复
      - 第二次删除（文章已是已删除状态）：永久物理删除，不可恢复
      - 仅作者本人可删（blog=本人站点）
      - 删除后清除首页 + 侧边栏缓存
    """

    @is_login_method
    def post(self, request):
        blog = request.user.blog
        article_id = request.POST.get('id')
        article = Article.objects.filter(id=article_id, blog=blog).first()
        if not article:
            return JsonResponse({'code': 400, 'msg': '文章不存在或无权操作'})

        if article.is_delete:
            # 文章已经是逻辑删除状态 -> 永久物理删除（从数据库中彻底移除）
            article.delete()
            _clear_article_caches(blog.id)
            return JsonResponse({'code': 200, 'msg': '文章已永久删除'})
        else:
            # 文章正常状态 -> 第一次删除：逻辑删除
            article.is_delete = True
            article.save()
            _clear_article_caches(blog.id)
            return JsonResponse({'code': 200, 'msg': '删除成功（可编辑恢复或再次删除永久移除）'})



# ==================== 17. 分类管理 CategoryView ====================
class CategoryView(View):
    """
    分类管理：
      GET  -> 渲染分类列表页
      POST -> 按 action 处理 add / edit / del（全部 AJAX）
    增删改后清除站点侧边栏缓存（分类统计变化）。
    """

    @is_login_method
    def get(self, request):
        blog = request.user.blog
        # 后台展示含逻辑删除？这里只展示未删除的，便于管理
        categories = Category.objects.filter(blog=blog, is_delete=False).order_by('-id')
        return render(request, 'backend/category.html', {'categories': categories})

    @is_login_method
    def post(self, request):
        blog = request.user.blog
        action = request.POST.get('action')
        name = (request.POST.get('name') or '').strip()
        cid = request.POST.get('id')

        if action == 'add':
            if not name:
                return JsonResponse({'code': 400, 'msg': '分类名不能为空'})
            # 同站点下分类名唯一校验
            if Category.objects.filter(blog=blog, name=name, is_delete=False).exists():
                return JsonResponse({'code': 400, 'msg': '该分类名已存在'})
            Category.objects.create(blog=blog, name=name)
            _clear_article_caches(blog.id)
            return JsonResponse({'code': 200, 'msg': '添加成功'})

        if action == 'edit':
            cat = Category.objects.filter(id=cid, blog=blog, is_delete=False).first()
            if not cat:
                return JsonResponse({'code': 400, 'msg': '分类不存在'})
            if not name:
                return JsonResponse({'code': 400, 'msg': '分类名不能为空'})
            cat.name = name
            cat.save()
            _clear_article_caches(blog.id)
            return JsonResponse({'code': 200, 'msg': '修改成功'})

        if action == 'del':
            cat = Category.objects.filter(id=cid, blog=blog, is_delete=False).first()
            if not cat:
                return JsonResponse({'code': 400, 'msg': '分类不存在'})
            # 逻辑删除（文章 category 外键 on_delete=SET_NULL，但逻辑删除不触发级联）
            cat.is_delete = True
            cat.save()
            _clear_article_caches(blog.id)
            return JsonResponse({'code': 200, 'msg': '删除成功'})

        return JsonResponse({'code': 400, 'msg': '未知操作'})


# ==================== 18. 标签管理 TagView ====================
class TagView(View):
    """
    标签管理：与分类管理结构完全一致。
      GET  -> 标签列表页
      POST -> action: add / edit / del
    """

    @is_login_method
    def get(self, request):
        blog = request.user.blog
        tags = Tag.objects.filter(blog=blog, is_delete=False).order_by('-id')
        return render(request, 'backend/tag.html', {'tags': tags})

    @is_login_method
    def post(self, request):
        blog = request.user.blog
        action = request.POST.get('action')
        name = (request.POST.get('name') or '').strip()
        tid = request.POST.get('id')

        if action == 'add':
            if not name:
                return JsonResponse({'code': 400, 'msg': '标签名不能为空'})
            if Tag.objects.filter(blog=blog, name=name, is_delete=False).exists():
                return JsonResponse({'code': 400, 'msg': '该标签名已存在'})
            Tag.objects.create(blog=blog, name=name)
            _clear_article_caches(blog.id)
            return JsonResponse({'code': 200, 'msg': '添加成功'})

        if action == 'edit':
            tag = Tag.objects.filter(id=tid, blog=blog, is_delete=False).first()
            if not tag:
                return JsonResponse({'code': 400, 'msg': '标签不存在'})
            if not name:
                return JsonResponse({'code': 400, 'msg': '标签名不能为空'})
            tag.name = name
            tag.save()
            _clear_article_caches(blog.id)
            return JsonResponse({'code': 200, 'msg': '修改成功'})

        if action == 'del':
            tag = Tag.objects.filter(id=tid, blog=blog, is_delete=False).first()
            if not tag:
                return JsonResponse({'code': 400, 'msg': '标签不存在'})
            tag.is_delete = True
            tag.save()
            _clear_article_caches(blog.id)
            return JsonResponse({'code': 200, 'msg': '删除成功'})

        return JsonResponse({'code': 400, 'msg': '未知操作'})


class CommentManageView(View):
    @is_login_method
    def get(self, request):
        # 只查自己发的、未逻辑删除的评论，按时间倒序
        comments = Comment.objects.filter(
            user=request.user, is_delete=False
        ).select_related('article').order_by('-create_time')
        return render(request, 'backend/comment.html', {'comments': comments})

class CommentDelView(View):
    """
    删除评论（逻辑删除）：
      - 仅能删自己发的评论（user=request.user 权限隔离）
      - article.comment_num -1（F 表达式防并发覆盖）
      - 清除首页缓存（首页展示评论数）
    """

    @is_login_method
    def post(self, request):
        cid = request.POST.get('id')
        comment = Comment.objects.filter(
            id=cid, user=request.user, is_delete=False
        ).first()
        if not comment:
            return JsonResponse({'code': 400, 'msg': '评论不存在或无权操作'})
        comment.is_delete = True
        comment.save()
        # 关联文章评论数 -1
        Article.objects.filter(id=comment.article_id).update(
            comment_num=F('comment_num') - 1
        )
        cache.delete(HOME_ARTICLE_CACHE_KEY)
        return JsonResponse({'code': 200, 'msg': '删除成功'})


import os
from django.conf import settings
# ==================== 20. 个人信息 InfoView ====================
class InfoView(View):
    """
    个人信息编辑：
      GET  -> 渲染个人信息页（回显用户名/年龄/性别/手机号 + 站点CSS）
      POST -> 修改用户名/年龄/性别/手机号；可选上传站点自定义 CSS 主题文件
    CSS 上传：仅 .css 后缀，保存到 media/css/user_{id}.css，
              把 /media/css/user_{id}.css 写入 blog.site_theme。
    """

    @is_login_method
    def get(self, request):
        return render(request, 'backend/info.html', {
            'user': request.user, 'blog': request.user.blog,
        })

    @is_login_method
    def post(self, request):
        user = request.user
        blog = user.blog
        username = (request.POST.get('username') or '').strip()
        age = request.POST.get('age') or '0'
        gender = request.POST.get('gender') or '3'
        phone = (request.POST.get('phone') or '').strip()
        # 个性签名：允许为空，为空时保存默认值
        signature = (request.POST.get('signature') or '').strip() or '用户未设置签名'
        css_file = request.FILES.get('site_theme')

        # 用户名校验：非空 + 不重复（排除自己）
        if not username:
            return JsonResponse({'code': 400, 'msg': '用户名不能为空'})
        if User.objects.filter(username=username).exclude(pk=user.id).exists():
            return JsonResponse({'code': 400, 'msg': '用户名已被占用'})

        user.username = username
        # 数值字段容错转换
        try:
            user.age = int(age)
        except ValueError:
            user.age = 0
        try:
            user.gender = int(gender)
        except ValueError:
            user.gender = 3
        user.phone = phone
        user.signature = signature
        user.save()

        # 站点自定义 CSS 主题上传
        if css_file:
            # 后缀校验（安全：仅 .css，禁止脚本）
            if not css_file.name.lower().endswith('.css'):
                return JsonResponse({'code': 400, 'msg': '主题文件仅支持 .css'})
            folder = os.path.join(settings.MEDIA_ROOT, 'css')
            os.makedirs(folder, exist_ok=True)
            # 固定命名 user_{id}.css，避免文件堆积
            fname = f'user_{user.id}.css'
            path = os.path.join(folder, fname)
            with open(path, 'wb') as f:
                for chunk in css_file.chunks():
                    f.write(chunk)
            # 把可访问地址写入 blog.site_theme（CharField 存路径字符串）
            blog.site_theme = settings.MEDIA_URL + 'css/' + fname
            blog.save()
            # 站点页用到 site_theme，清侧边栏缓存
            _clear_article_caches(blog.id)

        return JsonResponse({'code': 200, 'msg': '保存成功', 'url': '/backend/info/'})


