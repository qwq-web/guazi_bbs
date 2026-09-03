"""
app01/forms/user_forms.py  注册表单
------------------------------------------------------
  字段：username、password、confirm_password、email、site_title
  局部钩子：clean_username（敏感词+重复）、clean_site_title（重复）
  全局钩子：clean（两次密码一致）

错误信息格式：self.add_error('字段名', '错误内容')
前端拿到 errors 字典，按字段名定位到 span 显示红色文字。
"""
from django import forms
from app01.models import Blog, User

# 用户名敏感词黑名单（学习示例）
SENSITIVE_WORDS = ['admin', '超级管理员', 'fuck', 'root', '操', '傻逼']
class MyRegisterForm(forms.Form):
    # 用户名 （必填，3-16 位，不能为空）
    username = forms.CharField(
        max_length=16, min_length=3,
        error_messages={
            'required': '用户名不能为空',
            'min_length': '用户名至少 3 位',
            'max_length': '用户名最多 16 位',
        }
    )
    # 密码 （必填，6-32 位，不能为空）
    password = forms.CharField(
        max_length=32, min_length=6,
        widget=forms.PasswordInput,
        error_messages={
            'required': '密码不能为空',
            'min_length': '密码至少 6 位',
            'max_length': '密码最多 32 位',
        }
    )
    # 确认密码 （必填，与密码一致，不能为空）
    confirm_password = forms.CharField(
        max_length=32,
        widget=forms.PasswordInput,
        error_messages={'required': '请再次输入密码'}
    )
    email = forms.EmailField(
        error_messages={'required': '邮箱不能为空', 'invalid': '邮箱格式不正确'}
    )
    # 站点标题 （必填，最大64 位，不能为空）
    site_title = forms.CharField(
        max_length=64,
        error_messages={'required': '站点标题不能为空', 'max_length': '站点标题过长'}
    )

    # 局部钩子,校验用户名
    def clean_username(self):
        """敏感词校验 + 数据库存在性校验。"""
        username = self.cleaned_data.get('username', '').strip()
        lower = username.lower()
        for word in SENSITIVE_WORDS:
            if word in lower:
                raise forms.ValidationError('该用户名含敏感词，请更换')
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError('该用户名已被注册')
        return username  # 必须返回字段值

    # ---------- 局部钩子：站点标题 ----------
    def clean_site_title(self):
        """站点标题全局唯一校验。"""
        site_title = self.cleaned_data.get('site_title', '').strip()
        if Blog.objects.filter(site_title=site_title).exists():
            raise forms.ValidationError('该站点标题已存在，请更换')
        return site_title

        # ---------- 全局钩子：两次密码一致 ----------
    def clean(self):
        """
        全局校验。校验失败时用 self.add_error 挂到具体字段上，
        方便前端按字段定位展示；不要直接 raise。
        """
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm = cleaned_data.get('confirm_password')
        if password and confirm and password != confirm:
            self.add_error('confirm_password', '两次输入的密码不一致')
        return cleaned_data

