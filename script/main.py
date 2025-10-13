import schedule
import time
import os
import logging
from datetime import datetime
from dotenv import load_dotenv

from logging.handlers import RotatingFileHandler
from data_fetch import get_binance_data
from feature_engineering import add_indicators
from predict_signal import generate_signal
from send_notification import send_telegram
from performance_tracker import log_signal, evaluate_signal, generate_report

load_dotenv()
# === CONFIGURATION ===
SYMBOL = os.getenv("SYMBOL", "BTCUSDT")
INTERVAL = int(os.getenv("INTERVAL", 1))

# Configure logging
handler = RotatingFileHandler("crypto_bot.log", maxBytes=5_000_000, backupCount=3)
logging.getLogger().addHandler(handler)

#--job--
def job():
    try:
        logging .info("🚀 Fetching latest market data...")
        df = get_binance_data(symbol=SYMBOL, interval=INTERVAL, limit=1000)
        
        logging.info("📈 Computing indicators...")
        df = add_indicators(df)
        
        logging.info("🧠 Generating trading signal...")
        signal, prob = generate_signal(df)
        current_price = df["close"].iloc[-1]
        log_signal(symbol=SYMBOL, signal=signal, probability=prob, close_price=current_price)
    
        message = (
            f"🕒 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"📊 Symbol: {SYMBOL}\n"
            f"⏱ Interval: {INTERVAL}\n"
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
 
def tracker_job():
    try:
        logging.info("📈 Running performance evaluation...")
        evaluate_signal()
        summary = generate_report()
        if summary:
            send_telegram(summary)
        logging.info("✅ Performance evaluation complete.")
    except Exception as e:
        logging.error(f"❌ Error running performance tracker: {e}")
             
#----scheduler---
schedule.every(2).hours.do(job)
schedule.every(2).hours.at(":05").do(tracker_job)

startup_message = (
    "🤖 *Crypto Signal Bot Started*\n"
    "• Market Signal Job: every 2 hours\n"
    "• Performance Tracker: every 2 hours (offset by 5 min)"

)
print(startup_message)
send_telegram(startup_message)

if __name__ == "__main__":
    job()
    tracker_job()
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)
    except KeyboardInterrupt:
        print("\n🛑 stopped manually.")
        send_telegram("🛑 Bot stopped manually.")
    
