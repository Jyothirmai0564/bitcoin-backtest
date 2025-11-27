from trading_system import RealTradingSystem

def run_trading_system():
    """Run the trading system with Gmail alerts"""
    print("🚀 Starting Bitcoin Trading System with Gmail Alerts...")
    
    system = RealTradingSystem()
    
    # Run trading system
    success = system.run_complete_system()
    
    if success:
        print("✅ Trading system completed successfully!")
        print("📊 Launch dashboard with: streamlit run dashboard.py")
    else:
        print("❌ Trading system failed!")

if __name__ == "__main__":
    run_trading_system()