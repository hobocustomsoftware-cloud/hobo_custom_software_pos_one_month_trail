# WeldingProject/views.py - Page views for Landing, Login, Public pages, SRE
from django.shortcuts import render, redirect
from django.views.decorators.http import require_http_methods
from django.http import FileResponse, Http404, JsonResponse, HttpResponse
from django.conf import settings
from django.db import connection
from django.core.cache import cache
from pathlib import Path


def _content_type(path: Path) -> str:
    ext = path.suffix.lower()
    return {
        '.js': 'application/javascript',
        '.css': 'text/css',
        '.json': 'application/json',
        '.ico': 'image/x-icon',
        '.png': 'image/png',
        '.svg': 'image/svg+xml',
        '.woff': 'font/woff',
        '.woff2': 'font/woff2',
    }.get(ext, 'application/octet-stream')


def serve_manifest(request):
    """Serve PWA manifest as JSON so browser never gets HTML (fixes Manifest syntax error)."""
    frontend = _frontend_root()
    file_path = (frontend / 'manifest.json').resolve()
    if frontend.exists() and file_path.is_file() and str(file_path).startswith(str(frontend.resolve())):
        with open(file_path, 'r', encoding='utf-8') as f:
            return HttpResponse(f.read(), content_type='application/manifest+json')
    # Fallback minimal manifest when file missing (e.g. partial deploy)
    import json
    fallback = {
        'name': 'HoBo POS',
        'short_name': 'POS',
        'description': 'Standalone Cloud POS',
        'start_url': './',
        'display': 'standalone',
        'background_color': '#ffffff',
        'theme_color': '#16a34a',
    }
    return HttpResponse(json.dumps(fallback), content_type='application/manifest+json')


def _frontend_root():
    """Path to Vite build output (dist copied as static_frontend)."""
    return getattr(settings, 'STATIC_FRONTEND_DIR', Path(settings.BASE_DIR) / 'static_frontend')


def serve_favicon(request):
    """Serve /favicon.ico from static_frontend if present; else 204 to avoid 404 noise."""
    frontend = _frontend_root()
    file_path = (frontend / 'favicon.ico').resolve()
    if frontend.exists() and file_path.is_file() and str(file_path).startswith(str(frontend.resolve())):
        return FileResponse(open(file_path, 'rb'), content_type='image/x-icon')
    return HttpResponse(status=204)


def serve_frontend_logo(request, filename):
    """Serve /logo.png and /logo.svg from static_frontend (Vite public/ copied to dist root)."""
    if filename not in ('logo.png', 'logo.svg'):
        return HttpResponse('Forbidden', status=403)
    frontend = _frontend_root()
    file_path = (frontend / filename).resolve()
    if not str(file_path).startswith(str(frontend.resolve())) or not file_path.exists() or not file_path.is_file():
        return HttpResponse('Not Found', status=404)
    return FileResponse(open(file_path, 'rb'), content_type=_content_type(file_path))


def serve_frontend_assets(request, path):
    """Serve /assets/* from static_frontend/assets/ (Vite build.assetsDir='assets' → dist/assets/)."""
    frontend = _frontend_root()
    if not frontend.exists():
        return HttpResponse('Not Found', status=404)
    path = path.lstrip('/')  # normalize: /assets/foo.js → path can be 'foo.js'
    if '..' in path or path.startswith('/'):
        return HttpResponse('Forbidden', status=403)
    file_path = (frontend / 'assets' / path).resolve()
    if not str(file_path).startswith(str(frontend.resolve())):
        return HttpResponse('Forbidden', status=403)
    if not file_path.exists() or not file_path.is_file():
        return HttpResponse('Not Found', status=404)
    return FileResponse(open(file_path, 'rb'), content_type=_content_type(file_path))


def vue_spa_view(request, path=''):
    """Vue SPA serve (EXE / standalone). Serves index.html and /app/assets/* from static_frontend."""
    frontend = _frontend_root()
    if not frontend.exists():
        return HttpResponse(
            '<h1>Frontend not built</h1><p>Run: <code>cd yp_posf && set VITE_BASE=/app/ && npm run build</code></p>'
            '<p>Then copy dist to WeldingProject/static_frontend or restart Docker backend.</p>',
            status=503,
            content_type='text/html',
        )
    
    # Handle assets folder (Vite build.assetsDir='assets' → dist/assets/)
    path = path.lstrip('/') if path else ''
    if path.startswith('assets/'):
        file_path = frontend / path
        if file_path.exists() and file_path.is_file():
            return FileResponse(open(file_path, 'rb'), content_type=_content_type(file_path))
        # Try without assets/ prefix (some builds put files directly)
        alt_path = frontend / path.replace('assets/', '')
        if alt_path.exists() and alt_path.is_file():
            return FileResponse(open(alt_path, 'rb'), content_type=_content_type(alt_path))
        return HttpResponse('File not found', status=404)
    
    # Handle root files (favicon, logo, etc.)
    if path and not path.startswith('/'):
        file_path = frontend / path
        if file_path.exists() and file_path.is_file():
            return FileResponse(open(file_path, 'rb'), content_type=_content_type(file_path))
    
    # Serve index.html for SPA routing
    index = frontend / 'index.html'
    if index.exists():
        with open(index, 'rb') as f:
            content = f.read().decode('utf-8')
            # Inject API URL for Expo/WebView compatibility
            if 'window.EXPO_API_URL' not in content:
                api_url = f"{request.scheme}://{request.get_host()}/api"
                inject_script = f'<script>window.EXPO_API_URL="{api_url}";window.EXPO_READY=true;</script>'
                content = content.replace('</head>', f'{inject_script}</head>')
            return HttpResponse(content, content_type='text/html')
    
    return HttpResponse('Not found', status=404)


def home_view(request):
    """Landing / Home page"""
    return render(request, 'pages/home.html')


def pos_view(request):
    """Quick Sale POS - requires login (staff)"""
    return render(request, 'inventory/quick_sale.html')


def inventory_view(request):
    """Inventory management - redirect to admin or dashboard"""
    return render(request, 'pages/inventory.html')


def reports_view(request):
    """Reports page"""
    return render(request, 'pages/reports.html')


def settings_view(request):
    """Settings - redirect to Vue app (no Django admin)"""
    return redirect('/app/settings')


def about_view(request):
    """About page"""
    return render(request, 'pages/about.html')


def repair_track_view(request):
    """Public page - Customer များ Repair No. + Phone ဖြင့် Status စစ်ဆေးခြင်း"""
    return render(request, 'pages/repair_track.html')


def warranty_check_view(request):
    """Public page - Serial Number ဖြင့် Warranty စစ်ဆေးခြင်း"""
    return render(request, 'pages/warranty_check.html')


def login_page_view(request):
    """JWT Login page - form submits to API, stores token, redirects"""
    return render(request, 'pages/login.html')


@require_http_methods(["GET"])
def logout_view(request):
    """Logout - clears token via client script, redirects to home"""
    return render(request, 'pages/logout.html')


# --- SRE: Health check for load balancer / k8s / Docker ---
@require_http_methods(["GET"])
def health_view(request):
    """Liveness: app is running"""
    return JsonResponse({"status": "ok", "service": "hobopos"})


@require_http_methods(["GET"])
def health_ready_view(request):
    """Readiness: app + DB ready to serve traffic"""
    try:
        with connection.cursor() as c:
            c.execute("SELECT 1")
        return JsonResponse({"status": "ready", "db": "ok"})
    except Exception as e:
        return JsonResponse({"status": "not_ready", "db": str(e)[:100]}, status=503)


# --- SRE: Prometheus metrics (အာမခံချက် / monitoring) ---
try:
    from core.sre_middleware import (
        CACHE_KEY_REQUESTS_TOTAL,
        CACHE_KEY_REQUESTS_5XX,
        CACHE_KEY_RESPONSE_TIME_SUM_MS,
    )
except ImportError:
    CACHE_KEY_REQUESTS_TOTAL = CACHE_KEY_REQUESTS_5XX = CACHE_KEY_RESPONSE_TIME_SUM_MS = None


@require_http_methods(["GET"])
def metrics_view(request):
    """Prometheus-formatted metrics for SRE / Grafana."""
    if CACHE_KEY_REQUESTS_TOTAL is None:
        requests_total = 0
        requests_5xx = 0
        response_time_sum_ms = 0
    else:
        requests_total = cache.get(CACHE_KEY_REQUESTS_TOTAL) or 0
        requests_5xx = cache.get(CACHE_KEY_REQUESTS_5XX) or 0
        response_time_sum_ms = cache.get(CACHE_KEY_RESPONSE_TIME_SUM_MS) or 0

    lines = [
        "# HELP hobopos_requests_total Total HTTP requests.",
        "# TYPE hobopos_requests_total counter",
        f"hobopos_requests_total {requests_total}",
        "# HELP hobopos_requests_5xx_total Total 5xx responses.",
        "# TYPE hobopos_requests_5xx_total counter",
        f"hobopos_requests_5xx_total {requests_5xx}",
        "# HELP hobopos_response_time_sum_ms Sum of response times in milliseconds.",
        "# TYPE hobopos_response_time_sum_ms counter",
        f"hobopos_response_time_sum_ms {response_time_sum_ms}",
        "# HELP hobopos_info Application info.",
        "# TYPE hobopos_info gauge",
        'hobopos_info{service="hobopos",version="1.0"} 1',
    ]
    return HttpResponse("\n".join(lines) + "\n", content_type="text/plain; charset=utf-8")


# --- HTTP error handlers (404, 405, 500, 503) ---
def _wants_json(request):
    """True if client expects JSON (API or Accept header)."""
    path = getattr(request, 'path', '') or ''
    if path.startswith('/api/'):
        return True
    accept = request.META.get('HTTP_ACCEPT', '') or ''
    return 'application/json' in accept


def handler404(request, exception=None):
    """Custom 404: JSON for API, minimal HTML for browser."""
    if _wants_json(request):
        return JsonResponse(
            {'detail': 'Not found.', 'status': 404},
            status=404,
        )
    return HttpResponse(
        '<!DOCTYPE html><html><head><meta charset="utf-8"><title>404</title></head>'
        '<body style="font-family:sans-serif;text-align:center;padding:2rem;"><h1>404</h1><p>Page not found.</p>'
        '<p><a href="/app/">Go to app</a></p></body></html>',
        status=404,
        content_type='text/html; charset=utf-8',
    )


def handler405(request, exception=None):
    """Custom 405: Method Not Allowed."""
    if _wants_json(request):
        return JsonResponse(
            {'detail': 'Method not allowed.', 'status': 405},
            status=405,
        )
    return HttpResponse(
        '<!DOCTYPE html><html><head><meta charset="utf-8"><title>405</title></head>'
        '<body style="font-family:sans-serif;text-align:center;padding:2rem;"><h1>405</h1><p>Method not allowed.</p>'
        '<p><a href="/app/">Go to app</a></p></body></html>',
        status=405,
        content_type='text/html; charset=utf-8',
    )


def handler500(request):
    """Custom 500: Server error."""
    if _wants_json(request):
        return JsonResponse(
            {'detail': 'Internal server error.', 'status': 500},
            status=500,
        )
    return HttpResponse(
        '<!DOCTYPE html><html><head><meta charset="utf-8"><title>500</title></head>'
        '<body style="font-family:sans-serif;text-align:center;padding:2rem;"><h1>500</h1><p>Server error. Try again later.</p>'
        '<p><a href="/app/">Go to app</a></p></body></html>',
        status=500,
        content_type='text/html; charset=utf-8',
    )


def handler503(request, exception=None):
    """Custom 503: Service unavailable (e.g. DB down, maintenance)."""
    if _wants_json(request):
        return JsonResponse(
            {'detail': 'Service temporarily unavailable.', 'status': 503},
            status=503,
        )
    return HttpResponse(
        '<!DOCTYPE html><html><head><meta charset="utf-8"><title>503</title></head>'
        '<body style="font-family:sans-serif;text-align:center;padding:2rem;"><h1>503</h1><p>Service temporarily unavailable.</p>'
        '<p><a href="/app/">Go to app</a></p></body></html>',
        status=503,
        content_type='text/html; charset=utf-8',
    )
