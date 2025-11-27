import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from trading_system import RealTradingSystem
import pandas as pd
from datetime import datetime
import time

def send_daily_report():
    """Send daily report independently"""
    print("📧 SENDING DAILY TRADING REPORT...")
    
    system = RealTradingSystem()
    
    # Get current market data
    system.get_market_data_for_dashboard()
    
    # Send daily report
    success = system.send_daily_report()
    
    if success:
        print("✅ Daily report sent successfully!")
        
        # Show report summary
        try:
            trades_df = pd.read_csv("data/real_trading_history.csv")
            portfolio_df = pd.read_csv("data/portfolio_history.csv")
            
            print(f"\n📊 REPORT SUMMARY:")
            print(f"   Total Trades: {len(trades_df)}")
            print(f"   Portfolio Value: ${portfolio_df['total_value'].iloc[-1]:,.2f}" if not portfolio_df.empty else "   Portfolio Value: $100,000")
            print(f"   BTC Price: ${system.current_price:,.2f}")
            
        except Exception as e:
            print(f"❌ Error reading data: {e}")
    else:
        print("❌ Failed to send daily report")

if __name__ == "__main__":
    print("🚀 Daily Report System")
    print("=" * 50)
    
    send_daily_report()