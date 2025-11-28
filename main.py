from fastapi import FastAPI, BackgroundTasks
from fastapi.responses import HTMLResponse
import pandas as pd
import json
import os
import asyncio
import subprocess
from datetime import datetime
import uvicorn

app = FastAPI(title="Bitcoin AI Trading Dashboard", version="1.0.0")

class TradingSystem:
    def __init__(self):
        self.is_running = False
        self.last_run = None
        self.performance_data = {}
        self.portfolio_data = {}
        self.trading_data = {}
        
    async def initialize_system(self):
        """Run backtest automatically when system starts"""
        if not os.path.exists('data/backtest_performance.json'):
            print("🚀 Initializing: Running first backtest...")
            await self.run_backtest()
        else:
            print("✅ Loading existing backtest data...")
            self.load_existing_data()
    
    def load_existing_data(self):
        """Load existing backtest data"""
        try:
            with open('data/backtest_performance.json', 'r') as f:
                self.performance_data = json.load(f)
            
            portfolio_df = pd.read_csv('data/backtest_portfolio_history.csv')
            self.portfolio_data = portfolio_df.iloc[-1].to_dict() if len(portfolio_df) > 0 else {}
            
            trades_df = pd.read_csv('data/backtest_trading_history.csv')
            self.trading_data = {
                "total_trades": len(trades_df),
                "ai_decisions": len(trades_df[trades_df['decision_source'] == 'AI']),
                "rule_decisions": len(trades_df[trades_df['decision_source'] == 'RULES'])
            }
            
        except Exception as e:
            print(f"❌ Error loading existing data: {e}")
            self.performance_data = {}
            self.portfolio_data = {}
            self.trading_data = {}
    
    async def run_backtest(self):
        """Run the optimized backtest"""
        if self.is_running:
            return {"status": "already_running"}
            
        self.is_running = True
        try:
            print("🤖 Starting backtest...")
            
            # Run your backtest script
            process = await asyncio.create_subprocess_exec(
                'python', 'optimized_backtest.py',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            self.last_run = datetime.now()
            self.is_running = False
            
            if process.returncode == 0:
                print("✅ Backtest completed successfully!")
                # Reload the new data
                self.load_existing_data()
                return {"status": "success", "output": "Backtest completed!"}
            else:
                error_msg = stderr.decode()
                print(f"❌ Backtest failed: {error_msg}")
                return {"status": "error", "error": error_msg}
                
        except Exception as e:
            self.is_running = False
            print(f"❌ Backtest error: {e}")
            return {"status": "error", "error": str(e)}

# Initialize the trading system
trading_system = TradingSystem()

@app.on_event("startup")
async def startup_event():
    """Run when the app starts"""
    await trading_system.initialize_system()

@app.get("/")
async def dashboard():
    """Main dashboard page"""
    # Check if we have data
    has_data = bool(trading_system.performance_data)
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Bitcoin AI Trading Dashboard</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; background: #0f0f23; color: #00ff00; }}
            .container {{ max-width: 1200px; margin: 0 auto; }}
            .header {{ text-align: center; margin-bottom: 40px; }}
            .card {{ background: #1a1a2e; padding: 20px; margin: 10px; border-radius: 10px; border: 1px solid #00ff00; }}
            .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }}
            .btn {{ background: #00ff00; color: #000; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; margin: 5px; }}
            .btn:hover {{ background: #00cc00; }}
            .metric {{ font-size: 24px; font-weight: bold; color: #00ff00; }}
            .positive {{ color: #00ff00; }}
            .negative {{ color: #ff4444; }}
            .warning {{ color: #ffaa00; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🚀 Bitcoin AI Trading Dashboard</h1>
                <p>6-Month Backtest Results with Gemma AI</p>
                {"<p class='warning'>⚠️ No backtest data found. Click 'Run Backtest' below.</p>" if not has_data else ""}
            </div>
            
            <div class="card">
                <h2>⚡ System Controls</h2>
                <button class="btn" onclick="runBacktest()">Run 6-Month Backtest</button>
                <button class="btn" onclick="loadResults()">Refresh Results</button>
                <div id="status">{"✅ System ready" if has_data else "❌ No data - run backtest first"}</div>
            </div>
            
            {"<div class='grid'>" + (
                f'''
                <div class="card">
                    <h3>📊 Performance</h3>
                    <p>Total Return: <span class="metric {'positive' if trading_system.performance_data.get('total_return_percent', 0) >= 0 else 'negative'}">{trading_system.performance_data.get('total_return_percent', 0):.2f}%</span></p>
                    <p>Final Value: ${trading_system.performance_data.get('final_portfolio_value', 0):,.0f}</p>
                    <p>Realized Profit: ${trading_system.performance_data.get('realized_profit', 0):,.0f}</p>
                </div>
                
                <div class="card">
                    <h3>💰 Portfolio</h3>
                    <p>BTC Holdings: {trading_system.portfolio_data.get('btc_holdings', 0):.4f}</p>
                    <p>Cash: ${trading_system.portfolio_data.get('cash', 0):,.0f}</p>
                    <p>Total Value: ${trading_system.portfolio_data.get('total_value', 0):,.0f}</p>
                </div>
                
                <div class="card">
                    <h3>🤖 Trading Activity</h3>
                    <p>Total Trades: {trading_system.trading_data.get('total_trades', 0)}</p>
                    <p>AI Decisions: {trading_system.trading_data.get('ai_decisions', 0)}</p>
                    <p>Rule Decisions: {trading_system.trading_data.get('rule_decisions', 0)}</p>
                </div>
                '''
            ) if has_data else "<p>No data available. Run the backtest first.</p>") + "</div>"}
            
            <div class="card">
                <h3>📋 System Information</h3>
                <p>Last Run: {trading_system.last_run.strftime('%Y-%m-%d %H:%M:%S') if trading_system.last_run else 'Never'}</p>
                <p>Status: {"✅ Ready" if has_data else "❌ No data"}</p>
                <p>Backtest Period: 6 months</p>
            </div>
        </div>
        
        <script>
            async function runBacktest() {{
                document.getElementById('status').innerHTML = '🔄 Running backtest (this may take a few minutes)...';
                const response = await fetch('/run-backtest', {{method: 'POST'}});
                const result = await response.json();
                
                if(result.status === 'success') {{
                    document.getElementById('status').innerHTML = '✅ Backtest completed! Refreshing...';
                    setTimeout(() => location.reload(), 2000);
                }} else {{
                    document.getElementById('status').innerHTML = '❌ Error: ' + result.error;
                }}
            }}
            
            function loadResults() {{
                location.reload();
            }}
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.post("/run-backtest")
async def run_backtest():
    """Run the backtest"""
    result = await trading_system.run_backtest()
    return result

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "bitcoin-trading-dashboard"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)