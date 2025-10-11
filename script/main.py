import schedule
import time
import logging
from datetime import datetime

from data_fetch import get_binance_data
from feature_engineering import add_indicators
from predict_signal import generate_signal
from send_notification import send_telegram

# === CONFIGURATION ===
SYMBOL = "BTCUSDT"
TIMEFRAME = "1h"

# Configure logging
logging.basicConfig(
    filename="crypto_bot.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

#--job--
def job():
    try:
        logging .info("🚀 Fetching latest market data...")
        df = get_binance_data(symbol=SYMBOL, interval=TIMEFRAME, limit=1000, days=2475)
        
        logging.info("📈 Computing indicators...")
        df = add_indicators(df)
        
        logging.info("🧠 Generating trading signal...")
        signal, prob = generate_signal(df)
        
        message = (
            f"🕒 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"📊 Symbol: {SYMBOL}\n"
            f"⏱ Timeframe: {TIMEFRAME}\n"
            f"Signal: {signal}\n"
            f"Probability: {prob:.2%}"
        )
        
        print(message)
        send_telegram(message)
        logging.info("✅ Signal generated and sent successfully.")
        
    except Exception as e:
        error_msg = f"❌ Error in job: {e}"
        logging.error(error_msg)
        print(error_msg)
        send_telegram(error_msg)
        
#----scheduler---
schedule.every(2).hours.do(job)

print("🚀 Crypto Signal Bot running... (Press Ctrl+C to stop)")
send_telegram("🤖 Crypto Signal Bot started and running...")
job()

try:
    while True:
        schedule.run_pending()
        time.sleep(60)
except KeyboardInterrupt:
    print("\n🛑 Scheduler stopped manually.")
    logging.info("🛑 Scheduler stopped manually.")
    send_telegram("🛑 Crypto Signal Bot stopped manually.")