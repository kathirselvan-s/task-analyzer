"""
URL configuration for task_analyzer project.
"""
from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse

def api_info(request):
    """Root endpoint providing API information"""
    return JsonResponse({
        'name': 'Smart Task Analyzer API',
        'version': '2.0',
        'status': 'online',
        'endpoints': {
            'admin': '/admin/',
            'api_root': '/api/',
            'tasks': '/api/tasks/',
            'analyze': '/api/tasks/analyze/',
            'suggestions': '/api/tasks/suggestions/'
        },
        'documentation': 'Use POST /api/tasks/analyze/ with tasks array and strategy'
    })

urlpatterns = [
    path('', api_info, name='api-info'),
    path('admin/', admin.site.urls),
    path('api/', include('tasks.urls')),
]
