"""
Smart Task Analyzer - Core Scoring Algorithms

This module implements various task prioritization strategies with configurable weights
and handles edge cases like circular dependencies and missing data.

Strategies:
- fast_wins: Prioritizes quick tasks for maximum momentum (Speed Mode)
- high_impact: Focuses on important, high-value tasks (Effective Mode)
- deadline_driven: Urgency-first for deadline crisis situations
- smart_balance: Balanced approach considering all factors

User Preferences:
- available_hours: How many hours user has today
- energy_level: low/medium/high - affects task recommendations
- work_mode: speed/effective/deadline_crisis/balanced
"""
from datetime import date, timedelta
from typing import List, Dict, Any, Tuple
import math


def detect_circular_dependencies(tasks: List[Dict]) -> List[str]:
    """
    Detect circular dependencies using DFS algorithm.
    
    Args:
        tasks: List of task dictionaries with 'id' and 'dependencies' fields
        
    Returns:
        List of task titles that are part of circular dependencies
    """
    task_map = {task['id']: task for task in tasks}
    visited = set()
    rec_stack = set()
    circular_tasks = set()
    
    def dfs(task_id, path):
        if task_id in rec_stack:
            # Found a cycle, add all tasks in the cycle
            cycle_start = path.index(task_id)
            circular_tasks.update(path[cycle_start:])
            return True
        
        if task_id in visited:
            return False
        
        visited.add(task_id)
        rec_stack.add(task_id)
        path.append(task_id)
        
        task = task_map.get(task_id)
        if task:
            for dep_id in task.get('dependencies', []):
                if dep_id in task_map and dfs(dep_id, path):
                    return True
        
        rec_stack.remove(task_id)
        path.pop()
        return False
    
    # Check each task for cycles
    for task in tasks:
        if task['id'] not in visited:
            dfs(task['id'], [])
    
    # Return titles of circular tasks
    return [task_map[task_id]['title'] for task_id in circular_tasks if task_id in task_map]


def calculate_urgency_score(due_date_str: str, max_score: float = 10.0, crisis_mode: bool = False) -> Tuple[float, str]:
    """
    Calculate urgency score based on due date.

    Args:
        due_date_str: ISO format date string
        max_score: Maximum possible score
        crisis_mode: If True, applies more aggressive urgency scaling

    Returns:
        Tuple of (score, urgency_label)
    """
    try:
        due_date = date.fromisoformat(due_date_str)
        today = date.today()
        days_until_due = (due_date - today).days

        # Crisis mode multiplier
        multiplier = 1.5 if crisis_mode else 1.0

        if days_until_due < 0:
            # Overdue tasks get maximum urgency + severe penalty
            overdue_penalty = abs(days_until_due) * (1.0 if crisis_mode else 0.5)
            return min(max_score + overdue_penalty, 15.0) * multiplier, "OVERDUE"
        elif days_until_due == 0:
            return max_score * multiplier, "Due Today"
        elif days_until_due == 1:
            return max_score * 0.95 * multiplier, "Due Tomorrow"
        elif days_until_due <= 3:
            return max_score * 0.85 * multiplier, "Due in 2-3 days"
        elif days_until_due <= 7:
            return max_score * 0.65 * multiplier, "Due this week"
        elif days_until_due <= 14:
            return max_score * 0.45 * multiplier, "Due in 2 weeks"
        elif days_until_due <= 30:
            return max_score * 0.25 * multiplier, "Due this month"
        else:
            return max_score * 0.1, "Future task"
    except (ValueError, TypeError):
        return 1.0, "No deadline"


def calculate_effort_score(estimated_hours: float, strategy: str = "smart_balance",
                          energy_level: str = "medium") -> Tuple[float, str]:
    """
    Calculate effort-based score (rewards quick wins in most strategies).

    Args:
        estimated_hours: Estimated time to complete task
        strategy: Current prioritization strategy
        energy_level: User's current energy level (low/medium/high)

    Returns:
        Tuple of (score, effort_label)
    """
    try:
        hours = float(estimated_hours)
        if hours <= 0:
            return 1.0, "Quick task"

        # Energy level modifier
        energy_modifier = {
            'low': 0.7,    # Low energy = prefer shorter tasks
            'medium': 1.0,
            'high': 1.3    # High energy = can handle longer tasks
        }.get(energy_level, 1.0)

        # Determine effort label
        if hours <= 0.5:
            effort_label = "⚡ Quick (< 30 min)"
        elif hours <= 1:
            effort_label = "🏃 Short (< 1 hour)"
        elif hours <= 2:
            effort_label = "📝 Medium (1-2 hours)"
        elif hours <= 4:
            effort_label = "🎯 Focused (2-4 hours)"
        else:
            effort_label = "🏋️ Deep work (4+ hours)"

        if strategy == "fast_wins":
            # Heavily favor quick tasks - exponential decay
            base_score = max(10.0 - (hours ** 1.5), 1.0)
            return base_score * energy_modifier, effort_label
        elif strategy == "high_impact":
            # Effort matters less for high impact strategy
            # But still slight preference for achievable tasks
            return max(6.0 - (hours * 0.2), 4.0), effort_label
        elif strategy == "deadline_driven":
            # Moderate - focus on what can be done in time
            return max(7.0 - (hours * 0.3), 2.0), effort_label
        else:  # smart_balance
            # Moderate preference for quicker tasks
            return max(8.0 - (hours * 0.5), 1.0) * energy_modifier, effort_label
    except (ValueError, TypeError):
        return 1.0, "Unknown effort"


def calculate_dependency_boost(task: Dict, all_tasks: List[Dict]) -> float:
    """Calculate boost for tasks that block others (have dependents)."""
    task_id = task['id']
    dependent_count = 0
    
    # Count how many tasks depend on this one
    for other_task in all_tasks:
        if task_id in other_task.get('dependencies', []):
            dependent_count += 1
    
    # Boost score based on number of dependents
    return dependent_count * 2.0


def score_task(task: Dict, strategy: str = "smart_balance", config: Dict = None,
               all_tasks: List[Dict] = None, user_preferences: Dict = None) -> Tuple[float, str, Dict]:
    """
    Score a single task based on the selected strategy and user preferences.

    Args:
        task: Task dictionary with required fields
        strategy: Scoring strategy to use
        config: Optional configuration with custom weights
        all_tasks: All tasks (needed for dependency calculations)
        user_preferences: User preferences (energy_level, available_hours, etc.)

    Returns:
        Tuple of (score, explanation, metadata)
    """
    if config is None:
        config = {}

    if all_tasks is None:
        all_tasks = [task]

    if user_preferences is None:
        user_preferences = {}

    # Extract user preferences
    energy_level = user_preferences.get('energy_level', 'medium')
    crisis_mode = strategy == "deadline_driven"

    # Validate required fields
    required_fields = ['title', 'due_date', 'estimated_hours', 'importance']
    missing_fields = [field for field in required_fields if field not in task or task[field] is None]

    if missing_fields:
        return 0.0, f"Missing required fields: {', '.join(missing_fields)}", {}

    # Calculate component scores with enhanced functions
    urgency_score, urgency_label = calculate_urgency_score(task['due_date'], crisis_mode=crisis_mode)
    importance = float(task.get('importance', 5))
    effort_score, effort_label = calculate_effort_score(task['estimated_hours'], strategy, energy_level)
    dependency_boost = calculate_dependency_boost(task, all_tasks)

    # Strategy-specific scoring with enhanced weights
    if strategy == "fast_wins":
        weights = config.get('fast_wins_weights', {
            'urgency': 0.25,
            'importance': 0.15,
            'effort': 0.50,  # Heavy emphasis on quick tasks
            'dependency': 0.10
        })
        strategy_desc = "⚡ Speed Mode"
        reason = "Quick completion for maximum momentum"

    elif strategy == "high_impact":
        weights = config.get('high_impact_weights', {
            'urgency': 0.15,
            'importance': 0.55,  # Heavy emphasis on importance
            'effort': 0.10,
            'dependency': 0.20
        })
        strategy_desc = "🎯 Effective Mode"
        reason = "High-value task for maximum impact"

    elif strategy == "deadline_driven":
        weights = config.get('deadline_driven_weights', {
            'urgency': 0.65,  # Very heavy emphasis on deadlines
            'importance': 0.15,
            'effort': 0.10,
            'dependency': 0.10
        })
        strategy_desc = "🚨 Deadline Crisis Mode"
        reason = "Urgent deadline - immediate attention required"

    else:  # smart_balance
        weights = config.get('smart_balance_weights', {
            'urgency': 0.30,
            'importance': 0.30,
            'effort': 0.20,
            'dependency': 0.20
        })
        strategy_desc = "⚖️ Balanced Mode"
        reason = "Balanced prioritization for optimal productivity"

    # Calculate weighted score
    raw_score = (
        urgency_score * weights['urgency'] +
        importance * weights['importance'] +
        effort_score * weights['effort'] +
        dependency_boost * weights['dependency']
    )

    # Normalize score to 0-10 range
    score = min(max(raw_score, 0), 10)

    # Build detailed reason with context
    details = []

    # Urgency details
    if urgency_label == "OVERDUE":
        details.append("⚠️ OVERDUE")
    elif urgency_label == "Due Today":
        details.append("🔥 Due today")
    elif urgency_label == "Due Tomorrow":
        details.append("⏰ Due tomorrow")
    elif urgency_score > 7:
        details.append(f"📅 {urgency_label}")

    # Importance details
    if importance >= 9:
        details.append("💎 Critical importance")
    elif importance >= 7:
        details.append("⭐ High importance")

    # Effort details
    if effort_score > 7:
        details.append("⚡ Quick win")

    # Dependency details
    if dependency_boost > 0:
        blocking_count = int(dependency_boost / 2)
        details.append(f"🔗 Blocks {blocking_count} task{'s' if blocking_count > 1 else ''}")

    # Construct final reason
    if details:
        reason = f"{reason} | {' • '.join(details)}"

    # Metadata for frontend
    metadata = {
        'urgency_label': urgency_label,
        'effort_label': effort_label,
        'strategy_desc': strategy_desc,
        'urgency_score': round(urgency_score, 2),
        'effort_score': round(effort_score, 2),
        'importance_score': importance,
        'dependency_boost': round(dependency_boost, 2)
    }

    return round(score, 2), reason, metadata


def analyze_tasks(tasks: List[Dict], strategy: str = "smart_balance",
                  config: Dict = None, user_preferences: Dict = None) -> Dict[str, Any]:
    """
    Analyze and prioritize a list of tasks with user preferences.

    Args:
        tasks: List of task dictionaries
        strategy: Prioritization strategy
        config: Optional configuration
        user_preferences: User preferences (energy_level, available_hours, work_mode)

    Returns:
        Dictionary with analyzed tasks, metadata, and productivity insights
    """
    if user_preferences is None:
        user_preferences = {}

    if not tasks:
        return {
            'analyzed_tasks': [],
            'strategy_used': strategy,
            'total_tasks': 0,
            'warnings': ['No tasks provided for analysis'],
            'insights': {}
        }

    # Detect circular dependencies
    circular_deps = detect_circular_dependencies(tasks)
    warnings = []

    if circular_deps:
        warnings.append(f"Circular dependencies detected in: {', '.join(circular_deps)}")

    # Get user preferences
    available_hours = user_preferences.get('available_hours', 8)
    energy_level = user_preferences.get('energy_level', 'medium')

    # Score all tasks
    scored_tasks = []
    total_hours = 0

    for task in tasks:
        try:
            score, reason, metadata = score_task(task, strategy, config, tasks, user_preferences)

            # Determine priority level with more granularity
            if score >= 9:
                priority_level = "Critical"
            elif score >= 7:
                priority_level = "High"
            elif score >= 5:
                priority_level = "Medium"
            else:
                priority_level = "Low"

            task_hours = float(task.get('estimated_hours', 0))
            total_hours += task_hours

            scored_tasks.append({
                'task': task,
                'score': score,
                'reason': reason,
                'priority_level': priority_level,
                'metadata': metadata
            })
        except Exception as e:
            warnings.append(f"Error scoring task '{task.get('title', 'Unknown')}': {str(e)}")

    # Sort by score (highest first)
    scored_tasks.sort(key=lambda x: x['score'], reverse=True)

    # Calculate which tasks can be completed today
    cumulative_hours = 0
    tasks_today = 0
    for st in scored_tasks:
        task_hours = float(st['task'].get('estimated_hours', 0))
        if cumulative_hours + task_hours <= available_hours:
            cumulative_hours += task_hours
            tasks_today += 1
            st['can_complete_today'] = True
        else:
            st['can_complete_today'] = False

    # Generate productivity insights
    today = date.today()
    overdue_count = sum(1 for t in tasks if date.fromisoformat(t.get('due_date', str(today))) < today)
    urgent_count = sum(1 for st in scored_tasks if st['score'] >= 7)

    insights = {
        'total_hours_needed': round(total_hours, 1),
        'available_hours': available_hours,
        'tasks_completable_today': tasks_today,
        'hours_completable_today': round(cumulative_hours, 1),
        'overdue_tasks': overdue_count,
        'urgent_tasks': urgent_count,
        'energy_level': energy_level,
        'productivity_ratio': round(cumulative_hours / available_hours * 100, 1) if available_hours > 0 else 0
    }

    # Strategy descriptions
    strategy_descriptions = {
        'fast_wins': 'Optimized for quick completions to build momentum',
        'high_impact': 'Focused on high-value tasks for maximum impact',
        'deadline_driven': 'Prioritized by deadline urgency to prevent overdue tasks',
        'smart_balance': 'Balanced approach considering urgency, importance, and effort'
    }

    return {
        'analyzed_tasks': scored_tasks,
        'strategy_used': strategy,
        'strategy_description': strategy_descriptions.get(strategy, 'Custom strategy'),
        'total_tasks': len(scored_tasks),
        'circular_dependencies': circular_deps,
        'warnings': warnings,
        'insights': insights,
        'user_preferences': user_preferences
    }


def get_top_suggestions(tasks: List[Dict], strategy: str = "smart_balance", limit: int = 3) -> Dict[str, Any]:
    """Get top N task suggestions."""
    analysis = analyze_tasks(tasks, strategy)
    
    return {
        'suggestions': analysis['analyzed_tasks'][:limit],
        'strategy_used': strategy,
        'total_evaluated': analysis['total_tasks']
    }
