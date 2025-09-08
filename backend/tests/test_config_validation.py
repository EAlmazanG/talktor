"""
Test script to validate configuration and environment variables
"""
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_env_file_exists():
    """Test that .env file exists in project root"""
    print("\n📁 Testing .env File")
    print("=" * 50)
    
    project_root = Path(__file__).parent.parent.parent
    env_path = project_root / ".env"
    
    if env_path.exists():
        print(f"✅ .env file found: {env_path}")
        return True
    else:
        print(f"❌ .env file not found: {env_path}")
        return False


def test_env_variables():
    """Test that required environment variables are loaded"""
    print("\n🔧 Testing Environment Variables")
    print("=" * 50)
    
    # Load .env file
    from dotenv import load_dotenv
    project_root = Path(__file__).parent.parent.parent
    env_path = project_root / ".env"
    load_dotenv(env_path)
    
    required_vars = [
        "OPENAI_API_KEY",
        "POSTGRES_USER", 
        "POSTGRES_PASSWORD",
        "POSTGRES_DB"
    ]
    
    results = {}
    for var in required_vars:
        value = os.getenv(var)
        if value:
            # Mask sensitive values
            display_value = value[:10] + "..." if len(value) > 10 else value
            if "PASSWORD" in var or "KEY" in var:
                display_value = "***HIDDEN***"
            print(f"✅ {var}: {display_value}")
            results[var] = True
        else:
            print(f"❌ {var}: NOT SET")
            results[var] = False
    
    return all(results.values())


def test_config_loading():
    """Test that configuration loads correctly"""
    print("\n⚙️ Testing Configuration Loading")
    print("=" * 50)
    
    try:
        from core.config import settings
        
        print(f"✅ OpenAI Model: {settings.openai_model}")
        print(f"✅ Chat Model: {settings.openai_chat_model}")
        print(f"✅ Voice: {settings.openai_voice}")
        print(f"✅ Audio Format: {settings.audio_format}")
        print(f"✅ Sample Rate: {settings.audio_sample_rate}")
        print(f"✅ Transcriptions Enabled: {settings.enable_transcriptions}")
        print(f"✅ Transcription Model: {settings.transcription_model}")
        
        # Test that API key is loaded
        if settings.openai_api_key:
            print(f"✅ OpenAI API Key: ***LOADED***")
        else:
            print(f"❌ OpenAI API Key: NOT LOADED")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration loading failed: {e}")
        return False


def test_database_config():
    """Test database configuration"""
    print("\n🗄️ Testing Database Configuration")
    print("=" * 50)
    
    try:
        from db.database import (
            POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB, 
            POSTGRES_HOST, POSTGRES_PORT, DATABASE_URL
        )
        
        print(f"✅ Database User: {POSTGRES_USER}")
        print(f"✅ Database Name: {POSTGRES_DB}")
        print(f"✅ Database Host: {POSTGRES_HOST}")
        print(f"✅ Database Port: {POSTGRES_PORT}")
        print(f"✅ Database URL: postgresql://{POSTGRES_USER}:***@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}")
        
        return True
        
    except Exception as e:
        print(f"❌ Database configuration failed: {e}")
        return False


def test_imports():
    """Test that all modules can be imported"""
    print("\n📦 Testing Module Imports")
    print("=" * 50)
    
    imports_to_test = [
        ("core.config", "settings"),
        ("core.logging", "get_logger"),
        ("db.models", "Session, Transcript, Feedback"),
        ("db.database", "get_db, init_database"),
        ("db.crud", "SessionCRUD, TranscriptCRUD, FeedbackCRUD"),
        ("agents.realtime_agent", "RealtimeAgent"),
        ("agents.standard_agent", "StandardAgent"),
        ("services.openai_service", "OpenAIService"),
    ]
    
    results = []
    for module_name, items in imports_to_test:
        try:
            __import__(module_name)
            print(f"✅ {module_name}: {items}")
            results.append(True)
        except Exception as e:
            print(f"❌ {module_name}: {e}")
            results.append(False)
    
    return all(results)


def main():
    """Main validation function"""
    print("🔍 Configuration and Environment Validation")
    print("=" * 60)
    
    tests = [
        ("ENV File", test_env_file_exists),
        ("ENV Variables", test_env_variables),
        ("Configuration", test_config_loading),
        ("Database Config", test_database_config),
        ("Module Imports", test_imports),
    ]
    
    results = {}
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results[test_name] = False
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Validation Summary:")
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"   - {test_name}: {status}")
    
    total_tests = len(results)
    passed_tests = sum(results.values())
    
    print(f"\n🎯 Overall: {passed_tests}/{total_tests} validations passed")
    
    if passed_tests == total_tests:
        print("🎉 All validations passed! Configuration is correct.")
        return True
    else:
        print("⚠️ Some validations failed. Check the issues above.")
        return False


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n🛑 Validation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Validation suite failed: {e}")
        sys.exit(1)
