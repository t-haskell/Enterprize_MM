from sqlalchemy import create_engine, text
import os
import pandas as pd


def load_prices(symbol: str) -> pd.DataFrame:
    url = os.getenv("DATABASE_URL")
    eng = create_engine(url)
    with eng.begin() as conn:
        df = pd.read_sql(
            text("""
            SELECT o.ts, o.close
            FROM ohlcv o
            JOIN symbols s ON s.id = o.symbol_id
            WHERE s.symbol = :symbol
            ORDER BY 1
        """),
            conn,
            params={"symbol": symbol},
        )
    return df
