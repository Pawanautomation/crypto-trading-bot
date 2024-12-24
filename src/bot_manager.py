from py3cw.request import Py3CW
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from config.config import Config

class BotManager:
    def __init__(self):
        """Initialize 3Commas bot manager"""
        self.p3cw = Py3CW(
            key=Config.THREE_COMMAS_API_KEY,
            secret=Config.THREE_COMMAS_SECRET,
            request_options={
                'request_timeout': 30,
                'nr_of_retries': 3
            }
        )
        self.active_bots: Dict[str, int] = {}  # pair -> bot_id mapping
        self.deal_history: List[Dict] = []
        
    async def verify_credentials(self) -> bool:
        """Verify 3Commas API credentials"""
        try:
            error, response = self.p3cw.request(
                entity='accounts',
                action='',
            )
            
            if error:
                logging.error(f"3Commas credentials verification failed: {error}")
                return False
                
            return True
        except Exception as e:
            logging.error(f"Error verifying 3Commas credentials: {str(e)}")
            return False
            
    async def get_account_info(self) -> Optional[Dict]:
        """Get primary account information"""
        try:
            error, accounts = self.p3cw.request(
                entity='accounts',
                action='',
            )
            
            if error:
                logging.error(f"Error getting account info: {error}")
                return None
                
            if not accounts or len(accounts) == 0:
                logging.error("No accounts found")
                return None
                
            # Use the first account (usually the main one)
            return accounts[0]
        except Exception as e:
            logging.error(f"Error in get_account_info: {str(e)}")
            return None
            
    async def create_bot(self, pair: str) -> Optional[Dict]:
        """Create a new DCA bot for a trading pair"""
        try:
            # Get account info first
            account = await self.get_account_info()
            if not account:
                return None
                
            # Create bot with account ID
            error, bot = self.p3cw.request(
                entity='bots',
                action='create_bot',
                payload={
                    'name': f'AI_Bot_{pair}_{datetime.now().strftime("%Y%m%d")}',
                    'account_id': account['id'],
                    'pairs': pair,
                    'base_order_volume': Config.BASE_TRADE_AMOUNT,
                    'take_profit': Config.TAKE_PROFIT_PERCENTAGE,
                    'safety_order_volume': Config.BASE_TRADE_AMOUNT,
                    'martingale_volume_coefficient': 1.5,
                    'martingale_step_coefficient': 1.0,
                    'max_safety_orders': Config.MAX_SAFETY_ORDERS,
                    'active_safety_orders_count': Config.MAX_SAFETY_ORDERS,
                    'safety_order_step_percentage': 2.5,
                    'take_profit_type': 'total',
                    'strategy_list': [{'strategy': 'nonstop'}],
                    'min_volume_btc_24h': 0,
                    'profit_currency': 'quote_currency',
                    'start_order_type': 'limit',
                    'stop_loss_percentage': Config.STOP_LOSS_PERCENTAGE,
                    'cooldown': 1  # Minutes to wait between deals
                }
            )
            
            if error:
                logging.error(f"Error creating bot: {error}")
                return None
                
            self.active_bots[pair] = bot['id']
            logging.info(f"Created bot for {pair} with ID: {bot['id']}")
            return bot
            
        except Exception as e:
            logging.error(f"Error in create_bot: {str(e)}")
            return None
            
    async def update_bot_settings(self, bot_id: int, 
                                settings: Dict[str, Any]) -> bool:
        """Update existing bot settings"""
        try:
            error, response = self.p3cw.request(
                entity='bots',
                action='update',
                action_id=str(bot_id),
                payload=settings
            )
            
            if error:
                logging.error(f"Error updating bot {bot_id}: {error}")
                return False
                
            logging.info(f"Successfully updated bot {bot_id} settings")
            return True
            
        except Exception as e:
            logging.error(f"Error in update_bot_settings: {str(e)}")
            return False
            
    async def apply_ai_recommendations(self, bot_id: int, 
                                     recommendations: Dict[str, Any]) -> bool:
        """Apply AI trading recommendations to bot settings"""
        try:
            if not recommendations.get('should_trade', False):
                logging.info(f"Skipping bot update - AI doesn't recommend trading")
                return False
                
            # Extract recommendations
            take_profit = recommendations.get('take_profit')
            stop_loss = recommendations.get('stop_loss')
            
            if not take_profit or not stop_loss:
                logging.error("Missing take profit or stop loss recommendations")
                return False
                
            # Update bot settings
            new_settings = {
                'take_profit': take_profit,
                'stop_loss_percentage': stop_loss,
                # Only update safety orders if confidence is high
                'max_safety_orders': (
                    Config.MAX_SAFETY_ORDERS 
                    if recommendations.get('average_confidence', 0) > 85 
                    else 1
                )
            }
            
            success = await self.update_bot_settings(bot_id, new_settings)
            if success:
                logging.info(
                    f"Applied AI recommendations to bot {bot_id}:"
                    f"\nTake Profit: {take_profit}%"
                    f"\nStop Loss: {stop_loss}%"
                    f"\nConfidence: {recommendations.get('average_confidence')}%"
                )
            return success
            
        except Exception as e:
            logging.error(f"Error in apply_ai_recommendations: {str(e)}")
            return False
            
    async def get_bot_deals(self, bot_id: int, 
                           limit: int = 10) -> List[Dict]:
        """Get recent deals for a specific bot"""
        try:
            error, deals = self.p3cw.request(
                entity='bots',
                action='show',
                action_id=str(bot_id),
                payload={
                    'limit': limit,
                    'scope': 'completed'
                }
            )
            
            if error:
                logging.error(f"Error getting bot deals: {error}")
                return []
                
            return deals.get('completed_deals', [])
            
        except Exception as e:
            logging.error(f"Error in get_bot_deals: {str(e)}")
            return []
            
    async def start_bot(self, bot_id: int) -> bool:
        """Start a bot"""
        try:
            error, response = self.p3cw.request(
                entity='bots',
                action='enable',
                action_id=str(bot_id)
            )
            
            if error:
                logging.error(f"Error starting bot {bot_id}: {error}")
                return False
                
            logging.info(f"Successfully started bot {bot_id}")
            return True
            
        except Exception as e:
            logging.error(f"Error in start_bot: {str(e)}")
            return False
            
    async def stop_bot(self, bot_id: int) -> bool:
        """Stop a bot"""
        try:
            error, response = self.p3cw.request(
                entity='bots',
                action='disable',
                action_id=str(bot_id)
            )
            
            if error:
                logging.error(f"Error stopping bot {bot_id}: {error}")
                return False
                
            logging.info(f"Successfully stopped bot {bot_id}")
            return True
            
        except Exception as e:
            logging.error(f"Error in stop_bot: {str(e)}")
            return False
            
    async def get_bot_stats(self, bot_id: int) -> Optional[Dict]:
        """Get bot performance statistics"""
        try:
            error, stats = self.p3cw.request(
                entity='bots',
                action='stats',
                action_id=str(bot_id)
            )
            
            if error:
                logging.error(f"Error getting bot stats: {error}")
                return None
                
            return stats
            
        except Exception as e:
            logging.error(f"Error in get_bot_stats: {str(e)}")
            return None
            
    async def panic_sell_bot(self, bot_id: int) -> bool:
        """Emergency stop and sell all positions for a bot"""
        try:
            # First stop the bot
            await self.stop_bot(bot_id)
            
            # Then panic sell all deals
            error, response = self.p3cw.request(
                entity='bots',
                action='panic_sell_all_deals',
                action_id=str(bot_id)
            )
            
            if error:
                logging.error(f"Error panic selling bot {bot_id}: {error}")
                return False
                
            logging.info(f"Successfully panic sold all positions for bot {bot_id}")
            return True
            
        except Exception as e:
            logging.error(f"Error in panic_sell_bot: {str(e)}")
            return False
            
    async def get_active_deals_count(self) -> int:
        """Get number of currently active deals across all bots"""
        try:
            error, deals = self.p3cw.request(
                entity='deals',
                action='',
                payload={
                    'scope': 'active'
                }
            )
            
            if error:
                logging.error(f"Error getting active deals: {error}")
                return 0
                
            return len(deals) if deals else 0
            
        except Exception as e:
            logging.error(f"Error in get_active_deals_count: {str(e)}")
            return 0
        # In src/bot_manager.py - Add this debug method
async def debug_credentials(self):
    """Debug 3Commas credentials"""
    try:
        error, response = self.p3cw.request(
            entity='ver',
            action='show'
        )
        if error:
            logging.error(f"3Commas API Error: {error}")
            logging.error(f"API Key length: {len(Config.THREE_COMMAS_API_KEY)}")
            logging.error(f"API Secret length: {len(Config.THREE_COMMAS_SECRET)}")
            return False
        return True
    except Exception as e:
        logging.error(f"3Commas debug error: {str(e)}")
        return False