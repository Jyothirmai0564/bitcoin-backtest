import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from trading_system import RealTradingSystem
import pandas as pd
from datetime import datetime

def force_trading_activity():
    """Force some trades to generate dashboard data"""
    print("🚀 FORCING TRADING ACTIVITY FOR DASHBOARD...")
    
    system = RealTradingSystem()
    
    # Get market data first
    system.get_market_data_for_dashboard()
    
    print(f"📊 Current BTC Price: ${system.current_price:,.2f}")
    print(f"📊 Current ATR: ${system.indicators.get('atr', 0):,.0f}")
    print(f"📊 ATR High Threshold: ${system.atr_high}")
    
    # Temporarily lower ATR threshold to force trades
    original_atr_high = system.atr_high
    system.atr_high = 50000  # Set very high so trades will execute
    
    print("🔄 Executing forced trades...")
    
    # Force a DCA buy (simulate price drop)
    print("\n1. Forcing DCA Buy...")
    system.previous_price = system.current_price * 1.05  # Simulate 5% price drop
    dca_triggered = system.check_price_drop_dca()
    
    if dca_triggered:
        print("✅ DCA Buy executed!")
    else:
        print("❌ DCA Buy not triggered")
    
    # Force strategy trades
    print("\n2. Forcing Strategy Trades...")
    strategy_result = system.execute_gemma_strategy()
    print(f"Strategy Decision: {strategy_result}")
    
    if strategy_result['action'] != "HOLD":
        trade_executed = system.execute_strategy_trade(strategy_result)
        if trade_executed:
            print(f"✅ {strategy_result['action']} trade executed!")
    else:
        # Force a manual buy
        print("🔄 Forcing manual BUY trade...")
        manual_trade = {
            'action': 'BUY',
            'amount': 1000,
            'quantity': 1000 / system.current_price,
            'reason': 'Manual trade for dashboard data'
        }
        system.save_trade_to_history(manual_trade)
        print("✅ Manual BUY trade saved!")
    
    # Restore original ATR threshold
    system.atr_high = original_atr_high
    
    # Save final portfolio state
    system.save_portfolio_state()
    
    print("\n🎉 FORCED TRADING COMPLETED!")
    print("📊 Dashboard should now have data!")
    
    # Show what was created
    try:
        trades_df = pd.read_csv("data/real_trading_history.csv")
        portfolio_df = pd.read_csv("data/portfolio_history.csv")
        print(f"📈 Trades created: {len(trades_df)}")
        print(f"📊 Portfolio records: {len(portfolio_df)}")
        
        if len(trades_df) > 0:
            print("\n📋 Recent Trades:")
            for i, trade in trades_df.tail(3).iterrows():
                print(f"   - {trade['action']}: ${trade['amount']} at ${trade['price']}")
                
    except Exception as e:
        print(f"❌ Could not read data files: {e}")

if __name__ == "__main__":
    force_trading_activity()