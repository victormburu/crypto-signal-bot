import requests
import pandas as pd
import time
import os
import schedule
from datetime import datetime, timedelta, timezone



base_url = "https://api.binance.com/api/v3/klines"
SYMBOL = "BTCUSDT"
INTERVAL = "1h"
DATA_DIR = "../data"
LIMIT = 1000


def get_binance_data( symbol=SYMBOL, interval=INTERVAL, limit=LIMIT, start_time=None, end_time=None):
    all_data = []
    
    while True:
        params = {
            "symbol": symbol,
            "interval": interval,
            "limit": LIMIT,
        } 
        if start_time:
            params["startTime"] = int(start_time)
        if end_time:
            params["endTime"] =int(end_time)
            
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
        
        #move window forward
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
    
def update_csv(symbol=SYMBOL, interval=INTERVAL):
    os.makedirs(DATA_DIR, exist_ok=True)
    file_path = os.path.join(DATA_DIR, f"{symbol}_interval.csv")
    
    if os.path.exists(file_path):
        existing_df = pd.read_csv(file_path)
        existing_df["open_time"] = pd.to_datetime(existing_df["open_time"])
        
        last_time = existing_df["open_time"].max()
        print(f"📅 Last data point in file: {last_time}")
        
        start_time = int((last_time + timedelta(hours=1)).timestamp() * 1000)
    else:
        print("📂 No existing dataset found — fetching full history (30 days default).")
        start_time = int((datetime.now(timezone.utc) - timedelta(days=1825)).timestamp() * 1000)
        existing_df = pd.DataFrame()
    end_time = int(datetime.now(timezone.utc).timestamp() * 1000)
    start_dt = datetime.fromtimestamp(start_time / 1000, tz=timezone.utc)
    end_dt = datetime.fromtimestamp(end_time / 1000, tz=timezone.utc)
    print(f"🚀 Fetching new data from {start_dt.strftime('%Y-%m-%d %H:%M:%S')} "
          f"to {end_dt.strftime('%Y-%m-%d %H:%M:%S')}...")
    new_df = get_binance_data(SYMBOL, INTERVAL, LIMIT, start_time, end_time)

    if new_df.empty:
        print("✅ No new data available — already up to date.")
        return
    
    # Merge new with existing
    combined = pd.concat([existing_df, new_df], ignore_index=True)
    combined.drop_duplicates(subset="open_time", inplace=True)
    combined.sort_values("open_time", inplace=True)

    combined.to_csv(file_path, index=False)
    print(f"✅ Updated dataset saved: {file_path}")
    print(f"📈 Total records: {len(combined)}") 
    
def my_job():
    print(f"\n=== Running fetch at {datetime.now()} ===")
    update_csv()
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