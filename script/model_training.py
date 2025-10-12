import joblib
import pandas as pd
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from feature_engineering import add_indicators
from sklearn.utils import resample
from sklearn.metrics import classification_report, confusion_matrix


def train_model(df):
    df = add_indicators(df)
    df.columns = df.columns.str.lower()

    #target
    df['target'] = (df["close"].shift(-6) >df['close'] * 1.003).astype(int)
    df.dropna(inplace=True)

    #feature
    features = ['rsi_14', 'roc_10', 'sma_20', 'ema_20', 'ema_50',
                'ema_200', 'macd', 'macd_signal', 'macd_hist', 'atr_14',
                'bb_width', 'volume_ratio']
    X = df[features]
    y= df['target']
    
    data = df[features + ['target']]
    majority = data[data.target == 0]
    minority = data[data.target == 1]
    
    minority_upsampled = resample(
        minority,
        replace=True,
        n_samples=len(majority),
        random_state=42
        )
    df_balanced = pd.concat([majority, minority_upsampled]).sample(frac=1, random_state=42)
    X = df_balanced[features]
    y = df_balanced['target']
    
        #-----scaling----
    scaler = StandardScaler()
    X_scaled = pd.DataFrame(scaler.fit_transform(X), columns=X.columns, index=X.index)
        # --- Split Data ---
    # Split data
    X_train, X_test, y_train, y_test = train_test_split( X_scaled, 
        y , test_size=0.2, random_state=42
        )

    model = RandomForestClassifier(random_state=42,
    n_estimators=100,class_weight="balanced")
    params = {
        "n_estimators": [100, 300],
        "max_depth": [5, 10, 20],
        "min_samples_split": [2, 5, 10],
        
    }
    
    grid = GridSearchCV(model, params, cv=3, scoring="f1", n_jobs=-1)
    grid.fit(X_train, y_train)
    
    y_pred = grid.predict(X_test)
    print(confusion_matrix(y_test, y_pred))
    print(classification_report(y_test, y_pred))
    
    best_model = grid.best_estimator_
    acc = best_model.score(X_test, y_test)
    
    print("Best Params:", grid.best_params_)
    print(f"✅ Model trained — Accuracy: {acc:.2f}")

    joblib.dump(best_model, "/models/crypto_model.pkl")
    joblib.dump(scaler, "/models/scaler_model.pkl")
    
    return best_model



if __name__ == "__main__":
    df = pd.read_csv("/models/BTCUSDT_1h_20251009_1045_engineered_version.csv")
    df = train_model(df)
    

