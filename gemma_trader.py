import requests
import json
import pandas as pd
from datetime import datetime

class GemmaTradingAgent:
    """Gemma AI that learns from strategy rules and makes intelligent decisions"""
    
    def __init__(self):
        self.ollama_url = "http://localhost:11434/api/generate"
        self.ai_enabled = False
        self.learning_history = []
        self.check_ai_connection()
    
    def check_ai_connection(self):
        """Check if AI is available with better error handling"""
        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get("models", [])
                if any("gemma" in m.get("name", "").lower() for m in models):
                    self.ai_enabled = True
                    print("✅ Gemma AI: Connected and ready to learn")
                else:
                    print("⚠️ Gemma AI: No Gemma model found")
            else:
                print("⚠️ Gemma AI: Ollama not responding")
        except Exception as e:
            print(f"⚠️ Gemma AI: Cannot connect to Ollama - {e}")
            self.ai_enabled = False
    
    def get_ai_decision(self, market_data, strategy_state, rule_decision):
        """Get AI decision that learns from rule-based strategy with timeout handling"""
        if not self.ai_enabled:
            return rule_decision
        
        try:
            # Build learning prompt with rule-based context
            prompt = self._build_learning_prompt(market_data, strategy_state, rule_decision)
            
            payload = {
                "model": "gemma:2b",
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.1, "num_predict": 200}
            }
            
            response = requests.post(self.ollama_url, json=payload, timeout=15)
            if response.status_code == 200:
                result = response.json()
                ai_decision = self._parse_ai_response(result["response"])
                
                # Log learning for analysis
                self._log_learning(market_data, rule_decision, ai_decision)
                
                print(f"🤖 GEMMA: {ai_decision['action']} {ai_decision['position_size']}% - {ai_decision['reason'][:50]}...")
                return ai_decision
            else:
                print(f"⚠️ Gemma AI: HTTP error {response.status_code}")
                
        except Exception as e:
            print(f"⚠️ Gemma AI error: {e}, using rule-based strategy")
        
        return rule_decision
    
    def _build_learning_prompt(self, market_data, strategy_state, rule_decision):
        """Build prompt that teaches Gemma the trading strategy"""
        price = market_data['price']
        rsi = market_data['rsi']
        sma20 = market_data['sma20']
        sma50 = market_data['sma50']
        sma200 = market_data['sma200']
        ema12 = market_data['ema12']
        ema26 = market_data['ema26']
        macd = market_data['macd']
        atr = market_data['atr']
        
        cash = strategy_state['cash']
        btc = strategy_state['btc']
        
        # Current market analysis
        trend = "BULLISH" if sma50 > sma200 else "BEARISH"
        volatility = "HIGH" if atr > 1000 else "NORMAL"
        rsi_status = "OVERSOLD" if rsi < 30 else "OVERBOUGHT" if rsi > 70 else "NEUTRAL"
        
        return f"""You are an advanced Bitcoin trading AI. Learn from the rule-based strategy and make better decisions.

MARKET ANALYSIS:
- Price: ${price:.2f}, Trend: {trend}, Volatility: {volatility}
- RSI: {rsi:.1f} ({rsi_status}), MACD: {macd:.4f}
- SMA50: ${sma50:.2f}, SMA200: ${sma200:.2f}
- Holdings: BTC: {btc:.4f}, Cash: ${cash:.0f}

RULE-BASED STRATEGY DECISION:
- Action: {rule_decision['action']}
- Position Size: {rule_decision['position_size']}%
- Reason: {rule_decision['reason']}

YOUR TASK: Analyze if the rule-based decision is optimal. Consider risk management and market context.

Respond with JSON only:
{{
    "action": "BUY/SELL/HOLD",
    "position_size": 0-100,
    "reason": "Your improved reasoning",
    "improvement": "What you improved"
}}

JSON:"""
    
    def _parse_ai_response(self, response):
        """Parse AI response with error handling"""
        try:
            clean_response = response.strip()
            start = clean_response.find('{')
            end = clean_response.rfind('}') + 1
            
            if start != -1 and end != 0:
                json_str = clean_response[start:end]
                decision = json.loads(json_str)
                
                # Validate and sanitize
                if all(key in decision for key in ['action', 'position_size', 'reason']):
                    decision['action'] = decision['action'].upper()
                    decision['position_size'] = min(float(decision['position_size']), 100)
                    if 'improvement' not in decision:
                        decision['improvement'] = "No specific improvement noted"
                    return decision
        except:
            pass
        
        # Return safe default
        return {
            "action": "HOLD", 
            "position_size": 0, 
            "reason": "AI parse error", 
            "improvement": "Used fallback"
        }
    
    def _log_learning(self, market_data, rule_decision, ai_decision):
        """Log the learning process for analysis"""
        learning_entry = {
            "timestamp": datetime.now(),
            "market_data": market_data,
            "rule_decision": rule_decision,
            "ai_decision": ai_decision,
            "improvement": ai_decision.get('improvement', 'No improvement')
        }
        self.learning_history.append(learning_entry)