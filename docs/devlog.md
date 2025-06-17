# Development Log

## Step 1
- Initialize project structure
- Added src modules and placeholders
- Created requirements.txt
- Created .env.example

Implemented base structure with config loader and price fetch from Jupiter API.

## Step 2
- Added Pyth network price feed using `pythclient.HermesClient`.
- Updated `requirements.txt` with `pythclient` dependency.
- Expanded `main.py` to display prices from Jupiter and Pyth.

## Step 3
- Implemented EMA, RSI and Bollinger Bands helpers in `strategy/indicators.py`.
- Created `strategy/simple_strategy.py` with a basic signal generator.
- Updated `main.py` to collect recent prices and print the generated signal.
- Documented new modules in README.

## Step 4
- Implemented stubbed Jupiter client in `execution/jupiter_client.py`.
- Created `execution/portfolio.py` for basic position tracking.
- Added `utils/logger.py` and `utils/backtest.py` with simple helpers.
- Updated README with new module descriptions.

## Step 5
- Added `data/mock_feed.py` with a random-walk price generator for offline tests.
- Implemented `TradingBot` class orchestrating feed, strategy and portfolio.
- Simplified `main.py` to run the bot for a short demo.
- Documented new modules and trading loop in README.

## Step 6
- Implemented `AggregatedPriceFeed` combining Jupiter and Pyth sources.
- Updated `TradingBot` to use the aggregated feed by default and request
  swap quotes from Jupiter when executing trades.
- Added new module description and trading loop note in README.

## Step 7
- Introduced CLI in `main.py` with subcommands `trade` and `backtest`.
- `trade` ejecuta el `TradingBot` y acepta `--mock` para usar el feed simulado.
- `backtest` carga precios desde un CSV y reporta el rendimiento obtenido.
- Se añadieron instrucciones de uso en el README.
