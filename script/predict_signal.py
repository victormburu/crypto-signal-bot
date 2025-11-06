import joblib
import os
import pandas as pd
from performance_tracker import log_signal

base_path = os.path.dirname(os.path.abspath(__file__))
def generate_signal(df):
    # Load trained model
    scaler_path = os.path.join(base_path, "..", "models", "scaler_model.pkl")
    model_path = os.path.join(base_path, "..", "models", "crypto_model.pkl")
    model = joblib.load(model_path)
    scaler = joblib.load(scaler_path)

    #model = joblib.load("../models/crypto_model.pkl")
    #scaler = joblib.load("../models/scaler_model.pkl")

    # Select latest features
    features = [
        'rsi_14', 'roc_10', 'sma_20', 'ema_20', 'ema_50',
        'ema_200', 'macd', 'macd_signal', 'macd_hist', 'atr_14',
        'bb_width', 'volume_ratio'
    ]
    missing = [f for f in features if f not in df.columns]
    if missing:
        raise ValueError(f"Missing columns in input data: {missing}")

    latest_data = df[features].iloc[-1:].values

    # Scale the data
    latest_scaled = scaler.transform(latest_data)

    # Predict probability
    prob = model.predict_proba(latest_scaled)[0][1]

    # Convert probability to signal
    if prob > 0.85:
        signal = "🚀 STRONG BUY"
    elif prob > 0.65:
        signal = "BUY 📈"
    elif prob < 0.15:
        signal = "💥 STRONG SELL"
    elif prob < 0.35:
        signal = "SELL 📉"
    else:
        signal = "HOLD 🤔"

    print(f"Model Probability: {prob:.2f} → Signal: {signal}")
    return signal, prob


# ✅ Only run this block if you execute predict_signal.py directly
if __name__ == "__main__":
    df = pd.DataFrame({
        "rsi_14": [55],
        "roc_10": [0.6],
        "sma_20": [26100],
        "ema_20": [26000],
        "ema_50": [25800],
        "ema_200": [25500],
        "macd": [20],
        "macd_signal": [15],
        "macd_hist": [5],
        "atr_14": [150],
        "bb_width": [0.04],
        "volume_ratio": [1.2],
    })
    signal, prob = generate_signal(df)
    close_price = df["close"].iloc[-1]
    log_signal("BTCUSDT", signal, prob, close_price)
