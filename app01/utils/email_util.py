"""
app01/utils/email_util.py  QQ 邮箱发送工具
------------------------------------------------------
  - generate_email_code(length=6) 生成 6 位纯数字验证码
  - send_email_code(to_email, code) 发送验证码邮件到指定邮箱
依赖：settings.EMAIL_HOST_USER / EMAIL_HOST_PASSWORD 等配置。
"""
import random
import string
# 导入发送邮件的函数
from django.core.mail import send_mail
# 配置文件中的邮箱相关配置
from django.conf import settings

def generate_email_code(length=6):
    """生成 6 位数字字符串，例如 "384721"。"""
    return ''.join(random.choices(string.digits, k=length))

# 发送验证码邮件到指定邮箱 to_email ，验证码为 code
def send_email_code(to_email, code):
    """
    返回：True 成功 / False 失败
    关键：from_email 必须显式传 settings.EMAIL_HOST_USER，
         否则 QQ 邮箱返回 501 拒绝。
    """
    # 邮件主题
    subject = '【BBS博客系统】登录邮箱验证码'
    # 邮件内容
    message = (
        f'您正在登录 BBS 博客系统，本次验证码为：{code}\n'
        f'验证码 5 分钟内有效，请勿向他人泄露。\n'
        f'如非本人操作请忽略本邮件。'
    )
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.EMAIL_HOST_USER,   # 必须传授权账号本身
            recipient_list=[to_email],
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f'[email_util] 发送邮件失败: {e}')
        return False