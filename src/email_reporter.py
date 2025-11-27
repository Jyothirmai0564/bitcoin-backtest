import smtplib
import logging
import os
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
from datetime import datetime, timedelta
import pandas as pd
from typing import Dict, List

class EmailReporter:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587
        self.gmail_user = os.getenv('GMAIL_USER')
        self.gmail_password = os.getenv('GMAIL_PASSWORD')
        self.enabled = bool(self.gmail_user and self.gmail_password)
        
        if self.enabled:
            self.logger.info("✅ Email reporting enabled")
        else:
            self.logger.warning("❌ Email reporting disabled - set GMAIL_USER and GMAIL_PASSWORD")
    
    def send_weekly_report(self, data_manager, trading_agent) -> bool:
        """Send weekly performance report"""
        if not self.enabled:
            return False
            
        try:
            # Get data for report
            transactions = data_manager.load_transactions()
            portfolio_history = data_manager.load_portfolio_history()
            performance = trading_agent.get_performance_metrics()
            
            # Generate report content
            subject = f"📊 Bitcoin Trading Weekly Report - {datetime.now().strftime('%Y-%m-%d')}"
            html_content = self._generate_html_report(transactions, portfolio_history, performance)
            
            # Send email
            success = self._send_email(subject, html_content)
            
            if success:
                self.logger.info("✅ Weekly email report sent successfully")
            else:
                self.logger.error("❌ Failed to send weekly email report")
                
            return success
            
        except Exception as e:
            self.logger.error(f"❌ Error sending weekly report: {e}")
            return False
    
    def _generate_html_report(self, transactions: pd.DataFrame, portfolio_history: pd.DataFrame, performance: Dict) -> str:
        """Generate HTML email content"""
        
        # Calculate weekly metrics
        weekly_trades = len(transactions) if not transactions.empty else 0
        current_value = portfolio_history['total_value'].iloc[-1] if not portfolio_history.empty else 0
        initial_cash = 100000  # Default
        total_return_pct = ((current_value - initial_cash) / initial_cash) * 100
        
        # Recent trades (last 10)
        recent_trades = transactions.tail(10).to_dict('records') if not transactions.empty else []
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; color: #333; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; text-align: center; }}
                .metric-card {{ background: #f8f9fa; border-radius: 10px; padding: 20px; margin: 10px 0; border-left: 4px solid #667eea; }}
                .positive {{ color: #28a745; font-weight: bold; }}
                .negative {{ color: #dc3545; font-weight: bold; }}
                .trade-table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
                .trade-table th, .trade-table td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
                .trade-table th {{ background-color: #667eea; color: white; }}
                .buy {{ color: #28a745; }}
                .sell {{ color: #dc3545; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🚀 Bitcoin Trading Weekly Report</h1>
                <p>Week ending {datetime.now().strftime('%B %d, %Y')}</p>
            </div>
            
            <div class="metric-card">
                <h2>📈 Performance Summary</h2>
                <p><strong>Portfolio Value:</strong> <span class="{'positive' if total_return_pct >= 0 else 'negative'}">${current_value:,.2f}</span></p>
                <p><strong>Total Return:</strong> <span class="{'positive' if total_return_pct >= 0 else 'negative'}">{total_return_pct:+.2f}%</span></p>
                <p><strong>Weekly Trades:</strong> {weekly_trades}</p>
                <p><strong>Total Trades:</strong> {performance.get('total_trades', 0)}</p>
                <p><strong>Realized Profit:</strong> ${performance.get('realized_profit', 0):,.2f}</p>
            </div>
            
            <div class="metric-card">
                <h2>🔔 Recent Trading Activity</h2>
        """
        
        if recent_trades:
            html += """
                <table class="trade-table">
                    <tr>
                        <th>Action</th>
                        <th>Amount</th>
                        <th>Price</th>
                        <th>Quantity</th>
                        <th>Reason</th>
                    </tr>
            """
            for trade in recent_trades:
                action_class = "buy" if trade.get('action') == 'BUY' else "sell"
                html += f"""
                    <tr>
                        <td class="{action_class}">{trade.get('action', 'N/A')}</td>
                        <td>${trade.get('amount', 0):,.2f}</td>
                        <td>${trade.get('price', 0):,.2f}</td>
                        <td>{trade.get('quantity', 0):.6f}</td>
                        <td>{trade.get('reason', 'N/A')}</td>
                    </tr>
                """
            html += "</table>"
        else:
            html += "<p>No trades this week.</p>"
        
        html += """
            </div>
            
            <div class="metric-card">
                <h2>📊 System Status</h2>
                <p><strong>Status:</strong> <span style="color: #28a745;">● ACTIVE</span></p>
                <p><strong>Last Update:</strong> {}</p>
                <p><strong>Next Report:</strong> Next Monday 9:00 AM</p>
            </div>
            
            <div style="margin-top: 30px; padding: 20px; background: #f8f9fa; border-radius: 10px;">
                <p><em>This is an automated report from your Bitcoin Trading System.</em></p>
                <p><em>To adjust notification settings, update your configuration.</em></p>
            </div>
        </body>
        </html>
        """.format(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        
        return html
    
    def _send_email(self, subject: str, html_content: str) -> bool:
        """Send email via Gmail SMTP"""
        try:
            # Create message
            msg = MimeMultipart()
            msg['From'] = self.gmail_user
            msg['To'] = self.gmail_user  # Send to yourself
            msg['Subject'] = subject
            
            # Attach HTML content
            msg.attach(MimeText(html_content, 'html'))
            
            # Connect to Gmail SMTP server
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.gmail_user, self.gmail_password)
            
            # Send email
            text = msg.as_string()
            server.sendmail(self.gmail_user, self.gmail_user, text)
            server.quit()
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Email sending failed: {e}")
            return False