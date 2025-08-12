#!/usr/bin/env python3
"""
Test script for Talktor API endpoints - Updated version
Tests all implemented endpoints with proper session ID handling
"""

import requests
import json
import time
from typing import Dict, Any

# Configuration
BASE_URL = "http://localhost:8000"
TEST_USER_ID = "test_user_123"

def make_request(method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
    """Make HTTP request with error handling"""
    url = f"{BASE_URL}{endpoint}"
    headers = kwargs.get('headers', {})
    headers['X-User-ID'] = TEST_USER_ID
    kwargs['headers'] = headers
    
    try:
        response = requests.request(method, url, **kwargs)
        print(f"🌐 {method} {endpoint} -> {response.status_code}")
        
        if response.status_code >= 400:
            print(f"❌ Error: {response.text}")
            return {"error": response.text, "status_code": response.status_code}
        
        return response.json() if response.text else {}
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return {"error": str(e)}

def test_basic_endpoints():
    """Test basic API endpoints"""
    print("🔍 Testing basic endpoints...")
    
    # Test root endpoint
    result = make_request("GET", "/")
    print(f"✅ Root: {result.get('message', 'No message')}")
    
    # Test health endpoint
    result = make_request("GET", "/health")
    print(f"✅ Health: {result.get('status', 'No status')}")
    
    # Test API v1 info
    result = make_request("GET", "/api/v1")
    print(f"✅ API v1: {result.get('message', 'No message')}")

def test_session_management():
    """Test session creation and management"""
    print("\n📝 Testing session management...")
    
    # Create a new session
    session_data = {
        "user_id": TEST_USER_ID,
        "agent_type": "realtime",
        "conversation_mode": "voice",
        "language": "en"
    }
    
    result = make_request("POST", "/api/v1/sessions/", json=session_data)
    if "error" in result:
        print("❌ Failed to create session")
        return None
    
    session_id = result.get("session_id")
    print(f"✅ Created session: {session_id}")
    
    # Get session details
    result = make_request("GET", f"/api/v1/sessions/{session_id}")
    if "error" not in result:
        print(f"✅ Retrieved session: {result.get('session_id', 'Unknown')}")
    
    return session_id

def test_conversation_endpoints(session_id: str):
    """Test conversation-related endpoints"""
    print(f"\n💬 Testing conversation endpoints with session: {session_id}")
    
    # Start conversation
    start_data = {
        "user_id": TEST_USER_ID,
        "session_id": session_id
    }
    result = make_request("POST", f"/api/v1/conversations/start", json=start_data)
    if result and "error" not in result:
        print(f"✅ Started conversation: {result.get('message', 'Started')}")
    
    # Get conversation details (this will likely be empty for new session)
    result = make_request("GET", f"/api/v1/conversations/{session_id}")
    if result and "error" not in result:
        print(f"✅ Got conversation details: {len(result.get('messages', []))} messages")
    
    # Get transcripts (this will likely be empty for new session)
    result = make_request("GET", f"/api/v1/conversations/{session_id}/transcripts")
    if result and "error" not in result:
        print(f"✅ Got transcripts: {len(result)} transcripts")

def test_feedback_endpoints(session_id: str):
    """Test feedback-related endpoints"""
    print(f"\n📊 Testing feedback endpoints with session: {session_id}")
    
    # Get session feedback (likely empty for new session)
    result = make_request("GET", f"/api/v1/feedback/{session_id}")
    if result and "error" not in result:
        print(f"✅ Got feedback: {result.get('message', 'No feedback available')}")
    
    # Get feedback summary (likely empty for new session)
    result = make_request("GET", f"/api/v1/feedback/{session_id}/summary")
    if result and "error" not in result:
        print(f"✅ Got feedback summary: {result.get('message', 'No feedback available')}")
    
    # Generate feedback (this should work)
    generate_data = {
        "session_id": session_id,
        "force_generation": True
    }
    result = make_request("POST", f"/api/v1/feedback/{session_id}/generate", json=generate_data)
    if result and "error" not in result:
        print(f"✅ Generated feedback: {result.get('message', 'Generated')}")

def test_user_endpoints():
    """Test user-related endpoints"""
    print(f"\n👤 Testing user endpoints for user: {TEST_USER_ID}")
    
    # Get user sessions
    result = make_request("GET", f"/api/v1/users/{TEST_USER_ID}/sessions")
    if "error" not in result:
        sessions = result.get('sessions', [])
        total = result.get('total', 0)
        print(f"✅ Got user sessions: {len(sessions)} sessions (total: {total})")
    
    # Get user progress
    result = make_request("GET", f"/api/v1/users/{TEST_USER_ID}/progress")
    if "error" not in result:
        total_sessions = result.get('total_sessions', 0)
        avg_score = result.get('average_score')
        print(f"✅ Got user progress: {total_sessions} sessions, avg score: {avg_score}")
    
    # Get user statistics
    result = make_request("GET", f"/api/v1/users/{TEST_USER_ID}/stats")
    if "error" not in result:
        total_sessions = result.get('total_sessions', 0)
        total_time = result.get('total_conversation_time', 0)
        print(f"✅ Got user stats: {total_sessions} sessions, {total_time}s total time")

def test_with_existing_session():
    """Test endpoints with an existing session that has data"""
    print("\n🔍 Testing with existing sessions...")
    
    # Get user sessions to find one with data
    result = make_request("GET", f"/api/v1/users/{TEST_USER_ID}/sessions")
    if "error" in result:
        print("❌ Could not get user sessions")
        return
    
    sessions = result.get('sessions', [])
    if not sessions:
        print("ℹ️ No existing sessions found")
        return
    
    # Use the first session
    session = sessions[0]['session']
    session_id = session['session_id']
    print(f"🔍 Testing with existing session: {session_id}")
    
    # Test conversation endpoints
    result = make_request("GET", f"/api/v1/conversations/{session_id}")
    if result and "error" not in result:
        messages = result.get('messages', [])
        print(f"✅ Existing session has {len(messages)} messages")
    
    # Test feedback endpoints
    result = make_request("GET", f"/api/v1/feedback/{session_id}")
    if result and "error" not in result:
        if 'feedback' in result:
            print("✅ Existing session has feedback")
        else:
            print("ℹ️ Existing session has no feedback")

def main():
    """Run all tests"""
    print("🚀 Starting Talktor API endpoint tests...\n")
    
    # Test basic endpoints
    test_basic_endpoints()
    
    # Test session management
    session_id = test_session_management()
    
    if session_id:
        # Test conversation endpoints
        test_conversation_endpoints(session_id)
        
        # Test feedback endpoints
        test_feedback_endpoints(session_id)
    
    # Test user endpoints
    test_user_endpoints()
    
    # Test with existing data
    test_with_existing_session()
    
    print("\n✅ All tests completed!")

if __name__ == "__main__":
    main()
