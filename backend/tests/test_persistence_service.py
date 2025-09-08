"""
Test the new PersistenceService to verify it works correctly
"""
import asyncio
import uuid
import sys
import os
from datetime import datetime, timezone

# Add the backend directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.persistence_service import persistence_service
from db.models import AgentType, ConversationMode


async def test_persistence_service():
    """Test the new persistence service with a complete conversation flow"""
    print("🧪 Testing PersistenceService...")
    
    # Generate test data
    session_id = str(uuid.uuid4())
    user_id = "test_user_persistence"
    
    # Test messages
    test_messages = [
        {
            "role": "user",
            "content": "Hello, I want to practice English",
            "timestamp": datetime.now(timezone.utc)
        },
        {
            "role": "assistant", 
            "content": "Great! Let's have a conversation about your hobbies.",
            "timestamp": datetime.now(timezone.utc)
        },
        {
            "role": "user",
            "content": "I like reading books and playing guitar",
            "timestamp": datetime.now(timezone.utc)
        },
        {
            "role": "assistant",
            "content": "That's wonderful! What kind of books do you enjoy?",
            "timestamp": datetime.now(timezone.utc)
        }
    ]
    
    # Test feedback data
    test_feedback = {
        "overall_score": 8.5,
        "pillars": {
            "pronunciation": {
                "score": 8.0,
                "feedback": "Good pronunciation with clear articulation",
                "examples": ["'reading' pronounced correctly", "'guitar' well articulated"],
                "suggestions": ["Work on 'th' sounds"],
                "errors": []
            },
            "fluency": {
                "score": 8.5,
                "feedback": "Natural conversational flow",
                "examples": ["Smooth transitions between ideas"],
                "suggestions": ["Use more connecting words"],
                "errors": []
            },
            "grammar": {
                "score": 9.0,
                "feedback": "Excellent grammar usage",
                "examples": ["Correct verb tenses", "Proper sentence structure"],
                "suggestions": [],
                "errors": []
            },
            "vocabulary": {
                "score": 8.0,
                "feedback": "Good vocabulary range",
                "examples": ["'hobbies', 'articulation'"],
                "suggestions": ["Try using more advanced vocabulary"],
                "errors": []
            },
            "expressions": {
                "score": 7.5,
                "feedback": "Good use of common expressions",
                "examples": ["'That's wonderful!'"],
                "suggestions": ["Learn more idiomatic expressions"],
                "errors": []
            },
            "comprehension": {
                "score": 9.0,
                "feedback": "Excellent understanding",
                "examples": ["Responded appropriately to all questions"],
                "suggestions": [],
                "errors": []
            }
        }
    }
    
    try:
        print(f"📝 Testing session creation...")
        
        # Test 1: Save complete conversation
        result = await persistence_service.save_complete_conversation(
            session_id=session_id,
            user_id=user_id,
            messages=test_messages,
            feedback_data=test_feedback,
            duration_seconds=120,
            agent_type=AgentType.REALTIME,
            mode=ConversationMode.FREE_TOPIC,
            token_count=150,
            estimated_cost=0.05,
            topic="Hobbies and interests",
            notes="Test conversation for persistence service"
        )
        
        print(f"✅ Complete conversation saved successfully!")
        print(f"   - Session: {result['summary']['session_id']}")
        print(f"   - Messages: {result['summary']['message_count']}")
        print(f"   - Feedback items: {result['summary']['feedback_count']}")
        print(f"   - Duration: {result['summary']['duration_seconds']}s")
        
        # Test 2: Get session summary
        print(f"\n📊 Testing session summary retrieval...")
        summary = await persistence_service.get_session_summary(session_id)
        
        if summary:
            print(f"✅ Session summary retrieved!")
            print(f"   - User: {summary['session']['user_id']}")
            print(f"   - Status: {summary['session']['status']}")
            print(f"   - Messages: {summary['conversation']['message_count']}")
            print(f"   - Average score: {summary['feedback']['average_score']:.1f}")
            print(f"   - Feedback pillars: {summary['feedback']['pillar_count']}")
        else:
            print("❌ Session summary not found")
        
        # Test 3: Get user progress
        print(f"\n📈 Testing user progress analytics...")
        progress = await persistence_service.get_user_progress(user_id)
        
        print(f"✅ User progress retrieved!")
        print(f"   - Total sessions: {progress['total_sessions']}")
        print(f"   - Completed sessions: {progress['completed_sessions']}")
        print(f"   - Total duration: {progress['total_duration']}s")
        print(f"   - Average scores: {progress['average_scores']}")
        
        # Test 4: Health check
        print(f"\n🏥 Testing database health check...")
        health = await persistence_service.health_check()
        
        print(f"✅ Health check completed!")
        print(f"   - Status: {health['status']}")
        print(f"   - Database: {health['database']}")
        print(f"   - Tables: {health['tables']}")
        
        print(f"\n🎉 All PersistenceService tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_persistence_service())
    if success:
        print("\n✅ PersistenceService is working correctly!")
    else:
        print("\n❌ PersistenceService has issues!")
