import asyncio
import os
from dotenv import load_dotenv
from pathlib import Path
from config.config import Config
from src.market_data import MarketDataManager
from src.ai_analyzer import AIAnalyzer
from src.bot_manager import BotManager

def verify_env_variables():
    """Verify environment variables are loaded correctly"""
    # Get the project root directory
    base_dir = Path(__file__).resolve().parent
    env_path = base_dir / '.env'
    
    # Load environment variables
    load_dotenv(env_path)
    
    # Check each required variable
    required_vars = [
        'OPENAI_API_KEY',
        'CLAUDE_API_KEY',
        'THREE_COMMAS_API_KEY',
        'THREE_COMMAS_SECRET'
    ]
    
    print("\nEnvironment Variables Check:")
    all_present = True
    for var in required_vars:
        value = os.getenv(var)
        status = '✓ Present' if value else '✗ Missing'
        length = len(value) if value else 0
        print(f"{var}: {status} (Length: {length})")
        if not value:
            all_present = False
            
    return all_present

async def test_market_data():
    print("\nTesting Market Data...")
    market_data = MarketDataManager()
    data = await market_data.get_market_data("BTCUSDT")
    print(f"Market Data: {data}")
    return bool(data)

async def test_ai_analyzer():
    print("\nTesting AI Analyzer...")
    analyzer = AIAnalyzer()
    market_data = {
        'current_price': 50000,
        'price_change_24h': 2.5,
        'volume_24h': 1000000000,
        'trend': 'bullish',
        'volatility': 1.2,
        'indicators': {
            'sma_20': 49500,
            'rsi_14': 55,
            'price_vs_sma': 1.01
        }
    }
    analysis = await analyzer.analyze_market(market_data)
    print(f"AI Analysis: {analysis}")
    return bool(analysis)

async def test_bot_manager():
    print("\nTesting Bot Manager...")
    bot_manager = BotManager()
    bot = await bot_manager.create_bot("BTCUSDT")
    print(f"Created Bot: {bot}")
    return bool(bot)

async def main():
    print("Starting System Tests...")
    
    try:
        # Verify environment variables first
        if not verify_env_variables():
            print("❌ Environment variables missing or incorrect!")
            return
            
        print("✓ Environment variables verified")
        
        # Test configuration
        print("\nTesting Configuration...")
        Config.validate_config()
        print("✓ Configuration valid")
        
        # Test components
        tests = [
            ("Market Data", test_market_data()),
            ("AI Analyzer", test_ai_analyzer()),
            ("Bot Manager", test_bot_manager())
        ]
        
        for name, test in tests:
            try:
                result = await test
                print(f"✓ {name} {'passed' if result else 'failed'}")
            except Exception as e:
                print(f"✗ {name} error: {str(e)}")
                print(f"Error details: {str(e)}")
        
    except Exception as e:
        print(f"Test failed: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())