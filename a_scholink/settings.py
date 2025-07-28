from pathlib import Path
import os
import dj_database_url
import cloudinary
import cloudinary.uploader
import cloudinary.api
from cloudinary.utils import cloudinary_url


from environ import Env
env = Env()
Env.read_env()
ENVIRONMENT = env('ENVIRONMENT', default='production')
USE_CLOUDINARY = env.bool('USE_CLOUDINARY', default=False)


# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env('SECRET_KEY')


# SECURITY WARNING: don't run with debug turned on in production!
if ENVIRONMENT == 'development':
    DEBUG = True
else:
    DEBUG = False



ALLOWED_HOSTS = ['scholinksys.onrender.com', "*"]


CSRF_TRUSTED_ORIGINS = ["https://*.ngrok-free.app", "https://scholinksys.onrender.com"]


CORS_ALLOW_ALL_ORIGINS = True

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': 'student_creation.log',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}


# AUTH for Students
AUTH_USER_MODEL = 'stu_main.CustomUser'


# Application definition
INSTALLED_APPS = [
    # Kept here because of custom user migration
    'stu_main',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    # Apps
    'exams',
    'assignments',
    'academic_main',
    'principal',
    'parents',
    'teacher_logic.apps.TeacherLogicConfig',
    # Packages 
    'django_htmx',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    "whitenoise.middleware.WhiteNoiseMiddleware",
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    # Htmx Middleware
    'django_htmx.middleware.HtmxMiddleware',
]

ROOT_URLCONF = 'a_scholink.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'a_scholink.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}




POSTGRESS_LOCALLY = True
if ENVIRONMENT == 'production' or POSTGRESS_LOCALLY == True:
        DATABASES['default'] = dj_database_url.parse(env('DATABASE_URL'))



# Password validation
# https://docs.djangoproject.com/en/5.1/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/5.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True



# For Session based logout 
# Auto logout users after 30 minutes (1800 seconds) of inactivity
SESSION_COOKIE_AGE = 1800  

# Refresh session expiry time on every request
SESSION_SAVE_EVERY_REQUEST = True


# Flutterwave Keys (Would be set in an environ later)
FLUTTERWAVE_SECRET_KEY = env('FLUTTERWAVE_SECRET_KEY')


LOGIN_URL = '/login/'


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.1/howto/static-files/

if ENVIRONMENT == 'production' or USE_CLOUDINARY:
    # Cloudinary configuration
    CLOUDINARY = {
        'cloud_name': env('CLOUDINARY_CLOUD_NAME'),
        'api_key': env('CLOUDINARY_API_KEY'),
        'api_secret': env('CLOUDINARY_API_SECRET'),
    }

    cloudinary.config(**CLOUDINARY)

    # Media URL for Cloudinary
    MEDIA_URL = f"https://res.cloudinary.com/{CLOUDINARY['cloud_name']}/"
else:
    # Local media setup
    MEDIA_URL = '/media/'
    MEDIA_ROOT = BASE_DIR / 'media'


STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATIC_URL = 'static/'
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static')
]


# Default primary key field type
# https://docs.djangoproject.com/en/5.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Email configuration



USE_CONSOLE_EMAIL = env.bool("USE_CONSOLE_EMAIL", default=True)

EMAIL_BACKEND = (
    "django.core.mail.backends.console.EmailBackend"
    if USE_CONSOLE_EMAIL
    else "django.core.mail.backends.smtp.EmailBackend"
)

EMAIL_HOST = env("EMAIL_HOST", default="smtp.gmail.com")
EMAIL_PORT = env.int("EMAIL_PORT", default=587)
EMAIL_USE_TLS = env.bool("EMAIL_USE_TLS", default=True)
EMAIL_HOST_USER = env("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", default="")
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default=EMAIL_HOST_USER)
