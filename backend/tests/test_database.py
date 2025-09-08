"""
Test script for database models and operations
"""
import sys
import os
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db import (
    init_database, get_db_session, test_connection,
    SessionCRUD, TranscriptCRUD, FeedbackCRUD, HomeworkCRUD,
    AgentType, ConversationMode, Speaker, FeedbackPillar,
    get_session_summary
)
from core.logging import setup_logging, get_logger

# Setup logging
setup_logging("INFO")
logger = get_logger(__name__)


def test_database_connection():
    """Test database connection"""
    print("\n🔍 Testing Database Connection")
    print("=" * 50)
    
    try:
        if test_connection():
            print("✅ Database connection successful")
            return True
        else:
            print("❌ Database connection failed")
            return False
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return False


def test_table_creation():
    """Test table creation"""
    print("\n🏗️ Testing Table Creation")
    print("=" * 50)
    
    try:
        init_database()
        print("✅ Tables created successfully")
        return True
    except Exception as e:
        print(f"❌ Table creation failed: {e}")
        return False


def test_session_crud():
    """Test session CRUD operations"""
    print("\n📝 Testing Session CRUD")
    print("=" * 50)
    
    db = get_db_session()
    
    try:
        # Create a test session
        session = SessionCRUD.create_session(
            db=db,
            session_id=f"test_session_{datetime.now().strftime('%H%M%S')}",
            user_id="test_user_123",
            agent_type=AgentType.REALTIME,
            mode=ConversationMode.FREE_TOPIC,
            topic="English conversation practice"
        )
        print(f"✅ Created session: {session.session_id}")
        
        # Retrieve the session
        retrieved_session = SessionCRUD.get_session_by_id(db, session.session_id)
        if retrieved_session:
            print(f"✅ Retrieved session: {retrieved_session.session_id}")
        else:
            print("❌ Failed to retrieve session")
            return False
        
        # Update session completion
        updated_session = SessionCRUD.update_session_completion(
            db=db,
            session_id=session.session_id,
            duration_seconds=300,
            token_count=1500,
            estimated_cost=0.05
        )
        if updated_session:
            print(f"✅ Updated session completion: {updated_session.status}")
        else:
            print("❌ Failed to update session")
            return False
        
        return session.id  # Return database ID for other tests
        
    except Exception as e:
        print(f"❌ Session CRUD failed: {e}")
        return False
    finally:
        db.close()


def test_transcript_crud(session_db_id):
    """Test transcript CRUD operations"""
    print("\n💬 Testing Transcript CRUD")
    print("=" * 50)
    
    if not session_db_id:
        print("❌ No session ID provided, skipping transcript test")
        return False
    
    db = get_db_session()
    
    try:
        # Add some transcript messages
        messages = [
            ("Hello, I want to practice English today.", Speaker.USER),
            ("Hello! I'd be happy to help you practice English. What would you like to focus on?", Speaker.AI),
            ("I think my grammar needs improvement.", Speaker.USER),
            ("That's a great area to work on. Let's start with some conversation.", Speaker.AI)
        ]
        
        for i, (content, speaker) in enumerate(messages, 1):
            transcript = TranscriptCRUD.add_transcript_message(
                db=db,
                session_id=session_db_id,
                speaker=speaker,
                content=content,
                sequence_number=i,
                confidence_score=0.95 if speaker == Speaker.USER else None
            )
            print(f"✅ Added transcript {i}: {speaker.value}")
        
        # Retrieve transcripts
        transcripts = TranscriptCRUD.get_session_transcripts(db, session_db_id)
        print(f"✅ Retrieved {len(transcripts)} transcript messages")
        
        # Get full conversation text
        conversation_text = TranscriptCRUD.get_full_conversation_text(db, session_db_id)
        print(f"✅ Generated conversation text: {len(conversation_text)} characters")
        
        return True
        
    except Exception as e:
        print(f"❌ Transcript CRUD failed: {e}")
        return False
    finally:
        db.close()


def test_feedback_crud(session_db_id):
    """Test feedback CRUD operations"""
    print("\n📊 Testing Feedback CRUD")
    print("=" * 50)
    
    if not session_db_id:
        print("❌ No session ID provided, skipping feedback test")
        return False
    
    db = get_db_session()
    
    try:
        # Create sample feedback data (like StandardAgent would generate)
        feedback_data = {
            "pillars": {
                "pronunciation": {
                    "score": 7.5,
                    "feedback": "Good pronunciation overall, some areas for improvement",
                    "examples": ["clear articulation in 'practice'"],
                    "suggestions": ["Focus on 'th' sounds"]
                },
                "grammar": {
                    "score": 6.0,
                    "feedback": "Some grammar mistakes need attention",
                    "examples": ["Correct: 'I want to practice'"],
                    "errors": ["Watch out for verb tenses"]
                },
                "vocabulary": {
                    "score": 8.0,
                    "feedback": "Good vocabulary usage",
                    "examples": ["Good use of 'improvement'"],
                    "suggestions": ["Try more advanced synonyms"]
                }
            }
        }
        
        # Create feedback items
        feedback_items = FeedbackCRUD.create_session_feedback(
            db=db,
            session_id=session_db_id,
            feedback_data=feedback_data
        )
        print(f"✅ Created {len(feedback_items)} feedback items")
        
        # Retrieve feedback
        retrieved_feedback = FeedbackCRUD.get_session_feedback(db, session_db_id)
        print(f"✅ Retrieved {len(retrieved_feedback)} feedback items")
        
        for feedback in retrieved_feedback:
            print(f"   - {feedback.pillar.value}: {feedback.score}/10")
        
        return True
        
    except Exception as e:
        print(f"❌ Feedback CRUD failed: {e}")
        return False
    finally:
        db.close()


def test_homework_crud(session_db_id):
    """Test homework CRUD operations"""
    print("\n📚 Testing Homework CRUD")
    print("=" * 50)
    
    if not session_db_id:
        print("❌ No session ID provided, skipping homework test")
        return False
    
    db = get_db_session()
    
    try:
        # Create sample homework data (like StandardAgent would generate)
        homework_data = {
            "vocabulary": [
                {
                    "title": "Learn new expressions",
                    "description": "Study 5 new vocabulary words from today's conversation",
                    "difficulty": "intermediate",
                    "priority": "high",
                    "estimated_time_minutes": 30
                }
            ],
            "grammar": [
                {
                    "title": "Practice verb tenses",
                    "description": "Complete exercises on past and present tenses",
                    "difficulty": "beginner",
                    "priority": "high",
                    "estimated_time_minutes": 45
                }
            ]
        }
        
        # Create homework items
        homework_items = HomeworkCRUD.create_homework_items(
            db=db,
            session_id=session_db_id,
            homework_data=homework_data
        )
        print(f"✅ Created {len(homework_items)} homework items")
        
        for item in homework_items:
            print(f"   - {item.category}: {item.title} ({item.priority} priority)")
        
        return True
        
    except Exception as e:
        print(f"❌ Homework CRUD failed: {e}")
        return False
    finally:
        db.close()


def test_session_summary(session_id):
    """Test complete session summary"""
    print("\n📋 Testing Session Summary")
    print("=" * 50)
    
    db = get_db_session()
    
    try:
        summary = get_session_summary(db, session_id)
        if summary:
            print(f"✅ Session summary generated:")
            print(f"   - Session ID: {summary['session'].session_id}")
            print(f"   - Duration: {summary['session'].duration_seconds}s")
            print(f"   - Transcripts: {summary['transcript_count']}")
            print(f"   - Feedback items: {summary['feedback_count']}")
            print(f"   - Status: {summary['session'].status}")
            return True
        else:
            print("❌ Failed to generate session summary")
            return False
            
    except Exception as e:
        print(f"❌ Session summary failed: {e}")
        return False
    finally:
        db.close()


def main():
    """Main test function"""
    print("🚀 Starting Database Tests")
    print("=" * 60)
    
    # Test results tracking
    results = {}
    
    # Test 1: Database connection
    results['connection'] = test_database_connection()
    
    # Test 2: Table creation
    results['tables'] = test_table_creation() if results['connection'] else False
    
    # Test 3: Session CRUD
    session_db_id = test_session_crud() if results['tables'] else None
    results['sessions'] = bool(session_db_id)
    
    # Test 4: Transcript CRUD
    results['transcripts'] = test_transcript_crud(session_db_id) if session_db_id else False
    
    # Test 5: Feedback CRUD
    results['feedback'] = test_feedback_crud(session_db_id) if session_db_id else False
    
    # Test 6: Homework CRUD
    results['homework'] = test_homework_crud(session_db_id) if session_db_id else False
    
    # Test 7: Session summary
    if session_db_id:
        # Get session_id string for summary test
        db = get_db_session()
        session = db.query(SessionCRUD.get_session_by_id.__annotations__['return']).filter_by(id=session_db_id).first()
        session_id_str = session.session_id if session else None
        db.close()
        results['summary'] = test_session_summary(session_id_str) if session_id_str else False
    else:
        results['summary'] = False
    
    # Print summary
    print("\n" + "=" * 60)
    print("📊 Test Results Summary:")
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"   - {test_name.capitalize()}: {status}")
    
    total_tests = len(results)
    passed_tests = sum(results.values())
    
    print(f"\n🎯 Overall: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("🎉 All database tests passed! Ready for integration.")
    else:
        print("⚠️ Some tests failed. Check the logs above.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n🛑 Tests interrupted by user")
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        logger.exception("Database test suite error")
        sys.exit(1)
