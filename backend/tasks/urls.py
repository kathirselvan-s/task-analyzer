"""
URL patterns for the tasks app.
"""
from django.urls import path
from . import views

app_name = 'tasks'

urlpatterns = [
    # Health check
    path('health/', views.health_check, name='health_check'),
    
    # Task analysis endpoints
    path('tasks/analyze/', views.AnalyzeTasksView.as_view(), name='analyze_tasks'),
    path('tasks/suggest/', views.SuggestTasksView.as_view(), name='suggest_tasks'),
]
