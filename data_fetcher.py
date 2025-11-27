from binance.client import Client
import pandas as pd
from datetime import datetime, timedelta

# Initialize Binance Client
client = Client()

def fetch_binance_data(symbol="BTCUSDT", interval="1h", days=220):
    """
    Fetch cryptocurrency data from Binance API
    
    Parameters:
    - symbol: Trading pair (e.g., BTCUSDT, ETHUSDT)
    - interval: Kline interval (1m, 3m, 5m, 15m, 30m, 1h, 2h, 4h, 6h, 8h, 12h, 1d, 3d, 1w, 1M)
    - days: Number of days of historical data to fetch
    """
    print(f"🔄 Fetching {symbol} {interval} data for {days} days from Binance...")
    
    try:
        # Calculate start date
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Fetch klines (candlestick data)
        klines = client.get_historical_klines(
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
            'Open Time': 'Datetime',
            'Open': 'Open',
            'High': 'High', 
            'Low': 'Low',
            'Close': 'Close',
            'Volume': 'Volume'
        })
        
        # Select and reorder columns
        df = df[['Datetime', 'Open', 'High', 'Low', 'Close', 'Volume']]
        
        print(f"✅ Successfully fetched {len(df)} records")
        print(f"📅 Date range: {df['Datetime'].min()} to {df['Datetime'].max()}")
        print(f"💰 Price range: ${df['Close'].min():.2f} - ${df['Close'].max():.2f}")
        
        return df
        
    except Exception as e:
        print(f"❌ Error fetching data: {e}")
        return None

def save_to_csv(df, symbol="BTCUSDT"):
    """Save DataFrame to CSV"""
    filename = f"binance_{symbol}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    df.to_csv(filename, index=False)
    print(f"💾 Data saved to: {filename}")
    return filename

def display_data_summary(df):
    """Display data summary"""
    print(f"\n" + "="*50)
    print("📊 DATA SUMMARY")
    print("="*50)
    
    print(f"Shape: {df.shape}")
    print(f"Columns: {list(df.columns)}")
    
    print(f"\nFirst 5 rows:")
    print(df.head())
    
    print(f"\nLast 5 rows:")
    print(df.tail())
    
    print(f"\nBasic Statistics:")
    print(df[['Open', 'High', 'Low', 'Close', 'Volume']].describe())

# Main execution
if __name__ == "__main__":
    print("🚀 Binance Data Fetcher")
    print("=" * 50)
    
    # Fetch Bitcoin data
    btc_data = fetch_binance_data(symbol="BTCUSDT", interval="1h", days=220)
    
    if btc_data is not None:
        # Display summary
        display_data_summary(btc_data)
        
        # Save to CSV
        save_to_csv(btc_data)
        
        print(f"\n🎉 Data fetching completed successfully!")
    else:
        print("❌ Failed to fetch data from Binance")