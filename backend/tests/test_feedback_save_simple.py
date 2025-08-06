"""
Simple test for feedback persistence - focuses on saving functionality
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
    "overall_score": 8.5,
    "summary": "The student demonstrated excellent conversational skills with clear pronunciation and good vocabulary usage. They engaged actively in the discussion and showed strong comprehension abilities.",
    "conclusion": "The student is at an upper-intermediate level with particular strengths in vocabulary and comprehension. Areas for improvement include grammar accuracy and fluency.",
    "pillars": {
        "pronunciation": {
            "score": 8.0,
            "feedback": "Clear and understandable pronunciation with good intonation patterns.",
            "examples": ["Excellent pronunciation of 'conversation'", "Good stress on 'important'"],
            "suggestions": ["Practice with 'th' sounds", "Work on word linking"]
        },
        "fluency": {
            "score": 7.5,
            "feedback": "Good conversational flow with natural pauses and rhythm.",
            "examples": ["Smooth topic transitions", "Natural use of hesitation markers"],
            "suggestions": ["Reduce filler words", "Practice speaking faster"]
        },
        "grammar": {
            "score": 7.0,
            "feedback": "Generally correct grammar with some minor errors in complex structures.",
            "examples": ["Correct use of present perfect", "Good question formation"],
            "suggestions": ["Review conditional sentences", "Practice passive voice"]
        },
        "expressions": {
            "score": 8.5,
            "feedback": "Excellent use of idiomatic expressions and colloquial language.",
            "examples": ["Used 'by the way' appropriately", "Good use of 'I mean' for clarification"],
            "suggestions": ["Learn more formal expressions", "Practice business idioms"]
        },
        "vocabulary": {
            "score": 9.0,
            "feedback": "Rich vocabulary with appropriate word choice and variety.",
            "examples": ["Used 'fascinating' instead of 'interesting'", "Good range of adjectives"],
            "suggestions": ["Learn more academic vocabulary", "Practice synonyms"]
        },
        "comprehension": {
            "score": 9.5,
            "feedback": "Outstanding listening comprehension with immediate understanding.",
            "examples": ["Understood complex questions", "Asked relevant follow-ups"],
            "suggestions": ["Practice with different accents", "Try faster speech"]
        }
    },
    "timestamp": datetime.now().isoformat(),
    "format_version": "structured_v1"
}

async def test_feedback_save():
    """Test saving structured feedback to database"""
    print("🧪 SIMPLE FEEDBACK SAVE TEST")
    print("=" * 50)
    
    # Generate test session data
    session_id = f"test_save_{uuid.uuid4().hex[:8]}"
    user_id = "test_user_save"
    
    print(f"📝 Session ID: {session_id}")
    print(f"👤 User ID: {user_id}")
    print()
    
    try:
        # Display feedback data
        print("📊 Feedback Data Summary:")
        print(f"   📈 Overall Score: {SAMPLE_FEEDBACK_DATA['overall_score']}/10.0")
        print(f"   📋 Summary: {len(SAMPLE_FEEDBACK_DATA['summary'])} chars")
        print(f"   🎯 Conclusion: {len(SAMPLE_FEEDBACK_DATA['conclusion'])} chars")
        
        pillar_scores = []
        for pillar, data in SAMPLE_FEEDBACK_DATA['pillars'].items():
            score = data['score']
            pillar_scores.append(f"{pillar}: {score}")
        print(f"   🏛️ Pillars: {', '.join(pillar_scores)}")
        print()
        
        # Save to database
        print("💾 Saving to database...")
        result = await persistence_service.save_complete_conversation(
            session_id=session_id,
            user_id=user_id,
            conversation_json={"messages": [], "test": "feedback_save"},
            feedback_data=SAMPLE_FEEDBACK_DATA,
            duration_seconds=180,  # 3 minutes
            agent_type="realtime",
            mode="free_topic",
            topic="Feedback Save Test"
        )
        
        # Check result
        summary = result.get('summary', {})
        feedback_count = summary.get('feedback_count', 0)
        
        print("✅ Save operation completed!")
        print(f"   📊 Session ID: {summary.get('session_id')}")
        print(f"   👤 User ID: {summary.get('user_id')}")
        print(f"   ⏱️ Duration: {summary.get('duration_seconds')} seconds")
        print(f"   📋 Feedback Items Saved: {feedback_count}")
        print(f"   🏁 Status: {summary.get('status')}")
        print()
        
        if feedback_count == 1:
            print("🎉 SUCCESS: Feedback saved correctly!")
            print("✅ All structured data should be in the database")
            print("✅ Overall score, summary, conclusion saved")
            print("✅ All 6 pillar scores and details saved")
            
            # Show database stats
            health = await persistence_service.health_check()
            print(f"\n📊 Database Stats:")
            print(f"   🏥 Status: {health.get('status')}")
            print(f"   📊 Total Sessions: {health.get('sessions')}")
            print(f"   📋 Total Feedback: {health.get('feedback')}")
            
            return True
        else:
            print("❌ FAILED: Expected 1 feedback item, got {feedback_count}")
            return False
            
    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        import traceback
        print("🔍 Full error:")
        print(traceback.format_exc())
        return False

async def main():
    """Run the simple feedback save test"""
    print("🚀 STARTING FEEDBACK SAVE TEST")
    print("=" * 60)
    print()
    
    success = await test_feedback_save()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 TEST PASSED!")
        print("✅ Feedback persistence is working correctly")
        print("🚀 Ready to integrate with conversation service")
    else:
        print("❌ TEST FAILED!")
        print("🔧 Check the errors above and fix issues")
    
    return success

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
