"""
Comprehensive tests for the Smart Task Analyzer.
"""
from django.test import TestCase, Client
from django.urls import reverse
from datetime import date, timedelta
import json

from .models import Task
from .scoring import (
    detect_circular_dependencies,
    calculate_urgency_score,
    calculate_effort_score,
    score_task,
    analyze_tasks,
    get_top_suggestions
)


class ScoringAlgorithmTests(TestCase):
    """Test the core scoring algorithms."""
    
    def setUp(self):
        """Set up test data."""
        self.today = date.today()
        self.tomorrow = self.today + timedelta(days=1)
        self.next_week = self.today + timedelta(days=7)
        self.overdue = self.today - timedelta(days=2)
        
        self.sample_task = {
            'id': 1,
            'title': 'Test Task',
            'due_date': self.tomorrow.isoformat(),
            'estimated_hours': 2.0,
            'importance': 7,
            'dependencies': []
        }
    
    def test_urgency_calculation(self):
        """Test urgency score calculation for different due dates."""
        # Overdue task should have high urgency
        overdue_score = calculate_urgency_score(self.overdue.isoformat())
        self.assertGreater(overdue_score, 10.0)
        
        # Today's task should have maximum base urgency
        today_score = calculate_urgency_score(self.today.isoformat())
        self.assertEqual(today_score, 10.0)
        
        # Future task should have lower urgency
        future_score = calculate_urgency_score(self.next_week.isoformat())
        self.assertLess(future_score, today_score)
        
        # Invalid date should return default low score
        invalid_score = calculate_urgency_score("invalid-date")
        self.assertEqual(invalid_score, 1.0)
    
    def test_effort_scoring_strategies(self):
        """Test effort scoring for different strategies."""
        # Fast wins strategy should favor quick tasks
        quick_score = calculate_effort_score(1.0, "fast_wins")
        long_score = calculate_effort_score(10.0, "fast_wins")
        self.assertGreater(quick_score, long_score)
        
        # High impact strategy should be less sensitive to effort
        hi_quick = calculate_effort_score(1.0, "high_impact")
        hi_long = calculate_effort_score(10.0, "high_impact")
        self.assertEqual(hi_quick, hi_long)  # Should be same (5.0)
        
        # Invalid effort should return default
        invalid_score = calculate_effort_score(-1.0)
        self.assertEqual(invalid_score, 1.0)
    
    def test_circular_dependency_detection(self):
        """Test detection of circular dependencies."""
        # No circular dependencies
        tasks_no_cycle = [
            {'id': 1, 'title': 'Task 1', 'dependencies': []},
            {'id': 2, 'title': 'Task 2', 'dependencies': [1]},
            {'id': 3, 'title': 'Task 3', 'dependencies': [2]}
        ]
        circular = detect_circular_dependencies(tasks_no_cycle)
        self.assertEqual(len(circular), 0)
        
        # Simple circular dependency
        tasks_with_cycle = [
            {'id': 1, 'title': 'Task 1', 'dependencies': [2]},
            {'id': 2, 'title': 'Task 2', 'dependencies': [1]}
        ]
        circular = detect_circular_dependencies(tasks_with_cycle)
        self.assertEqual(len(circular), 2)
        self.assertIn('Task 1', circular)
        self.assertIn('Task 2', circular)
        
        # Complex circular dependency
        tasks_complex_cycle = [
            {'id': 1, 'title': 'Task 1', 'dependencies': [3]},
            {'id': 2, 'title': 'Task 2', 'dependencies': [1]},
            {'id': 3, 'title': 'Task 3', 'dependencies': [2]}
        ]
        circular = detect_circular_dependencies(tasks_complex_cycle)
        self.assertEqual(len(circular), 3)
    
    def test_task_scoring_strategies(self):
        """Test different scoring strategies."""
        # Test smart_balance strategy
        score, reason = score_task(self.sample_task, "smart_balance")
        self.assertIsInstance(score, float)
        self.assertGreater(score, 0)
        self.assertIn("Balanced prioritization", reason)
        
        # Test fast_wins strategy
        quick_task = self.sample_task.copy()
        quick_task['estimated_hours'] = 0.5
        score_quick, reason_quick = score_task(quick_task, "fast_wins")
        
        slow_task = self.sample_task.copy()
        slow_task['estimated_hours'] = 8.0
        score_slow, reason_slow = score_task(slow_task, "fast_wins")
        
        self.assertGreater(score_quick, score_slow)
        self.assertIn("quick completion", reason_quick)
        
        # Test high_impact strategy
        high_imp_task = self.sample_task.copy()
        high_imp_task['importance'] = 10
        score_high, reason_high = score_task(high_imp_task, "high_impact")
        
        low_imp_task = self.sample_task.copy()
        low_imp_task['importance'] = 2
        score_low, reason_low = score_task(low_imp_task, "high_impact")
        
        self.assertGreater(score_high, score_low)
        self.assertIn("maximum impact", reason_high)
    
    def test_missing_data_handling(self):
        """Test handling of missing or invalid data."""
        # Missing title
        invalid_task = {'due_date': self.tomorrow.isoformat(), 'estimated_hours': 2.0, 'importance': 7}
        score, reason = score_task(invalid_task)
        self.assertEqual(score, 0.0)
        self.assertIn("Missing required fields", reason)
        
        # Invalid importance
        invalid_task = self.sample_task.copy()
        invalid_task['importance'] = 15  # Out of range
        score, reason = score_task(invalid_task)
        self.assertGreater(score, 0)  # Should still work, just use the value
    
    def test_analyze_tasks_function(self):
        """Test the main analyze_tasks function."""
        tasks = [
            {
                'id': 1,
                'title': 'Urgent Task',
                'due_date': self.today.isoformat(),
                'estimated_hours': 1.0,
                'importance': 9,
                'dependencies': []
            },
            {
                'id': 2,
                'title': 'Future Task',
                'due_date': self.next_week.isoformat(),
                'estimated_hours': 5.0,
                'importance': 5,
                'dependencies': []
            }
        ]
        
        result = analyze_tasks(tasks, "smart_balance")
        
        self.assertEqual(result['total_tasks'], 2)
        self.assertEqual(result['strategy_used'], "smart_balance")
        self.assertEqual(len(result['analyzed_tasks']), 2)
        
        # First task should be the urgent one
        first_task = result['analyzed_tasks'][0]
        self.assertEqual(first_task['task']['title'], 'Urgent Task')
        self.assertGreater(first_task['score'], result['analyzed_tasks'][1]['score'])
    
    def test_get_top_suggestions(self):
        """Test the get_top_suggestions function."""
        tasks = [
            {'id': i, 'title': f'Task {i}', 'due_date': self.tomorrow.isoformat(),
             'estimated_hours': i, 'importance': 10-i, 'dependencies': []}
            for i in range(1, 6)
        ]
        
        result = get_top_suggestions(tasks, "smart_balance", limit=3)
        
        self.assertEqual(len(result['suggestions']), 3)
        self.assertEqual(result['strategy_used'], "smart_balance")
        self.assertEqual(result['total_evaluated'], 5)


class APIEndpointTests(TestCase):
    """Test the API endpoints."""
    
    def setUp(self):
        """Set up test client and data."""
        self.client = Client()
        self.analyze_url = reverse('tasks:analyze_tasks')
        self.suggest_url = reverse('tasks:suggest_tasks')
        self.health_url = reverse('tasks:health_check')
        
        self.sample_tasks = [
            {
                'id': 1,
                'title': 'Test Task 1',
                'due_date': (date.today() + timedelta(days=1)).isoformat(),
                'estimated_hours': 2.0,
                'importance': 8,
                'dependencies': []
            },
            {
                'id': 2,
                'title': 'Test Task 2',
                'due_date': (date.today() + timedelta(days=7)).isoformat(),
                'estimated_hours': 4.0,
                'importance': 6,
                'dependencies': [1]
            }
        ]
    
    def test_health_check_endpoint(self):
        """Test the health check endpoint."""
        response = self.client.get(self.health_url)
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        self.assertEqual(data['status'], 'healthy')
    
    def test_analyze_tasks_endpoint(self):
        """Test the analyze tasks endpoint."""
        payload = {
            'tasks': self.sample_tasks,
            'strategy': 'smart_balance'
        }
        
        response = self.client.post(
            self.analyze_url,
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        self.assertIn('analyzed_tasks', data)
        self.assertIn('strategy_used', data)
        self.assertIn('total_tasks', data)
        self.assertEqual(data['strategy_used'], 'smart_balance')
        self.assertEqual(data['total_tasks'], 2)
    
    def test_suggest_tasks_endpoint(self):
        """Test the suggest tasks endpoint."""
        payload = {
            'tasks': self.sample_tasks,
            'strategy': 'fast_wins'
        }
        
        response = self.client.post(
            self.suggest_url,
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        self.assertIn('suggestions', data)
        self.assertIn('strategy_used', data)
        self.assertEqual(data['strategy_used'], 'fast_wins')
        self.assertLessEqual(len(data['suggestions']), 3)
    
    def test_invalid_request_handling(self):
        """Test handling of invalid requests."""
        # Empty payload
        response = self.client.post(
            self.analyze_url,
            data=json.dumps({}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        
        # Invalid JSON
        response = self.client.post(
            self.analyze_url,
            data="invalid json",
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
