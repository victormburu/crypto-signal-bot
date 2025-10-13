import pandas as pd
import pandas_ta as ta


def  add_indicators(df):
        # --- Basic sanity checks ---
    df = df.copy()
    df.dropna(inplace=True)
    df.columns = df.columns.str.lower()

    # --- Momentum ---
    df["rsi_14"] = ta.rsi(df["close"], length=14)
    df["roc_10"] = ta.roc(df["close"], length=10)
    
    # --- Trend indicators ---
    df["sma_20"] = ta.sma(df["close"], length=20)
    df["ema_20"] = ta.ema(df["close"], length=20)
    df["ema_50"] = ta.ema(df["close"], length=50)
    df["ema_200"] = ta.ema(df["close"], length=200)

    # --- MACD ---
    macd_df = ta.macd(df["close"], fast=12, slow=26, signal=9)
    if macd_df is not None and not macd_df.empty:
        macd_cols = list(macd_df.columns)
        df["macd"] = macd_df[macd_cols[0]]
        df["macd_signal"] = macd_df[macd_cols[1]]
        df["macd_hist"] = macd_df[macd_cols[2]]
    else:
        print("⚠️ MACD not generated — insufficient data length.")

        # --- Volatility indicators ---
    df["atr_14"] = ta.atr(df["high"], df["low"], df["close"], length=14)
    bb = ta.bbands(df["close"], length=20, std=2)
    
    bb_cols = list(bb.columns)
    df["bb_upper"] = bb[bb_cols[0]]
    df["bb_middle"] = bb[bb_cols[1]]
    df["bb_lower"] = bb[bb_cols[2]]
    df["bb_width"] = df["bb_upper"] - df["bb_lower"]


        # --- Volume trend ---
    df["volume_ema_20"] = ta.ema(df["volume"], length=20)
    df["volume_ratio"] = df["volume"] / df["volume_ema_20"]

    # --- Drop any rows with NaN from indicator lookbacks ---
    


    return df


if __name__ == "__main__":
    df = pd.read_csv("/data/BTCUSDT_interval.csv")
    df = add_indicators(df)
    print(df.tail())
    df.to_csv("/models/BTCUSDT_1h_engineered_version.csv", index=False)
    
    
    
    