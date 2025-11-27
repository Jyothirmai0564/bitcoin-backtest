# enhanced_dashboard.py
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import numpy as np
from datetime import datetime, timedelta
import os
import json
import subprocess
import sys

# Page configuration
st.set_page_config(
    page_title="BTC AI Trading Dashboard",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        color: #00D4AA;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #1E1E1E;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 4px solid #00D4AA;
        margin: 0.5rem;
    }
    .positive {
        color: #00D4AA;
    }
    .negative {
        color: #FF4B4B;
    }
    .sidebar .sidebar-content {
        background-color: #f0f2f6;
    }
</style>
""", unsafe_allow_html=True)

def load_backtest_data():
    """Load backtest data with error handling"""
    try:
        # Check if data directory exists
        if not os.path.exists('data'):
            st.error("❌ 'data' directory not found!")
            return None, None, None, None
        
        # Load trading history
        trades_path = "data/backtest_trading_history.csv"
        portfolio_path = "data/backtest_portfolio_history.csv"
        market_path = "data/backtest_market_data.csv"
        performance_path = "data/backtest_performance.json"
        
        # Check if files exist
        files_exist = all([
            os.path.exists(trades_path), 
            os.path.exists(portfolio_path),
            os.path.exists(market_path),
            os.path.exists(performance_path)
        ])
        
        if not files_exist:
            st.warning("📊 Backtest data not found. Run the backtest first.")
            return None, None, None, None
        
        # Load data
        trades_df = pd.read_csv(trades_path)
        portfolio_df = pd.read_csv(portfolio_path)
        market_df = pd.read_csv(market_path)
        
        # Convert timestamps
        trades_df['timestamp'] = pd.to_datetime(trades_df['timestamp'])
        portfolio_df['timestamp'] = pd.to_datetime(portfolio_df['timestamp'])
        market_df['Datetime'] = pd.to_datetime(market_df['Datetime'])
        
        # Load performance
        with open(performance_path, 'r') as f:
            performance_data = json.load(f)
        
        st.success(f"✅ Loaded {len(trades_df)} trades and {len(portfolio_df)} portfolio records!")
        return trades_df, portfolio_df, market_df, performance_data
        
    except Exception as e:
        st.error(f"❌ Error loading data: {str(e)}")
        return None, None, None, None

def create_sample_backtest_data():
    """Create sample backtest data for demonstration"""
    st.warning("📊 Creating sample backtest data...")
    
    # Create sample trades
    sample_trades = []
    current_time = datetime.now()
    
    # Simulate 6 months of trading
    for i in range(30):
        action = 'BUY' if i % 3 == 0 else 'SELL' if i % 3 == 1 else 'HOLD'
        if action != 'HOLD':
            sample_trades.append({
                'timestamp': current_time - timedelta(days=i*6),
                'action': action,
                'price': 85000 - i*500 + np.random.normal(0, 1000),
                'position_size': np.random.choice([5, 10, 15]),
                'trade_amount': 2000 + i*200,
                'btc_traded': (2000 + i*200) / (85000 - i*500),
                'reason': f'Sample {action} trade',
                'decision_source': np.random.choice(['AI', 'RULES']),
                'cash_before': 100000 - i*3000,
                'btc_before': i*0.01,
                'portfolio_value_before': 100000 + i*500,
                'cash_after': 100000 - (i+1)*3000,
                'btc_after': (i+1)*0.01,
                'portfolio_value_after': 100000 + (i+1)*500,
                'realized_profit': i*100
            })
    
    trades_df = pd.DataFrame(sample_trades)
    trades_df.to_csv('data/backtest_trading_history.csv', index=False)
    
    # Create sample portfolio history
    sample_portfolio = []
    for i in range(60):
        sample_portfolio.append({
            'timestamp': current_time - timedelta(days=i*3),
            'price': 85000 - i*250 + np.random.normal(0, 500),
            'cash': 100000 - i*1000,
            'btc_holdings': i*0.005,
            'btc_value': i*0.005 * (85000 - i*250),
            'total_value': 100000 + i*250,
            'realized_profit': i*50,
            'unrealized_profit': i*250
        })
    
    portfolio_df = pd.DataFrame(sample_portfolio)
    portfolio_df.to_csv('data/backtest_portfolio_history.csv', index=False)
    
    # Create sample market data
    dates = pd.date_range(start=current_time - timedelta(days=180), end=current_time, freq='H')
    market_data = pd.DataFrame({
        'Datetime': dates,
        'Open': 80000 + np.cumsum(np.random.normal(0, 100, len(dates))),
        'High': 80000 + np.cumsum(np.random.normal(0, 100, len(dates))) + 200,
        'Low': 80000 + np.cumsum(np.random.normal(0, 100, len(dates))) - 200,
        'Close': 80000 + np.cumsum(np.random.normal(0, 100, len(dates))),
        'Volume': np.random.uniform(1000, 5000, len(dates)),
        'RSI_14': np.random.uniform(30, 70, len(dates)),
        'SMA_20': 80000 + np.cumsum(np.random.normal(0, 80, len(dates))),
        'SMA_50': 80000 + np.cumsum(np.random.normal(0, 60, len(dates))),
        'EMA_12': 80000 + np.cumsum(np.random.normal(0, 90, len(dates))),
        'MACD': np.random.normal(0, 50, len(dates)),
        'ATR_14': np.random.uniform(800, 1200, len(dates))
    })
    market_data.to_csv('data/backtest_market_data.csv', index=False)
    
    # Create performance summary
    performance = {
        'initial_capital': 100000,
        'final_portfolio_value': 115000,
        'total_return_percent': 15.0,
        'realized_profit': 5000,
        'btc_holdings': 0.15,
        'remaining_cash': 85000,
        'total_trades': 20,
        'ai_decisions': 8,
        'rule_decisions': 12,
        'backtest_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'data_period': "6 months"
    }
    
    with open('data/backtest_performance.json', 'w') as f:
        json.dump(performance, f, indent=2)
    
    st.success("✅ Sample backtest data created! Refresh to view dashboard.")
    return trades_df, portfolio_df, market_data, performance

def run_backtest():
    """Run the backtest system"""
    try:
        st.info("🚀 Running 6-month backtest with Gemma AI...")
        
        # Run the backtest script
        result = subprocess.run([
            sys.executable, "enhanced_backtest.py"
        ], capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0:
            st.success("✅ Backtest completed successfully!")
            st.rerun()
        else:
            st.error(f"❌ Backtest failed: {result.stderr}")
            
    except subprocess.TimeoutExpired:
        st.error("❌ Backtest timed out after 5 minutes")
    except Exception as e:
        st.error(f"❌ Error running backtest: {e}")

def run_trading_system():
    """Run the live trading system"""
    try:
        st.info("🔴 Starting live trading system...")
        
        result = subprocess.run([
            sys.executable, "main.py"
        ], capture_output=True, text=True, timeout=180)
        
        if result.returncode == 0:
            st.success("✅ Trading system completed!")
        else:
            st.error(f"❌ Trading system failed: {result.stderr}")
            
    except subprocess.TimeoutExpired:
        st.error("❌ Trading system timed out")
    except Exception as e:
        st.error(f"❌ Error: {e}")

def force_test_trades():
    """Force test trades for dashboard data"""
    try:
        st.info("⚡ Forcing test trades...")
        
        result = subprocess.run([
            sys.executable, "force_trades.py"
        ], capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            st.success("✅ Test trades created!")
            st.rerun()
        else:
            st.error(f"❌ Failed: {result.stderr}")
            
    except Exception as e:
        st.error(f"❌ Error: {e}")

def send_daily_report():
    """Send daily trading report"""
    try:
        from trading_system import RealTradingSystem
        system = RealTradingSystem()
        system.get_market_data_for_dashboard()
        success = system.send_daily_report()
        if success:
            st.sidebar.success("✅ Daily report sent!")
        else:
            st.sidebar.error("❌ Failed to send report")
    except Exception as e:
        st.sidebar.error(f"❌ Error: {e}")

def main():
    # Header
    st.markdown('<h1 class="main-header">🚀 Bitcoin AI Trading Dashboard</h1>', unsafe_allow_html=True)
    st.markdown("### 6-Month Backtest Results with Gemma AI")
    
    # Load data
    trades_df, portfolio_df, market_df, performance_data = load_backtest_data()
    
    # If no data, create sample data
    if trades_df is None:
        if st.button("🔄 Create Sample Backtest Data"):
            trades_df, portfolio_df, market_df, performance_data = create_sample_backtest_data()
            st.rerun()
        else:
            st.error("""
            ## 📊 No Backtest Data Found!
            
            **To get started:**
            
            1. **Run the 6-month backtest:**
               ```bash
               python enhanced_backtest.py
               ```
            
            2. **Or click the button above to create sample data**
            
            3. **Then refresh this dashboard**
            """)
            return
    
    # Display performance metrics
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        total_return = performance_data.get('total_return_percent', 0)
        delta_color = "normal" if total_return >= 0 else "inverse"
        st.metric(
            "Total Return", 
            f"{total_return:+.2f}%",
            delta=f"{total_return:+.2f}%",
            delta_color=delta_color
        )
    
    with col2:
        final_value = performance_data.get('final_portfolio_value', 100000)
        st.metric("Final Portfolio", f"${final_value:,.0f}")
    
    with col3:
        total_trades = performance_data.get('total_trades', 0)
        st.metric("Total Trades", total_trades)
    
    with col4:
        ai_decisions = performance_data.get('ai_decisions', 0)
        st.metric("AI Decisions", ai_decisions)
    
    with col5:
        rule_decisions = performance_data.get('rule_decisions', 0)
        st.metric("Rule Decisions", rule_decisions)
    
    # Additional metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        realized_profit = performance_data.get('realized_profit', 0)
        st.metric("Realized Profit", f"${realized_profit:,.0f}")
    
    with col2:
        btc_holdings = performance_data.get('btc_holdings', 0)
        st.metric("BTC Holdings", f"{btc_holdings:.4f}")
    
    with col3:
        remaining_cash = performance_data.get('remaining_cash', 0)
        st.metric("Remaining Cash", f"${remaining_cash:,.0f}")
    
    with col4:
        ai_utilization = (ai_decisions / total_trades * 100) if total_trades > 0 else 0
        st.metric("AI Utilization", f"{ai_utilization:.1f}%")
    
    # Tabs for different sections
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📈 Performance", "💰 Trades", "📊 Portfolio", "🤖 AI Analysis", "⚙️ System"
    ])
    
    with tab1:
        st.subheader("Portfolio Performance Analysis")
        
        if portfolio_df is not None and len(portfolio_df) > 0:
            # Portfolio value chart
            fig1 = go.Figure()
            fig1.add_trace(go.Scatter(
                x=portfolio_df['timestamp'],
                y=portfolio_df['total_value'],
                mode='lines+markers',
                name='Portfolio Value',
                line=dict(color='#00D4AA', width=3),
                fill='tozeroy',
                fillcolor='rgba(0, 212, 170, 0.1)'
            ))
            
            # Add buy/sell markers
            if trades_df is not None and len(trades_df) > 0:
                buy_trades = trades_df[trades_df['action'] == 'BUY']
                sell_trades = trades_df[trades_df['action'] == 'SELL']
                
                fig1.add_trace(go.Scatter(
                    x=buy_trades['timestamp'],
                    y=[portfolio_df[portfolio_df['timestamp'] <= t].iloc[-1]['total_value'] 
                       if len(portfolio_df[portfolio_df['timestamp'] <= t]) > 0 else final_value 
                       for t in buy_trades['timestamp']],
                    mode='markers',
                    name='BUY Signals',
                    marker=dict(color='#00D4AA', size=10, symbol='triangle-up')
                ))
                
                fig1.add_trace(go.Scatter(
                    x=sell_trades['timestamp'],
                    y=[portfolio_df[portfolio_df['timestamp'] <= t].iloc[-1]['total_value'] 
                       if len(portfolio_df[portfolio_df['timestamp'] <= t]) > 0 else final_value 
                       for t in sell_trades['timestamp']],
                    mode='markers',
                    name='SELL Signals',
                    marker=dict(color='#FF4B4B', size=10, symbol='triangle-down')
                ))
            
            fig1.update_layout(
                title='Portfolio Value Over Time with Trade Signals',
                height=500,
                xaxis_title='Date',
                yaxis_title='Portfolio Value ($)',
                template='plotly_white',
                showlegend=True
            )
            st.plotly_chart(fig1, use_container_width=True)
            
            # Profit/Loss breakdown
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Profit Analysis")
                
                # Realized vs Unrealized profit
                if 'realized_profit' in portfolio_df.columns and 'unrealized_profit' in portfolio_df.columns:
                    latest = portfolio_df.iloc[-1]
                    profit_data = {
                        'Type': ['Realized Profit', 'Unrealized Profit'],
                        'Amount': [latest['realized_profit'], latest['unrealized_profit']]
                    }
                    profit_df = pd.DataFrame(profit_data)
                    
                    fig_pie = px.pie(
                        profit_df, 
                        values='Amount', 
                        names='Type',
                        color='Type',
                        color_discrete_map={
                            'Realized Profit': '#00D4AA',
                            'Unrealized Profit': '#FFA726'
                        }
                    )
                    fig_pie.update_layout(title='Profit Distribution')
                    st.plotly_chart(fig_pie, use_container_width=True)
            
            with col2:
                st.subheader("Asset Allocation")
                
                # Current allocation
                if not portfolio_df.empty:
                    latest = portfolio_df.iloc[-1]
                    allocation_data = {
                        'Asset': ['Cash', 'Bitcoin'],
                        'Value': [latest['cash'], latest['btc_value']]
                    }
                    allocation_df = pd.DataFrame(allocation_data)
                    
                    fig_alloc = px.pie(
                        allocation_df, 
                        values='Value', 
                        names='Asset',
                        color='Asset',
                        color_discrete_map={'Cash': '#4CAF50', 'Bitcoin': '#FF9800'}
                    )
                    fig_alloc.update_layout(title='Current Portfolio Allocation')
                    st.plotly_chart(fig_alloc, use_container_width=True)
        else:
            st.info("No portfolio data available for performance analysis.")
    
    with tab2:
        st.subheader("Trading History & Analysis")
        
        if trades_df is not None and len(trades_df) > 0:
            # Display trades table
            display_df = trades_df.copy()
            display_df = display_df.sort_values('timestamp', ascending=False)
            
            # Format for display
            display_df['trade_amount_display'] = display_df['trade_amount'].apply(
                lambda x: f"${x:,.2f}" if pd.notna(x) else "N/A"
            )
            display_df['price_display'] = display_df['price'].apply(lambda x: f"${x:,.2f}")
            display_df['timestamp_display'] = display_df['timestamp'].dt.strftime('%Y-%m-%d %H:%M')
            display_df['position_size_display'] = display_df['position_size'].apply(lambda x: f"{x}%")
            
            # Color coding for actions
            def color_action(action):
                if action == 'BUY':
                    return 'color: #00D4AA'
                elif action == 'SELL':
                    return 'color: #FF4B4B'
                else:
                    return 'color: #666666'
            
            styled_df = display_df[[
                'timestamp_display', 'action', 'price_display', 
                'position_size_display', 'trade_amount_display', 
                'decision_source', 'reason'
            ]].style.applymap(color_action, subset=['action'])
            
            st.dataframe(styled_df, use_container_width=True, height=400)
            
            # Trade statistics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                total_volume = trades_df['trade_amount'].sum()
                st.metric("Total Volume", f"${total_volume:,.0f}")
            
            with col2:
                avg_trade_size = trades_df['trade_amount'].mean()
                st.metric("Avg Trade Size", f"${avg_trade_size:,.0f}")
            
            with col3:
                buy_volume = trades_df[trades_df['action'] == 'BUY']['trade_amount'].sum()
                st.metric("Buy Volume", f"${buy_volume:,.0f}")
            
            with col4:
                sell_volume = trades_df[trades_df['action'] == 'SELL']['trade_amount'].sum()
                st.metric("Sell Volume", f"${sell_volume:,.0f}")
        else:
            st.info("No trading history available.")
    
    with tab3:
        st.subheader("Portfolio Composition Over Time")
        
        if portfolio_df is not None and len(portfolio_df) > 0:
            # Portfolio composition chart
            fig_comp = go.Figure()
            
            fig_comp.add_trace(go.Scatter(
                x=portfolio_df['timestamp'],
                y=portfolio_df['cash'],
                mode='lines',
                name='Cash',
                stackgroup='one',
                line=dict(color='#4CAF50', width=2)
            ))
            
            fig_comp.add_trace(go.Scatter(
                x=portfolio_df['timestamp'],
                y=portfolio_df['btc_value'],
                mode='lines',
                name='Bitcoin Value',
                stackgroup='one',
                line=dict(color='#FF9800', width=2)
            ))
            
            fig_comp.update_layout(
                title='Portfolio Composition Over Time',
                height=400,
                xaxis_title='Date',
                yaxis_title='Value ($)',
                template='plotly_white'
            )
            st.plotly_chart(fig_comp, use_container_width=True)
            
            # BTC Holdings chart
            fig_btc = go.Figure()
            fig_btc.add_trace(go.Scatter(
                x=portfolio_df['timestamp'],
                y=portfolio_df['btc_holdings'],
                mode='lines',
                name='BTC Holdings',
                line=dict(color='#FF9800', width=3)
            ))
            
            fig_btc.update_layout(
                title='Bitcoin Holdings Over Time',
                height=300,
                xaxis_title='Date',
                yaxis_title='BTC Amount',
                template='plotly_white'
            )
            st.plotly_chart(fig_btc, use_container_width=True)
        else:
            st.info("No portfolio composition data available.")
    
    with tab4:
        st.subheader("AI Decision Analysis")
        
        if trades_df is not None and len(trades_df) > 0:
            # AI vs Rule decisions
            decision_counts = trades_df['decision_source'].value_counts()
            
            fig_ai = px.pie(
                values=decision_counts.values,
                names=decision_counts.index,
                title='AI vs Rule-Based Decisions',
                color=decision_counts.index,
                color_discrete_map={'AI': '#00D4AA', 'RULES': '#FFA726'}
            )
            st.plotly_chart(fig_ai, use_container_width=True)
            
            # Decision performance by source
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Decision Source Performance")
                
                # Calculate average profit by decision source
                if 'profit' in trades_df.columns:
                    profit_by_source = trades_df.groupby('decision_source')['profit'].mean()
                    st.bar_chart(profit_by_source)
            
            with col2:
                st.subheader("Trade Frequency")
                
                # Trades over time by source
                trades_over_time = trades_df.groupby([
                    pd.Grouper(key='timestamp', freq='W'),
                    'decision_source'
                ]).size().unstack(fill_value=0)
                
                if not trades_over_time.empty:
                    st.line_chart(trades_over_time)
        else:
            st.info("No AI analysis data available.")
    
    with tab5:
        st.subheader("System Configuration & Controls")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            ### 📊 System Status
            
            **Data Loaded:**
            - Trades: {}
            - Portfolio Records: {}
            - Market Data: {}
            
            **Backtest Period:**
            - {}
            
            **Initial Capital:** ${:,.0f}
            **Final Portfolio:** ${:,.0f}
            """.format(
                len(trades_df) if trades_df is not None else 0,
                len(portfolio_df) if portfolio_df is not None else 0,
                len(market_df) if market_df is not None else 0,
                performance_data.get('data_period', 'N/A'),
                performance_data.get('initial_capital', 0),
                performance_data.get('final_portfolio_value', 0)
            ))
        
        with col2:
            st.markdown("""
            ### ⚙️ System Information
            
            **Trading Strategy:**
            - Rule-based with Gemma AI enhancement
            - 6-month historical backtesting
            - Real-time market data integration
            
            **Technical Indicators:**
            - RSI, MACD, Moving Averages
            - ATR for volatility
            - Multiple timeframes
            
            **Risk Management:**
            - Position sizing
            - Stop-loss mechanisms
            - Portfolio rebalancing
            """)
    
    # Sidebar with controls (from your dashboard.py)
    st.sidebar.title("🚀 Trading Controls")
    st.sidebar.markdown("---")
    
    # Backtest Controls
    st.sidebar.subheader("📊 Backtest Operations")
    
    if st.sidebar.button("🔄 Run 6-Month Backtest", key="run_backtest"):
        run_backtest()
    
    if st.sidebar.button("📈 Create Sample Data", key="create_sample"):
        trades_df, portfolio_df, market_df, performance_data = create_sample_backtest_data()
        st.rerun()
    
    # Live Trading Controls
    st.sidebar.subheader("🔴 Live Trading")
    
    if st.sidebar.button("⚡ Run Trading System", key="run_trading"):
        run_trading_system()
    
    if st.sidebar.button("🔄 Force Test Trades", key="force_trades"):
        force_test_trades()
    
    # Report Controls
    st.sidebar.subheader("📧 Reports & Alerts")
    
    if st.sidebar.button("📧 Send Daily Report", key="send_report"):
        send_daily_report()
    
    if st.sidebar.button("🔄 Refresh Dashboard", key="refresh"):
        st.rerun()
    
    st.sidebar.markdown("---")
    
    # System Information
    st.sidebar.subheader("📋 System Info")
    st.sidebar.markdown(f"""
    **Last Updated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    
    **Backtest Date:** {performance_data.get('backtest_date', 'N/A')}
    
    **Total Return:** {performance_data.get('total_return_percent', 0):+.2f}%
    
    **Status:** {'✅ Ready' if trades_df is not None else '❌ No Data'}
    """)
    
    st.sidebar.markdown("---")
    st.sidebar.info("""
    **Need Help?**
    
    1. Run backtest for historical analysis
    2. Use sample data for testing
    3. Run live trading for real execution
    4. Refresh after each operation
    """)

if __name__ == "__main__":
    main()