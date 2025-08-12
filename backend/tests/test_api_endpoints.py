#!/usr/bin/env python3
"""
Test script for Talktor API endpoints
"""
import requests
import json
import time
from datetime import datetime

# API base URL
BASE_URL = "http://localhost:8000"
API_V1_URL = f"{BASE_URL}/api/v1"

# Test user ID
TEST_USER_ID = "test_user_123"

def print_section(title):
    """Print a section header"""
    print(f"\n{'='*60}")
    print(f"🧪 {title}")
    print(f"{'='*60}")

def print_response(response, description=""):
    """Print response details"""
    print(f"\n📡 {description}")
    print(f"Status: {response.status_code}")
    if response.headers.get('content-type', '').startswith('application/json'):
        try:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2, default=str)}")
        except:
            print(f"Response: {response.text}")
    else:
        print(f"Response: {response.text}")

def test_root_endpoints():
    """Test root and health endpoints"""
    print_section("ROOT AND HEALTH ENDPOINTS")
    
    # Test root endpoint
    response = requests.get(f"{BASE_URL}/")
    print_response(response, "GET /")
    
    # Test health endpoint
    response = requests.get(f"{BASE_URL}/health")
    print_response(response, "GET /health")
    
    # Test API info endpoint
    response = requests.get(f"{API_V1_URL}")
    print_response(response, "GET /api/v1")

def test_sessions_endpoints():
    """Test session endpoints"""
    print_section("SESSIONS ENDPOINTS")
    
    # Test health check
    response = requests.get(f"{API_V1_URL}/sessions/health")
    print_response(response, "GET /api/v1/sessions/health")
    
    # Test create session
    session_data = {
        "user_id": TEST_USER_ID,
        "agent_type": "realtime",
        "mode": "free_topic",
        "topic": "Travel and Tourism"
    }
    
    response = requests.post(
        f"{API_V1_URL}/sessions/",
        json=session_data,
        headers={"X-User-ID": TEST_USER_ID}
    )
    print_response(response, "POST /api/v1/sessions/")
    
    if response.status_code == 200:
        session_id = response.json().get("session_id")
        print(f"✅ Created session: {session_id}")
        
        # Test get session
        response = requests.get(
            f"{API_V1_URL}/sessions/{session_id}",
            headers={"X-User-ID": TEST_USER_ID}
        )
        print_response(response, f"GET /api/v1/sessions/{session_id}")
        
        return session_id
    
    return None

def test_conversations_endpoints(session_id=None):
    """Test conversation endpoints"""
    print_section("CONVERSATIONS ENDPOINTS")
    
    if not session_id:
        # Test start conversation
        conversation_data = {
            "user_id": TEST_USER_ID
        }
        
        response = requests.post(
            f"{API_V1_URL}/conversations/start",
            json=conversation_data
        )
        print_response(response, "POST /api/v1/conversations/start")
        
        if response.status_code == 200:
            session_id = response.json().get("session_id")
            print(f"✅ Started conversation: {session_id}")
    
    if session_id:
        # Test get conversation details
        response = requests.get(
            f"{API_V1_URL}/conversations/{session_id}",
            headers={"X-User-ID": TEST_USER_ID}
        )
        print_response(response, f"GET /api/v1/conversations/{session_id}")
        
        # Test get transcripts
        response = requests.get(
            f"{API_V1_URL}/conversations/{session_id}/transcripts",
            headers={"X-User-ID": TEST_USER_ID}
        )
        print_response(response, f"GET /api/v1/conversations/{session_id}/transcripts")
        
        return session_id
    
    return None

def test_feedback_endpoints(session_id):
    """Test feedback endpoints"""
    print_section("FEEDBACK ENDPOINTS")
    
    if not session_id:
        print("❌ No session ID provided for feedback tests")
        return
    
    # Test get feedback
    response = requests.get(
        f"{API_V1_URL}/feedback/{session_id}",
        headers={"X-User-ID": TEST_USER_ID}
    )
    print_response(response, f"GET /api/v1/feedback/{session_id}")
    
    # Test get feedback summary
    response = requests.get(
        f"{API_V1_URL}/feedback/{session_id}/summary",
        headers={"X-User-ID": TEST_USER_ID}
    )
    print_response(response, f"GET /api/v1/feedback/{session_id}/summary")

def test_users_endpoints():
    """Test user endpoints"""
    print_section("USERS ENDPOINTS")
    
    # Test get user sessions
    response = requests.get(
        f"{API_V1_URL}/users/{TEST_USER_ID}/sessions",
        headers={"X-User-ID": TEST_USER_ID}
    )
    print_response(response, f"GET /api/v1/users/{TEST_USER_ID}/sessions")
    
    # Test get user progress
    response = requests.get(
        f"{API_V1_URL}/users/{TEST_USER_ID}/progress",
        headers={"X-User-ID": TEST_USER_ID}
    )
    print_response(response, f"GET /api/v1/users/{TEST_USER_ID}/progress")
    
    # Test get user stats
    response = requests.get(
        f"{API_V1_URL}/users/{TEST_USER_ID}/stats",
        headers={"X-User-ID": TEST_USER_ID}
    )
    print_response(response, f"GET /api/v1/users/{TEST_USER_ID}/stats")

def main():
    """Run all API tests"""
    print(f"🚀 Starting Talktor API Tests")
    print(f"Base URL: {BASE_URL}")
    print(f"Test User: {TEST_USER_ID}")
    print(f"Time: {datetime.now()}")
    
    try:
        # Test root endpoints
        test_root_endpoints()
        
        # Test sessions
        session_id = test_sessions_endpoints()
        
        # Test conversations
        if not session_id:
            session_id = test_conversations_endpoints()
        else:
            test_conversations_endpoints(session_id)
        
        # Test feedback
        test_feedback_endpoints(session_id)
        
        # Test users
        test_users_endpoints()
        
        print_section("TEST SUMMARY")
        print("✅ All API endpoint tests completed!")
        print(f"📊 Check the responses above for detailed results")
        
    except requests.exceptions.ConnectionError:
        print("❌ Connection Error: Make sure the API server is running on http://localhost:8000")
    except Exception as e:
        print(f"❌ Error during testing: {str(e)}")

if __name__ == "__main__":
    main()
