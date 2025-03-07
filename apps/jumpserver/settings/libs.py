# -*- coding: utf-8 -*-
#
import os
import ssl

from .base import REDIS_SSL_CA_CERTS, REDIS_SSL_CERTFILE, REDIS_SSL_KEYFILE, REDIS_SSL_REQUIRED
from ..const import CONFIG, PROJECT_DIR

REST_FRAMEWORK = {
    # Use Django's standard `django.contrib.auth` permissions,
    # or allow read-only access for unauthenticated users.
    'DEFAULT_PERMISSION_CLASSES': (
        'rbac.permissions.RBACPermission',
    ),
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
        # 'rest_framework.renderers.BrowsableAPIRenderer',
        'common.drf.renders.CSVFileRenderer',
        'common.drf.renders.ExcelFileRenderer',

    ),
    'DEFAULT_PARSER_CLASSES': (
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.FormParser',
        'rest_framework.parsers.MultiPartParser',
        'common.drf.parsers.CSVFileParser',
        'common.drf.parsers.ExcelFileParser',
        'rest_framework.parsers.FileUploadParser',
    ),
    'DEFAULT_AUTHENTICATION_CLASSES': (
        # 'rest_framework.authentication.BasicAuthentication',
        'authentication.backends.drf.AccessKeyAuthentication',
        'authentication.backends.drf.AccessTokenAuthentication',
        'authentication.backends.drf.PrivateTokenAuthentication',
        'authentication.backends.drf.SignatureAuthentication',
        'authentication.backends.drf.SessionAuthentication',
    ),
    'DEFAULT_FILTER_BACKENDS': (
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ),
    'DEFAULT_METADATA_CLASS': 'common.drf.metadata.SimpleMetadataWithFilters',
    'ORDERING_PARAM': "order",
    'SEARCH_PARAM': "search",
    'DATETIME_FORMAT': '%Y/%m/%d %H:%M:%S %z',
    'DATETIME_INPUT_FORMATS': ['%Y/%m/%d %H:%M:%S %z', 'iso-8601', '%Y-%m-%d %H:%M:%S %z'],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.LimitOffsetPagination',
    'EXCEPTION_HANDLER': 'common.drf.exc_handlers.common_exception_handler',
    # 'PAGE_SIZE': 100,
    # 'MAX_PAGE_SIZE': 5000

}

SWAGGER_SETTINGS = {
    'DEFAULT_AUTO_SCHEMA_CLASS': 'jumpserver.views.swagger.CustomSwaggerAutoSchema',
    'USE_SESSION_AUTH': True,
    'SECURITY_DEFINITIONS': {
        'Bearer': {
            'type': 'apiKey',
            'name': 'Authorization',
            'in': 'header'
        }
    },
    'DEFAULT_INFO': 'jumpserver.views.swagger.api_info',
}


# Captcha settings, more see https://django-simple-captcha.readthedocs.io/en/latest/advanced.html
CAPTCHA_IMAGE_SIZE = (140, 34)
CAPTCHA_FOREGROUND_COLOR = '#001100'
CAPTCHA_NOISE_FUNCTIONS = ('captcha.helpers.noise_dots',)
CAPTCHA_CHALLENGE_FUNCT = 'captcha.helpers.math_challenge'

# Django bootstrap3 setting, more see http://django-bootstrap3.readthedocs.io/en/latest/settings.html
BOOTSTRAP3 = {
    'horizontal_label_class': 'col-md-2',
    # Field class to use in horizontal forms
    'horizontal_field_class': 'col-md-9',
    # Set placeholder attributes to label if no placeholder is provided
    'set_placeholder': False,
    'success_css_class': '',
    'required_css_class': 'required',
}


# Django channels support websocket
if not CONFIG.REDIS_USE_SSL:
    context = None
else:
    context = ssl.SSLContext()
    context.check_hostname = bool(CONFIG.REDIS_SSL_REQUIRED)
    if REDIS_SSL_CA_CERTS:
        context.load_verify_locations(REDIS_SSL_CA_CERTS)
    if REDIS_SSL_CERTFILE and REDIS_SSL_KEYFILE:
        context.load_cert_chain(REDIS_SSL_CERTFILE, REDIS_SSL_KEYFILE)

CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'common.cache.RedisChannelLayer',
        'CONFIG': {
            "hosts": [{
                'address': (CONFIG.REDIS_HOST, CONFIG.REDIS_PORT),
                'db': CONFIG.REDIS_DB_WS,
                'password': CONFIG.REDIS_PASSWORD or None,
                'ssl':  context
            }],
        },
    },
}
ASGI_APPLICATION = 'jumpserver.routing.application'


# Dump all celery log to here
CELERY_LOG_DIR = os.path.join(PROJECT_DIR, 'data', 'celery')

# Celery using redis as broker
CELERY_BROKER_URL = '%(protocol)s://:%(password)s@%(host)s:%(port)s/%(db)s' % {
    'protocol': 'rediss' if CONFIG.REDIS_USE_SSL else 'redis',
    'password': CONFIG.REDIS_PASSWORD,
    'host': CONFIG.REDIS_HOST,
    'port': CONFIG.REDIS_PORT,
    'db': CONFIG.REDIS_DB_CELERY,
}
CELERY_TASK_SERIALIZER = 'pickle'
CELERY_RESULT_SERIALIZER = 'pickle'
CELERY_RESULT_BACKEND = CELERY_BROKER_URL
CELERY_ACCEPT_CONTENT = ['json', 'pickle']
CELERY_RESULT_EXPIRES = 600
# CELERY_WORKER_LOG_FORMAT = '%(asctime)s [%(module)s %(levelname)s] %(message)s'
# CELERY_WORKER_LOG_FORMAT = '%(message)s'
# CELERY_WORKER_TASK_LOG_FORMAT = '%(task_id)s %(task_name)s %(message)s'
CELERY_WORKER_TASK_LOG_FORMAT = '%(message)s'
# CELERY_WORKER_LOG_FORMAT = '%(asctime)s [%(module)s %(levelname)s] %(message)s'
CELERY_WORKER_LOG_FORMAT = '%(message)s'
CELERY_TASK_EAGER_PROPAGATES = True
CELERY_WORKER_REDIRECT_STDOUTS = True
CELERY_WORKER_REDIRECT_STDOUTS_LEVEL = "INFO"
# CELERY_WORKER_HIJACK_ROOT_LOGGER = True
# CELERY_WORKER_MAX_TASKS_PER_CHILD = 40
CELERY_TASK_SOFT_TIME_LIMIT = 3600
if CONFIG.REDIS_USE_SSL:
    CELERY_BROKER_USE_SSL = CELERY_REDIS_BACKEND_USE_SSL = {
        'ssl_cert_reqs': REDIS_SSL_REQUIRED,
        'ssl_ca_certs': REDIS_SSL_CA_CERTS,
        'ssl_certfile': REDIS_SSL_CERTFILE,
        'ssl_keyfile': REDIS_SSL_KEYFILE
    }

ANSIBLE_LOG_DIR = os.path.join(PROJECT_DIR, 'data', 'ansible')

#
REDIS_HOST = CONFIG.REDIS_HOST
REDIS_PORT = CONFIG.REDIS_PORT
REDIS_PASSWORD = CONFIG.REDIS_PASSWORD
