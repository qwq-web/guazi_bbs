"""
app01/models.py
================================================
7 张业务表 + 1 个抽象基类：
  BaseModel  抽象基类（不建表），统一提供创建/更新时间、逻辑删除
  User       用户表（继承 AbstractUser + BaseModel），一对一 Blog
  Blog       个人站点表
  Tag        标签表（一对多 Blog）
  Category   分类表（一对多 Blog）
  Article    文章表（外键 Blog/Category，多对多 Tag）
  UpAndDown  点赞点踩表
  Comment    评论表（自关联 parent）
"""
# AbstractUser (用户表)
from django.contrib.auth.models import AbstractUser
from django.db import models

# ==================== 抽象基类 BaseModel ====================
class BaseModel(models.Model):
    """
    统一公共抽象基类
    abstract=True 设置为抽象模型，不会在数据库中生成对应的物理数据表
    所有业务模型继承该类，自动复用以下三个通用字段
    """
    # 创建时间：对象第一次入库时自动记录当前时间，后续更新不会自动修改
    create_time = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)
    # 更新时间：对象每次执行save保存时，都会自动刷新为当前时间
    update_time = models.DateTimeField(verbose_name='更新时间', auto_now=True)
    # 逻辑删除标记：False代表正常数据，True代表逻辑删除；不做物理删除数据库记录
    is_delete = models.BooleanField(verbose_name='是否逻辑删除', default=False)

    class Meta:
        # 抽象模型标识：设置True，Django迁移时不会为此模型建表
        abstract = True


# ==================== 1. 个人站点表 Blog ====================
class Blog(BaseModel):
    """
    个人站点模型
    每个用户注册成功后自动创建一个站点对象，和User模型做一对一关联
    保存博客站点基础信息：站点名称、页面标题、自定义主题CSS路径
    """
    # 站点名称，一般直接复用注册用户名，最大长度64字符
    site_name = models.CharField(verbose_name='站点名称', max_length=64)
    # 站点标题，浏览器标签页展示的标题，用户注册时填写
    site_title = models.CharField(verbose_name='站点标题', max_length=64)
    # 自定义主题 CSS 文件路径
    # 存储media下css资源访问字符串示例：/media/css/user_1.css
    # default='' 默认无主题；blank=True表单允许该字段为空，非必填
    site_theme = models.CharField(
        verbose_name='站点主题CSS', max_length=128, default='', blank=True
    )

    class Meta:
        verbose_name = '个人站点表'          # Django admin后台单数显示名称
        verbose_name_plural = verbose_name  # admin后台复数名称，和单数保持一致，避免自动加"s"
        db_table = 'bbs_blog'               # 指定数据库实际表名，不使用Django自动生成的app01_blog

    def __str__(self):
        """
        控制台打印、Admin后台展示对象时返回站点名称
        """
        return self.site_name

# ==================== 2. 用户表 User ====================
class User(AbstractUser, BaseModel):
    """继承 AbstractUser 拿到 username/password/email；扩展年龄/性别/头像/站点。"""
    GENDER_CHOICES = (
        (1, '男'),
        (2, '女'),
        (3, '保密'),
    )
    age = models.IntegerField(verbose_name='年龄', default=0, blank=True)
    gender = models.SmallIntegerField(
        verbose_name='性别', choices=GENDER_CHOICES, default=3
    )
    phone = models.CharField(verbose_name='手机号', max_length=11, default='', blank=True)
    # 头像：上传到 media/avatar 下
    avatar = models.ImageField(
        verbose_name='头像', upload_to='avatar', default='avatar/default.png'
    )
    # 一对一外键：User ↔ Blog，一个用户对应一个个人站点
    # to='Blog' 关联Blog模型；on_delete=models.CASCADE：删除用户则级联删除对应的个人站点
    # null=True数据库允许存null；blank=True表单可以不填
    # related_name='user'：反向查询，通过blog对象.blog.user即可拿到对应的User用户实例
    blog = models.OneToOneField(
        to='Blog', verbose_name='个人站点', on_delete=models.CASCADE,
        null=True, blank=True, related_name='user'
    )

    class Meta:
        verbose_name = '用户表'
        verbose_name_plural = verbose_name
        db_table = 'bbs_user'

    def __str__(self):
        return self.username


# ==================== 3. 标签表 Tag ====================
class Tag(BaseModel):
    """
        标签模型
        标签归属于某一个个人站点，Blog与Tag是一对多关系：一个站点可以拥有多个标签，一个标签只属于一个站点
        用于给文章打标签，做文章过滤筛选
        """
    name = models.CharField(verbose_name='标签名', max_length=32)
    blog = models.ForeignKey(
        to='Blog', verbose_name='所属站点', on_delete=models.CASCADE,
        related_name='tags'
    )

    class Meta:
        verbose_name = '标签表'
        verbose_name_plural = verbose_name
        db_table = 'bbs_tag'

    def __str__(self):
        return self.name

# ==================== 4. 分类表 Category ====================
class Category(BaseModel):
    """属于某个站点（一对多）。"""
    name = models.CharField(verbose_name='分类名', max_length=32)
    blog = models.ForeignKey(
        to='Blog', verbose_name='所属站点', on_delete=models.CASCADE,
        related_name='categories'
    )

    class Meta:
        verbose_name = '分类表'
        verbose_name_plural = verbose_name
        db_table = 'bbs_category'

    def __str__(self):
        return self.name


# ==================== 5. 文章表 Article ====================
class Article(BaseModel):
    """content 存原始 Markdown 文本；正文渲染由后端 markdown 库转 HTML。"""
    title = models.CharField(verbose_name='文章标题', max_length=128)
    content = models.TextField(verbose_name='文章内容(Markdown)')
    # 冗余计数字段：点赞数量，直接读取字段值展示，避免业务频繁执行count()统计，提升查询性能
    up_num = models.IntegerField(verbose_name='点赞数', default=0)
    down_num = models.IntegerField(verbose_name='点踩数', default=0)
    comment_num = models.IntegerField(verbose_name='评论数', default=0)

    blog = models.ForeignKey(
        to='Blog', verbose_name='所属站点', on_delete=models.CASCADE,
        related_name='articles'
    )
    category = models.ForeignKey(
        to='Category', verbose_name='所属分类', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='articles'
    )
    # 多对多：Article ↔ Tag
    tags = models.ManyToManyField(
        to='Tag', verbose_name='标签', blank=True, related_name='articles'
    )

    class Meta:
        verbose_name = '文章表'
        verbose_name_plural = verbose_name
        db_table = 'bbs_article'
        ordering = ['-create_time']   # 默认按创建时间倒序

    def __str__(self):
        return self.title

# ==================== 6. 点赞点踩表 UpAndDown ====================
class UpAndDown(BaseModel):
    """
    点赞点踩记录表
    记录用户对文章的点赞或者点踩行为；
    业务约束：一个用户对同一篇文章只能产生一条态度记录，通过联合唯一约束实现，不能同时存赞和踩两条数据。
    """
    # 外键：User ↔ Article ，一个用户可以点赞或点踩多篇文章，一个文章也可以被多个用户点赞或点踩
    user = models.ForeignKey(
        to='User', verbose_name='操作用户', on_delete=models.CASCADE,
        related_name='updowns'
    )
    # 外键：Article ↔ UpAndDown ，一个文章可以被多个用户点赞或点踩
    article = models.ForeignKey(
        to='Article', verbose_name='被操作文章', on_delete=models.CASCADE,
        related_name='updowns'
    )
    # 点赞点踩字段：是否点赞
    is_up = models.BooleanField(verbose_name='是否点赞')   # True=赞 / False=踩

    class Meta:
        verbose_name = '点赞点踩表'
        verbose_name_plural = verbose_name
        db_table = 'bbs_upanddown'
        unique_together = [('user', 'article')]   # 联合唯一

    def __str__(self):
        flag = '赞' if self.is_up else '踩'
        return f'{self.user.username} - {self.article.title} - {flag}'


# ==================== 7. 评论表 Comment ====================
class Comment(BaseModel):
    """自关联 parent：None 为根评论；非 None 为回复某条评论。"""
    # 外键：User ↔ Comment ，一个用户可以评论多篇文章，一个文章也可以被多个用户评论
    user = models.ForeignKey(
        to='User', verbose_name='评论用户', on_delete=models.CASCADE,
        related_name='comments'
    )
    # 外键：Article ↔ Comment ，一个文章可以被多个用户评论
    article = models.ForeignKey(
        to='Article', verbose_name='被评论文章', on_delete=models.CASCADE,
        related_name='comments'
    )
    content = models.TextField(verbose_name='评论内容')
    # 外键：Comment ↔ Comment ，一个评论可以有多个子评论
    # related_name='children' 反向查询：comment_obj.children 获取该评论的所有子回复
    parent = models.ForeignKey(
        to='self', verbose_name='父评论', on_delete=models.CASCADE,
        null=True, blank=True, related_name='children'
    )

    class Meta:
        verbose_name = '评论表'
        verbose_name_plural = verbose_name
        db_table = 'bbs_comment'
        ordering = ['create_time']   # 评论按时间正序

    def __str__(self):
        return f'{self.user.username} 评论 {self.article.title}'
