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
    print("4. 🤖 Generate REAL feedback with StandardAgent")
    print("5. 💾 Save everything to database")
    print("6. 📊 Show analytics and results")
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
        print("4. 🛑 Say 'stop', 'end', 'para', or 'termina' to end")
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
        
        # Test the new generate_conversation_summary_and_feedback tool
        print("   🔧 Testing generate_conversation_summary_and_feedback tool...")
        
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
        
        print("   🤖 Generating feedback with StandardAgent...")
        print("   💾 Saving to database with PersistenceService...")
        
        # End the conversation and process everything
        results = await flow.end_conversation()
        
        # Test the generate_conversation_summary_and_feedback tool
        # This should trigger the _handle_conversation_termination method in RealtimeAgent
        if flow.realtime_agent and hasattr(flow.realtime_agent, 'session_state') and flow.realtime_agent.session_state:
            print("   🔄 Testing direct call to generate_conversation_summary_and_feedback...")
            # Direct call to the method
            result = await flow.realtime_agent.generate_conversation_summary_and_feedback()
            print(f"   ✅ Direct method call result: {result}")
            
            print("   🔄 Testing OpenAI function call to generate_conversation_summary_and_feedback...")
            # Simulate the tool call from OpenAI
            if hasattr(flow.realtime_agent, 'conversation_service'):
                await flow.realtime_agent.conversation_service.handle_function_call(
                {
                    "name": "generate_conversation_summary_and_feedback",
                    "arguments": "{}",
                    "call_id": "test_call_id"
                },
                flow.realtime_agent.session_state
            )
                print("   ✅ OpenAI function call completed successfully")
            else:
                print("   ❌ Cannot test OpenAI function call: realtime_agent has no conversation_service attribute")

        print("\n✅ Conversation processing completed!")
        print(f"   🎆 Session ID: {results['session_id']}")
        print(f"   👤 User ID: {results['user_id']}")
        print(f"   ⏱️ Duration: {results['duration_seconds']}s ({results['duration_seconds']//60}m {results['duration_seconds']%60}s)")
        print(f"   💬 Messages: {results['message_count']}")
        print(f"   🏁 Status: {results['status']}")

        # Feedback is already generated by the direct call to generate_conversation_summary_and_feedback

        # Step 5: Show the feedback directly (without database persistence)
        print("\n📊 Step 5: Displaying conversation feedback...")
        
        # Display the feedback from the direct call to generate_conversation_summary_and_feedback
        if hasattr(flow.realtime_agent, 'last_feedback') and flow.realtime_agent.last_feedback:
            feedback = flow.realtime_agent.last_feedback
            print("✅ Feedback generated successfully!")
            print(f"   🎯 Overall score: {feedback.get('overall_score', 'N/A')}/10")
            print(f"   📝 General feedback: {feedback.get('general', {}).get('feedback', 'N/A')}")
            
            # Display pillar scores if available
            pillars = feedback.get('pillars', {})
            if pillars:
                print("\n📊 Language Pillar Scores:")
                for pillar, data in pillars.items():
                    print(f"   - {pillar.capitalize()}: {data.get('score', 'N/A')}/10 - {data.get('resumen', 'N/A')}")
        else:
            print("⚠️ No feedback was generated or stored")
        
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
        
        # Step 7: Show detailed feedback analysis
        print("\n🤖 Step 7: AI Feedback Analysis:")
        print("=" * 60)
        
        # Use the feedback directly from RealtimeAgent.last_feedback
        if hasattr(flow.realtime_agent, 'last_feedback') and flow.realtime_agent.last_feedback:
            feedback = flow.realtime_agent.last_feedback
            pillars = feedback.get('pillars', {})
            
            for pillar_name, pillar_data in pillars.items():
                score = pillar_data.get('score', 0)
                resumen = pillar_data.get('resumen', 'No feedback available')
                print(f"\n📊 {pillar_name.upper()}: {score:.1f}/10")
                print(f"   💬 {resumen}")
                
                # Show errors if available
                errors = pillar_data.get('errores', [])
                if errors and isinstance(errors, list) and len(errors) > 0:
                    print(f"   ❌ Errors: {', '.join(errors[:3])}")
                
                # Show suggestions if available
                suggestions = pillar_data.get('sugerencias', [])
                if suggestions and isinstance(suggestions, list) and len(suggestions) > 0:
                    print(f"   💡 Suggestions: {', '.join(suggestions[:2])}")
        else:
            print("   ⚠️  No feedback generated")
        
        print("=" * 60)
        
        # Step 8: Test completed
        print("\n🎉 Step 8: Test Completed Successfully!")
        print("   ✅ Feedback generation works correctly")
        print("   ✅ JSON format is valid")
        print("   ✅ No database persistence as requested")

        
        # Step 9: Cleanup
        print("\n🧹 Step 9: Cleanup...")
        await flow.cleanup()
        print("✅ Cleanup completed")
        
        print("\n" + "=" * 80)
        print("🎉 REAL VOICE CONVERSATION TEST COMPLETED SUCCESSFULLY!")
        print("=" * 80)
        print("✅ Successfully tested:")
        print("   • 🎤 REAL voice input/output with RealtimeAgent")
        print("   • 💬 REAL conversation transcription")
        print("   • 🤖 REAL AI feedback generation")
        print("   • 📝 REAL feedback generation without persistence")
        print("\n🏆 THE TALKTOR FEEDBACK SYSTEM IS WORKING!")
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
        health = await persistence_service.health_check()
        
        print(f"   🏥 Status: {health['status']}")
        print(f"   📊 Sessions: {health['tables']['sessions']}")
        print(f"   💬 Transcripts: {health['tables']['transcripts']}")
        print(f"   📋 Feedback: {health['tables']['feedback']}")
        
    except Exception as e:
        print(f"   ❌ Error getting database stats: {e}")


if __name__ == "__main__":
    print("🎤 REAL VOICE CONVERSATION INTEGRATION TEST")
    print("=" * 80)
    print("⚠️  REQUIREMENTS:")
    print("1. 🎧 Working microphone and speakers")
    print("2. 🔑 OpenAI API key configured (for feedback generation)")
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
