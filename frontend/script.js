// Smart Task Analyzer Frontend JavaScript

class TaskAnalyzer {
    constructor() {
        this.tasks = [];
        this.apiBaseUrl = 'http://127.0.0.1:8000/api';
        this.taskIdCounter = 1;
        this.isBackendConnected = false;
        this.currentPage = 'dashboard';
        this.userPreferences = {
            workMode: 'effective',
            availableHours: 8,
            energyLevel: 'medium',
            breakReminders: true
        };
        this.init();
    }

    init() {
        this.bindEvents();
        this.loadTasksFromStorage();
        this.loadPreferencesFromStorage();
        this.updateTasksDisplay();
        this.updateStats();
        this.updateProgress();
        this.updateConnectionStatus('connecting', 'Connecting...');
        this.checkBackendConnection();
    }

    // Navigation
    navigateTo(page) {
        this.currentPage = page;

        // Update nav links
        document.querySelectorAll('.nav-link').forEach(link => {
            link.classList.remove('active');
            if (link.dataset.page === page) {
                link.classList.add('active');
            }
        });

        // Update pages
        document.querySelectorAll('.page').forEach(p => {
            p.classList.remove('active');
        });
        document.getElementById(`page-${page}`).classList.add('active');

        // Update stats when returning to dashboard
        if (page === 'dashboard') {
            this.updateStats();
            this.updateTasksDisplay();
        }
    }

    updateStats() {
        const today = new Date();
        today.setHours(0, 0, 0, 0);
        const threeDaysFromNow = new Date(today.getTime() + 3 * 24 * 60 * 60 * 1000);

        const totalTasks = this.tasks.length;
        const completedTasks = this.tasks.filter(t => t.completed).length;
        const pendingTasks = this.tasks.filter(t => !t.completed);
        const dueSoon = pendingTasks.filter(t => {
            const dueDate = new Date(t.due_date);
            return dueDate <= threeDaysFromNow && dueDate >= today;
        }).length;
        const overdueTasks = pendingTasks.filter(t => new Date(t.due_date) < today).length;

        document.getElementById('totalTasks').textContent = totalTasks;
        document.getElementById('completedTasks').textContent = completedTasks;
        document.getElementById('dueSoon').textContent = dueSoon;
        document.getElementById('overdueTasks').textContent = overdueTasks;
    }

    updateProgress() {
        const totalTasks = this.tasks.length;
        const completedTasks = this.tasks.filter(t => t.completed).length;
        const pendingTasks = this.tasks.filter(t => !t.completed);
        const remainingHours = pendingTasks.reduce((sum, t) => sum + parseFloat(t.estimated_hours || 0), 0);

        const progressPercent = totalTasks > 0 ? Math.round((completedTasks / totalTasks) * 100) : 0;

        const progressFill = document.getElementById('progressFill');
        const progressPercentEl = document.getElementById('progressPercent');
        const completedCount = document.getElementById('completedCount');
        const totalCount = document.getElementById('totalCount');
        const remainingHoursEl = document.getElementById('remainingHours');

        if (progressFill) progressFill.style.width = `${progressPercent}%`;
        if (progressPercentEl) progressPercentEl.textContent = `${progressPercent}%`;
        if (completedCount) completedCount.textContent = completedTasks;
        if (totalCount) totalCount.textContent = totalTasks;
        if (remainingHoursEl) remainingHoursEl.textContent = remainingHours.toFixed(1);
    }

    updateConnectionStatus(status, message) {
        const dot = document.querySelector('.status-dot');
        const text = document.querySelector('.status-text');

        if (dot && text) {
            dot.className = `status-dot ${status}`;
            text.textContent = message;
        }
    }

    async checkBackendConnection() {
        try {
            const response = await fetch(`${this.apiBaseUrl}/tasks/analyze/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    tasks: [],
                    strategy: 'smart_balance'
                })
            });

            if (response.status === 200 || response.status === 400) {
                this.isBackendConnected = true;
                this.updateConnectionStatus('connected', 'Connected');
                this.showToast('Backend connected successfully!', 'success');
            } else {
                throw new Error('Backend not responding');
            }
        } catch (error) {
            this.isBackendConnected = false;
            this.updateConnectionStatus('disconnected', 'Disconnected');
            this.showToast('Backend offline. Please start the Django server.', 'error');
        }
    }

    bindEvents() {
        // Navigation
        document.querySelectorAll('.nav-link').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                this.navigateTo(link.dataset.page);
            });
        });

        // Task form submission
        document.getElementById('taskForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.addTask();
        });

        // Bulk import
        document.getElementById('bulkImportBtn').addEventListener('click', () => {
            this.bulkImportTasks();
        });

        // Analysis button
        document.getElementById('analyzeBtn').addEventListener('click', () => {
            this.analyzeTasks();
        });

        // Work Mode Selection
        document.querySelectorAll('input[name="workMode"]').forEach(radio => {
            radio.addEventListener('change', (e) => {
                this.userPreferences.workMode = e.target.value;
                this.savePreferencesToStorage();
                this.updateModeDescription(e.target.value);
            });
        });

        // Energy Level Selection
        document.querySelectorAll('input[name="energyLevel"]').forEach(radio => {
            radio.addEventListener('change', (e) => {
                this.userPreferences.energyLevel = e.target.value;
                this.savePreferencesToStorage();
            });
        });

        // Available Hours
        const availableHoursInput = document.getElementById('availableHours');
        if (availableHoursInput) {
            availableHoursInput.addEventListener('change', (e) => {
                this.userPreferences.availableHours = parseFloat(e.target.value) || 8;
                this.savePreferencesToStorage();
            });
        }

        // Break Reminders
        const breakRemindersCheckbox = document.getElementById('breakReminders');
        if (breakRemindersCheckbox) {
            breakRemindersCheckbox.addEventListener('change', (e) => {
                this.userPreferences.breakReminders = e.target.checked;
                this.savePreferencesToStorage();
            });
        }
    }

    updateModeDescription(mode) {
        const descriptions = {
            speed: '⚡ Speed Mode - Maximum tasks in minimum time!',
            effective: '🎯 Effective Mode - Focus on what matters most',
            deadline_crisis: '🚨 Deadline Crisis - Urgent tasks first!',
            balanced: '⚖️ Balanced Mode - Smart mix of all factors'
        };
        const descEl = document.getElementById('modeDescription');
        if (descEl) {
            descEl.textContent = descriptions[mode] || 'Select your work mode';
        }
    }

    addTask() {
        const form = document.getElementById('taskForm');
        const formData = new FormData(form);

        const task = {
            id: Date.now(),
            title: formData.get('title'),
            due_date: formData.get('due_date'),
            estimated_hours: parseFloat(formData.get('estimated_hours')),
            importance: parseInt(formData.get('importance')),
            dependencies: this.parseDependencies(formData.get('dependencies'))
        };

        if (this.validateTask(task)) {
            this.tasks.push(task);
            this.saveTasksToStorage();
            this.updateTasksDisplay();
            this.updateStats();
            form.reset();
            document.getElementById('importance').value = 5;
            document.getElementById('importanceValue').textContent = '5';
            this.showToast('Task added successfully!', 'success');
            this.navigateTo('dashboard');
        }
    }

    deleteTask(taskId) {
        this.tasks = this.tasks.filter(t => t.id !== taskId);
        this.saveTasksToStorage();
        this.updateTasksDisplay();
        this.updateStats();
        this.showToast('Task deleted', 'info');
    }

    clearAllTasks() {
        if (confirm('Are you sure you want to delete all tasks?')) {
            this.tasks = [];
            this.saveTasksToStorage();
            this.updateTasksDisplay();
            this.updateStats();
            this.showToast('All tasks cleared', 'info');
        }
    }

    exportTasks() {
        const dataStr = JSON.stringify(this.tasks, null, 2);
        const blob = new Blob([dataStr], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'tasks_export.json';
        a.click();
        URL.revokeObjectURL(url);
        this.showToast('Tasks exported successfully', 'success');
    }

    bulkImportTasks() {
        const bulkInput = document.getElementById('bulkInput').value.trim();

        if (!bulkInput) {
            this.showToast('Please enter JSON data for bulk import', 'warning');
            return;
        }

        try {
            const importedTasks = JSON.parse(bulkInput);

            if (!Array.isArray(importedTasks)) {
                throw new Error('JSON must be an array of tasks');
            }

            let validTasks = 0;
            importedTasks.forEach((task, index) => {
                task.id = Date.now() + index;
                task.dependencies = task.dependencies || [];

                if (this.validateTask(task)) {
                    this.tasks.push(task);
                    validTasks++;
                }
            });

            if (validTasks > 0) {
                this.saveTasksToStorage();
                this.updateTasksDisplay();
                this.updateStats();
                document.getElementById('bulkInput').value = '';
                this.showToast(`Successfully imported ${validTasks} tasks!`, 'success');
                this.navigateTo('dashboard');
            } else {
                this.showToast('No valid tasks found in the import data', 'warning');
            }
        } catch (error) {
            this.showToast(`Invalid JSON format: ${error.message}`, 'error');
        }
    }

    validateTask(task) {
        const errors = [];
        
        if (!task.title || task.title.trim() === '') {
            errors.push('Title is required');
        }
        
        if (!task.due_date) {
            errors.push('Due date is required');
        }
        
        if (!task.estimated_hours || task.estimated_hours <= 0) {
            errors.push('Estimated hours must be greater than 0');
        }
        
        if (!task.importance || task.importance < 1 || task.importance > 10) {
            errors.push('Importance must be between 1 and 10');
        }

        if (errors.length > 0) {
            this.showToast('Validation errors: ' + errors.join(', '), 'error');
            return false;
        }

        return true;
    }

    parseDependencies(dependenciesStr) {
        if (!dependenciesStr || dependenciesStr.trim() === '') {
            return [];
        }

        return dependenciesStr.split(',')
            .map(id => parseInt(id.trim()))
            .filter(id => !isNaN(id));
    }

    updateTasksDisplay() {
        const tasksList = document.getElementById('tasksList');

        if (this.tasks.length === 0) {
            tasksList.innerHTML = `
                <div class="empty-state">
                    <span class="empty-icon">📝</span>
                    <p>No tasks yet. Add your first task to get started!</p>
                </div>
            `;
            return;
        }

        const today = new Date();
        today.setHours(0, 0, 0, 0);

        const tasksHtml = this.tasks.map(task => {
            const dueDate = new Date(task.due_date);
            const isOverdue = !task.completed && dueDate < today;
            const taskClass = task.completed ? 'completed' : (isOverdue ? 'overdue' : '');
            const checkboxClass = task.completed ? 'checked' : '';

            return `
                <div class="task-item ${taskClass}">
                    <div style="display: flex; align-items: center;">
                        <div class="task-checkbox ${checkboxClass}" onclick="app.toggleTaskComplete(${task.id})">
                            ${task.completed ? '✓' : ''}
                        </div>
                        <div class="task-info">
                            <h4>${this.escapeHtml(task.title)}</h4>
                            <div class="task-meta">
                                <span>${isOverdue ? '🔥' : '📅'} ${task.due_date}</span>
                                <span>⏱️ ${task.estimated_hours}h</span>
                                <span>⭐ ${task.importance}/10</span>
                                ${isOverdue ? '<span class="badge badge-danger">Overdue</span>' : ''}
                            </div>
                        </div>
                    </div>
                    <div class="task-actions">
                        <button class="btn-delete" onclick="app.deleteTask(${task.id})">🗑️</button>
                    </div>
                </div>
            `;
        }).join('');

        tasksList.innerHTML = tasksHtml;
    }

    toggleTaskComplete(taskId) {
        const task = this.tasks.find(t => t.id === taskId);
        if (task) {
            task.completed = !task.completed;
            this.saveTasksToStorage();
            this.updateTasksDisplay();
            this.updateStats();
            this.updateProgress();

            if (task.completed) {
                this.showToast(`✅ "${task.title}" completed!`, 'success');
            } else {
                this.showToast(`Task "${task.title}" marked as pending`, 'info');
            }
        }
    }

    async analyzeTasks() {
        const pendingTasks = this.tasks.filter(t => !t.completed);

        if (pendingTasks.length === 0) {
            this.showToast('No pending tasks to analyze. Add tasks or unmark completed ones.', 'warning');
            return;
        }

        if (!this.isBackendConnected) {
            this.showToast('Reconnecting to backend...', 'info');
            await this.checkBackendConnection();
            if (!this.isBackendConnected) {
                return;
            }
        }

        // Get user preferences
        const workModeRadio = document.querySelector('input[name="workMode"]:checked');
        const workMode = workModeRadio ? workModeRadio.value : 'effective';

        const energyRadio = document.querySelector('input[name="energyLevel"]:checked');
        const energyLevel = energyRadio ? energyRadio.value : 'medium';

        const availableHours = parseFloat(document.getElementById('availableHours')?.value) || 8;
        const breakReminders = document.getElementById('breakReminders')?.checked ?? true;

        // Map work mode to strategy
        const strategyMap = {
            'speed': 'fast_wins',
            'effective': 'high_impact',
            'deadline_crisis': 'deadline_driven',
            'balanced': 'smart_balance'
        };
        const strategy = strategyMap[workMode] || 'smart_balance';

        this.showLoading(true);
        this.showToast(`Analyzing with ${workMode.replace('_', ' ')} mode...`, 'info');

        try {
            const response = await fetch(`${this.apiBaseUrl}/tasks/analyze/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    tasks: pendingTasks,
                    strategy: strategy,
                    user_preferences: {
                        available_hours: availableHours,
                        energy_level: energyLevel,
                        break_reminders: breakReminders,
                        work_mode: workMode
                    }
                })
            });

            if (!response.ok) {
                const errorText = await response.text();
                console.error('Backend error:', errorText);
                throw new Error(`Backend error: ${response.status} - ${errorText}`);
            }

            const result = await response.json();
            this.displayEnhancedResults(result, availableHours, energyLevel, breakReminders);
            this.showToast('Analysis complete!', 'success');
        } catch (error) {
            console.error('Analysis error:', error);
            this.isBackendConnected = false;
            this.updateConnectionStatus('disconnected', 'Disconnected');

            let errorMessage = 'Analysis failed';
            if (error.name === 'TypeError' && error.message.includes('fetch')) {
                errorMessage = 'Backend server is offline. Please start Django server.';
            } else if (error.message.includes('500')) {
                errorMessage = 'Internal server error. Check backend logs.';
            } else if (error.message.includes('404')) {
                errorMessage = 'API endpoint not found.';
            } else {
                errorMessage = error.message;
            }

            this.showToast(errorMessage, 'error');
            this.showError(errorMessage);

            setTimeout(() => {
                this.checkBackendConnection();
            }, 3000);
        } finally {
            this.showLoading(false);
        }
    }

    displayEnhancedResults(result, availableHours, energyLevel, breakReminders) {
        const resultsContainer = document.getElementById('results');
        const analyzedTasks = result.analyzed_tasks || result;

        if (!analyzedTasks || analyzedTasks.length === 0) {
            resultsContainer.innerHTML = '<div class="empty-state"><span class="empty-icon">📊</span><p>No results to display</p></div>';
            return;
        }

        // Use backend insights if available, otherwise calculate locally
        const insights = result.insights || {};
        const totalHours = insights.total_hours_needed || analyzedTasks.reduce((sum, item) => sum + parseFloat(item.task?.estimated_hours || 0), 0);
        const urgentTasks = insights.urgent_tasks || analyzedTasks.filter(item => item.score >= 7).length;
        const canComplete = insights.tasks_completable_today || analyzedTasks.filter((item, idx) => {
            const cumHours = analyzedTasks.slice(0, idx + 1).reduce((s, i) => s + parseFloat(i.task?.estimated_hours || 0), 0);
            return cumHours <= availableHours;
        }).length;
        const overdueTasks = insights.overdue_tasks || 0;
        const productivityRatio = insights.productivity_ratio || 0;

        // Energy-based recommendations
        const energyMultiplier = { low: 0.7, medium: 1, high: 1.3 };
        const effectiveHours = availableHours * (energyMultiplier[energyLevel] || 1);

        // Generate recommendations with backend data
        const recommendations = this.generateRecommendations(analyzedTasks, effectiveHours, energyLevel, result.warnings, overdueTasks);

        const html = `
            <!-- Insights Panel -->
            <div class="insights-panel">
                <div class="insights-header">
                    <span style="font-size: 24px;">📊</span>
                    <h3>Productivity Insights</h3>
                    ${result.strategy_description ? `<span class="strategy-badge">${result.strategy_description}</span>` : ''}
                </div>
                <div class="insights-grid">
                    <div class="insight-item">
                        <span class="insight-value">${analyzedTasks.length}</span>
                        <span class="insight-label">Tasks Analyzed</span>
                    </div>
                    <div class="insight-item ${overdueTasks > 0 ? 'overdue' : ''}">
                        <span class="insight-value">${overdueTasks}</span>
                        <span class="insight-label">Overdue</span>
                    </div>
                    <div class="insight-item ${urgentTasks > 0 ? 'urgent' : ''}">
                        <span class="insight-value">${urgentTasks}</span>
                        <span class="insight-label">Urgent</span>
                    </div>
                    <div class="insight-item">
                        <span class="insight-value">${canComplete}</span>
                        <span class="insight-label">Can Complete Today</span>
                    </div>
                    <div class="insight-item">
                        <span class="insight-value">${totalHours.toFixed(1)}h</span>
                        <span class="insight-label">Total Work</span>
                    </div>
                    <div class="insight-item">
                        <span class="insight-value">${productivityRatio.toFixed(0)}%</span>
                        <span class="insight-label">Productivity</span>
                    </div>
                </div>
            </div>

            <!-- Recommendations -->
            ${recommendations.length > 0 ? `
                <div class="recommendations">
                    <h3 style="margin-bottom: 16px; color: var(--text-primary);">💡 Smart Recommendations</h3>
                    ${recommendations.map(rec => `
                        <div class="recommendation-item">
                            <span class="recommendation-icon">${rec.icon}</span>
                            <div class="recommendation-content">
                                <h4>${rec.title}</h4>
                                <p>${rec.description}</p>
                            </div>
                        </div>
                    `).join('')}
                </div>
            ` : ''}

            <!-- Prioritized Tasks -->
            <div class="card" style="margin-top: 24px;">
                <div class="card-header">
                    <h2>📋 Prioritized Task Order</h2>
                    <span class="badge badge-info">${result.strategy_used || 'smart_balance'}</span>
                </div>
                ${analyzedTasks.map((item, index) => {
                    const task = item.task || item;
                    const score = item.score || 0;
                    const reason = item.reason || 'Prioritized based on analysis';
                    const priorityLevel = item.priority_level || this.getPriorityLevel(score);
                    const priorityClass = priorityLevel.toLowerCase();

                    return `
                        <div class="result-item ${priorityClass}-priority">
                            <div style="display: flex; align-items: center; margin-bottom: 12px; flex-wrap: wrap; gap: 8px;">
                                <span class="result-rank">${index + 1}</span>
                                <span class="result-title" style="flex: 1; min-width: 200px;">${this.escapeHtml(task.title)}</span>
                                <span class="priority-badge ${priorityClass}">${priorityLevel}</span>
                                <span class="result-score">Score: ${score.toFixed(2)}</span>
                            </div>
                            <div class="result-details">
                                <span class="time-badge">📅 ${task.due_date}</span>
                                <span class="time-badge">⏱️ ${task.estimated_hours}h</span>
                                <span class="time-badge">⭐ ${task.importance}/10</span>
                            </div>
                            <div class="result-reason">${this.escapeHtml(reason)}</div>
                        </div>
                    `;
                }).join('')}
            </div>
        `;

        resultsContainer.innerHTML = html;
    }

    generateRecommendations(tasks, effectiveHours, energyLevel, warnings, overdueTasks = 0) {
        const recommendations = [];
        const totalHours = tasks.reduce((sum, item) => sum + parseFloat(item.task?.estimated_hours || 0), 0);
        const urgentCount = tasks.filter(item => item.score >= 7).length;
        const criticalCount = tasks.filter(item => item.score >= 9).length;

        // Overdue tasks warning (highest priority)
        if (overdueTasks > 0) {
            recommendations.push({
                icon: '⚠️',
                title: 'Overdue Tasks Detected!',
                description: `You have ${overdueTasks} overdue task${overdueTasks > 1 ? 's' : ''}. These should be your immediate focus or consider renegotiating deadlines.`
            });
        }

        // Critical tasks alert
        if (criticalCount > 0) {
            recommendations.push({
                icon: '🔥',
                title: 'Critical Tasks Require Attention',
                description: `${criticalCount} task${criticalCount > 1 ? 's are' : ' is'} marked as critical. Complete these before moving to other work.`
            });
        }

        // Time management recommendation
        if (totalHours > effectiveHours) {
            const focusTasks = Math.max(1, Math.ceil(effectiveHours / 2));
            recommendations.push({
                icon: '⏰',
                title: 'Focus on Top Priorities',
                description: `You have ${totalHours.toFixed(1)} hours of work but ${effectiveHours.toFixed(1)} effective hours available. Focus on the top ${focusTasks} task${focusTasks > 1 ? 's' : ''} first.`
            });
        } else if (totalHours <= effectiveHours && tasks.length > 0) {
            recommendations.push({
                icon: '✅',
                title: 'Achievable Workload',
                description: `Great news! You can complete all ${tasks.length} tasks today with time to spare.`
            });
        }

        // Energy-based recommendation
        if (energyLevel === 'low') {
            recommendations.push({
                icon: '🔋',
                title: 'Start with Quick Wins',
                description: 'With lower energy, start with shorter tasks to build momentum. Consider tackling complex tasks after a break or tomorrow.'
            });
        } else if (energyLevel === 'high') {
            recommendations.push({
                icon: '🚀',
                title: 'Tackle Complex Tasks Now',
                description: 'Your high energy is perfect for complex, important tasks. Front-load your hardest work while you\'re at peak performance!'
            });
        }

        // Multiple urgent tasks warning
        if (urgentCount >= 3) {
            recommendations.push({
                icon: '🚨',
                title: 'Multiple Urgent Tasks',
                description: `You have ${urgentCount} urgent tasks. Consider delegating, batching similar tasks, or renegotiating deadlines if possible.`
            });
        }

        // Break reminder for long work sessions
        if (totalHours > 4) {
            recommendations.push({
                icon: '☕',
                title: 'Schedule Breaks',
                description: 'For optimal productivity, take a 10-15 minute break every 90 minutes. Stay hydrated and stretch!'
            });
        }

        // Warnings from backend (circular dependencies, etc.)
        if (warnings && warnings.length > 0) {
            warnings.forEach(warning => {
                if (warning.includes('Circular')) {
                    recommendations.push({
                        icon: '🔄',
                        title: 'Dependency Issue Detected',
                        description: warning
                    });
                }
            });
        }

        return recommendations;
    }

    getPriorityLevel(score) {
        if (score >= 9) return 'Critical';
        if (score >= 7) return 'High';
        if (score >= 5) return 'Medium';
        return 'Low';
    }

    displayResults(results) {
        const resultsContainer = document.getElementById('results');

        if (!results || results.length === 0) {
            resultsContainer.innerHTML = '<div class="empty-state"><span class="empty-icon">📊</span><p>No results to display</p></div>';
            return;
        }

        const resultsHtml = `
            <div class="results-container">
                ${results.map((item, index) => {
                    const task = item.task || item;
                    const score = item.score || 0;
                    const reason = item.reason || 'No explanation provided';
                    const priorityClass = this.getPriorityClass(score);

                    return `
                        <div class="result-item ${priorityClass}">
                            <div style="display: flex; align-items: center; margin-bottom: 8px;">
                                <span class="result-rank">${index + 1}</span>
                                <span class="result-title">${this.escapeHtml(task.title)}</span>
                                <span class="result-score">Score: ${score.toFixed(2)}</span>
                            </div>
                            <div class="result-details">
                                <span>📅 ${task.due_date}</span>
                                <span>⏱️ ${task.estimated_hours}h</span>
                                <span>⭐ ${task.importance}/10</span>
                            </div>
                            <div class="result-reason">${this.escapeHtml(reason)}</div>
                        </div>
                    `;
                }).join('')}
            </div>
        `;

        resultsContainer.innerHTML = resultsHtml;
    }

    getPriorityClass(score) {
        if (score >= 8) return 'high-priority';
        if (score >= 5) return 'medium-priority';
        return 'low-priority';
    }

    showLoading(show) {
        const loading = document.getElementById('loading');
        if (loading) {
            if (show) {
                loading.classList.remove('hidden');
            } else {
                loading.classList.add('hidden');
            }
        }
    }

    showError(message) {
        const errorDiv = document.getElementById('errorMessage');
        if (errorDiv) {
            errorDiv.textContent = message;
            errorDiv.classList.remove('hidden');

            setTimeout(() => {
                errorDiv.classList.add('hidden');
            }, 5000);
        }
    }

    showToast(message, type = 'info') {
        const container = document.getElementById('toast-container');
        if (!container) return;

        const toast = document.createElement('div');
        toast.className = `toast ${type}`;

        const icons = {
            'success': '✓',
            'error': '✕',
            'warning': '⚠',
            'info': 'ℹ'
        };

        toast.innerHTML = `
            <span style="font-size: 18px;">${icons[type] || icons.info}</span>
            <span>${message}</span>
        `;

        container.appendChild(toast);

        // Auto-remove after 4 seconds
        setTimeout(() => {
            if (toast.parentElement) {
                toast.style.animation = 'slideIn 0.3s ease-out reverse';
                setTimeout(() => {
                    if (toast.parentElement) {
                        container.removeChild(toast);
                    }
                }, 300);
            }
        }, 4000);
    }

    saveTasksToStorage() {
        localStorage.setItem('taskAnalyzerTasks', JSON.stringify(this.tasks));
    }

    loadTasksFromStorage() {
        const stored = localStorage.getItem('taskAnalyzerTasks');
        if (stored) {
            try {
                this.tasks = JSON.parse(stored);
                // Ensure completed field exists for older tasks
                this.tasks = this.tasks.map(t => ({ ...t, completed: t.completed || false }));
            } catch (error) {
                console.error('Error loading tasks from storage:', error);
                this.tasks = [];
            }
        }
    }

    savePreferencesToStorage() {
        localStorage.setItem('taskAnalyzerPreferences', JSON.stringify(this.userPreferences));
    }

    loadPreferencesFromStorage() {
        const stored = localStorage.getItem('taskAnalyzerPreferences');
        if (stored) {
            try {
                this.userPreferences = { ...this.userPreferences, ...JSON.parse(stored) };

                // Apply loaded preferences to UI
                const modeRadio = document.querySelector(`input[name="workMode"][value="${this.userPreferences.workMode}"]`);
                if (modeRadio) modeRadio.checked = true;

                const energyRadio = document.querySelector(`input[name="energyLevel"][value="${this.userPreferences.energyLevel}"]`);
                if (energyRadio) energyRadio.checked = true;

                const hoursInput = document.getElementById('availableHours');
                if (hoursInput) hoursInput.value = this.userPreferences.availableHours;

                const breakCheckbox = document.getElementById('breakReminders');
                if (breakCheckbox) breakCheckbox.checked = this.userPreferences.breakReminders;

                this.updateModeDescription(this.userPreferences.workMode);
            } catch (error) {
                console.error('Error loading preferences from storage:', error);
            }
        }
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Global app instance
let app;

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    app = new TaskAnalyzer();

    // Update importance value display
    const importanceSlider = document.getElementById('importance');
    const importanceValue = document.getElementById('importanceValue');
    if (importanceSlider && importanceValue) {
        importanceSlider.addEventListener('input', () => {
            importanceValue.textContent = importanceSlider.value;
        });
    }
});
