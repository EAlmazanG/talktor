#!/usr/bin/env python3
"""
Test script to verify feedback is saved correctly with English column names
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

import asyncio
import json
from services.conversation_flow import ConversationFlow
from services.persistence_service import PersistenceService
from core.logging import setup_logging

# Setup logging
setup_logging("test_feedback_english_columns")
import logging
logger = logging.getLogger(__name__)

async def test_feedback_with_english_columns():
    """Test that feedback is saved correctly with English column names"""
    
    logger.info("🚀 Starting Feedback English Columns Test")
    logger.info("=" * 60)
    
    user_id = "test_user_english_columns"
    
    try:
        # Create ConversationFlow
        flow = ConversationFlow(user_id=user_id)
        logger.info(f"✅ ConversationFlow initialized for user: {user_id}")
        
        # Mock feedback data with comprehensive structure
        mock_feedback_data = {
            "overall_score": 7.8,
            "general": {
                "feedback": "Good conversation with room for improvement",
                "errores": ["Some hesitation", "Minor pronunciation issues"],
                "sugerencias": ["Practice daily", "Focus on fluency"]
            },
            "pillars": {
                "pronunciation": {
                    "score": 8.0,
                    "resumen": "Clear pronunciation overall",
                    "errores": ["Difficulty with 'th' sounds"],
                    "sugerencias": ["Practice 'th' sound exercises"]
                },
                "fluency": {
                    "score": 7.5,
                    "resumen": "Natural flow with some hesitation",
                    "errores": ["Occasional pauses"],
                    "sugerencias": ["Practice speaking without stopping"]
                },
                "grammar": {
                    "score": 8.2,
                    "resumen": "Good grammar structure",
                    "errores": ["Past tense confusion"],
                    "sugerencias": ["Review past tense rules"]
                },
                "expressions": {
                    "score": 7.0,
                    "resumen": "Limited use of expressions",
                    "errores": ["Repetitive phrases"],
                    "sugerencias": ["Learn more idiomatic expressions"]
                },
                "vocabulary": {
                    "score": 8.5,
                    "resumen": "Rich vocabulary usage",
                    "errores": ["Some word choice issues"],
                    "sugerencias": ["Expand business vocabulary"]
                },
                "comprehension": {
                    "score": 9.0,
                    "resumen": "Excellent understanding",
                    "errores": [],
                    "sugerencias": ["Continue listening practice"]
                }
            }
        }
        
        # Mock conversation data
        mock_conversation_json = {
            "session_id": "test-session-english-columns",
            "message_count": 6,
            "duration_seconds": 45,
            "messages": [
                {"role": "user", "content": "Hello, how are you?", "timestamp": "2025-07-29T18:30:00", "order": 1},
                {"role": "assistant", "content": "I'm doing well, thank you!", "timestamp": "2025-07-29T18:30:01", "order": 2},
                {"role": "user", "content": "What's the weather like?", "timestamp": "2025-07-29T18:30:02", "order": 3},
                {"role": "assistant", "content": "It's sunny today.", "timestamp": "2025-07-29T18:30:03", "order": 4},
                {"role": "user", "content": "That's great!", "timestamp": "2025-07-29T18:30:04", "order": 5},
                {"role": "assistant", "content": "Yes, perfect weather for a walk.", "timestamp": "2025-07-29T18:30:05", "order": 6}
            ]
        }
        
        logger.info("💾 Testing persistence with comprehensive feedback...")
        
        # Save to database using PersistenceService
        persistence = PersistenceService()
        session_id = "test-session-english-columns-123"
        result = await persistence.save_complete_conversation(
            session_id=session_id,
            user_id=user_id,
            conversation_json=mock_conversation_json,
            feedback_data=mock_feedback_data,
            duration_seconds=45,
            token_count=150,
            estimated_cost=0.005
        )
        
        logger.info(f"📊 Persistence result: {result['summary']}")
        
        # Verify feedback was saved
        session_id = result['summary']['session_id']
        session_summary = await persistence.get_session_summary(session_id)
        
        if session_summary:
            feedback_info = session_summary['feedback']
            logger.info("✅ SUCCESS: Feedback retrieved from database")
            logger.info(f"   📊 Overall score: {feedback_info['overall_score']}")
            logger.info(f"   📝 General feedback: {feedback_info['general_feedback']}")
            logger.info(f"   🔢 Pillar count: {feedback_info['pillar_count']}")
            
            # Check specific pillars
            pillars = feedback_info['pillars']
            for pillar_name, pillar_data in pillars.items():
                logger.info(f"   🎯 {pillar_name.upper()}: score={pillar_data['score']}, summary='{pillar_data['summary'][:30]}...'")
            
            # Verify English column names are working
            if feedback_info['has_feedback'] and feedback_info['pillar_count'] == 6:
                logger.info("🎉 SUCCESS: All feedback saved with English column names!")
                logger.info("✅ Verified pillars:")
                for pillar in ['pronunciation', 'fluency', 'grammar', 'expressions', 'vocabulary', 'comprehension']:
                    if pillar in pillars:
                        logger.info(f"   ✅ {pillar}: ✓")
                    else:
                        logger.warning(f"   ❌ {pillar}: Missing")
                
                return True
            else:
                logger.error(f"❌ FAILURE: Expected 6 pillars, got {feedback_info['pillar_count']}")
                return False
        else:
            logger.error("❌ FAILURE: Could not retrieve session summary")
            return False
            
    except Exception as e:
        logger.error(f"❌ Test failed with error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

async def main():
    """Main test function"""
    logger.info("🧪 FEEDBACK ENGLISH COLUMNS TEST")
    logger.info("=" * 60)
    
    success = await test_feedback_with_english_columns()
    
    logger.info("=" * 60)
    if success:
        logger.info("🎉 ALL TESTS PASSED!")
        logger.info("✅ Feedback system working correctly with English column names")
    else:
        logger.error("❌ TEST FAILED!")
        logger.error("❌ Feedback system has issues with English column names")

if __name__ == "__main__":
    asyncio.run(main())
