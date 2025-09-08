"""
Test script for conversation termination commands
"""
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.realtime_agent import RealtimeAgent

def test_termination_detection():
    """Test termination command detection"""
    print("\n🛑 Testing Termination Command Detection")
    print("=" * 50)
    
    # Create a RealtimeAgent instance for testing
    agent = RealtimeAgent(session_id="test_session")
    
    # Test cases: (transcript, should_terminate)
    test_cases = [
        # English termination commands
        ("stop", True),
        ("end", True),
        ("finish", True),
        ("quit", True),
        ("bye", True),
        ("goodbye", True),
        ("stop conversation", True),
        ("end conversation", True),
        ("stop talking", True),
        ("that's all", True),
        ("i'm done", True),
        ("stop please", True),
        
        # Spanish termination commands
        ("para", True),
        ("termina", True),
        ("finaliza", True),
        ("adiós", True),
        ("chao", True),
        ("para conversación", True),
        ("termina conversación", True),
        ("es todo", True),
        ("ya terminé", True),
        ("para por favor", True),
        
        # Case variations
        ("STOP", True),
        ("End", True),
        ("PARA", True),
        ("Termina", True),
        
        # With extra spaces
        ("  stop  ", True),
        ("  end conversation  ", True),
        
        # Phrases that start with termination words
        ("stop now", True),
        ("end this", True),
        ("para ya", True),
        
        # Non-termination commands (should NOT terminate)
        ("hello", False),
        ("how are you", False),
        ("I want to practice English", False),
        ("stop sign", False),  # "stop" in different context
        ("the end of the story", False),  # "end" in different context
        ("I stopped walking", False),  # "stop" as past tense
        ("let's continue", False),
        ("tell me more", False),
        ("what's next", False),
        ("I understand", False),
        ("very good", False),
        ("", False),  # Empty string
        ("   ", False),  # Only spaces
    ]
    
    passed = 0
    failed = 0
    
    for transcript, expected in test_cases:
        result = agent._is_termination_command(transcript)
        status = "✅" if result == expected else "❌"
        
        if result == expected:
            passed += 1
        else:
            failed += 1
            
        print(f"{status} '{transcript}' -> {result} (expected: {expected})")
    
    print(f"\n📊 Results: {passed} passed, {failed} failed")
    
    return failed == 0


def test_edge_cases():
    """Test edge cases for termination detection"""
    print("\n🔍 Testing Edge Cases")
    print("=" * 50)
    
    agent = RealtimeAgent(session_id="test_session_edge")
    
    edge_cases = [
        # Mixed language
        ("stop por favor", True),
        ("para please", True),
        
        # Very short phrases
        ("bye", True),
        ("end", True),
        ("para", True),
        
        # Longer phrases with termination words
        ("I want to stop", True),
        ("please end", True),
        ("quiero para", True),
        
        # Punctuation
        ("stop!", True),
        ("end.", True),
        ("para?", True),
        
        # Multiple words but still short
        ("stop now", True),
        ("end please", True),
        ("para ya", True),
        
        # Borderline cases (4+ words, should be more careful)
        ("I think we should stop", False),  # Longer phrase, context matters
        ("can you please stop talking", False),  # Longer, different context
        ("the movie will end soon", False),  # "end" in different context
    ]
    
    passed = 0
    failed = 0
    
    for transcript, expected in edge_cases:
        result = agent._is_termination_command(transcript)
        status = "✅" if result == expected else "❌"
        
        if result == expected:
            passed += 1
        else:
            failed += 1
            
        print(f"{status} '{transcript}' -> {result} (expected: {expected})")
    
    print(f"\n📊 Edge Cases: {passed} passed, {failed} failed")
    
    return failed == 0


def main():
    """Main test function"""
    print("🧪 Termination Command Detection Tests")
    print("=" * 60)
    
    # Run tests
    basic_test_passed = test_termination_detection()
    edge_test_passed = test_edge_cases()
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Summary:")
    print(f"   - Basic Detection: {'✅ PASS' if basic_test_passed else '❌ FAIL'}")
    print(f"   - Edge Cases: {'✅ PASS' if edge_test_passed else '❌ FAIL'}")
    
    if basic_test_passed and edge_test_passed:
        print("\n🎉 All termination detection tests passed!")
        print("\n💡 Usage Examples:")
        print("   - User says: 'stop' -> Conversation ends")
        print("   - User says: 'para' -> Conversation ends")
        print("   - User says: 'goodbye' -> Conversation ends")
        print("   - User says: 'end conversation' -> Conversation ends")
        print("   - User says: 'hello' -> Conversation continues")
        return True
    else:
        print("\n⚠️ Some tests failed. Check the implementation.")
        return False


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n🛑 Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        sys.exit(1)
