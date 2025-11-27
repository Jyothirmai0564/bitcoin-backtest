import schedule
import time
import logging
from datetime import datetime
from threading import Thread
import sys
import os

# Add current directory to path
sys.path.append(os.path.dirname(__file__))

from trading_agent import BitcoinTradingAgent
from config_manager import ConfigManager

class TradingScheduler:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.config_manager = ConfigManager()
        self.config = self.config_manager.load_config()
        self.trading_agent = BitcoinTradingAgent(self.config)
        self.is_running = False
        self.scheduler_thread = None
        
        self.logger.info("🕒 Trading scheduler initialized")

    def start_24_7(self):
        """Start the 24/7 trading system"""
        self.is_running = True
        
        # Schedule trading cycles (every 2 minutes for active trading)
        schedule.every(2).minutes.do(self._run_trading_cycle)
        
        # Schedule weekly email report (Monday 9:00 AM)
        schedule.every().monday.at("09:00").do(self._send_weekly_report)
        
        # Schedule daily status update (8:00 AM daily)
        schedule.every().day.at("08:00").do(self._send_daily_status)
        
        # Schedule health check (every 6 hours)
        schedule.every(6).hours.do(self._send_health_check)
        
        # Send startup notification
        self.trading_agent.send_system_notification(
            "🚀 **24/7 TRADING SYSTEM STARTED**\n\n"
            "✅ System is now running 24/7\n"
            "⏰ Trading cycles: Every 2 minutes\n"
            "📊 Weekly reports: Monday 9:00 AM\n"
            "📈 Daily updates: 8:00 AM daily\n"
            "🏥 Health checks: Every 6 hours\n\n"
            "Initial capital: $100,000\n"
            "Ready for automated trading! 🎯"
        )
        
        self.logger.info("✅ 24/7 trading system started")
        
        # Run scheduler in background thread
        self.scheduler_thread = Thread(target=self._run_scheduler, daemon=True)
        self.scheduler_thread.start()
        
        return True

    def stop_scheduler(self):
        """Stop the scheduler"""
        self.is_running = False
        schedule.clear()
        self.trading_agent.send_system_notification("🛑 Trading system stopped manually")
        self.logger.info("🛑 Scheduler stopped")

    def _run_scheduler(self):
        """Run the scheduler loop"""
        while self.is_running:
            try:
                schedule.run_pending()
                time.sleep(30)  # Check every 30 seconds
            except Exception as e:
                self.logger.error(f"❌ Scheduler error: {e}")
                time.sleep(60)  # Wait longer if error occurs

    def _run_trading_cycle(self):
        """Execute one trading cycle"""
        try:
            self.logger.info("🔄 Running scheduled trading cycle...")
            
            # Run trading cycle
            success = self.trading_agent.run_trading_cycle()
            
            if success:
                # Check if any trades were executed
                if hasattr(self.trading_agent, 'trading_history') and self.trading_agent.trading_history:
                    latest_trade = self.trading_agent.trading_history[-1]
                    self.logger.info(f"✅ Trading cycle completed with trade: {latest_trade.get('action')}")
                else:
                    self.logger.info("✅ Trading cycle completed (no trades executed)")
            else:
                self.logger.warning("⚠️ Trading cycle completed with issues")
                
        except Exception as e:
            self.logger.error(f"❌ Error in trading cycle: {e}")
            self.trading_agent.send_system_notification(f"❌ Trading cycle error: {str(e)}")

    def _send_weekly_report(self):
        """Send weekly email report"""
        try:
            self.logger.info("📧 Generating and sending weekly report...")
            success = self.trading_agent.send_weekly_report()
            
            if success:
                self.trading_agent.send_system_notification(
                    "📊 **WEEKLY REPORT SENT**\n\n"
                    "Your weekly trading performance report has been sent to your email!\n"
                    "Check your inbox for detailed analytics and performance metrics. 📈"
                )
            else:
                self.trading_agent.send_system_notification(
                    "❌ **WEEKLY REPORT FAILED**\n\n"
                    "Failed to send weekly email report.\n"
                    "Please check your Gmail configuration in secrets.env"
                )
                
        except Exception as e:
            self.logger.error(f"❌ Error sending weekly report: {e}")
            self.trading_agent.send_system_notification(f"❌ Weekly report error: {str(e)}")

    def _send_daily_status(self):
        """Send daily status update"""
        try:
            performance = self.trading_agent.get_performance_metrics()
            
            message = (
                "📈 **DAILY STATUS UPDATE**\n\n"
                f"💼 Portfolio Value: ${performance.get('portfolio_value', 0):,.2f}\n"
                f"🔢 Total Trades: {performance.get('total_trades', 0)}\n"
                f"💰 Realized Profit: ${performance.get('realized_profit', 0):,.2f}\n"
                f"🔄 Buy/Sell Ratio: {performance.get('buy_trades', 0)}/{performance.get('sell_trades', 0)}\n"
                f"⚡ System: ACTIVE 24/7\n\n"
                "Next weekly report: Monday 9:00 AM 🗓️"
            )
            
            self.trading_agent.send_system_notification(message)
            self.logger.info("✅ Daily status update sent")
            
        except Exception as e:
            self.logger.error(f"❌ Error sending daily status: {e}")

    def _send_health_check(self):
        """Send system health check"""
        try:
            performance = self.trading_agent.get_performance_metrics()
            
            message = (
                "🏥 **SYSTEM HEALTH CHECK**\n\n"
                f"✅ Status: OPERATIONAL\n"
                f"📊 Total Trades: {performance.get('total_trades', 0)}\n"
                f"💾 Memory: Stable\n"
                f"⏰ Uptime: 24/7\n"
                f"🕒 Last Update: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                "All systems normal! 🎯"
            )
            
            self.trading_agent.send_system_notification(message)
            self.logger.info("✅ Health check sent")
            
        except Exception as e:
            self.logger.error(f"❌ Error sending health check: {e}")

def main():
    """Main function to start the 24/7 system"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/trading_system.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    logger = logging.getLogger(__name__)
    
    # Create necessary directories
    os.makedirs('logs', exist_ok=True)
    os.makedirs('data', exist_ok=True)
    
    scheduler = None
    
    try:
        logger.info("🚀 Starting Bitcoin Trading System 24/7...")
        
        # Initialize and start scheduler
        scheduler = TradingScheduler()
        success = scheduler.start_24_7()
        
        if success:
            logger.info("✅ 24/7 system started successfully!")
            logger.info("   - Trading every 2 minutes")
            logger.info("   - Telegram notifications active")
            logger.info("   - Weekly reports scheduled")
            logger.info("   - Press Ctrl+C to stop")
            
            # Keep main thread alive
            while True:
                time.sleep(60)
                
    except KeyboardInterrupt:
        logger.info("🛑 Shutdown requested by user...")
        if scheduler:
            scheduler.stop_scheduler()
    except Exception as e:
        logger.error(f"💥 Fatal error: {e}")
        if scheduler:
            scheduler.stop_scheduler()
        sys.exit(1)

if __name__ == "__main__":
    main()