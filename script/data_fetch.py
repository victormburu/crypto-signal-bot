import requests
import pandas as pd
import time
import schedule
from datetime import datetime

base_url = "https://api.binance.com/api/v3/klines"

def get_binance_data(symbol="BTCUSDT", interval="1h", limit=1000, days=2475):
    ms_per_day = 24 * 60 * 60 * 1000
    total_ms = days * ms_per_day
    end_time = int(time.time() * 1000)
    start_time = end_time - total_ms
    
    all_data = []
    
    while True:
        params = {
            "symbol": symbol,
            "interval": interval,
            "limit": limit,
            "startTime": int(start_time), 
            "endTime": int(end_time)
        } 
        response = requests.get(base_url, params=params)
        try:
            data = response.json()
        except ValueError:
            print("NON-JSON response received, skipping this batch.")
            break
        
        if isinstance(data, dict) and "code" in data:
            print(f"Binance API error: {data}")
            break
        
        if not data:
            break
        
        all_data.extend(data)
        
        if len(data) < limit:
            break
        
        end_time = data[0][0] - 1
        
        time.sleep(0.2)
        
    columns = [
        "open_time", "open", "high", "low", "close", "volume",
        "close_time", "quote_asset_volume", "trades", "taker_base_vol",
        "taker_quote_vol", "ignore"
    ]
    df = pd.DataFrame(all_data, columns=columns)
    
    df['open_time'] = pd.to_datetime(df['open_time'], unit='ms')
    df['close_time'] = pd.to_datetime(df['close_time'], unit='ms')
    for col in ['open', 'high', 'low', 'close', 'volume']:
        df[col] = df[col].astype(float)
        
    df.drop_duplicates(subset='open_time', inplace=True)
    df.sort_values('open_time', inplace=True)
    
    return df.reset_index(drop=True)
    
def save_to_csv(df, symbol="BTCUSDT", interval="1h"):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    file_name = f"../data{symbol}_{interval}_{timestamp}.csv"
    df.to_csv(file_name, index=False)
    print(f"Data save to {file_name}")
    return file_name

def my_job():
    print(f"\n=== Running fetch at {datetime.now()} ===")
    df = get_binance_data(symbol="BTCUSDT", interval="1h", limit=1000, days=2475)
    save_to_csv(df)
    print("Done.\n")

schedule.every(1).days.do(my_job)
    
if __name__ =="__main__":
    try:
        print("Starting scheduler... Press ctrl+c to stop.\n")
        while True:
            schedule.run_pending()
            time.sleep(60)
    except KeyboardInterrupt:
        print("\nScheduler stopped by Victor")