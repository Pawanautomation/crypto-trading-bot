from binance import Client
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from .websocket_manager import BinanceWebsocketManager
from config.config import Config

class MarketDataManager:
    def __init__(self):
        """Initialize market data manager"""
        self.client = Client("", "")  # No keys needed for public data
        self.ws_manager = BinanceWebsocketManager()
        self.cached_data = {}
        
    async def start(self):
        """Start market data services"""
        try:
            await self.ws_manager.start()
            if hasattr(Config, 'TRADING_PAIRS'):
                await self.ws_manager.subscribe_symbols(Config.TRADING_PAIRS)
            else:
                await self.ws_manager.subscribe_symbols(["BTCUSDT", "ETHUSDT"])
        except Exception as e:
            logging.error(f"Error starting market data services: {str(e)}")
            raise
            
    async def stop(self):
        """Stop market data services"""
        try:
            await self.ws_manager.stop()
        except Exception as e:
            logging.error(f"Error stopping market data services: {str(e)}")
            raise
            
    def add_price_callback(self, callback):
        """Add callback for price updates"""
        self.ws_manager.add_callback(callback)

    async def get_market_data(self, symbol: str = "BTCUSDT") -> Optional[Dict[str, Any]]:
        """Get current market data including price, volume, and indicators"""
        try:
            # Get live price from websocket
            current_price = self.ws_manager.get_latest_price(symbol)
            
            # If no websocket price, fall back to REST API
            if current_price is None:
                ticker = self.client.get_ticker(symbol=symbol)
                current_price = float(ticker['lastPrice'])
            
            # Get candlestick data for technical analysis
            klines = self.client.get_klines(
                symbol=symbol,
                interval=Client.KLINE_INTERVAL_1HOUR,
                limit=24
            )
            
            market_data = {
                'symbol': symbol,
                'current_price': current_price,
                'timestamp': datetime.now().isoformat(),
                'trend': self._calculate_trend(klines),
                'volatility': self._calculate_volatility(klines),
                'indicators': self._calculate_indicators(klines)
            }
            
            return market_data
            
        except Exception as e:
            logging.error(f"Error fetching market data: {str(e)}")
            return None
            
    def _calculate_trend(self, klines: list) -> str:
        """Calculate current trend based on recent prices"""
        if not klines or len(klines) < 2:
            return "neutral"
            
        recent_closes = [float(k[4]) for k in klines[-6:]]
        first_price = recent_closes[0]
        last_price = recent_closes[-1]
        
        price_change = ((last_price - first_price) / first_price) * 100
        
        if price_change > 1:
            return "bullish"
        elif price_change < -1:
            return "bearish"
        return "neutral"
            
    def _calculate_volatility(self, klines: list) -> float:
        """Calculate recent volatility"""
        if not klines or len(klines) < 2:
            return 0.0
            
        recent_prices = [float(k[4]) for k in klines[-12:]]
        price_changes = [
            abs((recent_prices[i] - recent_prices[i-1]) / recent_prices[i-1] * 100)
            for i in range(1, len(recent_prices))
        ]
        
        return sum(price_changes) / len(price_changes)
            
    def _calculate_indicators(self, klines: list) -> Dict[str, float]:
        """Calculate technical indicators"""
        if not klines or len(klines) < 14:
            return {}
            
        closes = [float(k[4]) for k in klines]
        
        return {
            'sma_20': self._calculate_sma(closes, 20),
            'rsi_14': self._calculate_rsi(closes, 14),
            'price_vs_sma': (closes[-1] / self._calculate_sma(closes, 20) - 1) * 100
        }
            
    def _calculate_sma(self, prices: list, period: int) -> float:
        if len(prices) < period:
            return 0.0
        return sum(prices[-period:]) / period
            
    def _calculate_rsi(self, prices: list, period: int = 14) -> float:
        if len(prices) < period + 1:
            return 50.0
            
        deltas = [prices[i] - prices[i-1] for i in range(1, len(prices))]
        gains = [d if d > 0 else 0 for d in deltas]
        losses = [-d if d < 0 else 0 for d in deltas]
        
        avg_gain = sum(gains[-period:]) / period
        avg_loss = sum(losses[-period:]) / period
        
        if avg_loss == 0:
            return 100.0
            
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return round(rsi, 2)