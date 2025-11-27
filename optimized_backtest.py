# optimized_backtest.py
from binance.client import Client
import pandas as pd
import numpy as np
import requests
import json
import time
import os
from datetime import datetime, timedelta
import warnings
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

# Load environment variables
load_dotenv('config/secrets.env')

warnings.filterwarnings('ignore')

# Initialize Binance Client
client = Client()

# Alert Configuration
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
GMAIL_USER = os.getenv('GMAIL_USER')
GMAIL_PASSWORD = os.getenv('GMAIL_PASSWORD')

# ==================== ALERT SYSTEM ====================
class AlertSystem:
    """Handles Telegram and Gmail alerts for recent trading activities only"""
    
    def __init__(self):
        self.bot_token = TELEGRAM_BOT_TOKEN
        self.chat_id = TELEGRAM_CHAT_ID
        self.gmail_user = GMAIL_USER
        self.gmail_password = GMAIL_PASSWORD
        self.alert_count = 0
        
    def send_telegram_alert(self, message):
        """Send formatted message to Telegram"""
        if not self.bot_token or not self.chat_id:
            print("❌ Missing Telegram credentials")
            return False
            
        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        payload = {
            'chat_id': self.chat_id,
            'text': message,
            'parse_mode': 'HTML'
        }
        
        try:
            response = requests.post(url, json=payload, timeout=10)
            if response.status_code == 200:
                self.alert_count += 1
                print("✅ Telegram alert sent!")
                return True
            else:
                print(f"❌ Telegram error: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Telegram error: {e}")
            return False
    
    def send_gmail_alert(self, subject, message):
        """Send email via Gmail with proper authentication"""
        if not self.gmail_user or not self.gmail_password:
            print("❌ Missing Gmail credentials")
            return False
            
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.gmail_user
            msg['To'] = self.gmail_user
            msg['Subject'] = subject
            
            # HTML content
            html_content = f"""
            <html>
                <head>
                    <style>
                        body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
                        .container {{ background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; }}
                        .trade-buy {{ background-color: #d4edda; border-left: 4px solid #28a745; padding: 15px; margin: 10px 0; border-radius: 5px; }}
                        .trade-sell {{ background-color: #f8d7da; border-left: 4px solid #dc3545; padding: 15px; margin: 10px 0; border-radius: 5px; }}
                        .metric {{ background: #f8f9fa; padding: 15px; margin: 10px 0; border-radius: 5px; border-left: 4px solid #007bff; }}
                    </style>
                </head>
                <body>
                    <div class="container">
                        {message}
                        <div style="margin-top: 20px; padding: 15px; background: #e9ecef; border-radius: 5px; font-size: 12px; color: #6c757d;">
                            <p>This is an automated message from your Bitcoin Trading System.</p>
                            <p>Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                        </div>
                    </div>
                </body>
            </html>
            """
            
            msg.attach(MIMEText(html_content, 'html'))
            
            # Send email
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(self.gmail_user, self.gmail_password)
            text = msg.as_string()
            server.sendmail(self.gmail_user, self.gmail_user, text)
            server.quit()
            
            self.alert_count += 1
            print("✅ Gmail alert sent!")
            return True
            
        except Exception as e:
            print(f"❌ Gmail error: {str(e)}")
            return False
    
    def send_trade_alert(self, trade_data, portfolio_state, current_price, market_conditions):
        """Send comprehensive trade alert via Telegram and Gmail for recent trades only"""
        action = trade_data['action']
        trade_amount = trade_data.get('trade_amount', 0)
        btc_traded = trade_data.get('btc_traded', 0)
        reason = trade_data.get('reason', '')
        decision_source = trade_data.get('decision_source', 'RULES')
        profit = trade_data.get('profit', 0)
        
        emoji = "🟢" if action == 'BUY' else "🔴" if action == 'SELL' else "⚪"
        
        # Telegram message
        telegram_message = f"""
{emoji} <b>TRADE EXECUTED: {action}</b>

💰 <b>Trade Details:</b>
Amount: ${trade_amount:,.2f}
Price: ${current_price:,.2f}
Quantity: {btc_traded:.6f} BTC
{f'Profit: ${profit:,.2f}' if action == 'SELL' and profit > 0 else ''}

📊 <b>Portfolio:</b>
• BTC: {portfolio_state['btc']:.4f} BTC
• Cash: ${portfolio_state['cash']:,.2f}
• Total: ${portfolio_state['total_value']:,.2f}

📝 <b>Reason:</b> {reason}
        """
        
        # Gmail content
        gmail_subject = f"Trade {action} - ${trade_amount:,.0f} at ${current_price:,.0f}"
        gmail_message = f"""
        <div class="header">
            <h2>🚀 Bitcoin Trading System</h2>
            <p>Live Trade Execution Alert</p>
        </div>
        <div class="{'trade-buy' if action == 'BUY' else 'trade-sell'}">
            <h3>{emoji} {action} Trade Executed</h3>
            <p><strong>Amount:</strong> ${trade_amount:,.2f}</p>
            <p><strong>Price:</strong> ${current_price:,.2f}</p>
            <p><strong>Quantity:</strong> {btc_traded:.6f} BTC</p>
            <p><strong>Reason:</strong> {reason}</p>
            {f'<p><strong>Profit:</strong> ${profit:,.2f}</p>' if action == 'SELL' and profit > 0 else ''}
        </div>
        
        <div class="metric">
            <h4>📊 Portfolio</h4>
            <p><strong>BTC:</strong> {portfolio_state['btc']:.4f} BTC</p>
            <p><strong>Cash:</strong> ${portfolio_state['cash']:,.2f}</p>
            <p><strong>Total:</strong> ${portfolio_state['total_value']:,.2f}</p>
        </div>
        """
        
        # Send both alerts
        telegram_success = self.send_telegram_alert(telegram_message)
        gmail_success = self.send_gmail_alert(gmail_subject, gmail_message)
        
        return telegram_success or gmail_success
    
    def send_system_activation_alert(self, current_price, initial_cash):
        """Send system activation alert"""
        message = f"""
🎬 <b>TRADING SYSTEM ACTIVATED</b>

Current Price: ${current_price:,.0f}
Initial Portfolio: ${initial_cash:,.0f}
        """
        
        self.send_telegram_alert(message)
        
        # Gmail for activation
        gmail_subject = "🚀 Trading System Activated"
        gmail_message = f"""
        <div class="header">
            <h2>Trading System Activated</h2>
            <p>Current Price: ${current_price:,.0f}</p>
        </div>
        <div class="metric">
            <p><strong>Initial Portfolio:</strong> ${initial_cash:,.0f}</p>
            <p><strong>BTC Price:</strong> ${current_price:,.0f}</p>
            <p><strong>Status:</strong> System Ready for Trading</p>
        </div>
        """
        self.send_gmail_alert(gmail_subject, gmail_message)
    
    def send_trading_completed_alert(self, final_portfolio, btc_holdings, strategy_action, strategy_reason):
        """Send trading completion alert"""
        message = f"""
🎉 <b>TRADING COMPLETED</b>

Final Portfolio: ${final_portfolio:,.0f}
BTC Holdings: {btc_holdings:.4f} BTC
Strategy: {strategy_action} - {strategy_reason}
        """
        
        self.send_telegram_alert(message)
        
        # Gmail for completion
        gmail_subject = "🎉 Trading Completed"
        gmail_message = f"""
        <div class="header">
            <h2>Trading Session Completed</h2>
            <p>Final Portfolio: ${final_portfolio:,.0f}</p>
        </div>
        <div class="metric">
            <p><strong>BTC Holdings:</strong> {btc_holdings:.4f} BTC</p>
            <p><strong>Strategy:</strong> {strategy_action}</p>
            <p><strong>Reason:</strong> {strategy_reason}</p>
        </div>
        """
        self.send_gmail_alert(gmail_subject, gmail_message)

class OptimizedBacktest:
    def __init__(self, initial_cash=100000):
        self.initial_cash = initial_cash
        self.portfolio = {
            'cash': initial_cash,
            'btc': 0.0,
            'total_value': initial_cash,
            'realized_profit': 0.0
        }
        self.trading_history = []
        self.portfolio_history = []
        self.alert_system = AlertSystem()
        
        # Trading parameters
        self.min_trade_usd = 10
        self.atr_high = 1000
        
    def fetch_6months_binance_data(self, symbol="BTCUSDT", interval="1h"):
        """Fetch 6 months of Bitcoin data from Binance"""
        print("📊 Fetching 6 months of Bitcoin data from Binance...")
        
        try:
            # Calculate 6 months ago
            end_date = datetime.now()
            start_date = end_date - timedelta(days=180)
            
            klines = client.get_historical_klines(
                symbol=symbol,
                interval=interval,
                start_str=start_date.strftime("%d %b, %Y"),
                end_str=end_date.strftime("%d %b, %Y")
            )
            
            df = pd.DataFrame(klines, columns=[
                'Open Time', 'Open', 'High', 'Low', 'Close', 'Volume',
                'Close Time', 'Quote Asset Volume', 'Number of Trades',
                'Taker Buy Base Asset Volume', 'Taker Buy Quote Asset Volume', 'Ignore'
            ])
            
            # Convert data types
            df['Open Time'] = pd.to_datetime(df['Open Time'], unit='ms')
            numeric_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
            for col in numeric_cols:
                df[col] = pd.to_numeric(df[col])
            
            df = df.rename(columns={'Open Time': 'Datetime'})
            df = df[['Datetime', 'Open', 'High', 'Low', 'Close', 'Volume']]
            
            print(f"✅ Fetched {len(df)} hours of Bitcoin data (6 months)")
            print(f"📅 Date range: {df['Datetime'].min()} to {df['Datetime'].max()}")
            
            return df
            
        except Exception as e:
            print(f"❌ Error fetching data: {e}")
            return None

    def calculate_technical_indicators(self, df):
        """Calculate comprehensive technical indicators"""
        print("📈 Calculating technical indicators...")
        
        data = df.copy()
        
        # RSI
        delta = data['Close'].diff()
        gain = delta.where(delta > 0, 0).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss
        data['RSI_14'] = 100 - (100 / (1 + rs))
        
        # Moving Averages
        data['SMA_20'] = data['Close'].rolling(20).mean()
        data['SMA_50'] = data['Close'].rolling(50).mean()
        data['SMA_200'] = data['Close'].rolling(200).mean()
        data['EMA_12'] = data['Close'].ewm(span=12).mean()
        data['EMA_26'] = data['Close'].ewm(span=26).mean()
        
        # MACD
        data['MACD'] = data['EMA_12'] - data['EMA_26']
        data['MACD_Signal'] = data['MACD'].ewm(span=9).mean()
        
        # ATR
        high_low = data['High'] - data['Low']
        high_close = abs(data['High'] - data['Close'].shift())
        low_close = abs(data['Low'] - data['Close'].shift())
        true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        data['ATR_14'] = true_range.rolling(14).mean()
        
        # Fill NaN values
        data = data.ffill().bfill()
        
        print("✅ Indicators calculated!")
        return data

    def rule_based_strategy(self, market_data, portfolio_state):
        """Enhanced rule-based strategy with better logic"""
        price = market_data['price']
        rsi = market_data['rsi']
        sma20 = market_data['sma20']
        sma50 = market_data['sma50']
        sma200 = market_data['sma200']
        ema12 = market_data['ema12']
        ema26 = market_data['ema26']
        macd = market_data['macd']
        atr = market_data['atr']
        
        cash = portfolio_state['cash']
        btc = portfolio_state['btc']
        
        strat_action = "HOLD"
        strat_percent = 0.0
        reason = ""

        # Market condition analysis
        trend_strength = "BULLISH" if sma50 > sma200 else "BEARISH"
        volatility_status = "HIGH" if atr > self.atr_high else "NORMAL"
        rsi_status = "OVERSOLD" if rsi < 30 else "OVERBOUGHT" if rsi > 70 else "NEUTRAL"
        
        # Enhanced strategy logic
        if volatility_status == "HIGH":
            strat_action = "HOLD"
            reason = f"High volatility (ATR: ${atr:.0f}) - Risk management"
            
        elif trend_strength == "BULLISH":
            if rsi_status == "OVERSOLD" and cash > self.min_trade_usd:
                strat_action, strat_percent = "BUY", 15.0
                reason = "Bullish trend with RSI oversold - Strong buy signal"
            elif macd > 0 and rsi < 60 and cash > self.min_trade_usd:
                strat_action, strat_percent = "BUY", 10.0
                reason = "Bullish momentum with room to grow"
            elif price > ema12 and ema12 > ema26 and cash > self.min_trade_usd:
                strat_action, strat_percent = "BUY", 8.0
                reason = "Strong uptrend confirmation"
            else:
                strat_action = "HOLD"
                reason = "Bullish but waiting for better entry"
                
        elif trend_strength == "BEARISH":
            if rsi_status == "OVERBOUGHT" and btc > 0:
                strat_action, strat_percent = "SELL", 15.0
                reason = "Bearish trend with RSI overbought - Strong sell signal"
            elif macd < 0 and rsi > 40 and btc > 0:
                strat_action, strat_percent = "SELL", 10.0
                reason = "Bearish momentum building"
            elif price < ema12 and ema12 < ema26 and btc > 0:
                strat_action, strat_percent = "SELL", 8.0
                reason = "Strong downtrend confirmation"
            else:
                strat_action = "HOLD"
                reason = "Bearish but waiting for better exit"
                
        else:
            # Sideways market
            if rsi < 35 and cash > self.min_trade_usd:
                strat_action, strat_percent = "BUY", 5.0
                reason = "RSI oversold in sideways market"
            elif rsi > 65 and btc > 0:
                strat_action, strat_percent = "SELL", 5.0
                reason = "RSI overbought in sideways market"
            else:
                strat_action = "HOLD"
                reason = "Sideways market - No clear signal"

        return {
            "action": strat_action,
            "position_size": strat_percent,
            "reason": reason,
            "source": "RULE_BASED"
        }

class FastGemmaAIAgent:
    """Optimized Gemma AI Trading Agent with faster response times"""
    
    def __init__(self):
        self.ollama_url = "http://localhost:11434/api/generate"
        self.ai_enabled = self.check_ai_connection()
        self.learning_history = []
        self.last_ai_call = 0
        self.ai_call_delay = 2  # Minimum seconds between AI calls
        
    def check_ai_connection(self):
        """Check if AI is available"""
        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=3)
            if response.status_code == 200:
                models = response.json().get("models", [])
                gemma_models = [m for m in models if "gemma" in m.get("name", "").lower()]
                if gemma_models:
                    print(f"✅ Gemma AI: Connected - {gemma_models[0]['name']}")
                    return True
            print("⚠️ Gemma AI: No suitable model found")
            return False
        except Exception as e:
            print(f"⚠️ Gemma AI: Cannot connect - {e}")
            return False
    
    def should_use_ai(self, market_data, rule_decision):
        """Determine if AI should be consulted for this decision"""
        # Don't use AI too frequently
        current_time = time.time()
        if current_time - self.last_ai_call < self.ai_call_delay:
            return False
            
        # Only use AI for significant market movements or conflicting signals
        price = market_data['price']
        sma50 = market_data['sma50']
        rsi = market_data['rsi']
        atr = market_data['atr']
        
        price_deviation = abs(price - sma50) / sma50
        rsi_extreme = abs(rsi - 50) > 20
        high_volatility = atr > 800
        
        # Use AI only for significant events
        significant_event = (
            price_deviation > 0.05 or  # 5% price deviation
            rsi_extreme or             # Extreme RSI
            high_volatility or         # High volatility
            rule_decision['position_size'] >= 15  # Large position size
        )
        
        return significant_event and self.ai_enabled
    
    def get_ai_decision(self, market_data, portfolio_state, rule_decision):
        """Get AI-enhanced trading decision with timeout protection"""
        if not self.should_use_ai(market_data, rule_decision):
            return rule_decision
        
        try:
            # Rate limiting
            current_time = time.time()
            if current_time - self.last_ai_call < self.ai_call_delay:
                return rule_decision
                
            self.last_ai_call = current_time
            
            prompt = self._build_fast_prompt(market_data, portfolio_state, rule_decision)
            
            payload = {
                "model": "gemma:2b",
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.1,
                    "num_predict": 100,  # Reduced for faster response
                    "top_k": 20,
                    "top_p": 0.8
                }
            }
            
            # Reduced timeout for faster fallback
            response = requests.post(self.ollama_url, json=payload, timeout=8)
            
            if response.status_code == 200:
                result = response.json()
                ai_decision = self._parse_ai_response(result["response"])
                
                # Only use AI decision if it's significantly different
                if self._is_meaningful_improvement(rule_decision, ai_decision):
                    print(f"🤖 GEMMA: {ai_decision['action']} {ai_decision['position_size']}% - {ai_decision['improvement']}")
                    return ai_decision
                else:
                    print(f"🤖 GEMMA: Using rule-based (no meaningful improvement)")
                    return rule_decision
            else:
                print(f"⚠️ Gemma AI: HTTP error {response.status_code}")
                
        except requests.exceptions.Timeout:
            print("⚠️ Gemma AI: Timeout - using rule-based strategy")
        except requests.exceptions.ConnectionError:
            print("⚠️ Gemma AI: Connection error - check Ollama server")
        except Exception as e:
            print(f"⚠️ Gemma AI error: {e}")
        
        return rule_decision
    
    def _build_fast_prompt(self, market_data, portfolio_state, rule_decision):
        """Build optimized prompt for faster response"""
        price, rsi, sma50, sma200 = market_data['price'], market_data['rsi'], market_data['sma50'], market_data['sma200']
        macd, atr = market_data['macd'], market_data['atr']
        cash, btc = portfolio_state['cash'], portfolio_state['btc']
        
        trend = "BULL" if sma50 > sma200 else "BEAR"
        rsi_status = "LOW" if rsi < 30 else "HIGH" if rsi > 70 else "MID"
        
        return f"""BTC: ${price:.0f} | Trend: {trend} | RSI: {rsi:.0f}({rsi_status}) | ATR: ${atr:.0f}
Cash: ${cash:.0f} | BTC: {btc:.4f}
Rule: {rule_decision['action']} {rule_decision['position_size']}% - {rule_decision['reason']}
Improve? Respond with JSON: {{"action":"BUY/SELL/HOLD","position_size":0-20,"reason":"brief","improvement":"what changed"}}"""
    
    def _is_meaningful_improvement(self, rule_decision, ai_decision):
        """Check if AI decision is meaningfully different"""
        if rule_decision['action'] != ai_decision['action']:
            return True
            
        size_diff = abs(rule_decision['position_size'] - ai_decision['position_size'])
        if size_diff > 5:  # At least 5% difference in position size
            return True
            
        return False
    
    def _parse_ai_response(self, response):
        """Parse AI response safely"""
        try:
            clean_response = response.strip()
            
            # Find JSON in response
            start = clean_response.find('{')
            end = clean_response.rfind('}') + 1
            
            if start != -1 and end != 0:
                json_str = clean_response[start:end]
                decision = json.loads(json_str)
                
                # Validate required fields
                if all(key in decision for key in ['action', 'position_size', 'reason']):
                    decision['action'] = decision['action'].upper()
                    # Limit position size for safety
                    decision['position_size'] = min(float(decision['position_size']), 20)
                    decision['source'] = "AI_ENHANCED"
                    if 'improvement' not in decision:
                        decision['improvement'] = "Risk-adjusted position sizing"
                    return decision
        except json.JSONDecodeError:
            print("⚠️ Gemma AI: Invalid JSON response")
        except Exception as e:
            print(f"⚠️ Gemma AI: Parse error - {e}")
        
        # Safe fallback
        return {
            "action": "HOLD", 
            "position_size": 0, 
            "reason": "AI parse error", 
            "improvement": "Used fallback",
            "source": "AI_FALLBACK"
        }

def run_optimized_backtest():
    """Run optimized 6-month backtest with alerts only for recent trades"""
    print("🚀 Starting Optimized 6-Month Bitcoin Backtest")
    print("=" * 60)
    
    start_time = time.time()
    
    # Initialize backtest
    backtest = OptimizedBacktest(initial_cash=100000)
    gemma_agent = FastGemmaAIAgent()
    
    # Step 1: Fetch 6 months of data
    print("\n1. 📊 FETCHING 6 MONTHS OF BINANCE DATA...")
    df = backtest.fetch_6months_binance_data()
    if df is None:
        print("❌ Failed to fetch data")
        return
    
    # Step 2: Calculate indicators
    print("\n2. 📈 CALCULATING TECHNICAL INDICATORS...")
    df_with_indicators = backtest.calculate_technical_indicators(df)
    
    # Step 3: Run backtest (silent mode for historical data)
    print("\n3. 🤖 RUNNING HISTORICAL BACKTEST (SILENT MODE)...")
    print("   Saving all trade decisions to CSV files...")
    print("   Alerts will only be sent for the most recent trades...")
    
    total_rows = len(df_with_indicators)
    processed = 0
    ai_decisions = 0
    rule_decisions = 0
    trades_executed = 0
    
    # Determine the cutoff point for "recent" trades (last 2 weeks of data)
    recent_cutoff = len(df_with_indicators) - (24 * 14)  # Last 14 days
    
    # Process data (every 24th row for performance - ~1 trade per day)
    for idx, row in df_with_indicators.iloc[::24].iterrows():
        if idx < 200:  # Skip warm-up period for indicators
            continue
            
        processed += 1
        timestamp = row["Datetime"]
        price = float(row["Close"])
        rsi = float(row["RSI_14"])
        sma20, sma50, sma200 = float(row["SMA_20"]), float(row["SMA_50"]), float(row["SMA_200"])
        ema12, ema26 = float(row["EMA_12"]), float(row["EMA_26"])
        macd = float(row["MACD"])
        atr = float(row["ATR_14"])
        
        # Market data
        market_data = {
            "price": price, "rsi": rsi, "sma20": sma20, "sma50": sma50, 
            "sma200": sma200, "ema12": ema12, "ema26": ema26, 
            "macd": macd, "atr": atr
        }
        
        # Get rule-based decision
        rule_decision = backtest.rule_based_strategy(market_data, backtest.portfolio)
        
        # Get AI-enhanced decision (with smart filtering)
        final_decision = gemma_agent.get_ai_decision(market_data, backtest.portfolio, rule_decision)
        
        if final_decision['source'] == "AI_ENHANCED":
            ai_decisions += 1
            decision_source = "AI"
        else:
            rule_decisions += 1
            decision_source = "RULES"
        
        # Execute trade
        action = final_decision['action']
        position_size = final_decision['position_size']
        reason = final_decision['reason']
        
        trade_executed = False
        trade_details = {
            'timestamp': timestamp,
            'action': action,
            'price': price,
            'position_size': position_size,
            'reason': reason,
            'decision_source': decision_source,
            'cash_before': backtest.portfolio['cash'],
            'btc_before': backtest.portfolio['btc'],
            'portfolio_value_before': backtest.portfolio['total_value'],
            'rsi': rsi,
            'atr': atr,
            'trend': "BULLISH" if sma50 > sma200 else "BEARISH"
        }
        
        if action == "BUY" and backtest.portfolio['cash'] > backtest.min_trade_usd:
            trade_amount = backtest.portfolio['cash'] * (position_size / 100.0)
            if trade_amount >= backtest.min_trade_usd:
                btc_bought = trade_amount / price
                backtest.portfolio['cash'] -= trade_amount
                backtest.portfolio['btc'] += btc_bought
                trade_executed = True
                
                trade_details.update({
                    'trade_amount': trade_amount,
                    'btc_traded': btc_bought,
                    'type': 'BUY'
                })
                
        elif action == "SELL" and backtest.portfolio['btc'] > 0:
            sell_quantity = backtest.portfolio['btc'] * (position_size / 100.0)
            if sell_quantity > 0:
                trade_amount = sell_quantity * price
                # Simple profit calculation
                profit = sell_quantity * (price - (backtest.portfolio['cash'] / backtest.portfolio['btc'])) if backtest.portfolio['btc'] > 0 else 0
                
                backtest.portfolio['cash'] += trade_amount
                backtest.portfolio['btc'] -= sell_quantity
                backtest.portfolio['realized_profit'] += max(profit, 0)  # Only positive profits
                trade_executed = True
                
                trade_details.update({
                    'trade_amount': trade_amount,
                    'btc_traded': sell_quantity,
                    'profit': max(profit, 0),
                    'type': 'SELL'
                })
        
        # Update portfolio value
        btc_value = backtest.portfolio['btc'] * price
        backtest.portfolio['total_value'] = backtest.portfolio['cash'] + btc_value
        
        # Record trade
        if trade_executed:
            trade_details.update({
                'cash_after': backtest.portfolio['cash'],
                'btc_after': backtest.portfolio['btc'],
                'portfolio_value_after': backtest.portfolio['total_value'],
                'realized_profit': backtest.portfolio['realized_profit']
            })
            backtest.trading_history.append(trade_details)
            trades_executed += 1
            
            # SEND ALERTS ONLY FOR RECENT TRADES (last 2 weeks)
            if idx >= recent_cutoff:
                market_conditions = {
                    'rsi': rsi,
                    'atr': atr,
                    'trend': "BULLISH" if sma50 > sma200 else "BEARISH"
                }
                backtest.alert_system.send_trade_alert(
                    trade_data=trade_details,
                    portfolio_state=backtest.portfolio,
                    current_price=price,
                    market_conditions=market_conditions
                )
                print(f"📧 Alert sent for recent trade: {action} ${trade_details.get('trade_amount', 0):,.0f}")
        
        # Record portfolio snapshot
        if len(backtest.portfolio_history) == 0 or processed % 30 == 0:
            portfolio_snapshot = {
                'timestamp': timestamp,
                'price': price,
                'cash': backtest.portfolio['cash'],
                'btc_holdings': backtest.portfolio['btc'],
                'btc_value': btc_value,
                'total_value': backtest.portfolio['total_value'],
                'realized_profit': backtest.portfolio['realized_profit'],
                'unrealized_profit': backtest.portfolio['total_value'] - backtest.initial_cash
            }
            backtest.portfolio_history.append(portfolio_snapshot)
        
        # Progress update
        if processed % 10 == 0:
            progress = (processed / (len(df_with_indicators.iloc[::24]) - 8)) * 100
            print(f"📈 Progress: {processed}/{(len(df_with_indicators.iloc[::24]) - 8)} ({progress:.1f}%) | "
                  f"Trades: {trades_executed} | AI: {ai_decisions} | Rules: {rule_decisions}")
    
    # Step 4: Save results
    print("\n4. 💾 SAVING BACKTEST RESULTS...")
    save_backtest_results(backtest, df_with_indicators, gemma_agent.learning_history)
    
    # Step 5: Send system activation and completion alerts
    print("\n5. 📧 SENDING SYSTEM ALERTS...")
    
    # Send system activation alert with current price
    current_price = df_with_indicators['Close'].iloc[-1]
    backtest.alert_system.send_system_activation_alert(
        current_price=current_price,
        initial_cash=backtest.initial_cash
    )
    
    # Send trading completed alert
    final_strategy_action = "BUY" if backtest.portfolio['btc'] > 0 else "SELL" if backtest.portfolio['cash'] < backtest.initial_cash else "HOLD"
    final_strategy_reason = "Portfolio rebalancing" if len(backtest.trading_history) > 0 else "Initial setup"
    
    backtest.alert_system.send_trading_completed_alert(
        final_portfolio=backtest.portfolio['total_value'],
        btc_holdings=backtest.portfolio['btc'],
        strategy_action=final_strategy_action,
        strategy_reason=final_strategy_reason
    )
    
    # Step 6: Display summary
    total_time = time.time() - start_time
    print(f"\n6. 📊 BACKTEST COMPLETED IN {total_time/60:.1f} MINUTES!")
    print("=" * 50)
    
    final_value = backtest.portfolio['total_value']
    total_return = ((final_value - backtest.initial_cash) / backtest.initial_cash) * 100
    
    # Buy & Hold comparison
    initial_price = df_with_indicators['Close'].iloc[200]
    final_price = df_with_indicators['Close'].iloc[-1]
    buy_hold_value = (backtest.initial_cash / initial_price) * final_price
    buy_hold_return = ((buy_hold_value - backtest.initial_cash) / backtest.initial_cash) * 100
    
    print(f"🏆 PERFORMANCE SUMMARY:")
    print(f"Initial Capital: ${backtest.initial_cash:,.2f}")
    print(f"Final Portfolio: ${final_value:,.2f}")
    print(f"Total Return: {total_return:+.2f}%")
    print(f"Buy & Hold Return: {buy_hold_return:+.2f}%")
    print(f"Outperformance: {total_return - buy_hold_return:+.2f}%")
    print(f"Realized Profit: ${backtest.portfolio['realized_profit']:,.2f}")
    print(f"BTC Holdings: {backtest.portfolio['btc']:.6f}")
    print(f"Remaining Cash: ${backtest.portfolio['cash']:,.2f}")
    
    print(f"\n🤖 TRADING ACTIVITY:")
    print(f"Total Trades: {trades_executed}")
    print(f"AI Decisions: {ai_decisions}")
    print(f"Rule Decisions: {rule_decisions}")
    if (ai_decisions + rule_decisions) > 0:
        print(f"AI Utilization: {(ai_decisions/(ai_decisions+rule_decisions))*100:.1f}%")
    
    print(f"\n📧 ALERTS SENT: {backtest.alert_system.alert_count} (Recent trades only)")
    
    print(f"\n📊 DASHBOARD DATA READY!")
    print("Run: streamlit run enhanced_dashboard.py")
    return backtest

def save_backtest_results(backtest, market_data, learning_history):
    """Save all backtest results for dashboard"""
    os.makedirs('data', exist_ok=True)
    
    # Save trading history
    if backtest.trading_history:
        trades_df = pd.DataFrame(backtest.trading_history)
        trades_df.to_csv('data/backtest_trading_history.csv', index=False)
        print(f"✅ Saved {len(trades_df)} trades to backtest_trading_history.csv")
    
    # Save portfolio history
    if backtest.portfolio_history:
        portfolio_df = pd.DataFrame(backtest.portfolio_history)
        portfolio_df.to_csv('data/backtest_portfolio_history.csv', index=False)
        print(f"✅ Saved {len(portfolio_df)} portfolio snapshots to backtest_portfolio_history.csv")
    
    # Save market data
    market_data.to_csv('data/backtest_market_data.csv', index=False)
    print("✅ Saved market data to backtest_market_data.csv")
    
    # Save AI learning history
    if learning_history:
        learning_df = pd.DataFrame(learning_history)
        learning_df.to_csv('data/ai_learning_history.csv', index=False)
        print(f"✅ Saved {len(learning_df)} AI learning records")
    
    # Save performance summary
    performance = {
        'initial_capital': backtest.initial_cash,
        'final_portfolio_value': backtest.portfolio['total_value'],
        'total_return_percent': ((backtest.portfolio['total_value'] - backtest.initial_cash) / backtest.initial_cash) * 100,
        'realized_profit': backtest.portfolio['realized_profit'],
        'btc_holdings': backtest.portfolio['btc'],
        'remaining_cash': backtest.portfolio['cash'],
        'total_trades': len(backtest.trading_history),
        'ai_decisions': len([t for t in backtest.trading_history if t['decision_source'] == 'AI']),
        'rule_decisions': len([t for t in backtest.trading_history if t['decision_source'] == 'RULES']),
        'backtest_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'data_period': f"{market_data['Datetime'].min()} to {market_data['Datetime'].max()}",
        'data_points_processed': len(market_data),
        'alerts_sent': backtest.alert_system.alert_count
    }
    
    with open('data/backtest_performance.json', 'w') as f:
        json.dump(performance, f, indent=2)
    print("✅ Saved performance summary to backtest_performance.json")

if __name__ == "__main__":
    run_optimized_backtest()