import pandas as pd
from binance.client import Client
import os
from dotenv import load_dotenv

load_dotenv()
# Initialize Binance client
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")
BINANCE_API_SECRET = os.getenv("BINANCE_API_SECRET")

client = Client(BINANCE_API_KEY, BINANCE_API_SECRET)
klines = client.get_historical_klines(
    "BTCUSDT", "1h", "1 Jan, 2023", "13 Oct, 2025"
)

data = pd.DataFrame(klines, columns=[
    "timestamp", "open", "high", "low", "close", "volume",
    "close_time", "quote_asset_volume", "num_trades",
    "taker_buy_base", "taker_buy_quote", "ignore"
])

data["timestamp"] = pd.to_datetime(data["timestamp"], unit='ms')
data.set_index("timestamp", inplace=True)
data = data[["open", "high", "low", "close", "volume"]].astype(float)

data.to_csv("../data/BTCUSDT_1h.csv", index=True)
print("✅ Historical data saved.")