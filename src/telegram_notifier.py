import requests
import logging
import os
from typing import Dict, Optional

class TelegramNotifier:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.chat_id = os.getenv('TELEGRAM_CHAT_ID')
        self.enabled = bool(self.bot_token and self.chat_id)
        
        if self.enabled:
            self.logger.info("✅ Telegram notifications enabled")
        else:
            self.logger.warning("❌ Telegram notifications disabled - set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID")
    
    def send_notification(self, message: str, trade_data: Optional[Dict] = None) -> bool:
        """Send notification to Telegram"""
        if not self.enabled:
            return False
            
        try:
            # Format message with trade details
            formatted_message = self._format_message(message, trade_data)
            
            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            payload = {
                'chat_id': self.chat_id,
                'text': formatted_message,
                'parse_mode': 'HTML'
            }
            
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()
            
            self.logger.info("📱 Telegram notification sent successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to send Telegram notification: {e}")
            return False
    
    def _format_message(self, message: str, trade_data: Optional[Dict] = None) -> str:
        """Format message with HTML formatting"""
        if trade_data:
            emoji = "🟢" if trade_data.get('action') == 'BUY' else "🔴"
            return f"""
{emoji} <b>BITCOIN TRADE ALERT</b> {emoji}

💰 <b>Action:</b> {trade_data.get('action', 'N/A')}
📊 <b>Amount:</b> ${trade_data.get('amount', 0):,.2f}
🎯 <b>Price:</b> ${trade_data.get('price', 0):,.2f}
⚖️ <b>Quantity:</b> {trade_data.get('quantity', 0):.6f} BTC
📝 <b>Reason:</b> {trade_data.get('reason', 'N/A')}
💼 <b>Portfolio Value:</b> ${trade_data.get('portfolio_value', 0):,.2f}

{message}
            """.strip()
        else:
            return f"🤖 <b>TRADING SYSTEM</b>\n\n{message}"
    
    def send_trade_alert(self, trade_data: Dict):
        """Send trade execution alert"""
        action = trade_data.get('action', '').upper()
        if action == 'BUY':
            message = "🟢 BUY order executed successfully!"
        elif action == 'SELL':
            message = "🔴 SELL order executed successfully!"
        else:
            message = "⚡ Trade executed!"
            
        return self.send_notification(message, trade_data)
    
    def send_system_alert(self, message: str):
        """Send system status alert"""
        return self.send_notification(f"⚡ SYSTEM ALERT:\n{message}")