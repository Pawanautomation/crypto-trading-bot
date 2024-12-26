import asyncio
import logging
from src.websocket_manager import BinanceWebsocketManager
from src.market_data import MarketDataManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def price_update_callback(price_data):
    """Example callback to handle price updates"""
    logger.info(f"\nPrice Update for {price_data['symbol']}:")
    logger.info(f"Price: ${price_data['current_price']:,.2f}")
    logger.info(f"24h Change: {price_data.get('price_change_24h', 'N/A')}%")
    logger.info(f"Volume: ${price_data.get('volume_24h', 'N/A'):,.2f}")

async def test_websocket():
    """Test websocket connection and price updates"""
    ws_manager = BinanceWebsocketManager()
    
    try:
        # Start websocket manager
        await ws_manager.start()
        
        # Add price update callback
        ws_manager.add_callback(price_update_callback)
        
        # Subscribe to BTC and ETH
        await ws_manager.subscribe_symbols(["BTCUSDT", "ETHUSDT"])
        
        # Run for 1 minute to see updates
        logger.info("Monitoring prices for 1 minute...")
        await asyncio.sleep(60)
        
        # Stop websocket manager
        await ws_manager.stop()
        return True
        
    except Exception as e:
        logger.error(f"Websocket test failed: {str(e)}")
        return False

async def test_market_data():
    """Test market data manager with websocket integration"""
    market_data = MarketDataManager()
    
    try:
        # Start market data manager
        await market_data.start()
        
        # Add price callback
        market_data.add_price_callback(price_update_callback)
        
        # Get market data a few times
        for _ in range(3):
            btc_data = await market_data.get_market_data("BTCUSDT")
            eth_data = await market_data.get_market_data("ETHUSDT")
            
            logger.info("\nMarket Data:")
            logger.info(f"BTC: ${btc_data['current_price']:,.2f}")
            logger.info(f"ETH: ${eth_data['current_price']:,.2f}")
            
            await asyncio.sleep(10)
        
        # Stop market data manager
        await market_data.stop()
        return True
        
    except Exception as e:
        logger.error(f"Market data test failed: {str(e)}")
        return False

async def main():
    """Run all tests"""
    logger.info("Starting websocket tests...")
    
    # Test websocket manager
    logger.info("\nTesting websocket manager:")
    ws_success = await test_websocket()
    logger.info(f"Websocket test: {'✓ Passed' if ws_success else '✗ Failed'}")
    
    # Test market data manager
    logger.info("\nTesting market data manager:")
    md_success = await test_market_data()
    logger.info(f"Market data test: {'✓ Passed' if md_success else '✗ Failed'}")

if __name__ == "__main__":
    asyncio.run(main())