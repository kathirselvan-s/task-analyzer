# 📚 Smart Task Analyzer v2.0 - Documentation

## 🎯 Quick Reference Guide

### Work Modes at a Glance

| Mode | Icon | Best For | Key Focus |
|------|------|----------|-----------|
| **Speed Mode** | ⚡ | Building momentum | Quick tasks first |
| **Effective Mode** | 🎯 | High-value work | Important tasks first |
| **Deadline Crisis** | 🚨 | Urgent situations | Due dates first |
| **Balanced** | ⚖️ | Daily productivity | All factors considered |

---

## 🚀 How to Use

### Step 1: Add Tasks
Navigate to **Add Task** page and fill in:
- **Title**: What needs to be done
- **Due Date**: Deadline
- **Estimated Hours**: Time required
- **Importance**: 1-10 scale

### Step 2: Configure Your Work Style
Go to **Analyze** page:
1. **Select Work Mode** based on your current needs
2. **Set Available Hours** - How much time you have today
3. **Choose Energy Level** - Low 😴, Medium 😊, or High 🔥

### Step 3: Analyze & Execute
Click **Analyze & Prioritize Tasks** to get:
- 📊 Productivity insights
- 💡 Smart recommendations
- 📋 Prioritized task order

### Step 4: Track Progress
- ✅ Check off completed tasks
- 📈 Watch your progress bar fill up
- 🎉 Celebrate completing your list!

---

## 🧮 Algorithm Details

### Score Formula
```
Score = (Urgency × W₁) + (Importance × W₂) + (Effort × W₃) + (Dependencies × W₄)
```

### Weight Distribution

| Mode | Urgency | Importance | Effort | Dependencies |
|------|---------|------------|--------|--------------|
| Speed | 25% | 15% | **50%** | 10% |
| Effective | 15% | **55%** | 10% | 20% |
| Deadline Crisis | **65%** | 15% | 10% | 10% |
| Balanced | 30% | 30% | 20% | 20% |

### Energy Modifiers
- **Low Energy** (😴): Shorter tasks get +30% boost
- **Medium Energy** (😊): Normal scoring
- **High Energy** (🔥): Can handle 30% longer tasks

### Priority Levels
- **Critical** (9-10): Requires immediate attention
- **High** (7-8.9): Should be done soon
- **Medium** (5-6.9): Can wait if needed
- **Low** (0-4.9): Do when time permits

---

## 📡 API Reference

### POST /api/tasks/analyze/

**Request:**
```json
{
  "tasks": [
    {
      "id": 1,
      "title": "Complete report",
      "due_date": "2025-12-01",
      "estimated_hours": 4,
      "importance": 8
    }
  ],
  "strategy": "high_impact",
  "user_preferences": {
    "available_hours": 8,
    "energy_level": "high",
    "work_mode": "effective"
  }
}
```

**Response includes:**
- `analyzed_tasks`: Prioritized task list with scores
- `insights`: Productivity statistics
- `warnings`: Any issues detected

---

## 💾 Data Storage

| Data | Location | Persistence |
|------|----------|-------------|
| Tasks | localStorage | Browser session |
| Preferences | localStorage | Browser session |
| Analysis | Memory | Per request |

---

## 🐛 Troubleshooting

### Connection Issues
1. Verify backend is running: `http://127.0.0.1:8000/`
2. Check browser console for errors
3. Restart backend: `python manage.py runserver 127.0.0.1:8000`

### UI Not Updating
1. Hard refresh: `Ctrl + F5`
2. Clear localStorage in Settings

### Analysis Fails
- Ensure all required fields are filled
- Check date format: `YYYY-MM-DD`
- Verify estimated hours > 0

---

## 📝 Changelog

### v2.0 (Current)
- ✅ Work Mode selection (Speed/Effective/Crisis/Balanced)
- ✅ Energy level preferences
- ✅ Task completion tracking with checkboxes
- ✅ Visual progress bar
- ✅ Smart AI recommendations
- ✅ Productivity insights panel
- ✅ Enhanced algorithm with user preferences
- ✅ Clean, light theme UI

### v1.0
- Basic task analysis
- Four prioritization strategies
- Dark cyberpunk theme

---

## 📞 Quick Commands

```bash
# Start Backend
cd task-analyzer/backend && python manage.py runserver 127.0.0.1:8000

# Start Frontend  
cd task-analyzer/frontend && python -m http.server 8080

# Open App
http://localhost:8080
```

