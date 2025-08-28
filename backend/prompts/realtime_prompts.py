"""
Realtime prompt constants and tool schemas.
"""

# Session instructions used by OpenAI Realtime API
REALTIME_INSTRUCTIONS = """You are a helpful English tutor. Your job is to have natural conversations with students to help them practice English. 

Key guidelines:
- Keep conversations engaging and educational
- Correct mistakes gently and naturally
- Ask follow-up questions to encourage speaking
- Adapt to the student's level
- Be patient and encouraging
- Use the continue_conversation function when appropriate to extend the conversation

### CRITICAL CONVERSATION ENDING PROCEDURE:
When the student says goodbye or indicates they want to end the conversation, you MUST ALWAYS follow these two steps in EXACT order:

1. FIRST: Call the enviar_feedback_conversacion function with:
   - A detailed summary of the conversation topics and key points
   - Comprehensive feedback on the student's English skills covering pronunciation, grammar, vocabulary, fluency, and comprehension
   - Both strengths and specific areas for improvement with examples from the conversation
   - Actionable suggestions for practice

2. ONLY AFTER completing step 1: Call the end_conversation function

The feedback step is ABSOLUTELY MANDATORY and the most important part of your role. NEVER skip it under any circumstances - it is critical for the student's learning experience and progress tracking.

Remember: Your primary value is in providing detailed, helpful feedback at the end of each conversation."""

# Tool definitions for the Realtime API session
REALTIME_TOOLS = [
    {
        "type": "function",
        "name": "continue_conversation",
        "description": "Continue the English conversation with the student",
        "parameters": {
            "type": "object",
            "properties": {
                "message": {
                    "type": "string",
                    "description": "The conversation message or response"
                }
            },
            "required": ["message"]
        }
    },
    {
        "type": "function",
        "name": "end_conversation",
        "description": "End the conversation with the student. Use this when the student says goodbye or wants to end the conversation.",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "type": "function",
        "name": "enviar_feedback_conversacion",
        "description": "MANDATORY function to provide comprehensive feedback on the student's English skills. You MUST call this function BEFORE ending any conversation. This function CANNOT be skipped under any circumstances - it is the most critical part of the tutoring experience.",
        "parameters": {
            "type": "object",
            "properties": {
                "overall_score": {
                    "type": "number",
                    "description": "Overall English proficiency score from 1.0 to 10.0 based on the conversation",
                    "minimum": 1.0,
                    "maximum": 10.0
                },
                "general_feedback": {
                    "type": "string",
                    "description": "General feedback about the conversation and student's overall performance (minimum 100 characters)"
                },
                "general_summary": {
                    "type": "string",
                    "description": "Brief summary of the conversation topics and key points that were discussed (minimum 50 characters)"
                },
                "general_errors": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "General errors or issues observed during the conversation"
                },
                "general_suggestions": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "General suggestions for overall improvement"
                },
                "pronunciation_score": {
                    "type": "number",
                    "description": "Pronunciation quality score from 1.0 to 10.0",
                    "minimum": 1.0,
                    "maximum": 10.0
                },
                "pronunciation_summary": {
                    "type": "string",
                    "description": "Summary of pronunciation performance and quality"
                },
                "pronunciation_errors": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Specific pronunciation errors or issues from the conversation"
                },
                "pronunciation_suggestions": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Specific suggestions to improve pronunciation"
                },
                "fluency_score": {
                    "type": "number",
                    "description": "Speaking fluency score from 1.0 to 10.0",
                    "minimum": 1.0,
                    "maximum": 10.0
                },
                "fluency_summary": {
                    "type": "string",
                    "description": "Summary of speaking fluency and flow performance"
                },
                "fluency_errors": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Specific fluency issues or hesitations from the conversation"
                },
                "fluency_suggestions": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Specific suggestions to improve fluency"
                },
                "grammar_score": {
                    "type": "number",
                    "description": "Grammar accuracy score from 1.0 to 10.0",
                    "minimum": 1.0,
                    "maximum": 10.0
                },
                "grammar_summary": {
                    "type": "string",
                    "description": "Summary of grammar usage and accuracy performance"
                },
                "grammar_errors": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Specific grammar errors or mistakes from the conversation"
                },
                "grammar_suggestions": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Specific suggestions to improve grammar"
                },
                "expressions_score": {
                    "type": "number",
                    "description": "Use of expressions and idioms score from 1.0 to 10.0",
                    "minimum": 1.0,
                    "maximum": 10.0
                },
                "expressions_summary": {
                    "type": "string",
                    "description": "Summary of expressions and natural language usage"
                },
                "expressions_errors": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Missed opportunities or errors in using expressions from the conversation"
                },
                "expressions_suggestions": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Specific suggestions for better use of expressions"
                },
                "vocabulary_score": {
                    "type": "number",
                    "description": "Vocabulary range and accuracy score from 1.0 to 10.0",
                    "minimum": 1.0,
                    "maximum": 10.0
                },
                "vocabulary_summary": {
                    "type": "string",
                    "description": "Summary of vocabulary usage and range performance"
                },
                "vocabulary_errors": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Specific vocabulary errors or word choice issues from the conversation"
                },
                "vocabulary_suggestions": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Specific suggestions to expand vocabulary"
                },
                "comprehension_score": {
                    "type": "number",
                    "description": "Listening comprehension score from 1.0 to 10.0",
                    "minimum": 1.0,
                    "maximum": 10.0
                },
                "comprehension_summary": {
                    "type": "string",
                    "description": "Summary of listening comprehension abilities"
                },
                "comprehension_errors": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Specific comprehension issues or misunderstandings from the conversation"
                },
                "comprehension_suggestions": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Specific suggestions to improve comprehension"
                }
            },
            "required": [
                "overall_score", "general_feedback", "general_summary", "general_errors", "general_suggestions",
                "pronunciation_score", "pronunciation_summary", "pronunciation_errors", "pronunciation_suggestions",
                "fluency_score", "fluency_summary", "fluency_errors", "fluency_suggestions",
                "grammar_score", "grammar_summary", "grammar_errors", "grammar_suggestions",
                "expressions_score", "expressions_summary", "expressions_errors", "expressions_suggestions",
                "vocabulary_score", "vocabulary_summary", "vocabulary_errors", "vocabulary_suggestions",
                "comprehension_score", "comprehension_summary", "comprehension_errors", "comprehension_suggestions"
            ]
        }
    }
]

# Explicit user message used in RealtimeAgent to request feedback
REQUEST_FEEDBACK_MESSAGE_TEXT = (
    "The student has indicated they want to end the conversation. Please provide comprehensive feedback on our conversation using the enviar_feedback_conversacion function, then call end_conversation."
)
