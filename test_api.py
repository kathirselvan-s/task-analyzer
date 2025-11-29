#!/usr/bin/env python3
"""
Enhanced test script to verify the Smart Task Analyzer API with comprehensive error handling
"""

import requests
import json
import time
import sys

def test_backend_connection():
    """Test basic backend connectivity"""
    print("🔍 TESTING BACKEND CONNECTION...")

    try:
        response = requests.get("http://127.0.0.1:8000/admin/", timeout=5)
        if response.status_code in [200, 302, 404]:  # Any response means server is running
            print("✅ Backend server is ONLINE")
            return True
        else:
            print(f"⚠️ Backend responded with status: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Backend server is OFFLINE")
        print("   Please start Django server: python manage.py runserver 127.0.0.1:8000")
        return False
    except Exception as e:
        print(f"❌ Connection test failed: {e}")
        return False

def test_api_endpoint():
    """Test the task analysis API endpoint"""
    print("\n🧪 TESTING API ENDPOINT...")

    # API endpoint
    url = "http://127.0.0.1:8000/api/tasks/analyze/"

    # Test data with comprehensive task structure
    test_data = {
        "tasks": [
            {
                "id": 1,
                "title": "Neural Task Alpha",
                "due_date": "2024-12-01",
                "estimated_hours": 2.5,
                "importance": 8,
                "dependencies": []
            },
            {
                "id": 2,
                "title": "Cyberpunk Task Beta",
                "due_date": "2024-12-05",
                "estimated_hours": 1.0,
                "importance": 5,
                "dependencies": [1]
            },
            {
                "id": 3,
                "title": "Priority Task Gamma",
                "due_date": "2024-11-30",
                "estimated_hours": 4.0,
                "importance": 9,
                "dependencies": []
            }
        ],
        "strategy": "smart_balance"
    }

    try:
        print(f"📡 Sending POST request to: {url}")
        print(f"📊 Test data: {len(test_data['tasks'])} tasks, strategy: {test_data['strategy']}")

        response = requests.post(
            url,
            headers={
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            json=test_data,
            timeout=15
        )

        print(f"📈 Response Status: {response.status_code}")
        print(f"📋 Response Headers: {dict(response.headers)}")

        if response.status_code == 200:
            result = response.json()
            print("✅ API ANALYSIS SUCCESSFUL!")
            print("🧠 Neural Analysis Results:")

            if 'analyzed_tasks' in result:
                for i, task in enumerate(result['analyzed_tasks'], 1):
                    score = task.get('priority_score', 'N/A')
                    title = task.get('title', 'Unknown')
                    print(f"  #{i} {title} - Score: {score}")
            elif isinstance(result, list):
                for i, task in enumerate(result, 1):
                    score = task.get('priority_score', task.get('score', 'N/A'))
                    title = task.get('title', task.get('task', {}).get('title', 'Unknown'))
                    print(f"  #{i} {title} - Score: {score}")
            else:
                print(f"  Raw result: {json.dumps(result, indent=2)}")

            return True

        else:
            print(f"❌ API TEST FAILED!")
            print(f"   Status: {response.status_code}")
            print(f"   Response: {response.text[:500]}...")
            return False

    except requests.exceptions.ConnectionError:
        print("❌ CONNECTION FAILED!")
        print("   Backend server is not responding")
        return False

    except requests.exceptions.Timeout:
        print("❌ REQUEST TIMEOUT!")
        print("   Backend is taking too long to respond")
        return False

    except json.JSONDecodeError as e:
        print(f"❌ JSON DECODE ERROR: {e}")
        print(f"   Response text: {response.text[:200]}...")
        return False

    except Exception as e:
        print(f"❌ UNEXPECTED ERROR: {e}")
        return False

def test_frontend_access():
    """Test frontend accessibility"""
    print("\n🌐 TESTING FRONTEND ACCESS...")

    try:
        response = requests.get("http://localhost:8080", timeout=5)
        if response.status_code == 200:
            print("✅ Frontend server is ACCESSIBLE")
            if "Cyberpunk Edition" in response.text:
                print("✅ Cyberpunk theme is ACTIVE")
            else:
                print("⚠️ Cyberpunk theme may not be loaded")
            return True
        else:
            print(f"⚠️ Frontend responded with status: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Frontend server is OFFLINE")
        print("   Please start frontend: python -m http.server 8080")
        return False
    except Exception as e:
        print(f"❌ Frontend test failed: {e}")
        return False

def main():
    """Run comprehensive system tests"""
    print("🚀 SMART TASK ANALYZER - COMPREHENSIVE SYSTEM TEST")
    print("=" * 60)

    # Test results
    backend_ok = test_backend_connection()
    time.sleep(1)

    api_ok = False
    if backend_ok:
        api_ok = test_api_endpoint()
        time.sleep(1)

    frontend_ok = test_frontend_access()

    print("\n" + "=" * 60)
    print("📊 FINAL TEST RESULTS:")
    print(f"   Backend Connection: {'✅ PASS' if backend_ok else '❌ FAIL'}")
    print(f"   API Functionality:  {'✅ PASS' if api_ok else '❌ FAIL'}")
    print(f"   Frontend Access:    {'✅ PASS' if frontend_ok else '❌ FAIL'}")

    if backend_ok and api_ok and frontend_ok:
        print("\n🎉 ALL SYSTEMS OPERATIONAL!")
        print("   Your Cyberpunk Task Analyzer is ready to use!")
        print("   Open: http://localhost:8080")
    else:
        print("\n⚠️ SOME SYSTEMS NEED ATTENTION")
        if not backend_ok:
            print("   → Start backend: cd task-analyzer/backend && python manage.py runserver")
        if not frontend_ok:
            print("   → Start frontend: cd task-analyzer/frontend && python -m http.server 8080")

    return 0 if (backend_ok and api_ok and frontend_ok) else 1

if __name__ == "__main__":
    sys.exit(main())
