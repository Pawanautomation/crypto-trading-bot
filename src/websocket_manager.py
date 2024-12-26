import logging
import json
import websockets
import asyncio
from typing import Dict, Any, Callable, List
from urllib.parse import urlencode

class BinanceWebsocketManager:
    def __init__(self):
        self.callbacks: List[Callable] = []
        self.live_data: Dict[str, Any] = {}
        self._running = False
        self._ws = None
        self._ready = asyncio.Event()
        self._task = None
        self.base_endpoint = "wss://stream.binance.com:9443/ws"

    async def start(self):
        """Start the websocket manager"""
        if not self._running:
            self._running = True
            logging.info("Websocket manager started")
            return True

    async def _connect(self, symbols: List[str]):
        """Establish WebSocket connection"""
        streams = [f"{symbol.lower()}@ticker" for symbol in symbols]
        endpoint = f"{self.base_endpoint}/{'/'.join(streams)}"
        
        try:
            async with websockets.connect(endpoint) as websocket:
                self._ws = websocket
                logging.info(f"Connected to Binance WebSocket for {symbols}")
                
                while self._running:
                    try:
                        message = await websocket.recv()
                        await self._process_message(json.loads(message))
                    except websockets.ConnectionClosed:
                        logging.error("WebSocket connection closed")
                        break
                    except Exception as e:
                        logging.error(f"Error processing message: {str(e)}")
                        continue
                        
        except Exception as e:
            logging.error(f"WebSocket connection error: {str(e)}")
            raise
        finally:
            self._ws = None

    async def stop(self):
        """Stop the websocket manager"""
        if self._running:
            self._running = False
            if self._task:
                self._task.cancel()
                try:
                    await self._task
                except asyncio.CancelledError:
                    pass
            if self._ws:
                await self._ws.close()
            logging.info("Websocket manager stopped")

    def add_callback(self, callback: Callable):
        """Add a callback function"""
        if callback not in self.callbacks:
            self.callbacks.append(callback)
            logging.info(f"Added callback. Total callbacks: {len(self.callbacks)}")

    async def subscribe_symbols(self, symbols: List[str]):
        """Subscribe to symbol updates"""
        try:
            logging.info(f"Subscribing to symbols: {symbols}")
            self._task = asyncio.create_task(self._connect(symbols))
            await asyncio.sleep(1)  # Give time for initial connection
            
        except Exception as e:
            logging.error(f"Error subscribing to symbols: {str(e)}")
            raise

    async def _process_message(self, msg: Dict):
        """Process incoming messages"""
        try:
            symbol = msg.get('s')
            if symbol and 'c' in msg:
                price = float(msg['c'])
                data = {
                    'symbol': symbol,
                    'current_price': price,
                    'price_change_24h': float(msg.get('P', 0)),
                    'volume_24h': float(msg.get('v', 0)),
                    'high_24h': float(msg.get('h', 0)),
                    'low_24h': float(msg.get('l', 0)),
                    'timestamp': msg.get('E', 0)
                }
                
                self.live_data[symbol] = data
                logging.info(f"Price update for {symbol}: {price}")
                
                for callback in self.callbacks:
                    try:
                        callback(data)
                    except Exception as e:
                        logging.error(f"Callback error: {str(e)}")
                        
        except Exception as e:
            logging.error(f"Message processing error: {str(e)}")

    def get_latest_price(self, symbol: str) -> float:
        """Get latest price for a symbol"""
        if symbol in self.live_data:
            return self.live_data[symbol]['current_price']
        return None

    def is_running(self) -> bool:
        """Check if manager is running"""
        return self._running