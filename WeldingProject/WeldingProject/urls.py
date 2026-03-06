"""
URL configuration for WeldingProject project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
import os
from django.urls import path, include, re_path
from django.shortcuts import redirect
from . import views as project_views
from django.conf import settings
from django.conf.urls.static import static
from rest_framework_simplejwt.views import TokenRefreshView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from core.throttling import AuthThrottle
from core.views import ShopSettingsView
from core.auth_views import CustomTokenObtainView


urlpatterns = [
    path('admin/', lambda r: redirect('/app/')),

    # SRE: Health checks + Prometheus metrics
    path('health/', project_views.health_view),
    path('health/ready/', project_views.health_ready_view),
    path('metrics/', project_views.metrics_view),

    # Favicon + Logo at root
    path('favicon.ico', project_views.serve_favicon, name='favicon'),
    path('logo.png', project_views.serve_frontend_logo, {'filename': 'logo.png'}, name='logo-png'),
    path('logo.svg', project_views.serve_frontend_logo, {'filename': 'logo.svg'}, name='logo-svg'),
    # Vue SPA assets (Vite build uses base: '/' so HTML requests /assets/xxx - must be at root)
    path('assets/<path:path>', project_views.serve_frontend_assets, name='vue-app-assets'),
    # Vue SPA (single entry: everything under /app/)
    path('app/', project_views.vue_spa_view, {'path': ''}, name='vue-app'),
    path('app/manifest.json', project_views.serve_manifest, name='vue-app-manifest'),
    path('app/<path:path>', project_views.vue_spa_view, name='vue-app-path'),

    # Redirect old Django page URLs to Vue SPA under /app/ (တစ်ခုတည်း localhost:8000/app/ ကနေ အကုန်သုံး)
    path('', lambda r: redirect('/app/')),
    path('pos/', lambda r: redirect('/app/sales/pos')),
    path('inventory/', lambda r: redirect('/app/inventory')),
    path('reports/', lambda r: redirect('/app/')),
    path('settings/', lambda r: redirect('/app/settings')),
    path('about/', lambda r: redirect('/app/')),
    path('login/', lambda r: redirect('/app/login')),
    path('logout/', lambda r: redirect('/app/login')),
    path('register/', lambda r: redirect('/app/register')),
    path('repair-track/', lambda r: redirect('/app/repair-track')),
    path('warranty-check/', lambda r: redirect('/app/warranty-check')),

    path('api/license/', include('license.urls')),
    re_path(r'^api/core/shop-settings/?$', ShopSettingsView.as_view(), name='api-shop-settings'),
    path('api/core/', include('core.urls')),
    path('api/', include('inventory.urls')),
    path('api-auth/', include('rest_framework.urls')),
    path('api/customers/', include('customer.urls')),
    path('api/service/', include('service.urls')),
    path('api/ai/', include('ai.urls')),
    path('api/accounting/', include('accounting.urls')),
    path('api/installation/', include('installation.urls')),

    # JWT: accept username+password or login (phone/email)+password (Loyverse)
    path('api/token/', CustomTokenObtainView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(throttle_classes=[AuthThrottle]), name='token_refresh'),

    # API Documentation (Swagger/OpenAPI - A to K recommendation)
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),

    # Catch-all: serve Vue SPA index.html for any non-API path (so asset 404s are avoided when using correct /assets/ and /app/)
    re_path(r'^.*$', lambda r: project_views.vue_spa_view(r, '')),
]

# Custom HTTP error handlers (404, 405, 500) — JSON for API, HTML for browser
handler404 = project_views.handler404
handler405 = project_views.handler405
handler500 = project_views.handler500

# Media + Static: DEBUG သို့မဟုတ် EXE (HOBOPOS_DB_DIR) မှာ serve
if settings.DEBUG or os.environ.get('HOBOPOS_DB_DIR'):
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)