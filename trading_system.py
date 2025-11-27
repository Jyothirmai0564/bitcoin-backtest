import requests
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
from dotenv import load_dotenv
from binance.client import Client
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import pytz

# Load environment variables
load_dotenv('config/secrets.env')

class RealTradingSystem:
    def __init__(self):
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.chat_id = os.getenv('TELEGRAM_CHAT_ID')
        
        # Initialize Binance Client (public API - no keys needed)
        self.client = Client()
        
        # Trading parameters
        self.portfolio = {
            'cash': 100000,
            'btc': 0.0,
            'total_value': 100000
        }
        self.dca_amount = 500
        self.dca_drop_percent = 3.0
        self.atr_multiplier = 1.5
        self.atr_high = 3000
        self.min_trade_usd = 10
        
        # Market data
        self.current_price = 0
        self.previous_price = 0
        self.indicators = {}
        
        # Gmail configuration
        self.gmail_user = os.getenv('GMAIL_USER')
        self.gmail_password = os.getenv('GMAIL_PASSWORD')
        
        # Riyadh timezone
        self.riyadh_tz = pytz.timezone('Asia/Riyadh')
        
        # Ensure data directory exists
        os.makedirs('data', exist_ok=True)
    
    def get_binance_data(self, symbol="BTCUSDT", interval="1h", days=60):
        """Fetch cryptocurrency data from Binance API"""
        print(f"🔄 Fetching {symbol} {interval} data for {days} days from Binance...")
        
        try:
            # Calculate start date
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            # Fetch klines (candlestick data)
            klines = self.client.get_historical_klines(
                symbol=symbol,
                interval=interval,
                start_str=start_date.strftime("%d %b, %Y"),
                end_str=end_date.strftime("%d %b, %Y")
            )
            
            # Convert to DataFrame
            df = pd.DataFrame(klines, columns=[
                'Open Time', 'Open', 'High', 'Low', 'Close', 'Volume',
                'Close Time', 'Quote Asset Volume', 'Number of Trades',
                'Taker Buy Base Asset Volume', 'Taker Buy Quote Asset Volume', 'Ignore'
            ])
            
            # Convert data types
            numeric_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
            
            for col in numeric_columns:
                df[col] = pd.to_numeric(df[col])
            
            # Convert timestamp to datetime
            df['Open Time'] = pd.to_datetime(df['Open Time'], unit='ms')
            df['Close Time'] = pd.to_datetime(df['Close Time'], unit='ms')
            
            # Rename columns to match standard format
            df = df.rename(columns={
                'Open Time': 'timestamp',
                'Open': 'open',
                'High': 'high', 
                'Low': 'low',
                'Close': 'close',
                'Volume': 'volume'
            })
            
            # Select and reorder columns
            df = df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]
            df.set_index('timestamp', inplace=True)
            
            # Set current and previous prices
            if len(df) >= 2:
                self.current_price = df['close'].iloc[-1]
                self.previous_price = df['close'].iloc[-2]
            elif len(df) == 1:
                self.current_price = df['close'].iloc[-1]
                self.previous_price = self.current_price
            
            print(f"✅ Successfully fetched {len(df)} records")
            print(f"💰 Current BTC Price: ${self.current_price:,.2f}")
            
            return df
            
        except Exception as e:
            print(f"❌ Error fetching Binance data: {e}")
            return None

    def save_portfolio_state(self):
        """Save current portfolio state for dashboard"""
        try:
            portfolio_data = {
                'timestamp': datetime.now().isoformat(),
                'cash': self.portfolio['cash'],
                'btc': self.portfolio['btc'],
                'total_value': self.portfolio['total_value'],
                'btc_price': self.current_price
            }
            
            file_path = 'data/portfolio_history.csv'
            df = pd.DataFrame([portfolio_data])
            
            if os.path.exists(file_path):
                df.to_csv(file_path, mode='a', header=False, index=False)
            else:
                df.to_csv(file_path, index=False)
                
            print(f"✅ Portfolio state saved: ${self.portfolio['total_value']:,.0f}")
            
        except Exception as e:
            print(f"❌ Error saving portfolio: {e}")

    def get_market_data_for_dashboard(self):
        """Get BTC data for dashboard"""
        try:
            btc_data = self.get_binance_data(symbol="BTCUSDT", interval="1h", days=30)
            
            if btc_data is None or btc_data.empty:
                raise Exception("No data received from Binance")
            
            # Calculate technical indicators
            self.calculate_technical_indicators(btc_data)
            
            # Save market data for dashboard
            market_data_path = 'data/btc_market_data.csv'
            btc_data.to_csv(market_data_path)
            
            print(f"✅ Market data saved: {len(btc_data)} records")
            return True
            
        except Exception as e:
            print(f"❌ Error fetching market data: {e}")
            return False

    def calculate_technical_indicators(self, data):
        """Calculate all technical indicators from Binance data"""
        try:
            # SMA
            data['SMA_20'] = data['close'].rolling(window=20).mean()
            data['SMA_50'] = data['close'].rolling(window=50).mean()
            data['SMA_200'] = data['close'].rolling(window=200).mean()
            
            # EMA
            data['EMA_12'] = data['close'].ewm(span=12, adjust=False).mean()
            data['EMA_26'] = data['close'].ewm(span=26, adjust=False).mean()
            
            # MACD
            data['MACD'] = data['EMA_12'] - data['EMA_26']
            data['MACD_Signal'] = data['MACD'].ewm(span=9, adjust=False).mean()
            
            # RSI
            delta = data['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            data['RSI_14'] = 100 - (100 / (1 + rs))
            
            # ATR
            high_low = data['high'] - data['low']
            high_close = np.abs(data['high'] - data['close'].shift())
            low_close = np.abs(data['low'] - data['close'].shift())
            ranges = pd.concat([high_low, high_close, low_close], axis=1)
            true_range = np.max(ranges, axis=1)
            data['ATR_14'] = true_range.rolling(window=14).mean()
            
            # Get latest values
            if not data.empty:
                self.indicators = {
                    'sma20': data['SMA_20'].iloc[-1] if not pd.isna(data['SMA_20'].iloc[-1]) else self.current_price,
                    'sma50': data['SMA_50'].iloc[-1] if not pd.isna(data['SMA_50'].iloc[-1]) else self.current_price,
                    'sma200': data['SMA_200'].iloc[-1] if not pd.isna(data['SMA_200'].iloc[-1]) else self.current_price,
                    'ema12': data['EMA_12'].iloc[-1] if not pd.isna(data['EMA_12'].iloc[-1]) else self.current_price,
                    'ema26': data['EMA_26'].iloc[-1] if not pd.isna(data['EMA_26'].iloc[-1]) else self.current_price,
                    'macd': data['MACD'].iloc[-1] if not pd.isna(data['MACD'].iloc[-1]) else 0,
                    'macd_signal': data['MACD_Signal'].iloc[-1] if not pd.isna(data['MACD_Signal'].iloc[-1]) else 0,
                    'rsi': data['RSI_14'].iloc[-1] if not pd.isna(data['RSI_14'].iloc[-1]) else 50,
                    'atr': data['ATR_14'].iloc[-1] if not pd.isna(data['ATR_14'].iloc[-1]) else 1000
                }
            
            print(f"📊 Indicators - RSI: {self.indicators['rsi']:.1f}, ATR: ${self.indicators['atr']:,.0f}")
            
        except Exception as e:
            print(f"❌ Error calculating indicators: {e}")
            self.indicators = {
                'sma20': self.current_price, 'sma50': self.current_price, 'sma200': self.current_price,
                'ema12': self.current_price, 'ema26': self.current_price, 'macd': 0, 'macd_signal': 0,
                'rsi': 50, 'atr': 1000
            }

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
            return response.status_code == 200
        except Exception as e:
            print(f"Telegram error: {e}")
            return False

    def send_gmail_alert(self, subject, message):
        """Send email via Gmail with proper authentication"""
        gmail_user = os.getenv('GMAIL_USER')
        gmail_password = os.getenv('GMAIL_PASSWORD')
        
        if not gmail_user or not gmail_password:
            print("❌ Missing Gmail credentials in environment variables")
            return False
            
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = gmail_user
            msg['To'] = gmail_user
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
                        .footer {{ margin-top: 20px; padding: 15px; background: #e9ecef; border-radius: 5px; font-size: 12px; color: #6c757d; }}
                    </style>
                </head>
                <body>
                    <div class="container">
                        <div class="header">
                            <h1>🚀 Bitcoin Trading System</h1>
                            <p>Automated Trading Report</p>
                        </div>
                        {message}
                        <div class="footer">
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
            server.login(gmail_user, gmail_password)
            text = msg.as_string()
            server.sendmail(gmail_user, gmail_user, text)
            server.quit()
            
            print(f"✅ Gmail alert sent: {subject}")
            return True
            
        except Exception as e:
            print(f"❌ Gmail error: {str(e)}")
            return False

    def send_comprehensive_telegram_report(self):
        """Send complete daily report via Telegram"""
        try:
            # Load trading data
            try:
                trades_df = pd.read_csv("data/real_trading_history.csv")
                portfolio_df = pd.read_csv("data/portfolio_history.csv")
            except:
                trades_df = pd.DataFrame()
                portfolio_df = pd.DataFrame()
            
            # Calculate metrics
            total_trades = len(trades_df)
            buy_trades = len(trades_df[trades_df['action'] == 'BUY']) if not trades_df.empty else 0
            sell_trades = len(trades_df[trades_df['action'] == 'SELL']) if not trades_df.empty else 0
            total_volume = trades_df['amount'].sum() if not trades_df.empty else 0
            
            current_value = portfolio_df['total_value'].iloc[-1] if not portfolio_df.empty else 100000
            total_return = ((current_value - 100000) / 100000) * 100
            
            # Get strategy decision
            strategy = self.execute_gemma_strategy()
            
            # Create comprehensive message
            message = f"""
📊 **DAILY TRADING REPORT**
━━━━━━━━━━━━━━━━━━━━

💰 **PORTFOLIO OVERVIEW**
• Total Value: ${current_value:,.2f}
• Return: <b>{total_return:+.2f}%</b>
• BTC Price: ${self.current_price:,.2f}

📈 **TRADING ACTIVITY**  
• Total Trades: {total_trades}
• Buy Trades: {buy_trades}
• Sell Trades: {sell_trades}
• Total Volume: ${total_volume:,.0f}

🎯 **MARKET CONDITIONS**
• RSI: {self.indicators.get('rsi', 0):.1f} ({'🔴 Overbought' if self.indicators.get('rsi', 0) > 70 else '🟢 Oversold' if self.indicators.get('rsi', 0) < 30 else '⚪ Neutral'})
• MACD: {self.indicators.get('macd', 0):.4f} ({'🟢 Bullish' if self.indicators.get('macd', 0) > 0 else '🔴 Bearish'})
• ATR: ${self.indicators.get('atr', 0):,.0f}
• Trend: {'🟢 BULLISH' if self.indicators.get('sma50', 0) > self.indicators.get('sma200', 0) else '🔴 BEARISH'}

🤖 **STRATEGY OUTLOOK**
• Action: <b>{strategy['action']}</b>
• Allocation: {strategy['percent']}%
• Reason: {strategy['reason']}

🕒 Report Time: {datetime.now().strftime('%Y-%m-%d %H:%M')}
━━━━━━━━━━━━━━━━━━━━
💡 <i>Bitcoin Trading System - Automated 24/7</i>
            """
            
            success = self.send_telegram_alert(message)
            if success:
                print("✅ Comprehensive Telegram report sent!")
            return success
            
        except Exception as e:
            print(f"❌ Telegram report error: {e}")
            return False

    def send_daily_report(self):
        """Send daily trading report - tries Gmail first, falls back to Telegram"""
        try:
            # Get current Riyadh time
            riyadh_time = datetime.now(self.riyadh_tz)
            print(f"🕒 Current Riyadh time: {riyadh_time.strftime('%Y-%m-%d %H:%M:%S %Z')}")
            
            # Load trading data
            try:
                trades_df = pd.read_csv("data/real_trading_history.csv")
                portfolio_df = pd.read_csv("data/portfolio_history.csv")
            except FileNotFoundError:
                print("❌ No trading data found")
                trades_df = pd.DataFrame()
                portfolio_df = pd.DataFrame()
            
            # Calculate daily metrics
            total_trades = len(trades_df)
            buy_trades = len(trades_df[trades_df['action'] == 'BUY']) if not trades_df.empty else 0
            sell_trades = len(trades_df[trades_df['action'] == 'SELL']) if not trades_df.empty else 0
            total_volume = trades_df['amount'].sum() if not trades_df.empty else 0
            
            if not portfolio_df.empty:
                current_value = portfolio_df['total_value'].iloc[-1]
                initial_value = 100000
                total_return = ((current_value - initial_value) / initial_value) * 100
            else:
                current_value = 100000
                total_return = 0
            
            # Get today's trades
            today = datetime.now().date()
            today_trades = trades_df[pd.to_datetime(trades_df['timestamp']).dt.date == today] if not trades_df.empty else pd.DataFrame()
            
            # Create email content
            subject = f"📊 Daily Trading Report - {riyadh_time.strftime('%Y-%m-%d')}"
            
            message = f"""
            <div class="header">
                <h3>📈 Daily Trading Summary</h3>
            </div>
            
            <div class="content">
                <h4>💰 Portfolio Overview</h4>
                <ul>
                    <li><strong>Current Portfolio Value:</strong> ${current_value:,.2f}</li>
                    <li><strong>Total Return:</strong> {total_return:+.2f}%</li>
                    <li><strong>BTC Price:</strong> ${self.current_price:,.2f}</li>
                </ul>
                
                <h4>📊 Trading Activity</h4>
                <ul>
                    <li><strong>Total Trades:</strong> {total_trades}</li>
                    <li><strong>Buy Trades:</strong> {buy_trades}</li>
                    <li><strong>Sell Trades:</strong> {sell_trades}</li>
                    <li><strong>Total Volume:</strong> ${total_volume:,.2f}</li>
                    <li><strong>Today's Trades:</strong> {len(today_trades)}</li>
                </ul>
                
                <h4>🎯 Market Conditions</h4>
                <ul>
                    <li><strong>RSI:</strong> {self.indicators.get('rsi', 0):.1f}</li>
                    <li><strong>MACD:</strong> {self.indicators.get('macd', 0):.2f}</li>
                    <li><strong>ATR:</strong> ${self.indicators.get('atr', 0):,.0f}</li>
                    <li><strong>Trend:</strong> {'Bullish' if self.indicators.get('sma50', 0) > self.indicators.get('sma200', 0) else 'Bearish'}</li>
                </ul>
            """
            
            # Add today's trades if any
            if len(today_trades) > 0:
                message += "<h4>🔄 Today's Trades</h4>"
                for _, trade in today_trades.iterrows():
                    emoji = "🟢" if trade['action'] == 'BUY' else "🔴"
                    message += f"""
                    <div class="trade">
                        {emoji} <strong>{trade['action']}</strong> - ${trade['amount']:,.2f} 
                        at ${trade['price']:,.2f}<br>
                        <em>Reason: {trade['reason']}</em>
                    </div>
                    """
            
            # Add strategy recommendation
            strategy_result = self.execute_gemma_strategy()
            message += f"""
            <h4>🤖 Strategy Outlook</h4>
            <div class="alert">
                <strong>Next Action:</strong> {strategy_result['action']}<br>
                <strong>Allocation:</strong> {strategy_result['percent']}%<br>
                <strong>Reason:</strong> {strategy_result['reason']}
            </div>
            """
            
            # Try Gmail first
            print("🔄 Attempting to send via Gmail...")
            gmail_success = self.send_gmail_alert(subject, message)
            
            if gmail_success:
                print("✅ Daily report sent via Gmail!")
                return True
            else:
                print("🔄 Gmail failed, falling back to Telegram...")
                # Fall back to Telegram
                telegram_success = self.send_comprehensive_telegram_report()
                if telegram_success:
                    print("✅ Daily report sent via Telegram!")
                    return True
                else:
                    print("❌ Both Gmail and Telegram failed")
                    return False
                
        except Exception as e:
            print(f"❌ Error sending daily report: {e}")
            # Try Telegram as last resort
            try:
                self.send_comprehensive_telegram_report()
            except:
                pass
            return False

    def save_trade_to_history(self, trade_data):
        """Save every trade to CSV for dashboard"""
        try:
            file_path = 'data/real_trading_history.csv'
            
            trade_record = {
                'timestamp': datetime.now().isoformat(),
                'action': trade_data['action'],
                'price': self.current_price,
                'amount': trade_data['amount'],
                'quantity': trade_data['quantity'],
                'reason': trade_data['reason'],
                'portfolio_value': self.portfolio['total_value'],
                'cash_balance': self.portfolio['cash'],
                'btc_balance': self.portfolio['btc'],
                'data_source': 'Binance'
            }
            
            df = pd.DataFrame([trade_record])
            if os.path.exists(file_path):
                df.to_csv(file_path, mode='a', header=False, index=False)
            else:
                df.to_csv(file_path, index=False)
                
            # Save portfolio state after each trade
            self.save_portfolio_state()
                
            print(f"✅ Trade saved to history: {trade_data['action']} ${trade_data['amount']}")
            
        except Exception as e:
            print(f"❌ Error saving trade: {e}")

    def check_price_drop_dca(self):
        """Check for price drop and execute DCA if triggered"""
        price_drop_percent = ((self.previous_price - self.current_price) / self.previous_price) * 100
        
        if price_drop_percent >= self.dca_drop_percent and self.portfolio['cash'] >= self.dca_amount:
            btc_bought = self.dca_amount / self.current_price
            self.portfolio['cash'] -= self.dca_amount
            self.portfolio['btc'] += btc_bought
            btc_value = self.portfolio['btc'] * self.current_price
            self.portfolio['total_value'] = self.portfolio['cash'] + btc_value
            
            trade_data = {
                'action': 'BUY',
                'amount': self.dca_amount,
                'quantity': btc_bought,
                'reason': f'DCA: Price dropped {price_drop_percent:.1f}%'
            }
            
            self.save_trade_to_history(trade_data)
            
            message = f"""🟢 DCA BUY TRIGGERED
BTC dropped {price_drop_percent:.1f}% to ${self.current_price:,.0f}
Bought: ${self.dca_amount} worth ({btc_bought:.5f} BTC)
Portfolio: {self.portfolio['btc']:.2f} BTC (${btc_value:,.0f})"""
            
            success = self.send_telegram_alert(message)
            if success:
                print("✅ DCA Buy executed and alert sent!")
            return True
        
        return False

    def execute_gemma_strategy(self):
        """Execute Gemma trading strategy"""
        price = self.current_price
        sma50 = self.indicators['sma50']
        sma200 = self.indicators['sma200']
        macd = self.indicators['macd']
        rsi = self.indicators['rsi']
        atr = self.indicators['atr']
        
        strat_action = "HOLD"
        strat_percent = 0.0
        reason = ""

        # Force some trades for testing if no trades exist
        try:
            trades_df = pd.read_csv('data/real_trading_history.csv')
            if len(trades_df) < 2:  # If less than 2 trades, force some
                strat_action, strat_percent, reason = "BUY", 10, "Initial portfolio setup"
            elif atr > self.atr_high:
                strat_action, strat_percent, reason = "HOLD", 0, "High volatility - too risky"
            elif sma50 > sma200:
                if rsi < 40:
                    strat_action, strat_percent, reason = "BUY", 15, "Bull market & RSI oversold"
                elif macd > 0 and rsi > 50:
                    strat_action, strat_percent, reason = "BUY", 10, "Bull market & momentum up"
                else:
                    strat_action, strat_percent, reason = "HOLD", 0, "Bull market but waiting"
            elif sma50 < sma200:
                if rsi > 60 and self.portfolio['btc'] > 0:
                    strat_action, strat_percent, reason = "SELL", 15, "Bear market & RSI overbought"
                elif macd < 0 and rsi < 50:
                    strat_action, strat_percent, reason = "SELL", 10, "Bear market & momentum down"
                else:
                    strat_action, strat_percent, reason = "HOLD", 0, "Bear market but waiting"
            else:
                if rsi < 35:
                    strat_action, strat_percent, reason = "BUY", 5, "RSI very oversold"
                elif rsi > 65:
                    strat_action, strat_percent, reason = "SELL", 5, "RSI very overbought" 
                else:
                    strat_action, strat_percent, reason = "HOLD", 0, "Market neutral - no clear signal"
        except:
            # If no trade file exists, force initial trade
            strat_action, strat_percent, reason = "BUY", 10, "Initial portfolio setup"

        print(f"🎯 Strategy Decision: {strat_action} {strat_percent}% - {reason}")
        
        return {
            'action': strat_action,
            'percent': strat_percent,
            'reason': reason
        }

    def execute_strategy_trade(self, strategy_result):
        """Execute trade based on strategy decision"""
        action = strategy_result['action']
        percent = strategy_result['percent']
        reason = strategy_result['reason']
        
        if action == "HOLD":
            return False

        trade_data = {
            'action': action,
            'percent': percent,
            'reason': reason,
            'amount': 0,
            'quantity': 0
        }
        
        if action == "BUY" and self.portfolio['cash'] > self.min_trade_usd:
            trade_amount = min(self.portfolio['cash'] * (percent / 100), self.portfolio['cash'])
            btc_bought = trade_amount / self.current_price
            self.portfolio['cash'] -= trade_amount
            self.portfolio['btc'] += btc_bought
            
            trade_data.update({
                'amount': trade_amount,
                'quantity': btc_bought
            })
            
        elif action == "SELL" and self.portfolio['btc'] > 0:
            sell_quantity = min(self.portfolio['btc'] * (percent / 100), self.portfolio['btc'])
            trade_amount = sell_quantity * self.current_price
            self.portfolio['cash'] += trade_amount
            self.portfolio['btc'] -= sell_quantity
            
            trade_data.update({
                'amount': trade_amount,
                'quantity': sell_quantity
            })
        
        else:
            return False

        btc_value = self.portfolio['btc'] * self.current_price
        self.portfolio['total_value'] = self.portfolio['cash'] + btc_value
        
        self.save_trade_to_history(trade_data)
        
        success = self.send_trade_alert(trade_data)
        if success:
            print(f"✅ Strategy trade executed and saved: {action}")
        return success

    def send_trade_alert(self, trade_data):
        """Send formatted trade alert"""
        emoji = "🟢" if trade_data['action'] == 'BUY' else "🔴"
        message = f"""
{emoji} TRADE EXECUTED: {trade_data['action']}

Amount: ${trade_data['amount']:,.2f}
Price: ${self.current_price:,.2f}
Quantity: {trade_data['quantity']:.6f} BTC
Reason: {trade_data['reason']}

Portfolio:
• BTC: {self.portfolio['btc']:.4f} BTC
• Cash: ${self.portfolio['cash']:,.2f}
• Total: ${self.portfolio['total_value']:,.2f}"""
        
        return self.send_telegram_alert(message)

    def run_complete_system(self):
        """Run complete trading system"""
        print("🚀 Starting Trading System with Binance Data")
        
        # Get market data first
        if not self.get_market_data_for_dashboard():
            print("❌ Failed to get market data")
            return False
        
        # Send startup message
        startup_msg = f"""🎬 TRADING SYSTEM ACTIVATED

Current Price: ${self.current_price:,.0f}
Initial Portfolio: ${self.portfolio['cash']:,.0f}"""
        self.send_telegram_alert(startup_msg)
        
        try:
            print("\n1. Checking Price Drop → DCA Buy...")
            dca_triggered = self.check_price_drop_dca()
            
            print("\n2. Running Gemma Strategy Analysis...")
            strategy_result = self.execute_gemma_strategy()
            
            print("\n3. Executing Strategy Trade...")
            if strategy_result['action'] != "HOLD":
                self.execute_strategy_trade(strategy_result)
            else:
                print("📊 No trade executed - HOLD position")
            
            print("\n4. Saving final portfolio state...")
            self.save_portfolio_state()
            
            # Send daily report
            print("\n5. Sending Daily Gmail Report...")
            self.send_daily_report()
            
            final_msg = f"""🎉 TRADING COMPLETED

Final Portfolio: ${self.portfolio['total_value']:,.0f}
BTC Holdings: {self.portfolio['btc']:.4f} BTC
Strategy: {strategy_result['action']} - {strategy_result['reason']}"""
            
            self.send_telegram_alert(final_msg)
            print("\n🎉 Trading system completed successfully!")
            print("📊 Data saved for dashboard!")
            return True
            
        except Exception as e:
            print(f"❌ System error: {e}")
            error_msg = f"❌ Trading system error: {str(e)}"
            self.send_telegram_alert(error_msg)
            return False

# Test the system
if __name__ == "__main__":
    system = RealTradingSystem()
    system.run_complete_system()