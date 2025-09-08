"""
Standard Agent for text-based interactions using GPT-4o
Handles feedback analysis, homework generation, exercises, and other non-realtime tasks
"""
import asyncio
import json
from typing import Dict, List, Any, Optional, Union
from datetime import datetime

from core.logging import get_logger
from core.colors import colorize, Colors
from services.session_state import SessionState
from services.openai_service import OpenAIService
from prompts import (
    FEEDBACK_ANALYSIS_SYSTEM_PROMPT,
    HOMEWORK_SYSTEM_PROMPT,
    FLASHCARDS_SYSTEM_PROMPT,
    build_exercises_system_prompt,
    ADVICE_SYSTEM_PROMPT,
)

logger = get_logger(__name__)


class StandardAgent:
    """
    Agent for standard text-based interactions using GPT-4o
    Handles feedback analysis, homework generation, exercises, and other non-realtime tasks
    """
    
    def __init__(self):
        self.openai_service = OpenAIService()
        
    async def analyze_conversation_feedback(
        self, 
        session_state: SessionState,
        user_transcript: str,
        ai_transcript: str,
        conversation_duration: int
    ) -> Dict[str, Any]:
        """
        Analyze conversation and generate detailed feedback across 6 pillars
        
        Args:
            session_state: Current session state
            user_transcript: Complete user transcript
            ai_transcript: Complete AI transcript  
            conversation_duration: Duration in seconds
            
        Returns:
            Structured feedback with scores, errors, suggestions, and homework
        """
        logger.info(f"🔍 Analyzing conversation feedback for session {session_state.session_id}")
        
        system_prompt = FEEDBACK_ANALYSIS_SYSTEM_PROMPT

        user_prompt = f"""
**Conversation Analysis Request**

**Duration:** {conversation_duration} seconds
**Session ID:** {session_state.session_id}

**Student Transcript:**
{user_transcript}

**AI Tutor Transcript:**
{ai_transcript}

Please analyze this conversation and provide detailed feedback following the structure requested.
"""

        try:
            response = await self._send_chat_completion(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.3,
                response_format="json"
            )
            
            feedback = json.loads(response)
            logger.info(colorize(f"✅ Feedback analysis completed for session {session_state.session_id}", Colors.BRIGHT_GREEN))
            return feedback
            
        except Exception as e:
            logger.error(f"❌ Error analyzing conversation feedback: {e}")
            return self._get_fallback_feedback()
    
    async def generate_homework(
        self,
        session_state: SessionState,
        feedback: Dict[str, Any],
        previous_homework: Optional[List[Dict]] = None
    ) -> Dict[str, List[Dict]]:
        """
        Generate personalized homework based on feedback and previous assignments
        
        Args:
            session_state: Current session state
            feedback: Feedback from conversation analysis
            previous_homework: Previous homework assignments
            
        Returns:
            Categorized homework assignments
        """
        logger.info(f"📚 Generating homework for session {session_state.session_id}")
        
        system_prompt = HOMEWORK_SYSTEM_PROMPT

        previous_hw_text = ""
        if previous_homework:
            previous_hw_text = f"\n**Previous Homework:**\n{json.dumps(previous_homework, indent=2)}"

        user_prompt = f"""
**Homework Generation Request**

**Session:** {session_state.session_id}
**Feedback Summary:** {json.dumps(feedback, indent=2)}
{previous_hw_text}

Generate personalized homework assignments based on this feedback.
"""

        try:
            response = await self._send_chat_completion(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.4
            )
            
            homework = json.loads(response)
            logger.info(colorize(f"✅ Homework generated for session {session_state.session_id}", Colors.BRIGHT_GREEN))
            return homework
            
        except Exception as e:
            logger.error(f"❌ Error generating homework: {e}")
            return self._get_fallback_homework()
    
    async def create_flashcards(
        self,
        vocabulary_items: List[str],
        grammar_concepts: List[str],
        errors: List[Dict[str, str]]
    ) -> List[Dict[str, Any]]:
        """
        Create Anki-style flashcards from vocabulary, grammar, and errors
        
        Args:
            vocabulary_items: List of vocabulary words/phrases
            grammar_concepts: List of grammar concepts
            errors: List of common errors with corrections
            
        Returns:
            List of flashcard objects
        """
        logger.info("🃏 Creating flashcards from learning materials")
        
        system_prompt = FLASHCARDS_SYSTEM_PROMPT

        user_prompt = f"""
**Flashcard Creation Request**

**Vocabulary Items:**
{json.dumps(vocabulary_items, indent=2)}

**Grammar Concepts:**
{json.dumps(grammar_concepts, indent=2)}

**Common Errors:**
{json.dumps(errors, indent=2)}

Create comprehensive flashcards covering all these materials.
"""

        try:
            response = await self._send_chat_completion(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.5
            )
            
            flashcards = json.loads(response)
            logger.info(colorize(f"✅ Created {len(flashcards)} flashcards", Colors.BRIGHT_GREEN))
            return flashcards
            
        except Exception as e:
            logger.error(f"❌ Error creating flashcards: {e}")
            return []
    
    async def generate_exercises(
        self,
        topic: str,
        difficulty: str = "intermediate",
        exercise_type: str = "mixed"
    ) -> Dict[str, Any]:
        """
        Generate practice exercises for specific topics
        
        Args:
            topic: Topic to focus on (grammar, vocabulary, etc.)
            difficulty: beginner, intermediate, advanced
            exercise_type: grammar, vocabulary, comprehension, mixed
            
        Returns:
            Structured exercises with questions and answers
        """
        logger.info(f"📝 Generating {exercise_type} exercises for topic: {topic}")
        
        system_prompt = build_exercises_system_prompt(topic, difficulty, exercise_type)

        user_prompt = f"""
Create practice exercises for:
- **Topic**: {topic}
- **Difficulty**: {difficulty}
- **Type**: {exercise_type}

Generate 5-10 varied exercises that help reinforce learning.
"""

        try:
            response = await self._send_chat_completion(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.4
            )
            
            exercises = json.loads(response)
            logger.info(colorize(f"✅ Generated exercises for {topic}", Colors.BRIGHT_GREEN))
            return exercises
            
        except Exception as e:
            logger.error(f"❌ Error generating exercises: {e}")
            return {"exercises": [], "error": str(e)}
    
    async def provide_personalized_advice(
        self,
        user_history: Dict[str, Any],
        recent_performance: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Generate personalized learning advice based on user history
        
        Args:
            user_history: Complete user learning history
            recent_performance: Recent session performances
            
        Returns:
            Personalized advice and recommendations
        """
        logger.info("💡 Generating personalized learning advice")
        
        system_prompt = ADVICE_SYSTEM_PROMPT

        user_prompt = f"""
**Personalized Advice Request**

**User History:**
{json.dumps(user_history, indent=2)}

**Recent Performance:**
{json.dumps(recent_performance, indent=2)}

Provide comprehensive, personalized learning advice.
"""

        try:
            response = await self._send_chat_completion(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.6
            )
            
            advice = json.loads(response)
            logger.info(colorize("✅ Personalized advice generated", Colors.BRIGHT_GREEN))
            return advice
            
        except Exception as e:
            logger.error(f"❌ Error generating advice: {e}")
            return {"error": str(e)}
    
    async def _send_chat_completion(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.7,
        response_format: str = "json"
    ) -> str:
        """
        Send chat completion request to OpenAI GPT-4o
        
        Args:
            system_prompt: System instructions
            user_prompt: User message
            temperature: Response randomness
            response_format: Expected response format
            
        Returns:
            Response content from OpenAI
        """
        try:
            # Use the OpenAI service to send chat completion
            # This will need to be implemented in openai_service.py
            response = await self.openai_service.send_chat_completion(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=temperature,
                response_format=response_format
            )
            
            return response
            
        except Exception as e:
            logger.error(f"❌ Error in chat completion: {e}")
            raise
    
    def _get_fallback_feedback(self) -> Dict[str, Any]:
        """Fallback feedback structure if analysis fails"""
        return {
            "pillars": {
                "pronunciation": {"score": 5, "feedback": "Unable to analyze - please try again"},
                "fluency": {"score": 5, "feedback": "Unable to analyze - please try again"},
                "grammar": {"score": 5, "feedback": "Unable to analyze - please try again"},
                "expressions": {"score": 5, "feedback": "Unable to analyze - please try again"},
                "vocabulary": {"score": 5, "feedback": "Unable to analyze - please try again"},
                "comprehension": {"score": 5, "feedback": "Unable to analyze - please try again"}
            },
            "summary": "Analysis failed - please try again",
            "errors": [],
            "vocabulary": [],
            "homework_suggestions": []
        }
    
    def _get_fallback_homework(self) -> Dict[str, List[Dict]]:
        """Fallback homework structure if generation fails"""
        return {
            "vocabulary": [{"item": "Review basic vocabulary", "priority": "medium"}],
            "grammar": [{"item": "Practice basic grammar", "priority": "medium"}],
            "pronunciation": [{"item": "Practice pronunciation", "priority": "low"}],
            "comprehension": [{"item": "Listen to English content", "priority": "low"}]
        }
