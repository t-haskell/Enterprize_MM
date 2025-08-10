-- Basic schema for prices, news, and social signals
CREATE TABLE IF NOT EXISTS symbols (
  id SERIAL PRIMARY KEY,
  symbol TEXT UNIQUE NOT NULL,
  name TEXT
);
CREATE TABLE IF NOT EXISTS ohlcv (
  ts TIMESTAMP NOT NULL,
  symbol_id INT REFERENCES symbols(id),
  open NUMERIC, high NUMERIC, low NUMERIC, close NUMERIC, volume NUMERIC,
  PRIMARY KEY (ts, symbol_id)
);
CREATE TABLE IF NOT EXISTS news (
  id BIGSERIAL PRIMARY KEY,
  ts TIMESTAMP NOT NULL,
  symbol_id INT REFERENCES symbols(id),
  title TEXT,
  content TEXT,
  sentiment NUMERIC, -- [-1, 1]
  source TEXT
);
CREATE INDEX IF NOT EXISTS idx_news_symbol_ts ON news(symbol_id, ts);
CREATE TABLE IF NOT EXISTS social (
  id BIGSERIAL PRIMARY KEY,
  ts TIMESTAMP NOT NULL,
  symbol_id INT REFERENCES symbols(id),
  text TEXT,
  sentiment NUMERIC,
  platform TEXT
);
CREATE INDEX IF NOT EXISTS idx_social_symbol_ts ON social(symbol_id, ts);
CREATE TABLE IF NOT EXISTS predictions (
  ts TIMESTAMP NOT NULL,
  symbol_id INT REFERENCES symbols(id),
  horizon_minutes INT NOT NULL,
  yhat NUMERIC,
  model_version TEXT,
  created_at TIMESTAMP DEFAULT now(),
  PRIMARY KEY (ts, symbol_id, horizon_minutes, model_version)
);
