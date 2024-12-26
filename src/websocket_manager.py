# Add the websocket_manager.py code here (same as provided earlier)
from binance import ThreadedWebsocketManager
import logging
from typing import Dict, Any, Callable
from datetime import datetime

class BinanceWebsocketManager:
    def __init__(self):
        """Initialize websocket manager for Binance"""
        self.twm = ThreadedWebsocketManager()
        self.callbacks = []
        self.live_data = {}
        self._running = False
        
    async def start(self):
        """Start the websocket manager"""
        if not self._running:
            self.twm.start()
            self._running = True
            logging.info("Websocket manager started")