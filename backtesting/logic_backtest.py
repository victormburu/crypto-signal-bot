import pandas as pd
import joblib
import sys
import time
import schedule
import os
import matplotlib.pyplot as plt
from datetime import datetime

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from script.feature_engineering import add_indicators
from portfolio.portfolio_manager import PortfolioManager

def run_backtest():
    print("\n🚀 Running backtest...")

    model = joblib.load("../models/crypto_model.pkl")
    scaler = joblib.load("../models/scaler_model.pkl")

    df = pd.read_csv("../data/BTCUSDT_1h.csv")
    df = add_indicators(df)
    df.columns = df.columns.str.lower()
    df.dropna(inplace=True)

    features = [
        'rsi_14', 'roc_10', 'sma_20', 'ema_20', 'ema_50',
        'ema_200', 'macd', 'macd_signal', 'macd_hist', 'atr_14',
        'bb_width', 'volume_ratio'
    ]
    X = df[features].dropna()
    X_scaled = scaler.transform(X)

    # === Predict probabilities and signals ===
    df["probability"] = model.predict_proba(X_scaled)[:, 1]
    low, high = df["probability"].quantile([0.35, 0.65])
    df["signal"] = df["probability"].apply(
        lambda p: "BUY" if p > high else "SELL" if p < low else "HOLD"
    )

    # === Initialize Portfolio ===
    pm = PortfolioManager(initial_cash=1000, max_risk_per_trade=0.02)
    symbol = "BTCUSDT"

    for _, row in df.iterrows():
        price = row["close"]
        signal = row["signal"]
        timestamp = row["timestamp"]

        if signal == "BUY" and symbol not in pm.positions:
            qty = pm.size_from_risk(symbol, price)
            pm.open_position(symbol, price, qty)

        elif signal == "SELL" and symbol in pm.positions:
            pm.close_position(symbol, price)

        pm.mark_to_market({symbol: price})
        pm.check_stops_and_tps({symbol: price})

    # === Summary ===
    summary = pm.summary({symbol: df["close"].iloc[-1]})
    pm.save_history_csv("../backtesting/logs/portfolio_backtest_log.csv")

    final_value = summary["total_value"]
    roi = summary["roi_%"]

    # === Log to text file ===
    log_dir = "../backtesting/logs"
    os.makedirs(log_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(log_dir, f"backtest_log_{timestamp}.txt")

    with open(log_file, "w") as f:
        f.write("===== BACKTEST REPORT =====\n")
        f.write(f"Final Portfolio Value: ${final_value:.2f}\n")
        f.write(f"ROI: {roi:.2f}%\n")
        f.write(f"Open Positions: {summary['open_positions']}\n")
        f.write(f"Unrealized PnL: ${summary['unrealized_pnl']:.2f}\n")
        f.write("============================\n")

    print(f"📊 Final ROI: {roi:.2f}%")
    print(f"💰 Final Portfolio Value: ${final_value:.2f}")
    print(f"📈 Open Positions: {summary['open_positions']}")

    # === Plot performance ===
    log_path = "../backtesting/logs/portfolio_backtest_log.csv"

    if os.path.exists(log_path) and os.path.getsize(log_path) > 0:
        try:
            portfolio_df = pd.read_csv(log_path)
            if not portfolio_df.empty and "total_value" in portfolio_df.columns:
                plt.figure(figsize=(10, 5))
                plt.plot(portfolio_df["total_value"], label="Portfolio Value", color="green")
                plt.title("Portfolio Performance Over Time")
                plt.xlabel("Trade Index")
                plt.ylabel("Portfolio Value ($)")
                plt.legend()
                plt.grid(True)
                plt.tight_layout()
                plt.show()
            else:
                print("⚠️ No valid trade data to plot.")
        except Exception as e:
            print(f"⚠️ Could not read portfolio log: {e}")
    else:
        print("⚠️ No portfolio log found or it’s empty — skipping plot.")

    print("✅ Backtest complete.\n")

# === Schedule the backtest ===
schedule.every().day.at("09:30").do(run_backtest)
print("🕒 Scheduler started — waiting for next backtest run...")

while True:
    try:
        schedule.run_pending()
        time.sleep(60)
    except KeyboardInterrupt:
        print("\n🛑 Stopped manually.")
        break