from dataclasses import dataclass
import os
from dotenv import load_dotenv

load_dotenv()

@dataclass
class Settings:
    private_key: str = os.getenv("PRIVATE_KEY", "")
    rpc_endpoint: str = os.getenv("RPC_ENDPOINT", "https://api.mainnet-beta.solana.com")
    base_mint: str = os.getenv("BASE_MINT", "So11111111111111111111111111111111111111112")
    quote_mint: str = os.getenv("QUOTE_MINT", "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v")
    trading_interval_sec: int = int(os.getenv("TRADING_INTERVAL_SEC", 60))
    slippage_bps: int = int(os.getenv("SLIPPAGE_BPS", 50))
    max_drawdown_pct: int = int(os.getenv("MAX_DRAWDOWN_PCT", 20))

settings = Settings()
