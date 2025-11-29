"""
Serializers for the Task model and API responses.
"""
from rest_framework import serializers
from .models import Task


class TaskSerializer(serializers.ModelSerializer):
    """
    Serializer for Task model with dependency handling.
    """
    dependencies = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Task.objects.all(),
        required=False
    )
    
    # Read-only fields for additional information
    is_overdue = serializers.ReadOnlyField()
    days_until_due = serializers.ReadOnlyField()
    dependency_count = serializers.ReadOnlyField()
    dependent_count = serializers.ReadOnlyField()
    
    class Meta:
        model = Task
        fields = [
            'id',
            'title',
            'due_date',
            'estimated_hours',
            'importance',
            'dependencies',
            'is_overdue',
            'days_until_due',
            'dependency_count',
            'dependent_count',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def validate_estimated_hours(self, value):
        """Validate that estimated hours is positive."""
        if value <= 0:
            raise serializers.ValidationError("Estimated hours must be greater than 0")
        return value
    
    def validate_importance(self, value):
        """Validate that importance is between 1 and 10."""
        if not (1 <= value <= 10):
            raise serializers.ValidationError("Importance must be between 1 and 10")
        return value
    
    def validate(self, data):
        """Validate the entire task data."""
        # Check for circular dependencies if this is an update
        if self.instance:
            dependencies = data.get('dependencies', [])
            if self.instance in dependencies:
                raise serializers.ValidationError(
                    "A task cannot depend on itself"
                )
        
        return data


class TaskAnalysisRequestSerializer(serializers.Serializer):
    """
    Serializer for task analysis requests.
    """
    STRATEGY_CHOICES = [
        ('smart_balance', 'Smart Balance'),
        ('fast_wins', 'Fast Wins'),
        ('high_impact', 'High Impact'),
        ('deadline_driven', 'Deadline Driven'),
    ]
    
    tasks = TaskSerializer(many=True)
    strategy = serializers.ChoiceField(
        choices=STRATEGY_CHOICES,
        default='smart_balance'
    )
    config = serializers.DictField(required=False, default=dict)


class TaskAnalysisResultSerializer(serializers.Serializer):
    """
    Serializer for task analysis results.
    """
    task = TaskSerializer()
    score = serializers.FloatField()
    reason = serializers.CharField()
    priority_level = serializers.CharField()


class TaskAnalysisResponseSerializer(serializers.Serializer):
    """
    Serializer for the complete analysis response.
    """
    analyzed_tasks = TaskAnalysisResultSerializer(many=True)
    strategy_used = serializers.CharField()
    total_tasks = serializers.IntegerField()
    circular_dependencies = serializers.ListField(
        child=serializers.CharField(),
        required=False
    )
    warnings = serializers.ListField(
        child=serializers.CharField(),
        required=False
    )


class TaskSuggestionResponseSerializer(serializers.Serializer):
    """
    Serializer for task suggestion responses.
    """
    suggestions = TaskAnalysisResultSerializer(many=True)
    strategy_used = serializers.CharField()
    total_evaluated = serializers.IntegerField()
