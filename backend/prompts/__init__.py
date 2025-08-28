"""
Prompt modules for Talktor backend.
All prompt text and tool schemas are centralized here to keep logic clean.
"""

from .realtime_prompts import (
    REALTIME_INSTRUCTIONS,
    REALTIME_TOOLS,
    REQUEST_FEEDBACK_MESSAGE_TEXT,
)

from .standard_prompts import (
    FEEDBACK_ANALYSIS_SYSTEM_PROMPT,
    HOMEWORK_SYSTEM_PROMPT,
    FLASHCARDS_SYSTEM_PROMPT,
    build_exercises_system_prompt,
    ADVICE_SYSTEM_PROMPT,
)
