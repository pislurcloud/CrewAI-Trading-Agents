#!/usr/bin/env python
"""
Setup Verification Script for AI Trading Crew
Checks all dependencies, API keys, and runs a minimal test
"""

import os
import sys
import subprocess


def print_header(text):
    print("\n" + "="*60)
    print(f"  {text}")
    print("="*60)


def check_python_version():
    """Check Python version"""
    print_header("1️⃣  CHECKING PYTHON VERSION")
    version = sys.version_info
    print(f"Python version: {version.major}.{version.minor}.{version.micro}")
    
    if version.major == 3 and 10 <= version.minor < 13:
        print("✅ Python version is compatible (3.10-3.12)")
        return True
    else:
        print("❌ Python version must be 3.10, 3.11, or 3.12")
        print(f"   Your version: {version.major}.{version.minor}")
        return False


def check_env_file():
    """Check .env file exists and has required keys"""
    print_header("2️⃣  CHECKING .ENV FILE")
    
    if not os.path.exists('.env'):
        print("❌ .env file not found!")
        print("\n📝 Create a .env file with:")
        print("""
OPENROUTER_API_KEY=your_key_here
OPENROUTER_DEEPSEEK_R1=deepseek/deepseek-r1:free
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1

TWELVE_API_KEY=your_key_here
TIMEGPT_API_KEY=your_key_here
RAPID_API_KEY=your_key_here
        """)
        return False
    
    print("✅ .env file found")
    
    # Check for required keys
    from dotenv import load_dotenv
    load_dotenv()
    
    required_keys = {
        'OPENROUTER_API_KEY': 'OpenRouter',
        'TWELVE_API_KEY': 'TwelveData',
        'TIMEGPT_API_KEY': 'Nixtla TimeGPT',
        'RAPID_API_KEY': 'RapidAPI (StockTwits)'
    }
    
    missing = []
    for key, name in required_keys.items():
        value = os.getenv(key)
        if value:
            # Mask the key for security
            masked = value[:4] + '...' + value[-4:] if len(value) > 8 else '***'
            print(f"✅ {name}: {masked}")
        else:
            print(f"❌ {name}: NOT SET")
            missing.append(key)
    
    if missing:
        print(f"\n❌ Missing API keys: {', '.join(missing)}")
        return False
    
    return True


def check_dependencies():
    """Check if required packages are installed"""
    print_header("3️⃣  CHECKING DEPENDENCIES")
    
    required_packages = [
        'crewai',
        'pandas',
        'requests',
        'beautifulsoup4',
        'talib',
        'nixtla',
        'python-dotenv',
        'pytz',
        'pydantic',
        'pydantic-settings'
    ]
    
    missing = []
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package}")
            missing.append(package)
    
    if missing:
        print(f"\n❌ Missing packages: {', '.join(missing)}")
        print("\n💡 Install with:")
        print(f"   pip install {' '.join(missing)}")
        return False
    
    return True


def check_directories():
    """Check/create required directories"""
    print_header("4️⃣  CHECKING DIRECTORIES")
    
    required_dirs = [
        'output',
        'output/agents_inputs',
        'output/agents_outputs',
        'logs',
        'resources/data'
    ]
    
    for directory in required_dirs:
        if os.path.exists(directory):
            print(f"✅ {directory}")
        else:
            os.makedirs(directory, exist_ok=True)
            print(f"📁 Created: {directory}")
    
    return True


def test_api_connection():
    """Test API connectivity"""
    print_header("5️⃣  TESTING API CONNECTIONS")
    
    # Test TwelveData
    print("\n🔌 Testing TwelveData API...")
    try:
        import requests
        api_key = os.getenv('TWELVE_API_KEY')
        url = f"https://api.twelvedata.com/quote?symbol=AAPL&apikey={api_key}"
        response = requests.get(url, timeout=10)
        if response.status_code == 200 and 'symbol' in response.json():
            print("✅ TwelveData API: Connected")
        else:
            print(f"❌ TwelveData API: Failed (status: {response.status_code})")
            return False
    except Exception as e:
        print(f"❌ TwelveData API: Error - {str(e)}")
        return False
    
    # Test Nixtla TimeGPT
    print("\n🔌 Testing Nixtla TimeGPT API...")
    try:
        from nixtla import NixtlaClient
        client = NixtlaClient(api_key=os.getenv('TIMEGPT_API_KEY'))
        if client.validate_api_key():
            print("✅ Nixtla TimeGPT API: Connected")
        else:
            print("❌ Nixtla TimeGPT API: Invalid key")
            return False
    except Exception as e:
        print(f"❌ Nixtla TimeGPT API: Error - {str(e)}")
        return False
    
    # Test OpenRouter
    print("\n🔌 Testing OpenRouter API...")
    try:
        import requests
        api_key = os.getenv('OPENROUTER_API_KEY')
        url = "https://openrouter.ai/api/v1/models"
        headers = {"Authorization": f"Bearer {api_key}"}
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            print("✅ OpenRouter API: Connected")
        else:
            print(f"❌ OpenRouter API: Failed (status: {response.status_code})")
            return False
    except Exception as e:
        print(f"❌ OpenRouter API: Error - {str(e)}")
        return False
    
    return True


def run_minimal_test():
    """Run a minimal test to verify system works"""
    print_header("6️⃣  RUNNING MINIMAL TEST")
    
    print("\n🧪 Testing basic functionality...")
    try:
        # Test company name lookup
        from ai_trading_crew.utils.company_info import get_company_name
        company = get_company_name("AAPL")
        print(f"✅ Company lookup: AAPL = {company}")
        
        # Test date utilities
        from ai_trading_crew.utils.dates import get_today_str
        today = get_today_str()
        print(f"✅ Date utility: {today}")
        
        # Test config loading
        from ai_trading_crew.config import settings
        print(f"✅ Config loaded: {len(settings.SYMBOLS)} symbols")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all checks"""
    print("\n" + "🔍" + " "*18 + "AI TRADING CREW" + " "*18 + "🔍")
    print(" "*16 + "Setup Verification Script" + " "*16)
    
    checks = [
        ("Python Version", check_python_version),
        ("Environment File", check_env_file),
        ("Dependencies", check_dependencies),
        ("Directories", check_directories),
        ("API Connections", test_api_connection),
        ("Basic Functionality", run_minimal_test)
    ]
    
    results = []
    for name, check_func in checks:
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ {name} check failed with exception: {str(e)}")
            results.append((name, False))
    
    # Summary
    print_header("📊 SUMMARY")
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅" if result else "❌"
        print(f"{status} {name}")
    
    print(f"\n{passed}/{total} checks passed")
    
    if passed == total:
        print("\n" + "🎉" * 20)
        print("\n✅ ALL CHECKS PASSED! You're ready to run the AI Trading Crew!")
        print("\n💡 Next steps:")
        print("   1. Run full analysis: python main_debug.py")
        print("   2. Run single stock test: python main_debug.py single AAPL")
        print("\n" + "🎉" * 20)
        return True
    else:
        print("\n❌ Some checks failed. Please fix the issues above before running.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)