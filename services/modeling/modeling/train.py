import os, mlflow, joblib, tempfile
from datetime import datetime, timedelta
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score
from .data import load_prices

def make_features(y, window=5):
    X, Y = [], []
    for i in range(window, len(y)):
        X.append(y[i-window:i])
        Y.append(y[i])
    return np.array(X), np.array(Y)

def train(symbol="AAPL"):
    mlflow.set_tracking_uri(os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5000"))
    mlflow.set_experiment("market-magic")
    with mlflow.start_run(run_name=f"{symbol}-{datetime.utcnow().isoformat()}"):
        df = load_prices(symbol)
        if len(df) < 10:
            raise RuntimeError("Not enough data to train")
        y = df["close"].values.astype(float)
        X, Y = make_features(y, window=5)
        model = LinearRegression().fit(X, Y)
        yhat = model.predict(X)
        score = r2_score(Y, yhat)
        mlflow.log_metric("r2", score)
        with tempfile.TemporaryDirectory() as tmp:
            p = os.path.join(tmp, "model.pkl")
            joblib.dump(model, p)
            mlflow.sklearn.log_model(model, "model", registered_model_name="market-magic-model")
        mv = mlflow.register_model(f"runs:/{mlflow.active_run().info.run_id}/model", "market-magic-model")
        # Note: promote manually or via CI; here we just log.
        print("Registered model version:", mv.version)

if __name__ == "__main__":
    train()
