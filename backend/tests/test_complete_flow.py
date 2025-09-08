"""
Test script for complete conversation flow integration:
RealtimeAgent → StandardAgent → Database
"""
import sys
import os
import asyncio
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.conversation_flow import ConversationFlow
from agents.standard_agent import StandardAgent
from db.database import get_db, init_database
from db.crud import SessionCRUD, TranscriptCRUD, FeedbackCRUD
from core.logging import get_logger
from core.colors import colorize, Colors

logger = get_logger(__name__)


async def test_standard_agent_with_sample_conversation():
    """Test StandardAgent with a sample conversation"""
    print("\n🤖 Testing StandardAgent with Sample Conversation")
    print("=" * 60)
    
    try:
        # Sample conversation text (simulating what RealtimeAgent would provide)
        sample_conversation = """
        User: Hello, how are you today?
        AI: Hello! I'm doing well, thank you for asking. How are you doing?
        User: I'm good, thanks. I want to practice my English speaking.
        AI: That's wonderful! I'd be happy to help you practice. What would you like to talk about?
        User: Can we talk about my hobbies? I like to read books and play guitar.
        AI: Those are great hobbies! What kind of books do you enjoy reading?
        User: I like mystery novels and sometimes science fiction. My favorite author is Agatha Christie.
        AI: Excellent choice! Agatha Christie wrote amazing mystery stories. Do you have a favorite book by her?
        User: Yes, I really like "Murder on the Orient Express". The plot was very interesting.
        AI: That's one of her most famous works! What did you think about the ending?
        User: The ending was surprising. I didn't expect that all passengers were involved.
        AI: You're absolutely right! That twist ending is what makes it so memorable. How long have you been playing guitar?
        User: I started playing about two years ago. I can play some basic songs now.
        AI: That's great progress! What style of music do you like to play?
        User: I mostly play pop songs and some rock music. I'm still learning though.
        AI: Keep practicing! Playing guitar is a wonderful skill. Do you take lessons or are you self-taught?
        User: I take lessons once a week with a local teacher. It helps me a lot.
        """
        
        # Initialize StandardAgent
        standard_agent = StandardAgent()
        
        # Test feedback analysis
        print("📊 Generating conversation feedback...")
        feedback = await standard_agent.analyze_conversation_feedback(
            conversation_text=sample_conversation,
            user_level="intermediate"
        )
        
        print("✅ Feedback generated successfully!")
        print(f"   - Overall Score: {feedback.get('overall_score', 'N/A')}")
        
        pillars = feedback.get('pillars', {})
        for pillar_name, pillar_data in pillars.items():
            score = pillar_data.get('score', 'N/A')
            feedback_text = pillar_data.get('feedback', 'No feedback')[:50] + "..."
            print(f"   - {pillar_name.title()}: {score}/10 - {feedback_text}")
        
        return feedback
        
    except Exception as e:
        print(f"❌ StandardAgent test failed: {e}")
        return None


async def test_database_integration():
    """Test database integration with sample data"""
    print("\n🗄️ Testing Database Integration")
    print("=" * 60)
    
    try:
        # Initialize database
        init_database()
        print("✅ Database initialized")
        
        # Test session creation
        session_crud = SessionCRUD()
        transcript_crud = TranscriptCRUD()
        feedback_crud = FeedbackCRUD()
        
        session_id = f"test_flow_{datetime.now().strftime('%H%M%S')}"
        
        with get_db() as db:
            # Create session
            session_data = {
                "session_id": session_id,
                "user_id": "test_user",
                "agent_type": "REALTIME",
                "conversation_mode": "VOICE",
                "status": "ACTIVE"
            }
            
            db_session = session_crud.create_session(db, session_data)
            print(f"✅ Created session: {session_id}")
            
            # Add sample transcripts
            messages = [
                {"role": "user", "content": "Hello, how are you?"},
                {"role": "ai", "content": "I'm doing well, thank you!"},
                {"role": "user", "content": "I want to practice English."},
                {"role": "ai", "content": "Great! Let's practice together."}
            ]
            
            for i, msg in enumerate(messages):
                transcript_data = {
                    "session_id": db_session.id,
                    "speaker": "USER" if msg["role"] == "user" else "AI",
                    "content": msg["content"],
                    "sequence_number": i + 1
                }
                transcript_crud.add_transcript(db, transcript_data)
            
            print(f"✅ Added {len(messages)} transcript messages")
            
            # Add sample feedback
            feedback_items = [
                {
                    "session_id": db_session.id,
                    "pillar": "PRONUNCIATION",
                    "score": 8.0,
                    "feedback_text": "Good pronunciation overall"
                },
                {
                    "session_id": db_session.id,
                    "pillar": "GRAMMAR",
                    "score": 7.5,
                    "feedback_text": "Grammar is mostly correct"
                },
                {
                    "session_id": db_session.id,
                    "pillar": "VOCABULARY",
                    "score": 8.5,
                    "feedback_text": "Good vocabulary usage"
                }
            ]
            
            feedback_crud.create_feedback_batch(db, feedback_items)
            print(f"✅ Added {len(feedback_items)} feedback items")
            
            # Complete session
            completion_data = {
                "status": "COMPLETED",
                "duration_seconds": 180,
                "notes": "Test session completed successfully"
            }
            
            session_crud.complete_session(db, session_id, completion_data)
            print("✅ Session marked as completed")
            
        return True
        
    except Exception as e:
        print(f"❌ Database integration test failed: {e}")
        return False


async def test_conversation_flow_service():
    """Test the ConversationFlow service (without RealtimeAgent)"""
    print("\n🔄 Testing ConversationFlow Service")
    print("=" * 60)
    
    try:
        # Initialize ConversationFlow
        flow = ConversationFlow(user_id="test_flow_user")
        print("✅ ConversationFlow initialized")
        
        # Test StandardAgent integration
        sample_conversation = """
        User: Hi there! I'm excited to practice English today.
        AI: Hello! That's wonderful to hear. What would you like to focus on?
        User: I want to improve my pronunciation and vocabulary.
        AI: Great goals! Let's start with some conversation practice.
        User: I have been studying English for three years now.
        AI: That's impressive! What has been the most challenging part for you?
        User: Sometimes I struggle with irregular verbs and their past tenses.
        AI: That's very common! Practice makes perfect with irregular verbs.
        """
        
        # Test feedback generation
        feedback_data = await flow._generate_feedback(sample_conversation)
        print("✅ Feedback generated via ConversationFlow")
        print(f"   - Overall Score: {feedback_data.get('overall_score', 'N/A')}")
        
        # Test database operations (simulation)
        session_id = f"flow_test_{datetime.now().strftime('%H%M%S')}"
        flow.session_id = session_id
        
        # Create a test session in database
        with get_db() as db:
            session_data = {
                "session_id": session_id,
                "user_id": flow.user_id,
                "agent_type": "REALTIME",
                "conversation_mode": "VOICE",
                "status": "ACTIVE"
            }
            
            db_session = flow.session_crud.create_session(db, session_data)
            print(f"✅ Test session created: {session_id}")
        
        # Test transcript saving
        mock_messages = [
            {"role": "user", "content": "Hi there! I'm excited to practice English today."},
            {"role": "ai", "content": "Hello! That's wonderful to hear. What would you like to focus on?"},
            {"role": "user", "content": "I want to improve my pronunciation and vocabulary."},
            {"role": "ai", "content": "Great goals! Let's start with some conversation practice."}
        ]
        
        await flow._save_transcripts(mock_messages)
        print(f"✅ Saved {len(mock_messages)} transcript messages")
        
        # Test feedback saving
        await flow._save_feedback(feedback_data)
        print("✅ Feedback saved to database")
        
        # Test session completion
        await flow._complete_session(120)  # 2 minutes
        print("✅ Session marked as completed")
        
        # Cleanup
        await flow.cleanup()
        print("✅ ConversationFlow cleanup completed")
        
        return True
        
    except Exception as e:
        print(f"❌ ConversationFlow test failed: {e}")
        return False


async def main():
    """Main test function"""
    print("🧪 Complete Flow Integration Tests")
    print("=" * 70)
    print("Testing: RealtimeAgent → StandardAgent → Database")
    print("=" * 70)
    
    # Run all tests
    tests = [
        ("StandardAgent Analysis", test_standard_agent_with_sample_conversation),
        ("Database Integration", test_database_integration),
        ("ConversationFlow Service", test_conversation_flow_service),
    ]
    
    results = {}
    for test_name, test_func in tests:
        try:
            print(f"\n🔍 Running: {test_name}")
            result = await test_func()
            results[test_name] = result is not None and result is not False
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results[test_name] = False
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 Integration Test Summary:")
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"   - {test_name}: {status}")
    
    total_tests = len(results)
    passed_tests = sum(results.values())
    
    print(f"\n🎯 Overall: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print(colorize("🎉 All integration tests passed!", Colors.BRIGHT_GREEN))
        print("\n💡 Next Steps:")
        print("   1. Test with real RealtimeAgent conversation")
        print("   2. Implement FastAPI endpoints")
        print("   3. Create frontend interface")
        return True
    else:
        print(colorize("⚠️ Some tests failed. Check the issues above.", Colors.BRIGHT_YELLOW))
        return False


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n🛑 Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        sys.exit(1)
