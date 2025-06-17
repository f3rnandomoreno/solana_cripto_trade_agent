"""
Wallet management with support for multiple derivation methods.
"""

import os
from typing import Optional, List, Dict
from dataclasses import dataclass
from solders.keypair import Keypair
from solana.rpc.async_api import AsyncClient
from solana.rpc.commitment import Confirmed
from mnemonic import Mnemonic
import hashlib
import hmac


@dataclass
class WalletAccount:
    """Represents a wallet account with its keypair and metadata."""
    keypair: Keypair
    derivation_method: str
    account_index: int = 0
    address_index: int = 0
    
    @property
    def public_key(self):
        return self.keypair.pubkey()
    
    @property
    def private_key_array(self) -> List[int]:
        return list(self.keypair.to_bytes())


class MultiWallet:
    """
    Wallet that can derive multiple accounts from a single mnemonic
    using different derivation methods to match various wallet implementations.
    """
    
    def __init__(self, mnemonic: str, rpc_endpoint: str):
        self.mnemonic = mnemonic
        self.rpc_endpoint = rpc_endpoint
        self.client = AsyncClient(rpc_endpoint)
        self.mnemo = Mnemonic("english")
        self.accounts: List[WalletAccount] = []
        
        # Validate mnemonic
        if not self.mnemo.check(mnemonic):
            raise ValueError("Invalid mnemonic phrase")
    
    def derive_standard_account(self, account_index: int = 0) -> WalletAccount:
        """Derive account using Phantom's standard ED25519 method"""
        from src.config import derive_private_key_from_mnemonic
        
        # Use the same derivation logic as config.py
        private_key_array = derive_private_key_from_mnemonic(self.mnemonic)
        if private_key_array:
            keypair = Keypair.from_bytes(bytes(private_key_array))
            return WalletAccount(
                keypair=keypair,
                derivation_method="phantom_standard",
                account_index=account_index
            )
        else:
            # Fallback to old method
            seed = self.mnemo.to_seed(self.mnemonic)
            keypair = Keypair.from_seed(seed[:32])
            return WalletAccount(
                keypair=keypair,
                derivation_method="standard_fallback",
                account_index=account_index
            )
    
    def derive_phantom_style_accounts(self, max_accounts: int = 10) -> List[WalletAccount]:
        """Derive multiple accounts using Phantom-style derivation methods"""
        accounts = []
        base_seed = self.mnemo.to_seed(self.mnemonic)
        
        for account_index in range(max_accounts):
            # Method 1: SHA256 hash with account index
            account_seed = hashlib.sha256(base_seed + account_index.to_bytes(4, 'little')).digest()
            keypair1 = Keypair.from_seed(account_seed[:32])
            accounts.append(WalletAccount(
                keypair=keypair1,
                derivation_method=f"sha256_account_{account_index}",
                account_index=account_index
            ))
            
            # Method 2: HMAC derivation
            hmac_seed = hmac.new(base_seed, account_index.to_bytes(4, 'big'), hashlib.sha256).digest()
            keypair2 = Keypair.from_seed(hmac_seed[:32])
            accounts.append(WalletAccount(
                keypair=keypair2,
                derivation_method=f"hmac_account_{account_index}",
                account_index=account_index
            ))
            
            # Method 3: Seed offset (if available)
            offset = account_index * 32
            if offset + 32 <= len(base_seed):
                keypair3 = Keypair.from_seed(base_seed[offset:offset+32])
                accounts.append(WalletAccount(
                    keypair=keypair3,
                    derivation_method=f"offset_account_{account_index}",
                    account_index=account_index
                ))
        
        return accounts
    
    def derive_with_passphrases(self, passphrases: List[str]) -> List[WalletAccount]:
        """Derive accounts using different BIP39 passphrases"""
        accounts = []
        
        for passphrase in passphrases:
            try:
                seed = self.mnemo.to_seed(self.mnemonic, passphrase)
                keypair = Keypair.from_seed(seed[:32])
                accounts.append(WalletAccount(
                    keypair=keypair,
                    derivation_method=f"passphrase_{passphrase or 'empty'}",
                    account_index=0
                ))
            except Exception:
                continue
        
        return accounts
    
    async def find_account_with_funds(self, target_address: Optional[str] = None) -> Optional[WalletAccount]:
        """
        Find account that either matches target address or has SOL balance.
        """
        # Generate all possible accounts
        all_accounts = []
        
        # Standard derivation
        all_accounts.append(self.derive_standard_account())
        
        # Phantom-style derivations
        all_accounts.extend(self.derive_phantom_style_accounts(max_accounts=5))
        
        # Passphrase variations
        passphrases = ["", "phantom", "solana", "wallet", "crypto", " "]
        all_accounts.extend(self.derive_with_passphrases(passphrases))
        
        from src.utils.logger import setup_logger
        logger = setup_logger()
        logger.info(f"🔍 Scanning {len(all_accounts)} derived accounts...")
        
        found_accounts = []
        
        for account in all_accounts:
            address = str(account.public_key)
            
            # Check if this matches target address
            if target_address and address == target_address:
                logger.info(f"✅ Found target address: {address}")
                logger.info(f"   Derivation: {account.derivation_method}")
                return account
            
            # Check balance
            try:
                response = await self.client.get_balance(account.public_key, commitment=Confirmed)
                balance_sol = response.value / 1e9
                
                if balance_sol > 0:
                    found_accounts.append((account, balance_sol))
                    logger.info(f"💰 Found account with {balance_sol:.6f} SOL: {address}")
                    logger.info(f"   Derivation: {account.derivation_method}")
            except Exception as e:
                logger.error(f"❌ Error checking {address}: {e}")
                continue
        
        # Return account with highest balance, or target address match
        if found_accounts:
            best_account = max(found_accounts, key=lambda x: x[1])
            return best_account[0]
        
        return None
    
    async def get_account_info(self, account: WalletAccount) -> Dict:
        """Get detailed account information"""
        try:
            response = await self.client.get_balance(account.public_key, commitment=Confirmed)
            balance_sol = response.value / 1e9
            
            return {
                "address": str(account.public_key),
                "balance_sol": balance_sol,
                "balance_lamports": response.value,
                "derivation_method": account.derivation_method,
                "account_index": account.account_index,
                "private_key_array": account.private_key_array[:5],  # First 5 bytes only
            }
        except Exception as e:
            return {
                "address": str(account.public_key),
                "error": str(e),
                "derivation_method": account.derivation_method,
            }
    
    async def close(self):
        """Close RPC client connection"""
        await self.client.close()


# Helper function for config integration
def find_correct_private_key_from_mnemonic(mnemonic: str, rpc_endpoint: str, target_address: str) -> Optional[str]:
    """
    Find the correct private key derivation that matches the target address.
    Returns private key as array string if found.
    """
    import asyncio
    
    async def _find():
        wallet = MultiWallet(mnemonic, rpc_endpoint)
        try:
            account = await wallet.find_account_with_funds(target_address)
            if account:
                return str(account.private_key_array)
            return None
        finally:
            await wallet.close()
    
    return asyncio.run(_find())