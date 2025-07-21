"""
Color utilities for enhanced logging
"""

class Colors:
    """ANSI color codes for terminal output"""
    
    # Basic colors
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    
    # Bright colors
    BRIGHT_RED = '\033[91;1m'
    BRIGHT_GREEN = '\033[92;1m'
    BRIGHT_YELLOW = '\033[93;1m'
    BRIGHT_BLUE = '\033[94;1m'
    BRIGHT_MAGENTA = '\033[95;1m'
    BRIGHT_CYAN = '\033[96;1m'
    
    # Styles
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    RESET = '\033[0m'
    
    # Background colors
    BG_RED = '\033[101m'
    BG_GREEN = '\033[102m'
    BG_YELLOW = '\033[103m'
    BG_BLUE = '\033[104m'

def colorize(text: str, color: str) -> str:
    """Add color to text"""
    return f"{color}{text}{Colors.RESET}"

def highlight_keywords(text: str, keywords: dict) -> str:
    """
    Highlight specific keywords in text with colors
    
    Args:
        text: The text to colorize
        keywords: Dict mapping keywords to colors
    
    Returns:
        Colorized text
    """
    result = text
    for keyword, color in keywords.items():
        if keyword in result:
            colored_keyword = colorize(keyword, color)
            result = result.replace(keyword, colored_keyword)
    return result

# Predefined keyword color schemes
AUDIO_KEYWORDS = {
    "SPEECH STARTED": Colors.BRIGHT_RED,
    "AI STARTED SPEAKING": Colors.BRIGHT_GREEN,
    "FINISHED SPEAKING": Colors.BRIGHT_BLUE,
    "clearing audio buffer": Colors.BRIGHT_YELLOW,
    "Microphone activated": Colors.CYAN,
    "Audio streams started": Colors.GREEN,
    "interruption": Colors.BRIGHT_MAGENTA,
    "cancellation": Colors.MAGENTA,
    "🚨": Colors.BRIGHT_RED,
    "🎧": Colors.BRIGHT_CYAN,
}

SESSION_KEYWORDS = {
    "session": Colors.BLUE,
    "Connected": Colors.GREEN,
    "Starting": Colors.CYAN,
    "Stopping": Colors.YELLOW,
    "Error": Colors.RED,
    "WARNING": Colors.YELLOW,
    "SUCCESS": Colors.GREEN,
    "🚀": Colors.BRIGHT_CYAN,
    "✅": Colors.BRIGHT_GREEN,
    "🔗": Colors.BRIGHT_BLUE,
    "⚙️": Colors.BRIGHT_YELLOW,
    "🛑": Colors.BRIGHT_RED,
}

def colorize_audio_log(text: str) -> str:
    """Colorize audio-related log messages"""
    return highlight_keywords(text, AUDIO_KEYWORDS)

def colorize_session_log(text: str) -> str:
    """Colorize session-related log messages"""
    return highlight_keywords(text, SESSION_KEYWORDS)
