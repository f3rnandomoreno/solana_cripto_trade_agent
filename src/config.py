
from dataclasses import dataclass
import os
from dotenv import load_dotenv

load_dotenv()

def derive_private_key_from_mnemonic(mnemonic: str):
    try:
        from mnemonic import Mnemonic
        from solders.keypair import Keypair
        mnemo = Mnemonic("english")
        seed = mnemo.to_seed(mnemonic)
        keypair = Keypair.from_seed(seed[:32])
        return list(keypair.to_bytes())
    except Exception as e:
        print(f"Error derivando clave privada del mnemonic: {e}")
        return None

@dataclass
class Settings:
    private_key: str = ""
    rpc_endpoint: str = os.getenv("RPC_ENDPOINT", "https://api.mainnet-beta.solana.com")
    base_mint: str = os.getenv("BASE_MINT", "So11111111111111111111111111111111111111112")
    quote_mint: str = os.getenv("QUOTE_MINT", "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v")
    trading_interval_sec: int = int(os.getenv("TRADING_INTERVAL_SEC", 60))
    slippage_bps: int = int(os.getenv("SLIPPAGE_BPS", 50))
    max_drawdown_pct: int = int(os.getenv("MAX_DRAWDOWN_PCT", 20))

    def __post_init__(self):
        pk = os.getenv("PRIVATE_KEY", "")
        if pk:
            self.private_key = pk
        else:
            mnemonic = os.getenv("MNEMONIC", "")
            if mnemonic:
                derived = derive_private_key_from_mnemonic(mnemonic)
                if derived:
                    self.private_key = str(derived)
                else:
                    print("No se pudo derivar la clave privada del MNEMONIC.")
            else:
                print("No se encontró PRIVATE_KEY ni MNEMONIC en el entorno.")

settings = Settings()
