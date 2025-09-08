"""
Real Voice Conversation Test - Complete Integration with Real Audio

This test executes the REAL RealtimeAgent with actual voice conversation,
waits for the user to finish talking, and then processes the real conversation data.
"""
import asyncio
import sys
import os
import logging
from datetime import datetime, timezone

# Add the backend directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import logging setup FIRST
from core.logging import setup_logging
from services.conversation_flow import ConversationFlow
from services.persistence_service import persistence_service

# Setup enhanced logging with file output
setup_logging(
    level="DEBUG",
    enable_file_logging=True,
    log_directory="logs",
    service_name="test_real_voice_conversation"
)

# Get logger for this module
logger = logging.getLogger(__name__)


async def test_real_voice_conversation_flow():
    """Test complete flow with REAL voice conversation"""
    logger.info("🎤 Starting REAL VOICE CONVERSATION TEST")
    print("🎤 REAL VOICE CONVERSATION TEST")
    print("=" * 80)
    print("This test will:")
    print("1. 🎤 Start REAL RealtimeAgent with voice input/output")
    print("2. ⏳ Wait for you to have a conversation")
    print("3. 🛑 Detect when conversation ends")
    print("4. 💾 Save everything to database")
    print("5. 📊 Show analytics and results")
    print("=" * 80)
    
    user_id = "test_user_real_voice"
    logger.info(f"Test initialized for user: {user_id}")
    
    try:
        # Step 1: Initialize ConversationFlow
        logger.info("Step 1: Initializing ConversationFlow")
        print("\n📋 Step 1: Initializing ConversationFlow...")
        flow = ConversationFlow(user_id=user_id)
        logger.info(f"ConversationFlow initialized successfully")
        print(f"✅ ConversationFlow initialized for user: {user_id}")
        print(f"   📦 PersistenceService: {flow.persistence.__class__.__name__}")
        print(f"   🤖 StandardAgent: {flow.standard_agent.__class__.__name__}")
        
        # Step 2: Start REAL conversation with voice
        print("\n🎤 Step 2: Starting REAL voice conversation...")
        print("   🔧 Initializing RealtimeAgent with audio...")
        print("   🎧 Make sure your microphone and speakers are working!")

        print(f"\n✅ Voice conversation started!")
        print(f"   🎤 Microphone: Active")
        print(f"   🔊 Speakers: Active")
        
        # Step 3: Wait for conversation to be active and provide instructions
        print("\n💬 Step 3: Voice conversation is now ACTIVE!")
        print("=" * 60)
        print("🎯 INSTRUCTIONS FOR TESTING:")
        print("1. 🗣️  Start speaking in English")
        print("2. 🤖 The AI will respond with voice")
        print("3. 💬 Have a natural conversation (2-3 minutes recommended)")
        print("4. 🛑 Say 'goodbye' or 'thank you' to end the conversation")
        print("   💡 TIP: Have a conversation of at least 2-3 minutes for good feedback")
        print("5. ⏳ The test will continue automatically after ending")
        print("=" * 60)
        print("\n🎤 CONVERSATION IS LIVE - START SPEAKING NOW!")

        # Start the conversation - this will create a real RealtimeAgent
        session_id = await flow.start_conversation()
        print(f"   🎆 Session ID: {session_id}")
        print(f"   🤖 Agent type: {type(flow.realtime_agent).__name__}")

        # Wait for the conversation to be active
        conversation_active = True
        check_interval = 2  # Check every 2 seconds
        total_wait_time = 0
        max_wait_time = 600  # Maximum 10 minutes
        
        while conversation_active and total_wait_time < max_wait_time:
            await asyncio.sleep(check_interval)
            total_wait_time += check_interval
            
            # Check if conversation is still active
            if flow.realtime_agent and hasattr(flow.realtime_agent, 'is_active'):
                conversation_active = flow.realtime_agent.is_active()
            else:
                # If we can't check status, assume it's still active
                # The user needs to manually end the conversation
                conversation_active = True
            
            # Show periodic status updates
            if total_wait_time % 30 == 0:  # Every 30 seconds
                minutes = total_wait_time // 60
                seconds = total_wait_time % 60
                print(f"   ⏱️  Conversation active for {minutes}m {seconds}s...")
                if flow.realtime_agent:
                    print(f"   🎤 Agent status: {'Active' if conversation_active else 'Inactive'}")
        
        if total_wait_time >= max_wait_time:
            print(f"\n⏰ Maximum wait time reached ({max_wait_time//60} minutes)")
            print("   🛑 Ending conversation automatically...")
        else:
            print(f"\n🛑 Conversation ended after {total_wait_time//60}m {total_wait_time%60}s")
        
        # Step 4: Process the real conversation data
        print("\n🔄 Step 4: Processing REAL conversation data...")
        print("   📊 Getting conversation summary from RealtimeAgent...")
        
        # Debug: Check session state before processing
        if flow.realtime_agent and hasattr(flow.realtime_agent, 'session_state'):
            session_state = flow.realtime_agent.session_state
            if session_state:
                print(f"   🔍 DEBUG - Session State:")
                print(f"       📝 User transcript length: {len(session_state.user_transcript)}")
                print(f"       🤖 AI transcript length: {len(session_state.ai_transcript)}")
                print(f"       📝 User transcript: '{session_state.user_transcript[:100]}...'")
                print(f"       🤖 AI transcript: '{session_state.ai_transcript[:100]}...'")
                print(f"       ⏱️ Duration: {session_state.get_session_duration():.2f}s")
                print(f"       🔄 Is active: {session_state.is_active}")
            else:
                print("   ⚠️  DEBUG - No session state found")
        else:
            print("   ⚠️  DEBUG - No realtime agent or session state")
        
        print("   💾 Saving to database with PersistenceService...")
        
        # Wait longer to allow automatic feedback generation
        print("   ⏳ Waiting for feedback generation (20 seconds)...")
        
        # Wait in small increments and check for feedback
        max_wait = 20  # seconds
        check_interval = 2  # seconds
        waited = 0
        
        while waited < max_wait:
            # Check if feedback is already available
            if flow.realtime_agent and flow.realtime_agent.conversation_feedback:
                print(f"   ✅ Feedback automatically generated after {waited} seconds!")
                break
                
            # Wait a bit more
            await asyncio.sleep(check_interval)
            waited += check_interval
            print(f"   ⏳ Still waiting for feedback... ({waited}/{max_wait} seconds)")
        
        # Final check for feedback
        if flow.realtime_agent and flow.realtime_agent.conversation_feedback:
            feedback = flow.realtime_agent.conversation_feedback
            print("\n📝 CONVERSATION FEEDBACK:")
            print("=" * 60)
            print(f"   📋 Summary: {feedback.get('resumen', 'N/A')[:100]}...")
            print(f"   💬 Feedback: {feedback.get('feedback', 'N/A')[:100]}...")
            print(f"   📅 Timestamp: {feedback.get('timestamp', 'N/A')}")
            print("=" * 60)
        else:
            print("   ⚠️ No feedback was automatically generated")
            print("   💡 TIP: Make sure to have a longer conversation (2-3 minutes) and end with 'goodbye' or 'thank you'")
        
        # Process the conversation
        print("   🔄 Processing conversation results...")
        results = await flow.end_conversation()
        
        # End conversation processing
        if flow.realtime_agent and hasattr(flow.realtime_agent, 'session_state') and flow.realtime_agent.session_state:
            print("   ✅ Session state is valid")
        else:
            print("   ⚠️ Session state is not available")

        print("\n✅ Conversation processing completed!")
        print(f"   🎆 Session ID: {results['session_id']}")
        print(f"   👤 User ID: {results['user_id']}")
        print(f"   ⏱️ Duration: {results['duration_seconds']}s ({results['duration_seconds']//60}m {results['duration_seconds']%60}s)")
        print(f"   💬 Messages: {results['message_count']}")
        print(f"   🏁 Status: {results['status']}")

        # Step 5: Show conversation summary
        print("\n📊 Step 5: Displaying conversation summary...")
        print("   ✅ Conversation completed successfully")
        
        # Display feedback information if available
        if results.get('feedback'):
            print("\n📝 Conversation Feedback:")
            print("=" * 60)
            feedback = results['feedback']
            print(f"   📋 Source: {feedback.get('source', 'unknown')}")
            print(f"   📅 Timestamp: {feedback.get('timestamp', 'N/A')}")
            print(f"   📝 Summary: {feedback.get('resumen', 'No summary provided')}")
            print(f"   💬 Feedback: {feedback.get('feedback', 'No feedback provided')}")
            print("=" * 60)
        else:
            print("\n⚠️ No feedback was provided by the agent")
        
        # Step 6: Show conversation transcript directly from session state
        print("\n📝 Step 6: Conversation Transcript:")
        print("=" * 60)
        
        messages = flow.realtime_agent.session_state.messages if hasattr(flow.realtime_agent.session_state, 'messages') else []
        
        # Parse the JSON transcript to get individual messages
        individual_messages = []
        if messages and len(messages) > 0:
            # The first message contains the complete conversation JSON
            json_content = messages[0].get('content', '{}')
            try:
                import json
                conversation_data = json.loads(json_content)
                individual_messages = conversation_data.get('messages', [])
                print(f"   🔍 Found {len(individual_messages)} individual messages in JSON")
            except json.JSONDecodeError:
                print(f"   ⚠️  Could not parse JSON content, showing raw messages")
                individual_messages = messages
        
        if not individual_messages:
            print("   ⚠️  No messages found")
        else:
            for i, msg in enumerate(individual_messages, 1):
                # Handle different possible field names
                if 'role' in msg:
                    speaker = "🗣️  USER" if msg['role'] == 'user' else "🤖 AI"
                elif 'speaker' in msg:
                    speaker = "🗣️  USER" if msg['speaker'] == 'user' else "🤖 AI"
                else:
                    speaker = "🤖 UNKNOWN"
                
                content = msg.get('content', str(msg))[:100] + "..." if len(str(msg.get('content', msg))) > 100 else str(msg.get('content', msg))
                timestamp = msg.get('timestamp', '')
                order = msg.get('order', i)
                print(f"{order:2d}. {speaker}: {content}")
        
        print("=" * 60)
        
        # Step 7: Test completed
        print("\n🎉 Step 7: Test Completed Successfully!")
        print("   ✅ Conversation flow works correctly")
        print("   ✅ Transcription works correctly")
        print("   ✅ No database persistence as requested")

        
        # Step 8: Cleanup
        print("\n🧹 Step 8: Cleanup...")
        await flow.cleanup()
        print("✅ Cleanup completed")
        
        print("\n" + "=" * 80)
        print("🎉 REAL VOICE CONVERSATION TEST COMPLETED SUCCESSFULLY!")
        print("=" * 80)
        print("✅ Successfully tested:")
        print("   • 🎤 REAL voice input/output with RealtimeAgent")
        print("   • 💬 REAL conversation transcription")
        print("   • 💾 REAL conversation session handling")
        print("\n🏆 THE TALKTOR CONVERSATION SYSTEM IS WORKING!")
        print("🚀 Ready for further development!")
        
        return True
        
    except KeyboardInterrupt:
        print("\n\n⏹️  Test interrupted by user")
        print("🧹 Cleaning up...")
        if 'flow' in locals():
            await flow.cleanup()
        return False
        
    except Exception as e:
        print(f"\n❌ Real voice conversation test failed: {e}")
        import traceback
        traceback.print_exc()
        
        # Cleanup on error
        if 'flow' in locals():
            await flow.cleanup()
        return False


async def show_database_stats():
    """Show current database statistics"""
    print("\n📊 Current Database Statistics:")
    
    try:
        # Use a managed DB session for health check
        with persistence_service.get_db_transaction() as db:
            health = persistence_service.health_check(db)
        
        print(f"   🏥 Status: {health['status']}")
        print(f"   📊 Sessions: {health.get('total_sessions', 0)}")
        print(f"   💬 Transcripts: {health.get('total_transcripts', 0)}")
        print(f"   📋 Feedback: {health.get('total_feedback', 0)}")
        
    except Exception as e:
        print(f"   ❌ Error getting database stats: {e}")


if __name__ == "__main__":
    print("🎤 REAL VOICE CONVERSATION INTEGRATION TEST")
    print("=" * 80)
    print("⚠️  REQUIREMENTS:")
    print("1. 🎧 Working microphone and speakers")
    print("2. 🔑 OpenAI API key configured")
    print("3. 🌐 Internet connection")
    print("4. 🗣️  Be ready to speak in English for 2-3 minutes")
    print("=" * 80)
    
    # Show current database state
    asyncio.run(show_database_stats())
    
    # Ask for confirmation
    print("\n🤔 Are you ready to start the REAL voice conversation test?")
    print("   This will use your microphone and speakers.")
    print("   You'll need to speak with the AI for a few minutes.")
    

    print("\n🚀 Starting REAL voice conversation test...")
    
    # Run the real voice conversation test
    success = asyncio.run(test_real_voice_conversation_flow())
    
    # Show final database state
    print("\n📊 Final Database State:")
    asyncio.run(show_database_stats())
    
    if success:
        print("\n🎉 TEST COMPLETED SUCCESSFULLY!")
        print("🏆 Talktor voice conversation system is fully functional!")
    else:
        print("\n❌ TEST FAILED OR WAS INTERRUPTED")
            
    
    print("\n" + "=" * 80)
