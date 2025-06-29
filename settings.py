import os

import django
import environ
from django.core.files.storage import FileSystemStorage
from django.utils.translation import gettext
from django.utils.translation import gettext_lazy as _
from import_export.formats.base_formats import CSV
from rest_framework.authentication import SessionAuthentication

django.utils.translation.ugettext = gettext
env = environ.Env()
env.read_env()

# Path helper
location = lambda x: os.path.join(
    os.path.dirname(os.path.realpath(__file__)), x)

DEBUG = env.bool('DEBUG', default=True)

ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=[
    "*",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "https://localhost:8000",
    "https://heehaw.uk",
    "http://heehaw.uk",
    "https://www.heehaw.uk",
    "http://www.heehaw.uk"
])

# CSRF settings - Add your Hetzner domain here
CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS", default=[
    "https://heehaw.uk",
    "http://heehaw.uk",
    "https://www.heehaw.uk",
    "http://www.heehaw.uk",
    "http://localhost:8000",
    "https://localhost:8000",
    "http://127.0.0.1:8000",
    "https://127.0.0.1:8000"
])

# Additional CSRF settings for production
CSRF_COOKIE_SECURE = not DEBUG  # Use secure cookies in production
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = 'Lax'
CSRF_USE_SESSIONS = False

# CORS settings for API access
CORS_ALLOW_ALL_ORIGINS = DEBUG  # Allow all origins in development
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOWED_ORIGINS = [
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "https://heehaw.uk",
    "http://heehaw.uk",
    "https://www.heehaw.uk",
    "http://www.heehaw.uk"
]

EMAIL_SUBJECT_PREFIX = env.str('EMAIL_SUBJECT_PREFIX', '')

# Use console backend for development to avoid SMTP issues
if DEBUG:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
else:
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_HOST = env.str('EMAIL_HOST')
    EMAIL_USE_TLS = True
    EMAIL_PORT = env.int('EMAIL_PORT')
    EMAIL_HOST_USER = env.str('EMAIL_HOST_USER')
    EMAIL_HOST_PASSWORD = env.str('EMAIL_HOST_PASSWORD')

WHATSAPP_TOKEN = env.str('WHATSAPP_TOKEN')
WHATSAPP_PHONE_NUMBER_ID = env.str('WHATSAPP_PHONE_NUMBER_ID')

# Use a Sqlite database by default
DATABASES = {
    'default': {
        'ENGINE': os.environ.get('DATABASE_ENGINE', 'django.db.backends.sqlite3'),
        'NAME': os.environ.get('DATABASE_NAME', location('db.sqlite')),
        'USER': os.environ.get('DATABASE_USER', None),
        'PASSWORD': os.environ.get('DATABASE_PASSWORD', None),
        'HOST': os.environ.get('DATABASE_HOST', None),
        'PORT': os.environ.get('DATABASE_PORT', None),
        'ATOMIC_REQUESTS': True
    }
}

CACHES = {
    'default': env.cache(default='locmemcache://'),
}

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# On Unix systems, a value of None will cause Django to use the same
# timezone as the operating system.
USE_TZ = True
TIME_ZONE = 'Europe/London'

TEST_RUNNER = 'django.test.runner.DiscoverRunner'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en'

# Includes all languages that have >50% coverage in Transifex
# Taken from Django's default setting for LANGUAGES
gettext_noop = lambda s: s
LANGUAGES = (
    ('ar', gettext_noop('Arabic')),
    ('ca', gettext_noop('Catalan')),
    ('cs', gettext_noop('Czech')),
    ('da', gettext_noop('Danish')),
    ('de', gettext_noop('German')),
    ('en', gettext_noop('British English')),
    ('el', gettext_noop('Greek')),
    ('es', gettext_noop('Spanish')),
    ('fi', gettext_noop('Finnish')),
    ('fr', gettext_noop('French')),
    ('it', gettext_noop('Italian')),
    ('ko', gettext_noop('Korean')),
    ('nl', gettext_noop('Dutch')),
    ('pl', gettext_noop('Polish')),
    ('pt', gettext_noop('Portuguese')),
    ('pt-br', gettext_noop('Brazilian Portuguese')),
    ('ro', gettext_noop('Romanian')),
    ('ru', gettext_noop('Russian')),
    ('sk', gettext_noop('Slovak')),
    ('uk', gettext_noop('Ukrainian')),
    ('zh-cn', gettext_noop('Simplified Chinese')),
)

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale
USE_L10N = True

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
MEDIA_ROOT = location("public/media")

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
MEDIA_URL = '/media/'

STATIC_URL = '/static/'
STATIC_ROOT = location('public/static')
STATICFILES_DIRS = (
    location('static/'),
)
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
)

# Default primary key field type
# https://docs.djangoproject.com/en/dev/ref/settings/#default-auto-field
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Make this unique, and don't share it with anybody.
SECRET_KEY = env.str('SECRET_KEY', default='UajFCuyjDKmWHe29neauXzHi9eZoRXr6RMbT5JyAdPiACBP6Cra2')

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            location('templates'),
        ],
        'OPTIONS': {
            'loaders': [
                'django.template.loaders.filesystem.Loader',
                'django.template.loaders.app_directories.Loader',
            ],
            'context_processors': [
                'django.contrib.auth.context_processors.auth',
                'django.template.context_processors.request',
                'django.template.context_processors.debug',
                'django.template.context_processors.i18n',
                'django.template.context_processors.media',
                'django.template.context_processors.static',
                'django.contrib.messages.context_processors.messages',

                # Oscar specific
                'oscar.apps.search.context_processors.search_form',
                'oscar.apps.communication.notifications.context_processors.notifications',
                'oscar.apps.checkout.context_processors.checkout',
                'oscar.core.context_processors.metadata',
            ],
            'debug': DEBUG,
        }
    }
]

MIDDLEWARE = [
    'debug_toolbar.middleware.DebugToolbarMiddleware',

    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',  # Add CSRF middleware
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.contrib.flatpages.middleware.FlatpageFallbackMiddleware',

    # Allow languages to be selected
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.http.ConditionalGetMiddleware',
    'django.middleware.common.CommonMiddleware',

    # Ensure a valid basket is added to the request instance for every request
    'oscarapi.middleware.ApiBasketMiddleWare',
]

ROOT_URLCONF = 'urls'

# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s %(message)s',
        },
        'simple': {
            'format': '[%(asctime)s] %(message)s'
        },
    },
    'root': {
        'level': 'DEBUG',
        'handlers': ['console'],
    },
    'handlers': {
        'null': {
            'level': 'DEBUG',
            'class': 'logging.NullHandler',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        },
    },
    'loggers': {
        'oscar': {
            'level': 'DEBUG',
            'propagate': True,
        },
        'oscar.catalogue.import': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'oscar.alerts': {
            'handlers': ['null'],
            'level': 'INFO',
            'propagate': False,
        },

        # Django loggers
        'django': {
            'handlers': ['null'],
            'propagate': True,
            'level': 'INFO',
        },
        'django.request': {
            'handlers': ['console'],
            'level': 'ERROR',
            'propagate': True,
        },
        'django.db.backends': {
            'level': 'WARNING',
            'propagate': True,
        },
        'django.security.DisallowedHost': {
            'handlers': ['null'],
            'propagate': False,
        },

        # Third party
        'raven': {
            'level': 'DEBUG',
            'handlers': ['console'],
            'propagate': False,
        },
        'sorl.thumbnail': {
            'handlers': ['console'],
            'propagate': True,
            'level': 'INFO',
        },
        "import_export": {
            "handlers": ["console"],
            "level": "INFO",
        },
    }
}

INSTALLED_APPS = [
    'daphne',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    'django.contrib.flatpages',
    'corsheaders',
    'import_export',
    'oscar.config.Shop',
    'apps.core.apps.CoreConfig',
    'oscar.apps.analytics.apps.AnalyticsConfig',
    'apps.checkout.apps.CheckoutConfig',
    'apps.address.apps.AddressConfig',
    'apps.shipping.apps.ShippingConfig',
    'apps.catalogue.apps.CatalogueConfig',
    'oscar.apps.catalogue.reviews.apps.CatalogueReviewsConfig',
    'apps.communication.apps.CommunicationConfig',
    'oscar.apps.partner.apps.PartnerConfig',
    'apps.basket.apps.BasketConfig',
    'oscar.apps.payment.apps.PaymentConfig',
    'oscar.apps.offer.apps.OfferConfig',
    'apps.order.apps.OrderConfig',
    'oscar.apps.customer.apps.CustomerConfig',
    'oscar.apps.search.apps.SearchConfig',
    'oscar.apps.voucher.apps.VoucherConfig',
    'oscar.apps.wishlists.apps.WishlistsConfig',
    'oscar.apps.dashboard.apps.DashboardConfig',
    'oscar.apps.dashboard.reports.apps.ReportsDashboardConfig',
    'oscar.apps.dashboard.users.apps.UsersDashboardConfig',
    'oscar.apps.dashboard.orders.apps.OrdersDashboardConfig',
    'oscar.apps.dashboard.catalogue.apps.CatalogueDashboardConfig',
    'oscar.apps.dashboard.offers.apps.OffersDashboardConfig',
    'oscar.apps.dashboard.partners.apps.PartnersDashboardConfig',
    'oscar.apps.dashboard.pages.apps.PagesDashboardConfig',
    'oscar.apps.dashboard.ranges.apps.RangesDashboardConfig',
    'oscar.apps.dashboard.reviews.apps.ReviewsDashboardConfig',
    'oscar.apps.dashboard.vouchers.apps.VouchersDashboardConfig',
    'oscar.apps.dashboard.communications.apps.CommunicationsDashboardConfig',
    'oscar.apps.dashboard.shipping.apps.ShippingDashboardConfig',

    # 3rd-party apps that Oscar depends on
    'widget_tweaks',
    'haystack',
    'treebeard',
    'sorl.thumbnail',
    'django_tables2',
    'tinymce',
    'paypal',

    # Django apps that the sandbox depends on
    'django.contrib.sitemaps',

    # 3rd-party apps that the sandbox depends on
    'django_extensions',
    'debug_toolbar',

    # local apps
    'apps.system.apps.SystemConfigAppConfig',
    'apps.custom_api.apps.CustomAPIConfig',
    'rest_framework',
    'drf_spectacular',
    'oscarapi',
]

# Add Oscar's custom auth backend so users can sign in using their email
# address.
AUTHENTICATION_BACKENDS = (
    'oscar.apps.customer.auth_backends.EmailBackend',
    'django.contrib.auth.backends.ModelBackend',
)

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 9,
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
]

LOGIN_REDIRECT_URL = '/'
APPEND_SLASH = True
# ====================
# Messages contrib app
# ====================

from django.contrib.messages import constants as messages

MESSAGE_TAGS = {
    messages.ERROR: 'danger'
}

# Haystack settings
HAYSTACK_CONNECTIONS = {
    'default': {
        'ENGINE': 'haystack.backends.whoosh_backend.WhooshEngine',
        'PATH': location('whoosh_index'),
    },
}

# =============
# Debug Toolbar
# =============

INTERNAL_IPS = ['127.0.0.1', '::1']

# ==============
# Oscar settings
# ==============

from oscar.defaults import *

# Meta
# ====

OSCAR_SHOP_TAGLINE = env.str('OSCAR_SHOP_TAGLINE', 'Sandbox')
OSCAR_DEFAULT_CURRENCY = env.str(OSCAR_DEFAULT_CURRENCY, 'GBP')

OSCAR_RECENTLY_VIEWED_PRODUCTS = 20
OSCAR_ALLOW_ANON_CHECKOUT = True

OSCAR_FROM_EMAIL = env.str('OSCAR_FROM_EMAIL')
OSCARAPI_BLOCK_ADMIN_API_ACCESS = False

# Order processing
# ================

PENDING = 'Pending'
PROCESSING = 'Processing'
READY = 'Ready'
DONE = 'Done'
CANCELLED = 'Canceled'

# Sample order/line status settings. This is quite simplistic. It's like you'll
# want to override the set_status method on the order object to do more
# sophisticated things.
OSCAR_INITIAL_ORDER_STATUS = PENDING
OSCAR_INITIAL_LINE_STATUS = PENDING

ORDER_STATUSES = (PENDING, PROCESSING, READY, DONE, CANCELLED)
ORDER_STATUSES_LOWER = tuple(status.lower() for status in ORDER_STATUSES)

# This dict defines the new order statuses than an order can move to
OSCAR_ORDER_STATUS_PIPELINE = {
    PENDING: (READY, PROCESSING, CANCELLED,),
    PROCESSING: (READY, DONE, CANCELLED,),
    READY: (DONE, CANCELLED,),
    DONE: (CANCELLED,),
    CANCELLED: (),
}

OSCAR_LINE_STATUS_PIPELINE = OSCAR_ORDER_STATUS_PIPELINE

# This dict defines the line statuses that will be set when an order's status
# is changed
OSCAR_ORDER_STATUS_CASCADE = {
    PENDING: PENDING,
    PROCESSING: PROCESSING,
    READY: READY,
    DONE: DONE,
    CANCELLED: CANCELLED,
}

OSCARAPI_ORDER_FIELDS = (
    "id",
    "number",
    "owner",
    "currency",
    "total_incl_tax",
    "total_excl_tax",
    "shipping_incl_tax",
    "shipping_excl_tax",
    "shipping_address",
    "billing_address",
    "shipping_method",
    "shipping_code",
    "status",
    "email",
    "date_placed",
    "offer_discounts",
    "voucher_discounts",
    "surcharges",
    "available_statuses",
    "created",
    "updated",
    "is_anonymous",
    "guest_first_name",
    "guest_last_name",
    "guest_phone_number",
    "lines",
    "payment_url",
)

# Sorl
# ====
THUMBNAIL_DEBUG = DEBUG
THUMBNAIL_KEY_PREFIX = 'oscar-sandbox'
THUMBNAIL_KVSTORE = env(
    'THUMBNAIL_KVSTORE',
    default='sorl.thumbnail.kvstores.cached_db_kvstore.KVStore')
THUMBNAIL_REDIS_URL = env('THUMBNAIL_REDIS_URL', default=None)

# Django 1.6 has switched to JSON serializing for security reasons, but it does not
# serialize Models. We should resolve this by extending the
# django/core/serializers/json.Serializer to have the `dumps` function. Also
# in tests/config.py
SESSION_SERIALIZER = 'django.contrib.sessions.serializers.JSONSerializer'

# Security
SECURE_SSL_REDIRECT = env.bool('SECURE_SSL_REDIRECT', default=False)
SECURE_HSTS_SECONDS = env.int('SECURE_HSTS_SECONDS', default=0)
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True

TINYMCE_DEFAULT_CONFIG = {
    "height": "320px",
    "width": "960px",
    "menubar": False,
    "plugins": "advlist autolink lists link image charmap print preview anchor searchreplace visualblocks code "
               "fullscreen insertdatetime media table paste code help wordcount spellchecker",
    "toolbar": "undo redo | bold italic underline strikethrough link |forecolor |"
               "backcolor casechange permanentpen formatpainter removeformat | fontselect fontsizeselect formatselect | alignleft "
               "aligncenter alignright alignjustify | outdent indent |  numlist bullist checklist | "
               " pagebreak | charmap emoticons | "
               "fullscreen  preview save print | insertfile image media pageembed template anchor codesample | "
               "a11ycheck ltr rtl | showcomments addcomment code",
    "custom_undo_redo_levels": 10,
    "language": "en",  # To force a specific language instead of the Django current language.
}
# Try and import local settings which can be used to override any of the above.
try:
    from settings_local import *
except ImportError:
    pass

# Custom SessionAuthentication that doesn't enforce CSRF for API endpoints
class CsrfExemptSessionAuthentication(SessionAuthentication):
    def enforce_csrf(self, request):
        return  # To not perform the csrf check previously happening

REST_FRAMEWORK = {
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'settings.CsrfExemptSessionAuthentication',
        'rest_framework.authentication.BasicAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny',  # Allow anonymous access for basket operations
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
}

SPECTACULAR_SETTINGS = {
    'TITLE': 'Django Oscar API',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    "PREPROCESSING_HOOKS": ["apps.system.services.preprocessing_filter_spec"],
    "APPEND_COMPONENTS": {
        "securitySchemes": {"ApiKeyAuth": {"type": "apiKey", "in": "header", "name": "X-Auth"}},
    },
    "SECURITY": [{"ApiKeyAuth": [], }],
}

OSCARAPI_OVERRIDE_MODULES = ["apps.custom_api"]

PAYMENT_METHOD_CASH = 'Cash'
PAYMENT_METHOD_CARD = 'Card'
PAYMENT_METHOD_PAYPAL = 'Paypal'
PAYMENT_METHODS = (
    (PAYMENT_METHOD_CASH, 'Cash'),
    (PAYMENT_METHOD_CARD, 'Credit / Debit card'),
    (PAYMENT_METHOD_PAYPAL, 'Paypal'),
)

PAYPAL_API_USERNAME = env('PAYPAL_API_USERNAME')
PAYPAL_API_PASSWORD = env('PAYPAL_API_PASSWORD')
PAYPAL_API_SIGNATURE = env('PAYPAL_API_SIGNATURE')
PAYPAL_SANDBOX_MODE = env('PAYPAL_SANDBOX_MODE', default=True)
PAYPAL_CALLBACK_HTTPS = env('PAYPAL_CALLBACK_HTTPS', default=True)

STRIPE_SECRET_KEY = env('STRIPE_SECRET_KEY')
STRIPE_PUBLISH_KEY = env('STRIPE_PUBLISH_KEY')

PAYMENT_EVENT_SETTLED = 'Settled'

STRIPE_EMAIL = 'stripeEmail'
STRIPE_TOKEN = 'stripeToken'

IMPORT_FORMATS = [CSV]
IMPORT_EXPORT_SKIP_ADMIN_CONFIRM = True
OSCAR_DASHBOARD_NAVIGATION += [
    {
        'label': _('System'),
        'icon': 'fa-solid fa-gear',
        'children': [
            {
                'label': _('Schedule'),
                'url_name': 'schedule-config',
                'access_fn': lambda user, url_name, url_args, url_kwargs: user.is_staff,
            },
            {
                'label': _('Link Device'),
                'url_name': 'link-device',
                'access_fn': lambda user, url_name, url_args, url_kwargs: user.is_staff,
            }
        ],
    }

]

# Private folder for firebase keys
FIREBASE_KEY_FILE_STORAGE = FileSystemStorage(location="firebase_keys")

# Channels
ASGI_APPLICATION = "asgi.application"

WEBSOCKET_REDIS_URL = env.str('WEBSOCKET_REDIS_URL', default='redis://localhost:6379/0')
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [WEBSOCKET_REDIS_URL],
        },
    },
}
