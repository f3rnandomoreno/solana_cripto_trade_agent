
from dataclasses import dataclass
import os
from dotenv import load_dotenv

load_dotenv()

def derive_private_key_from_mnemonic(mnemonic: str):
    """
    Derive private key from mnemonic using Phantom-compatible ED25519 derivation.
    Uses path m/44'/501'/0'/0' which is Phantom's default.
    """
    try:
        import hashlib
        import hmac
        import struct
        from mnemonic import Mnemonic
        from solders.keypair import Keypair

        def hmac_sha512(key, data):
            return hmac.new(key, data, hashlib.sha512).digest()

        def derive_ed25519_path(seed, path):
            """ED25519 HD key derivation compatible with Phantom wallet"""
            if not path.startswith('m/'):
                raise ValueError("Path must start with 'm/'")
            path_parts = path[2:].split('/')
            indices = []
            for part in path_parts:
                if part.endswith("'"):
                    index = int(part[:-1]) + 2**31
                else:
                    index = int(part)
                indices.append(index)
            master_secret = hmac_sha512(b"ed25519 seed", seed)
            master_private_key = master_secret[:32]
            master_chain_code = master_secret[32:]
            private_key = master_private_key
            chain_code = master_chain_code
            for index in indices:
                if index < 2**31:
                    index += 2**31
                data = b'\x00' + private_key + struct.pack('>I', index)
                derived = hmac_sha512(chain_code, data)
                private_key = derived[:32]
                chain_code = derived[32:]
            return private_key

        mnemo = Mnemonic("english")
        seed = mnemo.to_seed(mnemonic)
        path = "m/44'/501'/0'/0'"
        private_key_32 = derive_ed25519_path(seed, path)
        keypair = Keypair.from_seed(private_key_32)
        return list(keypair.to_bytes())
    except Exception as e:
        print(f"Error derivando clave privada del mnemonic: {e}")
        return None
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
        if pk and pk != "CHANGE_ME":
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
