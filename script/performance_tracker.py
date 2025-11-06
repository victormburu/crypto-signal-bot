import os
from dotenv import load_dotenv
import pandas as pd
from datetime import datetime, timedelta
from binance.client import Client
from monitoring.metric_logger import log_metrics, log_performance_metrics



load_dotenv()
# -----------------------------
# CONFIGURATION
# -----------------------------
LOG_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "signal_log.csv"))
    
SYMBOL = "BTCUSDT"
TIME_HORIZON_MINUTES = 60

# Initialize Binance client
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")
BINANCE_API_SECRET = os.getenv("BINANCE_API_SECRET")
client = Client(BINANCE_API_KEY, BINANCE_API_SECRET)

# -----------------------------
# STEP 1: LOG SIGNAL
# -----------------------------
def log_signal(symbol, signal, probability, close_price, model_version="v1"):
    try:
        os.makedirs(os.path.dirname(LOG_FILE),exist_ok=True)
        
        entry = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "symbol": symbol,
            "signal": signal,
            "probability": probability,
            "close_price": close_price,
            "model_version": model_version,
            "evaluated": False,
            "outcome": None,
            "profit_loss": None
        }
    
        df = pd.DataFrame([entry])
        df.to_csv(LOG_FILE, mode='a', index=False, header=not os.path.exists(LOG_FILE))
        print(f"✅ Logged signal: {signal} at {close_price}")
    except Exception as e:
        print(f"❌ Error while logging signal: {e}")
# -----------------------------
# STEP 2: EVALUATE OUTCOMES
# -----------------------------
def evaluate_signal():
    if not os.path.exists(LOG_FILE):
        print("No log file found.")
        return
    
    df = pd.read_csv(LOG_FILE)
    
    # ✅ Add missing columns if needed
    for col in ["evaluated", "outcome", "profit_loss"]:
        if col not in df.columns:
            df[col] = None
    
        # ✅ Handle missing type conversions
    df["evaluated"] = df["evaluated"].fillna(False).infer_objects(copy=False)
            
    pending = df[df["evaluated"] == False]
    if pending.empty:
        print("All signals have been evaluated.")
        return
    
    for i, row in pending.iterrows():
        signal_time = datetime.strptime(str(row["timestamp"]), "%Y-%m-%d %H:%M:%S")
        target_time = signal_time + timedelta(minutes=TIME_HORIZON_MINUTES)
        
        # Fetch candle data to find actual price later
        klines = client.get_historical_klines(
            SYMBOL, Client.KLINE_INTERVAL_1MINUTE,
            start_str = signal_time.strftime("%Y-%m-%d %H:%M:%S"),
            end_str = target_time.strftime("%Y-%m-%d %H:%M:%S")
        )
        
        if not klines:
            continue
        
        end_price = float(klines[-1][4])
        initial_price = row["close_price"]
        profit_loss = end_price - initial_price
        outcome = "UP" if profit_loss > 0 else "DOWN"
        
        df.at[i, "evaluated"] = True
        df.at[i, "outcome"] = outcome
        df.at[i, "profit_loss"] = profit_loss
    
    df.to_csv(LOG_FILE, index=False)
    print("✅ Evaluation complete.")
    
# -----------------------------
# STEP 3: PERFORMANCE METRICS
# -----------------------------
def generate_report():
    if not os.path.exists(LOG_FILE):
        print("⚠️ No log file found.")
        return "⚠️ No log file found."

    df = pd.read_csv(LOG_FILE)

    # ✅ Ensure required columns exist
    for col in ["evaluated", "outcome", "profit_loss"]:
        if col not in df.columns:
            df[col] = None

    df["evaluated"] = df["evaluated"].fillna(False)

    evaluated_df = df[df["evaluated"] == True]

    if evaluated_df.empty:
        print("No evaluated signals yet.")
        return "No evaluated signals yet."

    # --- Summary statistics ---
   
    total = len(df)
    evaluated = len(evaluated_df)
    wins = (evaluated_df["profit_loss"] > 0).sum()
    win_rate = (wins / evaluated * 100) if evaluated > 0 else 0
    
    summary = (
        f"📊 Performance Report\n"
        f"• Total Signals: {total}\n"
        f"• Evaluated: {evaluated}\n"
        f"• Wins: {wins}\n"
        f"• Win Rate: {win_rate:.2f}%\n"
    )

    # --- Save report to file ---
    report_path = os.path.join(os.path.dirname(LOG_FILE), "performance_report.txt")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(summary)

    print(summary)

    try:
        avg_profit = evaluated_df["profit_loss"].mean() if not evaluated_df.empty else 0
        avg_abs = evaluated_df["profit_loss"].abs().mean()
        roi = (avg_profit / avg_abs * 100)if avg_abs > 0 else 0
        portfolio_value = 1000 + evaluated_df["profit_loss"].sum()  # simulated equity curve
        log_metrics(SYMBOL, price=0, signal="REPORT", roi=roi, portfolio_value=portfolio_value, open_positions=0)
        log_performance_metrics(symbol=SYMBOL, total_signals=total,roi=0.0, evaluated=evaluated, win_rate=win_rate, wins=wins)
    except Exception as e:
        print(f"⚠️ Failed to log report metrics: {e}")

    # ✅ Return summary so main.py can send it to Telegram
    return summary


# -----------------------------
# Example Usage
# -----------------------------
if __name__ == "__main__":
    evaluate_signal()
    generate_report()