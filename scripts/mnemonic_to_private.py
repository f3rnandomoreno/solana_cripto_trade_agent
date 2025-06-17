from mnemonic import Mnemonic
from solders.keypair import Keypair
import os
from dotenv import load_dotenv

load_dotenv()

MNEMONIC = os.getenv("MNEMONIC", "")

if MNEMONIC:
    mnemo = Mnemonic("english")
    seed = mnemo.to_seed(MNEMONIC)
    # Solana uses the first 32 bytes of the seed for the private key
    keypair = Keypair.from_seed(seed[:32])
    PRIVATE_KEY_ARRAY = list(keypair.to_bytes())
    print(f"Clave privada derivada (array): {PRIVATE_KEY_ARRAY}")
    # Si quieres en hex:
    print(f"Clave privada derivada (hex): {keypair.to_bytes().hex()}")
else:
    print("No se encontró MNEMONIC en el entorno.")
