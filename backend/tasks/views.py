"""
API Views for the Smart Task Analyzer.
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
import json
import logging

from .serializers import (
    TaskAnalysisRequestSerializer,
    TaskAnalysisResponseSerializer,
    TaskSuggestionResponseSerializer,
    TaskSerializer
)
from .scoring import analyze_tasks, get_top_suggestions
from .models import Task

logger = logging.getLogger(__name__)


@method_decorator(csrf_exempt, name='dispatch')
class AnalyzeTasksView(APIView):
    """
    API endpoint for analyzing and prioritizing tasks.
    
    POST /api/tasks/analyze/
    """
    
    def post(self, request):
        """
        Analyze tasks and return prioritized list.
        
        Expected payload:
        {
            "tasks": [list of task objects],
            "strategy": "smart_balance|fast_wins|high_impact|deadline_driven",
            "config": {optional configuration}
        }
        """
        try:
            # Parse request data
            try:
                if hasattr(request, 'data') and request.data:
                    data = request.data
                else:
                    data = json.loads(request.body.decode('utf-8'))
            except json.JSONDecodeError:
                return Response({
                    'error': 'Invalid JSON format'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Simple validation instead of using serializer for now
            if 'tasks' not in data or not isinstance(data['tasks'], list):
                return Response({
                    'error': 'Invalid input data - tasks field is required and must be a list'
                }, status=status.HTTP_400_BAD_REQUEST)

            tasks_data = data['tasks']
            strategy = data.get('strategy', 'smart_balance')
            config = data.get('config', {})
            user_preferences = data.get('user_preferences', {})

            # Convert tasks to dictionaries for scoring
            task_dicts = []
            for task_data in tasks_data:
                if isinstance(task_data, dict):
                    task_dict = task_data.copy()
                else:
                    task_dict = dict(task_data)

                # Ensure dependencies is a list of IDs
                if 'dependencies' in task_dict:
                    deps = task_dict['dependencies']
                    if hasattr(deps, 'values_list'):
                        task_dict['dependencies'] = list(deps.values_list('id', flat=True))
                    elif isinstance(deps, list):
                        task_dict['dependencies'] = [dep.id if hasattr(dep, 'id') else dep for dep in deps]
                    else:
                        task_dict['dependencies'] = []
                else:
                    task_dict['dependencies'] = []
                task_dicts.append(task_dict)

            # Perform analysis with user preferences
            analysis_result = analyze_tasks(task_dicts, strategy, config, user_preferences)

            # Format response with enhanced data
            response_data = {
                'analyzed_tasks': analysis_result['analyzed_tasks'],
                'strategy_used': analysis_result['strategy_used'],
                'strategy_description': analysis_result.get('strategy_description', ''),
                'total_tasks': analysis_result['total_tasks'],
                'insights': analysis_result.get('insights', {}),
                'user_preferences': analysis_result.get('user_preferences', {})
            }

            # Add warnings if any
            if analysis_result.get('warnings'):
                response_data['warnings'] = analysis_result['warnings']

            if analysis_result.get('circular_dependencies'):
                response_data['circular_dependencies'] = analysis_result['circular_dependencies']

            return Response(response_data, status=status.HTTP_200_OK)
            
        except json.JSONDecodeError:
            return Response({
                'error': 'Invalid JSON format'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        except Exception as e:
            logger.error(f"Error in AnalyzeTasksView: {str(e)}")
            return Response({
                'error': 'Internal server error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@method_decorator(csrf_exempt, name='dispatch')
class SuggestTasksView(APIView):
    """
    API endpoint for getting top task suggestions.
    
    POST /api/tasks/suggest/
    GET /api/tasks/suggest/?strategy=smart_balance
    """
    
    def post(self, request):
        """Get top 3 task suggestions via POST with task data."""
        try:
            # Parse request data
            try:
                if hasattr(request, 'data') and request.data:
                    data = request.data
                else:
                    data = json.loads(request.body.decode('utf-8'))
            except json.JSONDecodeError:
                return Response({
                    'error': 'Invalid JSON format'
                }, status=status.HTTP_400_BAD_REQUEST)

            strategy = request.GET.get('strategy', data.get('strategy', 'smart_balance'))
            tasks_data = data.get('tasks', [])

            if not tasks_data:
                return Response({
                    'error': 'No tasks provided'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Convert to dictionaries for scoring
            task_dicts = []
            for task_data in tasks_data:
                task_dict = dict(task_data)
                # Handle dependencies
                if 'dependencies' in task_dict and task_dict['dependencies']:
                    if isinstance(task_dict['dependencies'], list):
                        task_dict['dependencies'] = [int(dep) if isinstance(dep, str) and dep.isdigit() else dep for dep in task_dict['dependencies']]
                    else:
                        task_dict['dependencies'] = []
                else:
                    task_dict['dependencies'] = []
                task_dicts.append(task_dict)
            
            # Get suggestions
            suggestions_result = get_top_suggestions(task_dicts, strategy, limit=3)
            
            return Response(suggestions_result, status=status.HTTP_200_OK)
            
        except json.JSONDecodeError:
            return Response({
                'error': 'Invalid JSON format'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        except Exception as e:
            logger.error(f"Error in SuggestTasksView: {str(e)}")
            return Response({
                'error': 'Internal server error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def get(self, request):
        """Get suggestions from stored tasks (if any)."""
        strategy = request.GET.get('strategy', 'smart_balance')
        
        # Get tasks from database
        tasks = Task.objects.all()
        if not tasks.exists():
            return Response({
                'suggestions': [],
                'strategy_used': strategy,
                'total_evaluated': 0,
                'message': 'No tasks found in database'
            }, status=status.HTTP_200_OK)
        
        # Convert to dictionaries
        task_dicts = []
        for task in tasks:
            task_dict = {
                'id': task.id,
                'title': task.title,
                'due_date': task.due_date.isoformat(),
                'estimated_hours': task.estimated_hours,
                'importance': task.importance,
                'dependencies': list(task.dependencies.values_list('id', flat=True))
            }
            task_dicts.append(task_dict)
        
        # Get suggestions
        suggestions_result = get_top_suggestions(task_dicts, strategy, limit=3)
        
        return Response(suggestions_result, status=status.HTTP_200_OK)


@api_view(['GET'])
def health_check(request):
    """Simple health check endpoint."""
    return Response({
        'status': 'healthy',
        'message': 'Smart Task Analyzer API is running'
    }, status=status.HTTP_200_OK)
