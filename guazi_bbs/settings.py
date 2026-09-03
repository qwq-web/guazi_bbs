"""
bbs 项目主配置文件 settings.py
----------------------------------------------------------------
本配置基于 Django 5.2.17，涵盖：
  - MySQL 数据库（guazi_bbs）
  - Redis 缓存（django-redis 作为唯一缓存后端，session 也存 Redis）
  - QQ 邮箱 SMTP 发送
  - 用户上传 media 资源 / 静态文件 static
  - 自定义用户模型 app01.User
"""

from pathlib import Path

# 项目根目录：settings.py 所在目录的上一级
# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/6.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
# ============== 1. 安全密钥与调试开关 (默认)==============
SECRET_KEY = 'django-insecure-uj!mmjf@^jl&i1^$qw1e$34iued0m33uzj7!yj@dj7tp4y3g9e'
# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True
ALLOWED_HOSTS = ['*']


# Application definition
# ============== 2. 已安装应用 INSTALLED_APPS (新增 redis 和 app01) ==============
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_redis',           # 对接 Redis 缓存
    'app01.apps.App01Config', # 自定义模块
]

# ============== 3. 中间件 MIDDLEWARE (默认)==============
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    "app01.middleware.ip_form.VisitLogMiddleware",
]

# ============== 4. 根 URL 配置 ROOT_URLCONF (默认) ==============
ROOT_URLCONF = 'guazi_bbs.urls'

# ============== 5. 模板配置 TEMPLATES (默认) ==============
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates']
        ,
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# ============== 6. WSGI 应用 WSGI_APPLICATION (默认) ==============
WSGI_APPLICATION = 'guazi_bbs.wsgi.application'


# Database
# https://docs.djangoproject.com/en/6.1/ref/settings/#databases
# ============== 7. 数据库配置 DATABASES (修改为 MySQL)==============
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'guazi_bbs',
        'USER': 'root',
        'PASSWORD': '123123',
        'HOST': 'localhost',
        'PORT': '3306',
        'OPTIONS': {'charset': 'utf8mb4'},   # 支持 emoji
    }
}

# ============== 8. 缓存配置 CACHES (新增 Redis 缓存)==============
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
        'OPTIONS': {'CLIENT_CLASS': 'django_redis.client.DefaultClient'},
        'KEY_PREFIX': 'bbs',
    }
}

# ============== 9. 会话配置 SESSION_ENGINE  (新增 session 缓存)==============
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'
SESSION_COOKIE_AGE = 14 * 24 * 60 * 60   # 14 天（秒）

# ============== 10. 媒体文件配置 MEDIA_URL (新增 media 目录和 URL 前缀)==============
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Password validation
# https://docs.djangoproject.com/en/6.1/ref/settings/#auth-password-validators
# ============== 8. 密码验证器 AUTH_PASSWORD_VALIDATORS (默认)==============
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/6.1/topics/i18n/

# ============== 11. 国际化配置 LANGUAGE_CODE (修改为中文)==============
LANGUAGE_CODE = 'zh-hans'
TIME_ZONE = 'Asia/Shanghai'
USE_I18N = True
USE_TZ = False   # 使用本地时间存库，便于调试阅读


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/6.1/howto/static-files/
# ============== 12. 静态文件配置 STATIC_URL (新增 static 目录和 URL 前缀)==============
STATIC_URL = 'static/'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]
# ============== 静态文件配置 STATIC_ROOT (新增 static_collected 目录)==============
STATIC_ROOT = BASE_DIR / 'static_collected'


# Email
# https://docs.djangoproject.com/en/6.1/topics/email/#topic-email-configuration


MAILERS = {
    'default': {
        'BACKEND': 'django.core.mail.backends.console.EmailBackend',
    },
}

# ============== 12. 自定义用户模型 AUTH_USER_MODEL (新增 app01.User)==============
AUTH_USER_MODEL = 'app01.User'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ============== 7. QQ 邮箱 SMTP ==============
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.qq.com'
EMAIL_PORT = 587
EMAIL_HOST_USER = '449150781@qq.com'        # 替换为自己的 QQ 邮箱
EMAIL_HOST_PASSWORD = 'gaftiumxdyqmcahg'    # 替换为邮箱授权码（非登录密码）
EMAIL_USE_TLS = True
EMAIL_FROM = '449150781@qq.com'
# 关键：DEFAULT_FROM_EMAIL 必须等于授权账号，否则 QQ 报 501
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER

# ============== 13. 登录配置 LOGIN_URL (新增 /login/)==============
LOGIN_URL = '/login/'