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
