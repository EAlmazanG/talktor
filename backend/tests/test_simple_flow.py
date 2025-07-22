"""
Simplified test for the complete conversation flow integration
"""
import sys
import os
import asyncio
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.standard_agent import StandardAgent
from db.database import get_db_session, init_database
from db.crud import SessionCRUD, TranscriptCRUD, FeedbackCRUD
from core.logging import get_logger
from core.colors import colorize, Colors

logger = get_logger(__name__)


async def test_standard_agent_simple():
    """Test StandardAgent with mock session state"""
    print("\n🤖 Testing StandardAgent (Simplified)")
    print("=" * 50)
    
    try:
        # Create mock session state
        class MockSessionState:
            def __init__(self):
                self.session_id = "test_session_simple"
        
        session_state = MockSessionState()
        
        # Sample transcripts
        user_transcript = """
        Hello, how are you today?
        I want to practice my English speaking.
        Can we talk about my hobbies? I like to read books and play guitar.
        I like mystery novels and sometimes science fiction. My favorite author is Agatha Christie.
        Yes, I really like "Murder on the Orient Express". The plot was very interesting.
        The ending was surprising. I didn't expect that all passengers were involved.
        I started playing about two years ago. I can play some basic songs now.
        I mostly play pop songs and some rock music. I'm still learning though.
        I take lessons once a week with a local teacher. It helps me a lot.
        """
        
        ai_transcript = """
        Hello! I'm doing well, thank you for asking. How are you doing?
        That's wonderful! I'd be happy to help you practice. What would you like to talk about?
        Those are great hobbies! What kind of books do you enjoy reading?
        Excellent choice! Agatha Christie wrote amazing mystery stories. Do you have a favorite book by her?
        That's one of her most famous works! What did you think about the ending?
        You're absolutely right! That twist ending is what makes it so memorable. How long have you been playing guitar?
        That's great progress! What style of music do you like to play?
        Keep practicing! Playing guitar is a wonderful skill. Do you take lessons or are you self-taught?
        That's excellent! Having a good teacher makes a big difference in your progress.
        """
        
        # Initialize StandardAgent
        standard_agent = StandardAgent()
        
        # Test feedback analysis
        print("📊 Generating conversation feedback...")
        feedback = await standard_agent.analyze_conversation_feedback(
            session_state=session_state,
            user_transcript=user_transcript,
            ai_transcript=ai_transcript,
            conversation_duration=300  # 5 minutes
        )
        
        print("✅ Feedback generated successfully!")
        print(f"   - Session: {session_state.session_id}")
        
        # Display feedback summary
        if isinstance(feedback, dict):
            overall_score = feedback.get('overall_score', 'N/A')
            print(f"   - Overall Score: {overall_score}")
            
            pillars = feedback.get('pillars', {})
            for pillar_name, pillar_data in pillars.items():
                if isinstance(pillar_data, dict):
                    score = pillar_data.get('score', 'N/A')
                    feedback_text = pillar_data.get('feedback', 'No feedback')
                    # Truncate long feedback
                    if len(feedback_text) > 50:
                        feedback_text = feedback_text[:50] + "..."
                    print(f"   - {pillar_name.title()}: {score}/10 - {feedback_text}")
        
        return feedback
        
    except Exception as e:
        print(f"❌ StandardAgent test failed: {e}")
        import traceback
        traceback.print_exc()
        return None


async def test_database_simple():
    """Test database operations (simplified)"""
    print("\n🗄️ Testing Database Operations (Simplified)")
    print("=" * 50)
    
    try:
        # Initialize database
        init_database()
        print("✅ Database initialized")
        
        # Test CRUD operations
        session_crud = SessionCRUD()
        transcript_crud = TranscriptCRUD()
        feedback_crud = FeedbackCRUD()
        
        session_id = f"simple_test_{datetime.now().strftime('%H%M%S')}"
        
        # Create session
        db = get_db_session()
        try:
            # Import required enums
            from db.models import AgentType, ConversationMode
            
            db_session = session_crud.create_session(
                db=db,
                session_id=session_id,
                user_id="test_user_simple",
                agent_type=AgentType.REALTIME,
                mode=ConversationMode.FREE_TOPIC
            )
            print(f"✅ Created session: {session_id}")
            
            # Add sample transcripts
            messages = [
                {"role": "user", "content": "Hello, how are you?", "sequence": 1},
                {"role": "ai", "content": "I'm doing well, thank you!", "sequence": 2},
                {"role": "user", "content": "I want to practice English.", "sequence": 3},
                {"role": "ai", "content": "Great! Let's practice together.", "sequence": 4}
            ]
            
            # Import Speaker enum
            from db.models import Speaker
            
            for msg in messages:
                speaker = Speaker.USER if msg["role"] == "user" else Speaker.AI
                transcript_crud.add_transcript_message(
                    db=db,
                    session_id=db_session.id,
                    speaker=speaker,
                    content=msg["content"],
                    sequence_number=msg["sequence"]
                )
            
            print(f"✅ Added {len(messages)} transcript messages")
            
            # Add sample feedback
            from db.models import FeedbackPillar
            
            feedback_items = [
                {
                    "pillar": FeedbackPillar.PRONUNCIATION,
                    "score": 8.0,
                    "feedback_text": "Good pronunciation overall"
                },
                {
                    "pillar": FeedbackPillar.GRAMMAR,
                    "score": 7.5,
                    "feedback_text": "Grammar is mostly correct"
                }
            ]
            
            for item in feedback_items:
                feedback_crud.create_feedback_item(
                    db=db,
                    session_id=db_session.id,
                    pillar=item["pillar"],
                    score=item["score"],
                    feedback_text=item["feedback_text"]
                )
            
            print(f"✅ Added {len(feedback_items)} feedback items")
            
            # Complete session
            session_crud.update_session_completion(
                db=db,
                session_id=session_id,
                duration_seconds=180,
                token_count=1500,
                estimated_cost=0.05,
                status="completed"
            )
            print("✅ Session marked as completed")
            
            return True
            
        finally:
            db.close()
            
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Main test function"""
    print("🧪 Simplified Flow Integration Test")
    print("=" * 60)
    print("Testing: StandardAgent + Database (Core Components)")
    print("=" * 60)
    
    # Run tests
    tests = [
        ("StandardAgent Analysis", test_standard_agent_simple),
        ("Database Operations", test_database_simple),
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
    print("\n" + "=" * 60)
    print("📊 Test Summary:")
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"   - {test_name}: {status}")
    
    total_tests = len(results)
    passed_tests = sum(results.values())
    
    print(f"\n🎯 Overall: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print(colorize("🎉 Core components working!", Colors.BRIGHT_GREEN))
        print("\n💡 Ready for:")
        print("   1. ✅ RealtimeAgent voice conversations")  
        print("   2. ✅ StandardAgent feedback analysis")
        print("   3. ✅ Database persistence")
        print("   4. 🔄 Full flow integration")
        return True
    else:
        print(colorize("⚠️ Some core components need attention.", Colors.BRIGHT_YELLOW))
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
