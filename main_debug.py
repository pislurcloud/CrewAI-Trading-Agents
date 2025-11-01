#!/usr/bin/env python
import asyncio
import os
import sys
import warnings
import pytz
import pandas as pd
import datetime
import traceback
from ai_trading_crew.config import settings
from ai_trading_crew.analysts.market_overview import HistoricalMarketFetcher
from ai_trading_crew.market_overview_agents import MarketOverviewAnalyst
from ai_trading_crew.stock_processor import process_stock_symbol_sync as process_stock_symbol, process_stock_symbol as process_stock_symbol_async
from ai_trading_crew.crew import StockComponentsSummarizeCrew
from ai_trading_crew.analysts.timegpt import get_timegpt_forecast

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")


def check_environment():
    """Check if all required environment variables are set"""
    required_vars = [
        'OPENROUTER_API_KEY',
        'OPENROUTER_LLAMA_4', 
        'OPENROUTER_BASE_URL',
        'TWELVE_API_KEY',
        'TIMEGPT_API_KEY',
        'RAPID_API_KEY'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print("❌ ERROR: Missing environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\n📝 Please create a .env file with all required keys")
        sys.exit(1)
    
    print("✅ All environment variables found")
    return True


def check_directories():
    """Check if output directories exist"""
    from ai_trading_crew.config import OUTPUT_FOLDER, AGENT_INPUTS_FOLDER, AGENT_OUTPUTS_FOLDER, LOG_FOLDER
    
    directories = {
        'Output': OUTPUT_FOLDER,
        'Agent Inputs': AGENT_INPUTS_FOLDER,
        'Agent Outputs': AGENT_OUTPUTS_FOLDER,
        'Logs': LOG_FOLDER
    }
    
    print("\n📁 Checking directories:")
    for name, path in directories.items():
        exists = os.path.exists(path)
        status = "✅" if exists else "❌"
        print(f"   {status} {name}: {path}")
        if not exists:
            os.makedirs(path, exist_ok=True)
            print(f"      Created: {path}")
    
    return True


def test_api_connectivity():
    """Test if APIs are accessible"""
    print("\n🔌 Testing API connectivity:")
    
    # Test TwelveData
    try:
        from ai_trading_crew.utils.twelve_data_manager import twelve_data_manager
        test_data = twelve_data_manager.get_quote_data("AAPL")
        print("   ✅ TwelveData API: Connected")
    except Exception as e:
        print(f"   ❌ TwelveData API: Failed - {str(e)}")
        return False
    
    # Test Nixtla TimeGPT
    try:
        from nixtla import NixtlaClient
        client = NixtlaClient(api_key=os.getenv('TIMEGPT_API_KEY'))
        if client.validate_api_key():
            print("   ✅ Nixtla TimeGPT API: Connected")
        else:
            print("   ❌ Nixtla TimeGPT API: Invalid key")
            return False
    except Exception as e:
        print(f"   ❌ Nixtla TimeGPT API: Failed - {str(e)}")
        return False
    
    return True


async def run_async_execution_debug():
    """
    Run the crew asynchronously with debug output.
    """
    print("\n" + "="*60)
    print("🚀 STARTING AI TRADING CREW - DEBUG MODE")
    print("="*60)
    
    try:
        # Step 1: Fetch market data
        print("\n📊 Step 1: Fetching market overview data...")
        vix_data = HistoricalMarketFetcher().get_vix(days=30)
        print(f"   ✅ VIX data fetched: {len(vix_data)} days")
        
        global_market_data = HistoricalMarketFetcher().get_global_market(days=30)
        print(f"   ✅ Global market data fetched")
        
        # Step 2: Create market overview analyst
        print("\n🧠 Step 2: Creating market overview analyst...")
        market_analyst = MarketOverviewAnalyst()
        market_agent, market_task = market_analyst.get_agent_and_task()
        print("   ✅ Market analyst created")
        
        # Step 3: Get TimeGPT forecasts
        print("\n🔮 Step 3: Getting TimeGPT forecasts...")
        timegpt_forecasts = get_timegpt_forecast()
        print(f"   ✅ TimeGPT forecasts obtained: {len(timegpt_forecasts)} rows")
        
        # Step 4: Process market overview (SPY)
        print(f"\n📈 Step 4: Processing market overview ({settings.STOCK_MARKET_OVERVIEW_SYMBOL})...")
        await process_stock_symbol_async(
            settings.STOCK_MARKET_OVERVIEW_SYMBOL,
            vix_data=vix_data,
            global_market_data=global_market_data,
            additional_agents=[market_agent],
            additional_tasks=[market_task]
        )
        print(f"   ✅ Market overview ({settings.STOCK_MARKET_OVERVIEW_SYMBOL}) completed")
        
        # Step 5: Process individual symbols
        print(f"\n📊 Step 5: Processing {len(settings.SYMBOLS)} individual stocks...")
        for i, symbol in enumerate(settings.SYMBOLS, 1):
            print(f"\n   [{i}/{len(settings.SYMBOLS)}] Processing {symbol}...")
            try:
                await process_stock_symbol_async(symbol)
                print(f"   ✅ {symbol} completed")
            except Exception as e:
                print(f"   ❌ {symbol} failed: {str(e)}")
                traceback.print_exc()
        
        print("\n" + "="*60)
        print("✅ ALL PROCESSING COMPLETED!")
        print("="*60)
        
        # Show output locations
        from ai_trading_crew.utils.dates import get_today_str_no_min
        today = get_today_str_no_min()
        output_dir = f"output/agents_outputs/{today}"
        
        print(f"\n📂 Check outputs in: {output_dir}")
        if os.path.exists(output_dir):
            for symbol in [settings.STOCK_MARKET_OVERVIEW_SYMBOL] + settings.SYMBOLS:
                symbol_dir = os.path.join(output_dir, symbol)
                if os.path.exists(symbol_dir):
                    files = os.listdir(symbol_dir)
                    print(f"   {symbol}: {len(files)} files")
        
    except Exception as e:
        print("\n" + "="*60)
        print("❌ ERROR OCCURRED!")
        print("="*60)
        print(f"\nError: {str(e)}")
        print("\nFull traceback:")
        traceback.print_exc()
        sys.exit(1)


def run():
    """
    Run the crew with comprehensive debugging.
    """
    print("\n🔍 PRE-FLIGHT CHECKS")
    print("="*60)
    
    # Check environment
    check_environment()
    
    # Check directories
    check_directories()
    
    # Test APIs
    if not test_api_connectivity():
        print("\n❌ API connectivity failed. Please check your API keys.")
        sys.exit(1)
    
    print("\n✅ All pre-flight checks passed!")
    print("\n🚀 Starting execution...")
    
    # Run async execution
    asyncio.run(run_async_execution_debug())


def run_single_stock(symbol):
    """
    Debug mode: Run analysis for a single stock only.
    Usage: python main_debug.py single AAPL
    """
    print(f"\n🔍 DEBUG MODE: Single Stock Analysis ({symbol})")
    print("="*60)
    
    check_environment()
    check_directories()
    
    async def run_single():
        try:
            print(f"\n📊 Processing {symbol}...")
            await process_stock_symbol_async(symbol)
            print(f"\n✅ {symbol} completed!")
            
            from ai_trading_crew.utils.dates import get_today_str_no_min
            today = get_today_str_no_min()
            output_dir = f"output/agents_outputs/{today}/{symbol}"
            
            if os.path.exists(output_dir):
                files = os.listdir(output_dir)
                print(f"\n📂 Generated {len(files)} files in: {output_dir}")
                for file in files:
                    print(f"   - {file}")
            else:
                print(f"\n⚠️  No output directory found: {output_dir}")
                
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")
            traceback.print_exc()
    
    asyncio.run(run_single())


if __name__ == "__main__":
    # Check for single stock mode
    if len(sys.argv) > 2 and sys.argv[1] == "single":
        run_single_stock(sys.argv[2])
    else:
        run()