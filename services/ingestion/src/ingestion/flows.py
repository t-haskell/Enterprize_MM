from prefect import flow, task
from .db import engine
import pandas as pd
from datetime import datetime, timedelta

@task
def fetch_ohlcv(symbol: str, days: int = 5) -> pd.DataFrame:
    # TODO: replace with real provider call (e.g., Yahoo/Polygon)
    now = datetime.utcnow()
    data = [{
        "ts": now - timedelta(days=i),
        "open": 100+i, "high": 101+i, "low": 99+i,
        "close": 100+i, "volume": 1000+i
    } for i in range(days)]
    return pd.DataFrame(data)

@task
def write_prices(symbol: str, df: pd.DataFrame):
    with engine().begin() as conn:
        sid = conn.execute(text("INSERT INTO symbols(symbol) VALUES(:s) ON CONFLICT(symbol) DO UPDATE SET symbol=EXCLUDED.symbol RETURNING id"), {"s": symbol}).scalar()
        df["symbol_id"] = sid
        df.to_sql("ohlcv", conn.connection, if_exists="append", index=False)

@flow
def ingest_ohlcv(symbol: str = "AAPL"):
    df = fetch_ohlcv(symbol)
    write_prices(symbol, df)
