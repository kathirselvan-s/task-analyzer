"""
Task models for the Smart Task Analyzer application.
"""
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone


class Task(models.Model):
    """
    Task model representing a single task with all required fields for analysis.
    """
    title = models.CharField(
        max_length=200,
        help_text="The title/name of the task"
    )
    
    due_date = models.DateField(
        help_text="When the task is due"
    )
    
    estimated_hours = models.FloatField(
        validators=[MinValueValidator(0.1)],
        help_text="Estimated time to complete the task in hours"
    )
    
    importance = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        help_text="Importance level from 1 (low) to 10 (high)"
    )
    
    dependencies = models.ManyToManyField(
        'self',
        blank=True,
        symmetrical=False,
        related_name='dependents',
        help_text="Tasks that must be completed before this task"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Task"
        verbose_name_plural = "Tasks"
    
    def __str__(self):
        return f"{self.title} (Due: {self.due_date})"
    
    @property
    def is_overdue(self):
        """Check if the task is overdue."""
        return self.due_date < timezone.now().date()
    
    @property
    def days_until_due(self):
        """Calculate days until due date (negative if overdue)."""
        delta = self.due_date - timezone.now().date()
        return delta.days
    
    @property
    def dependency_count(self):
        """Get the number of dependencies."""
        return self.dependencies.count()
    
    @property
    def dependent_count(self):
        """Get the number of tasks that depend on this task."""
        return self.dependents.count()
    
    def get_all_dependencies(self):
        """Get all dependencies recursively (for circular dependency detection)."""
        visited = set()
        dependencies = set()
        
        def _get_deps(task):
            if task.id in visited:
                return
            visited.add(task.id)
            
            for dep in task.dependencies.all():
                dependencies.add(dep)
                _get_deps(dep)
        
        _get_deps(self)
        return dependencies
    
    def has_circular_dependency(self):
        """Check if this task has circular dependencies."""
        try:
            all_deps = self.get_all_dependencies()
            return self in all_deps
        except RecursionError:
            return True
