"""
Test script for the Standard Agent
Tests feedback analysis, homework generation, flashcards, and exercises
"""
import asyncio
import json
import sys
import os
from datetime import datetime

# Add parent directory to path to import from backend modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.standard_agent import StandardAgent
from services.session_state import SessionState
from core.logging import setup_logging, get_logger
from core.config import settings

# Setup logging
setup_logging("INFO")
logger = get_logger(__name__)


async def test_feedback_analysis():
    """Test conversation feedback analysis"""
    print("\n🔍 Testing Feedback Analysis")
    print("=" * 50)
    
    # Create test session
    session_state = SessionState(
        session_id=f"test_feedback_{datetime.now().strftime('%H%M%S')}",
        user_id="test_user"
    )
    
    # Sample conversation transcripts
    user_transcript = """
    Hello, I want to practice my English today. I think my grammar is not very good and I need to improve.
    Yesterday I go to the store and I buy some food. The weather was very nice so I walk there.
    I like to read books but sometimes the words are too difficult for me to understand.
    Can you help me with my pronunciation? I think I don't speak very clear.
    """
    
    ai_transcript = """
    Hello! I'd be happy to help you practice your English today. It's great that you're motivated to improve.
    I noticed a few grammar points we can work on. For example, when talking about yesterday, we use past tense: "I went to the store and bought some food."
    That's wonderful that you enjoy reading! When words are difficult, try using a dictionary or asking for help.
    I'd be glad to help with pronunciation. Speaking clearly takes practice, but you're doing well!
    """
    
    agent = StandardAgent()
    
    try:
        feedback = await agent.analyze_conversation_feedback(
            session_state=session_state,
            user_transcript=user_transcript,
            ai_transcript=ai_transcript,
            conversation_duration=300  # 5 minutes
        )
        
        print("✅ Feedback Analysis Results:")
        print(json.dumps(feedback, indent=2))
        return feedback
        
    except Exception as e:
        print(f"❌ Error in feedback analysis: {e}")
        return None


async def test_homework_generation(feedback):
    """Test homework generation"""
    print("\n📚 Testing Homework Generation")
    print("=" * 50)
    
    if not feedback:
        print("❌ Skipping homework test - no feedback available")
        return None
    
    session_state = SessionState(
        session_id=f"test_homework_{datetime.now().strftime('%H%M%S')}",
        user_id="test_user"
    )
    
    agent = StandardAgent()
    
    try:
        homework = await agent.generate_homework(
            session_state=session_state,
            feedback=feedback,
            previous_homework=None
        )
        
        print("✅ Homework Generation Results:")
        print(json.dumps(homework, indent=2))
        return homework
        
    except Exception as e:
        print(f"❌ Error in homework generation: {e}")
        return None


async def test_flashcard_creation():
    """Test flashcard creation"""
    print("\n🃏 Testing Flashcard Creation")
    print("=" * 50)
    
    # Sample learning materials
    vocabulary_items = [
        "pronunciation - the way words are spoken",
        "grammar - rules for using language correctly",
        "fluency - speaking smoothly and easily"
    ]
    
    grammar_concepts = [
        "Past tense verbs (went, bought, walked)",
        "Present perfect vs simple past",
        "Articles (a, an, the)"
    ]
    
    errors = [
        {"incorrect": "I go to the store yesterday", "correct": "I went to the store yesterday"},
        {"incorrect": "I don't speak very clear", "correct": "I don't speak very clearly"},
        {"incorrect": "The words are too much difficult", "correct": "The words are too difficult"}
    ]
    
    agent = StandardAgent()
    
    try:
        flashcards = await agent.create_flashcards(
            vocabulary_items=vocabulary_items,
            grammar_concepts=grammar_concepts,
            errors=errors
        )
        
        print(f"✅ Created {len(flashcards)} flashcards:")
        for i, card in enumerate(flashcards[:3], 1):  # Show first 3
            print(f"\n📇 Flashcard {i}:")
            print(f"   Front: {card.get('front', 'N/A')}")
            print(f"   Back: {card.get('back', 'N/A')}")
            print(f"   Type: {card.get('type', 'N/A')}")
        
        return flashcards
        
    except Exception as e:
        print(f"❌ Error creating flashcards: {e}")
        return None


async def test_exercise_generation():
    """Test exercise generation"""
    print("\n📝 Testing Exercise Generation")
    print("=" * 50)
    
    agent = StandardAgent()
    
    try:
        exercises = await agent.generate_exercises(
            topic="Past tense verbs",
            difficulty="beginner",
            exercise_type="grammar"
        )
        
        print("✅ Exercise Generation Results:")
        print(json.dumps(exercises, indent=2))
        return exercises
        
    except Exception as e:
        print(f"❌ Error generating exercises: {e}")
        return None


async def test_personalized_advice():
    """Test personalized advice generation"""
    print("\n💡 Testing Personalized Advice")
    print("=" * 50)
    
    # Sample user history
    user_history = {
        "total_sessions": 5,
        "average_scores": {
            "pronunciation": 6.5,
            "fluency": 7.2,
            "grammar": 5.8,
            "expressions": 6.0,
            "vocabulary": 7.5,
            "comprehension": 8.0
        },
        "common_errors": ["past tense", "articles", "pronunciation"],
        "strengths": ["vocabulary", "comprehension"]
    }
    
    recent_performance = [
        {"session_id": "session_1", "overall_score": 6.8, "weak_areas": ["grammar", "pronunciation"]},
        {"session_id": "session_2", "overall_score": 7.1, "weak_areas": ["grammar", "expressions"]},
        {"session_id": "session_3", "overall_score": 6.9, "weak_areas": ["pronunciation", "fluency"]}
    ]
    
    agent = StandardAgent()
    
    try:
        advice = await agent.provide_personalized_advice(
            user_history=user_history,
            recent_performance=recent_performance
        )
        
        print("✅ Personalized Advice Results:")
        print(json.dumps(advice, indent=2))
        return advice
        
    except Exception as e:
        print(f"❌ Error generating advice: {e}")
        return None


async def main():
    """Main test function"""
    print("🚀 Starting Standard Agent Tests")
    print("=" * 60)
    
    print(f"📋 Configuration:")
    print(f"   - OpenAI API Key: {'✅ Set' if settings.openai_api_key else '❌ Missing'}")
    print(f"   - Model: gpt-4o (standard)")
    print(f"   - Test timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # Test 1: Feedback Analysis
        feedback = await test_feedback_analysis()
        
        # Test 2: Homework Generation (depends on feedback)
        homework = await test_homework_generation(feedback)
        
        # Test 3: Flashcard Creation
        flashcards = await test_flashcard_creation()
        
        # Test 4: Exercise Generation
        exercises = await test_exercise_generation()
        
        # Test 5: Personalized Advice
        advice = await test_personalized_advice()
        
        print("\n" + "=" * 60)
        print("📊 Test Summary:")
        print(f"   - Feedback Analysis: {'✅ PASS' if feedback else '❌ FAIL'}")
        print(f"   - Homework Generation: {'✅ PASS' if homework else '❌ FAIL'}")
        print(f"   - Flashcard Creation: {'✅ PASS' if flashcards else '❌ FAIL'}")
        print(f"   - Exercise Generation: {'✅ PASS' if exercises else '❌ FAIL'}")
        print(f"   - Personalized Advice: {'✅ PASS' if advice else '❌ FAIL'}")
        
        print("\n✅ Standard Agent tests completed!")
        
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        logger.exception("Test suite error")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Tests interrupted by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)
