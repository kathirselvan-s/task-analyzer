"""
Custom CORS Middleware for Django.
This is a simple CORS implementation that works without django-cors-headers.
"""


class CorsMiddleware:
    """
    Middleware to handle CORS (Cross-Origin Resource Sharing).
    Allows requests from different origins to access the API.
    """

    def __init__(self, get_response):
        self.get_response = get_response
        # Origins that are allowed to access this API
        self.allowed_origins = [
            'http://localhost:3000',
            'http://127.0.0.1:3000',
            'http://localhost:8080',
            'http://127.0.0.1:8080',
            'http://localhost:8000',
            'http://127.0.0.1:8000',
        ]

    def __call__(self, request):
        # Handle preflight OPTIONS requests
        if request.method == 'OPTIONS':
            response = self._create_preflight_response(request)
        else:
            response = self.get_response(request)
            response = self._add_cors_headers(request, response)
        return response

    def _create_preflight_response(self, request):
        """Create a response for preflight OPTIONS requests."""
        from django.http import HttpResponse
        response = HttpResponse()
        response.status_code = 200
        response = self._add_cors_headers(request, response)
        return response

    def _add_cors_headers(self, request, response):
        """Add CORS headers to the response."""
        origin = request.META.get('HTTP_ORIGIN', '')
        
        # In development, allow all origins
        # In production, you should check against allowed_origins
        if origin:
            response['Access-Control-Allow-Origin'] = origin
        else:
            response['Access-Control-Allow-Origin'] = '*'
        
        response['Access-Control-Allow-Methods'] = 'GET, POST, PUT, PATCH, DELETE, OPTIONS'
        response['Access-Control-Allow-Headers'] = (
            'Accept, Accept-Encoding, Authorization, Content-Type, DNT, '
            'Origin, User-Agent, X-CSRFToken, X-Requested-With'
        )
        response['Access-Control-Allow-Credentials'] = 'true'
        response['Access-Control-Max-Age'] = '86400'  # Cache preflight for 24 hours
        
        return response

