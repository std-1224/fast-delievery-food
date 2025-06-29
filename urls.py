import django
from django.apps import apps
from django.conf import settings
from django.conf.urls.i18n import i18n_patterns
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.sitemaps import views
from django.urls import include, path, re_path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView
from oscar.views import handler403, handler404, handler500

from apps.sitemaps import base_sitemaps

admin.autodiscover()

urlpatterns = [
    # Include admin as convenience. It's unsupported and only included
    # for developers.
    path('admin/', admin.site.urls),
    # i18n URLS need to live outside of i18n_patterns scope of Oscar
    path('i18n/', include(django.conf.urls.i18n)),

    # include a basic sitemap
    path('sitemap.xml', views.index,
         {'sitemaps': base_sitemaps}),
    path('sitemap-<slug:section>.xml', views.sitemap,
         {'sitemaps': base_sitemaps},
         name='django.contrib.sitemaps.views.sitemap'),
    path('tinymce/', include('tinymce.urls')),
    path("api/", include('apps.custom_api.urls')),
    path("api/", include("oscarapi.urls")),
    path("api/", include("apps.system.api_urls")),
    re_path('^checkout/paypal/', include('paypal.express.urls')),
    re_path(r'^dashboard/system/', include(apps.get_app_config('system').urls[0])),
]

# Prefix Oscar URLs with language codes
urlpatterns += i18n_patterns(
    path('', include(apps.get_app_config('oscar').urls[0])),
)

if settings.DEBUG:
    import debug_toolbar

    # Server statics and uploaded media
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    # Allow error pages to be tested
    urlpatterns += [
        path('403', handler403, {'exception': Exception()}),
        path('404', handler404, {'exception': Exception()}),
        path('500', handler500),
        path('__debug__/', include(debug_toolbar.urls)),
    ]

    urlpatterns += [
        path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
        path('api/docs', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
        path('api/redoc', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    ]
