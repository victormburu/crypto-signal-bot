from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
from datetime import datetime
from dotenv import load_dotenv
import os

load_dotenv()
INFLUX_URL = os.getenv("INFLUX_URL", "http://localhost:8086")
INFLUX_TOKEN = os.getenv("INFLUX_TOKEN", "MyInfluxSuperToken")
INFLUX_ORG = os.getenv("INFLUX_ORG", "CryptoOrg")
INFLUX_BUCKET = os.getenv("INFLUX_BUCKET", "CryptoData")

client = InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG)
write_api = client.write_api(write_options=SYNCHRONOUS)

def log_metrics(symbol, price, signal, roi=None, portfolio_value=None, open_positions=None):
    try:
        roi = float(roi) if roi is not None else 0.0
        portfolio_value = float(portfolio_value) if portfolio_value is not None else 0.0
        open_positions = int(open_positions) if open_positions is not None else 0
        point = (
            Point("crypto_bot")
            .tag("symbol", symbol)
            .field("price", float(price))
            .field("roi", float(roi))
            .field("portfolio_value", float(portfolio_value))
            .field("open_positions", int(open_positions))
            .field("signal", str(signal))
            .time(datetime.now(), WritePrecision.NS)
        )
        write_api.write(bucket=INFLUX_BUCKET, org=INFLUX_ORG, record=point)
        print("✅ InfluxDB write success")
    except Exception as e:
        print(f"❌ Error writing to InfluxDB: {e}")

def log_performance_metrics(symbol, win_rate, evaluated, roi, wins, total_signals):
    try:
        point = (
            Point("crypto_bot")
            .tag("symbol", symbol)
            .field("win_rate", float(win_rate))
            .field("evaluated_signals", int(evaluated))
            .field("roi", float(roi))
            .field("wins", int(wins))
            .field("total_signals", int(total_signals))
            .time(datetime.now(), WritePrecision.NS)
        )
        write_api.write(bucket=INFLUX_BUCKET, org=INFLUX_ORG, record=point)
        print("✅ InfluxDB performance metrics written successfully")
    except Exception as e:
        print(f"❌ Error writing performance metrics to InfluxDB: {e}")