import logging
import os
import requests
from dotenv import load_dotenv
load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
chat_id = os.getenv("TELEGRAM_CHAT_ID")
url =f"https://api.telegram.org/bot7691144523:AAGvY9iTcPF5zrpnTxxFIoTX6dd8ct3OXu4/sendMessage"

def send_telegram(message: str):
    if not bot_token or not chat_id:
        logging.error("❌ Missing BOT_TOKEN or CHAT_ID environment variables.")
        return False
    
    payload = {"chat_id": chat_id, "text": message}
    try:
        response = requests.post(url, data=payload, timeout=10)
        response.raise_for_status()
        logging.info("✅ Telegram message sent successfully.")
        return True
    except requests.exceptions.RequestException as e:
        logging.error(f"⚠️ Telegram notification failed: {e}")
        return False
    
if __name__ == "__main__":
    send_telegram("🚀 Test message from Vic28 trading bot!")