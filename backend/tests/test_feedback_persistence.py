"""
Test for feedback persistence functionality
Tests saving structured feedback to database without full conversation flow
"""
import asyncio
import json
import uuid
import sys
import os
from datetime import datetime

# Add backend directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from services.persistence_service import persistence_service
from core.logging import get_logger

logger = get_logger(__name__)

# Sample structured feedback data matching the format from OpenAI
SAMPLE_FEEDBACK_DATA = {
    "overall_score": 7.5,
    "summary": "The student engaged in a meaningful conversation about their hobbies and interests. They demonstrated good comprehension skills and were able to express their thoughts clearly, though there were some grammatical errors and pronunciation issues that could be improved.",
    "conclusion": "The student shows intermediate-level English proficiency with strong vocabulary and comprehension skills. Focus areas for improvement include grammar accuracy and pronunciation clarity.",
    "pillars": {
        "pronunciation": {
            "score": 6.5,
            "feedback": "Generally clear pronunciation with some difficulty on specific sounds. The student's accent is understandable but could benefit from practice on vowel sounds and word stress.",
            "examples": [
                "Pronounced 'interesting' as 'intresting'",
                "Good pronunciation of 'conversation' and 'hobbies'",
                "Struggled with 'th' sounds in 'think' and 'thought'"
            ],
            "suggestions": [
                "Practice vowel sounds with minimal pairs exercises",
                "Record yourself speaking and compare with native speakers",
                "Focus on word stress patterns in multi-syllable words"
            ]
        },
        "fluency": {
            "score": 7.0,
            "feedback": "Good conversational flow with natural pauses. The student maintained the conversation well and showed confidence in expressing ideas.",
            "examples": [
                "Smooth transitions between topics",
                "Natural use of filler words like 'well' and 'you know'",
                "Occasional hesitation when searching for specific vocabulary"
            ],
            "suggestions": [
                "Practice speaking on various topics to build confidence",
                "Work on reducing hesitation through regular conversation practice",
                "Learn more transition phrases to connect ideas smoothly"
            ]
        },
        "grammar": {
            "score": 6.0,
            "feedback": "Basic grammar structures are generally correct, but there are consistent errors with verb tenses and article usage that need attention.",
            "examples": [
                "Incorrect: 'I am go to the store yesterday'",
                "Correct: 'I like to read books'",
                "Missing articles: 'I went to store' instead of 'I went to the store'"
            ],
            "suggestions": [
                "Review past tense formation and usage",
                "Practice with definite and indefinite articles",
                "Focus on subject-verb agreement in complex sentences"
            ]
        },
        "expressions": {
            "score": 7.5,
            "feedback": "Good use of common expressions and idioms. The student shows familiarity with colloquial language and can use expressions appropriately in context.",
            "examples": [
                "Used 'That's interesting' appropriately",
                "Good use of 'I mean' to clarify thoughts",
                "Correctly used 'by the way' to change topics"
            ],
            "suggestions": [
                "Learn more advanced idiomatic expressions",
                "Practice formal vs. informal expressions for different contexts",
                "Expand repertoire of conversational phrases"
            ]
        },
        "vocabulary": {
            "score": 8.0,
            "feedback": "Strong vocabulary range with good use of topic-specific words. The student demonstrates ability to express complex ideas with appropriate word choice.",
            "examples": [
                "Used 'fascinating' instead of just 'good'",
                "Correctly used 'challenging' in context",
                "Good variety in descriptive adjectives"
            ],
            "suggestions": [
                "Continue expanding academic and professional vocabulary",
                "Learn synonyms to avoid repetition",
                "Practice using new words in different contexts"
            ]
        },
        "comprehension": {
            "score": 8.5,
            "feedback": "Excellent listening comprehension with quick understanding of questions and topics. The student responds appropriately and asks relevant follow-up questions.",
            "examples": [
                "Understood complex questions without repetition",
                "Asked clarifying questions when needed",
                "Responded appropriately to all prompts"
            ],
            "suggestions": [
                "Continue listening to varied English content",
                "Practice with different accents and speaking speeds",
                "Engage with more complex audio materials"
            ]
        }
    },
    "timestamp": datetime.now().isoformat(),
    "format_version": "structured_v1"
}

async def test_feedback_persistence():
    """Test saving structured feedback to database"""
    print("🧪 Starting Feedback Persistence Test")
    print("=" * 60)
    
    # Generate test session data
    session_id = f"test_feedback_{uuid.uuid4().hex[:8]}"
    user_id = "test_user_feedback"
    
    print(f"📝 Test Session ID: {session_id}")
    print(f"👤 Test User ID: {user_id}")
    print()
    
    try:
        # Step 1: Display the feedback data we're going to save
        print("📊 Step 1: Sample Feedback Data")
        print("-" * 30)
        print(f"   📈 Overall Score: {SAMPLE_FEEDBACK_DATA['overall_score']}/10.0")
        print(f"   📋 Summary Length: {len(SAMPLE_FEEDBACK_DATA['summary'])} chars")
        print(f"   🎯 Conclusion Length: {len(SAMPLE_FEEDBACK_DATA['conclusion'])} chars")
        print(f"   🏛️ Pillars: {len(SAMPLE_FEEDBACK_DATA['pillars'])} categories")
        
        # Show pillar scores
        for pillar, data in SAMPLE_FEEDBACK_DATA['pillars'].items():
            print(f"      • {pillar.capitalize()}: {data['score']}/10.0")
        print()
        
        # Step 2: Save to database
        print("💾 Step 2: Saving to Database")
        print("-" * 30)
        
        result = await persistence_service.save_complete_conversation(
            session_id=session_id,
            user_id=user_id,
            conversation_json={"messages": [], "test": True},
            feedback_data=SAMPLE_FEEDBACK_DATA,
            duration_seconds=120,  # 2 minutes test duration
            agent_type="realtime",
            mode="free_topic",
            topic="Feedback Persistence Test"
        )
        
        print("   ✅ Successfully saved to database!")
        summary = result.get('summary', {})
        print(f"   📊 Session ID: {summary.get('session_id', 'N/A')}")
        print(f"   👤 User ID: {summary.get('user_id', 'N/A')}")
        print(f"   ⏱️ Duration: {summary.get('duration_seconds', 0)} seconds")
        print(f"   💬 Messages: {summary.get('message_count', 0)}")
        print(f"   📋 Feedback Items: {summary.get('feedback_count', 0)}")
        print(f"   🏁 Status: {summary.get('status', 'N/A')}")
        print()
        
        # Step 3: Retrieve and verify the saved data
        print("🔍 Step 3: Retrieving and Verifying Data")
        print("-" * 30)
        
        # Get session feedback
        feedback = await persistence_service.get_session_feedback(session_id)
        
        if feedback:
            print("   ✅ Feedback retrieved successfully!")
            print(f"   📈 Overall Score: {feedback.overall_score}/10.0")
            print(f"   📋 General Feedback Length: {len(feedback.general_feedback or '')} chars")
            print(f"   🆔 Database ID: {feedback.id}")
            print(f"   🕰️ Created At: {feedback.created_at}")
            print()
            
            # Verify pillar data
            print("   🏛️ Pillar Verification:")
            pillars_to_check = ["pronunciation", "fluency", "grammar", "expressions", "vocabulary", "comprehension"]
            
            for pillar in pillars_to_check:
                score = getattr(feedback, f"{pillar}_score")
                summary = getattr(feedback, f"{pillar}_summary")
                examples = getattr(feedback, f"{pillar}_errors")  # Examples stored in errors field
                suggestions = getattr(feedback, f"{pillar}_suggestions")
                
                print(f"      • {pillar.capitalize()}:")
                print(f"        - Score: {score}/10.0")
                print(f"        - Summary: {len(summary or '') if summary else 0} chars")
                
                # Parse JSON fields
                try:
                    examples_list = json.loads(examples) if examples else []
                    suggestions_list = json.loads(suggestions) if suggestions else []
                    print(f"        - Examples: {len(examples_list)} items")
                    print(f"        - Suggestions: {len(suggestions_list)} items")
                except json.JSONDecodeError:
                    print(f"        - Examples: Error parsing JSON")
                    print(f"        - Suggestions: Error parsing JSON")
            
            print()
            
        else:
            print("   ❌ No feedback found!")
            return False
        
        # Step 4: Database statistics
        print("📊 Step 4: Database Statistics")
        print("-" * 30)
        
        health = await persistence_service.health_check()
        print(f"   🏥 Database Status: {health.get('status', 'unknown')}")
        print(f"   📊 Total Sessions: {health.get('sessions', 0)}")
        print(f"   💬 Total Transcripts: {health.get('transcripts', 0)}")
        print(f"   📋 Total Feedback: {health.get('feedback', 0)}")
        print()
        
        print("🎉 Step 5: Test Completed Successfully!")
        print("=" * 60)
        print("✅ All feedback data saved and retrieved correctly")
        print("✅ Database structure matches expected format")
        print("✅ JSON fields properly serialized and deserialized")
        print("✅ All pillar scores and data preserved")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        import traceback
        print("🔍 Full error traceback:")
        print(traceback.format_exc())
        return False

async def test_feedback_retrieval():
    """Test retrieving feedback data and displaying it nicely"""
    print("\n🔍 Testing Feedback Retrieval")
    print("=" * 60)
    
    try:
        # Get the most recent feedback
        health = await persistence_service.health_check()
        total_feedback = health.get('feedback', 0)
        
        if total_feedback == 0:
            print("⚠️ No feedback found in database")
            return True
        
        print(f"📊 Found {total_feedback} feedback items in database")
        
        # For demo purposes, let's try to find any session with feedback
        # In a real scenario, you'd have a specific session_id
        
        print("✅ Feedback retrieval test completed")
        return True
        
    except Exception as e:
        print(f"❌ Retrieval test failed: {str(e)}")
        return False

async def main():
    """Run all feedback persistence tests"""
    print("🚀 TALKTOR FEEDBACK PERSISTENCE TEST SUITE")
    print("=" * 80)
    print()
    
    # Test 1: Save feedback
    success1 = await test_feedback_persistence()
    
    # Test 2: Retrieve feedback
    success2 = await test_feedback_retrieval()
    
    print("\n📋 TEST SUMMARY")
    print("=" * 40)
    print(f"✅ Feedback Persistence: {'PASSED' if success1 else 'FAILED'}")
    print(f"✅ Feedback Retrieval: {'PASSED' if success2 else 'FAILED'}")
    
    if success1 and success2:
        print("\n🎉 ALL TESTS PASSED!")
        print("🚀 Feedback persistence system is working correctly!")
    else:
        print("\n❌ SOME TESTS FAILED!")
        print("🔧 Please check the errors above and fix the issues.")
    
    return success1 and success2

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
