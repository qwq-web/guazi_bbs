
from django.utils.html import strip_tags
from django.utils.safestring import mark_safe
import markdown
from django import template
import re
# 注册器：自定义标签/过滤器必须挂到它上面
register = template.Library()


# ==================== plain_text：markdown 转纯文本（用于文章摘要）====================
@register.filter(name='plain_text')
def plain_text(value):
    """把 markdown 文本转成纯文本（剥掉 md 语法和 HTML 标签），用于列表摘要。

    入参：value - markdown 原文
    返回：纯文本字符串（已折叠多余空白）
    说明：先 markdown 转 HTML，再 strip_tags 去标签，得到干净文本，
          避免列表摘要里出现 #、```、** 等 md 语法符号。
    """
    if not value:
        return ''
    html = markdown.markdown(str(value), extensions=['extra', 'fenced_code'])
    text = strip_tags(html)                       # 去掉所有 HTML 标签
    text = re.sub(r'\s+', ' ', text).strip()      # 折叠多余空白/换行
    return text


# ==================== md_safe：轻量 XSS 净化过滤器 ====================
# 危险成对标签：<script>...</script>、<iframe>、<style>、<object>、<embed>、<form>
_SCRIPT_TAG = re.compile(r'<\s*(script|style|iframe|object|embed|form)\b[\s\S]*?</\1\s*>', re.I)
# 危险自闭合/孤立标签：<meta http-equiv=refresh>、<link>、<base>、<iframe/>
_SELF_TAG = re.compile(r'<\s*/?(meta|link|base|iframe|object|embed)\b[^>]*/?>', re.I)
# onXxx 事件属性：onclick、onerror、onload ...
_ON_ATTR = re.compile(r'\s+on\w+\s*=\s*(?:"[^"]*"|\'[^\']*\'|[^\s>]+)', re.I)
# 危险协议：href/src="javascript:..."、"vbscript:..."、"data:..."
_JS_PROTO = re.compile(r'(href|src)\s*=\s*("|\')\s*(?:javascript|vbscript|data):', re.I)


@register.filter(name='md_safe')
def md_safe(value):
    """markdown→HTML 后做轻量净化，再 mark_safe 渲染。

    入参：value - HTML 字符串
    返回：净化后的 SafeString（模板中 {{ xxx|md_safe }} 直接渲染）
    """
    if not value:
        return mark_safe('')
    html = str(value)
    html = _SCRIPT_TAG.sub('', html)        # 剥离 script/iframe 等成对标签
    html = _SELF_TAG.sub('', html)          # 剥离 meta/link 等自闭合标签
    html = _ON_ATTR.sub('', html)           # 剥离 onXxx 事件属性
    html = _JS_PROTO.sub(r'\1=\2', html)    # 把 javascript:/vbscript:/data: 协议改写为空
    return mark_safe(html)
