"""
SRE Middleware: Structured Logging, response time, and Prometheus metrics
"""
import logging
import time
from django.utils.deprecation import MiddlewareMixin
from django.core.cache import cache

logger = logging.getLogger('django.request')

# Prometheus metrics cache keys (Redis-backed for multi-worker)
CACHE_KEY_REQUESTS_TOTAL = 'sre_metrics_requests_total'
CACHE_KEY_REQUESTS_5XX = 'sre_metrics_requests_5xx_total'
CACHE_KEY_RESPONSE_TIME_SUM_MS = 'sre_metrics_response_time_sum_ms'


class StructuredLoggingMiddleware(MiddlewareMixin):
    """
    Structured logging middleware for SRE standards.
    Logs: user_id, status_code, method, path, response_time
    """
    
    def process_request(self, request):
        """Store start time for response time calculation"""
        request._start_time = time.time()
        return None
    
    def process_response(self, request, response):
        """Log structured request/response data"""
        # Calculate response time
        if hasattr(request, '_start_time'):
            response_time = (time.time() - request._start_time) * 1000  # milliseconds
        else:
            response_time = 0
        
        # Get user_id
        user_id = None
        if hasattr(request, 'user') and request.user.is_authenticated:
            user_id = request.user.id
        
        # Skip logging for health checks and static files
        path = request.path
        if path.startswith('/health/') or path.startswith('/static/') or path.startswith('/media/'):
            return response
        
        # Structured log entry (formatted for structured formatter)
        log_msg = (
            f"user_id={user_id} status_code={response.status_code} "
            f"method={request.method} path={path} "
            f"response_time_ms={round(response_time, 2)} ip={self.get_client_ip(request)}"
        )
        
        # Log level based on status code
        if response.status_code >= 500:
            logger.error(log_msg)
        elif response.status_code >= 400:
            logger.warning(log_msg)
        else:
            logger.info(log_msg)

        # Prometheus metrics (SRE) - request count and response time sum (Redis incr requires integer)
        # Wrap in try so Redis/cache errors never break the request
        try:
            cache.incr(CACHE_KEY_REQUESTS_TOTAL, delta=1)
        except (ValueError, TypeError, Exception):
            try:
                cache.set(CACHE_KEY_REQUESTS_TOTAL, 1, timeout=86400 * 7)
            except Exception:
                pass
        if response.status_code >= 500:
            try:
                cache.incr(CACHE_KEY_REQUESTS_5XX, delta=1)
            except (ValueError, TypeError, Exception):
                try:
                    cache.set(CACHE_KEY_REQUESTS_5XX, 1, timeout=86400 * 7)
                except Exception:
                    pass
        try:
            response_time_int = int(round(response_time))
            cache.incr(CACHE_KEY_RESPONSE_TIME_SUM_MS, delta=response_time_int)
        except (ValueError, TypeError, Exception):
            try:
                cache.set(CACHE_KEY_RESPONSE_TIME_SUM_MS, int(round(response_time)), timeout=86400 * 7)
            except Exception:
                pass

        return response
    
    def get_client_ip(self, request):
        """Extract client IP from request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
