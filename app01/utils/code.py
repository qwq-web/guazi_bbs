"""
app01/utils/code.py  图形验证码生成工具
------------------------------------------------------
  - Pillow 生成一张 4 位验证码图片（带干扰线/噪点）
  - 返回 (验证码字符串, 图片二进制 BytesIO)
  - 调用方：把验证码存 Redis(key=code:{随机串}, 60s)，图片以 HTTPResponse 返回
"""
import string
import random
import io
from PIL import Image, ImageDraw, ImageFont

# 随机四位数验证码
def random_code(length=4):
    """生成 4 位随机验证码，排除 0/O/1/I 易混字符。"""
    chars = ''.join(set(string.ascii_letters + string.digits) - {'0', 'O', '1', 'I', 'l'})
    return ''.join(random.choices(chars, k=length))

# 随机 RGB 三元组
def _random_rgb():
    """随机 RGB 三元组。"""
    return tuple(random.randint(0, 255) for _ in range(3))

def get_code_image():
    """
    返回：(验证码文本, PNG 图片 BytesIO)
    """
    # 创建验证码尺寸
    width, height = 130,34
    # 创建验证码图片,rgb模式,宽度高度,背景颜色
    img = Image.new('RGB', (width, height), 'white')
    # 绘制图片
    draw = ImageDraw.Draw(img)

    # 设置字体
    try:
        font = ImageFont.truetype('arial.ttf', 24)
        # static/fonts/guazi.ttf
    except OSError:
        font = ImageFont.load_default()

    code = random_code(4)
    print('图形验证码:', code)  # 学习阶段方便调试

    # 写 4 个字符（位置抖动、颜色随机）
    for i, ch in enumerate(code):
        #字符位置
        x = 8 + i * 28
        y = random.randint(0, 6)
        draw.text((x, y), ch, font=font, fill=_random_rgb())

    # 80 个干扰点
    for _ in range(80):
        # 随机点,x,y坐标
        draw.point(
            (random.randint(0, width - 1), random.randint(0, height - 1)),
            fill=_random_rgb()
        )
    # 2 条干扰线
    for _ in range(2):
        # 随机线,x,y 起点坐标, 结点坐标
        start = (random.randint(0, width), random.randint(0, height))
        end = (random.randint(0, width), random.randint(0, height))
        draw.line([start, end], fill=_random_rgb(), width=1)

    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    return code, buf