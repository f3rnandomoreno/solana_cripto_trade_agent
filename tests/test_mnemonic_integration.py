import pytest
import asyncio
import os
from solders.keypair import Keypair
from solana.rpc.async_api import AsyncClient
from solana.rpc.commitment import Confirmed
from src.config import settings, derive_private_key_from_mnemonic


class MnemonicWallet:
    """Wallet integration specifically for mnemonic testing."""
    
    def __init__(self, mnemonic: str, rpc_endpoint: str):
        self.rpc_endpoint = rpc_endpoint
        self.client = AsyncClient(rpc_endpoint)
        self.mnemonic = mnemonic
        self.keypair = self._derive_keypair_from_mnemonic(mnemonic)
    
    def _derive_keypair_from_mnemonic(self, mnemonic: str) -> Keypair:
        """Derive keypair from mnemonic phrase."""
        try:
            from mnemonic import Mnemonic
            mnemo = Mnemonic("english")
            
            # Validate mnemonic
            if not mnemo.check(mnemonic):
                raise ValueError("Invalid mnemonic phrase")
            
            # Generate seed and keypair
            seed = mnemo.to_seed(mnemonic)
            keypair = Keypair.from_seed(seed[:32])
            return keypair
            
        except Exception as e:
            raise ValueError(f"Failed to derive keypair from mnemonic: {e}")
    
    @property
    def public_key(self):
        """Get wallet public key."""
        return self.keypair.pubkey()
    
    @property
    def private_key_array(self):
        """Get private key as array format."""
        return list(self.keypair.to_bytes())
    
    async def get_sol_balance(self) -> float:
        """Get SOL balance in SOL units."""
        try:
            response = await self.client.get_balance(
                self.public_key, 
                commitment=Confirmed
            )
            return response.value / 1e9
        except Exception as e:
            raise Exception(f"Failed to get SOL balance: {e}")
    
    async def close(self):
        """Close RPC client connection."""
        await self.client.close()


@pytest.mark.asyncio
async def test_mnemonic_processing():
    """Test that mnemonic is correctly processed by config system."""
    
    # Get mnemonic from environment
    mnemonic = os.getenv('MNEMONIC', '')
    if not mnemonic:
        pytest.skip("MNEMONIC not configured in .env - set valid mnemonic to run test")
    
    print(f"\n=== Testing Mnemonic Processing ===")
    print(f"Mnemonic words count: {len(mnemonic.split())}")
    print(f"First 3 words: {' '.join(mnemonic.split()[:3])}")
    
    # Test direct mnemonic processing
    try:
        private_key_array = derive_private_key_from_mnemonic(mnemonic)
        assert private_key_array is not None, "Mnemonic should derive private key"
        assert len(private_key_array) == 64, f"Private key should be 64 bytes, got {len(private_key_array)}"
        print(f"✅ Direct mnemonic processing: SUCCESS")
        print(f"   Private key length: {len(private_key_array)} bytes")
        print(f"   First 5 bytes: {private_key_array[:5]}")
    except Exception as e:
        pytest.fail(f"Direct mnemonic processing failed: {e}")
    
    # Test config system processing
    try:
        assert settings.private_key, "Settings should have private key from mnemonic"
        assert settings.private_key != "CHANGE_ME", "Settings should process mnemonic correctly"
        
        # Parse the private key from settings
        config_private_key = eval(settings.private_key)
        assert len(config_private_key) == 64, f"Config private key should be 64 bytes, got {len(config_private_key)}"
        assert config_private_key == private_key_array, "Config and direct processing should match"
        
        print(f"✅ Config system processing: SUCCESS")
        print(f"   Settings private key length: {len(settings.private_key)} chars")
        print(f"   Parsed key matches direct: {config_private_key == private_key_array}")
    except Exception as e:
        pytest.fail(f"Config system processing failed: {e}")


@pytest.mark.asyncio
async def test_mnemonic_wallet_integration():
    """Full integration test: mnemonic -> keypair -> wallet -> balance."""
    
    mnemonic = os.getenv('MNEMONIC', '')  
    if not mnemonic:
        pytest.skip("MNEMONIC not configured in .env")
    
    wallet = None
    try:
        print(f"\n=== Testing Full Wallet Integration ===")
        
        # Create wallet from mnemonic
        wallet = MnemonicWallet(mnemonic, settings.rpc_endpoint)
        
        # Test keypair generation
        assert wallet.keypair is not None, "Keypair should be generated"
        assert wallet.public_key is not None, "Public key should be available"
        
        print(f"✅ Keypair generation: SUCCESS")
        print(f"   Public key: {wallet.public_key}")
        
        # Test private key format
        private_key = wallet.private_key_array
        assert len(private_key) == 64, f"Private key should be 64 bytes, got {len(private_key)}"
        
        print(f"✅ Private key format: SUCCESS")
        print(f"   Length: {len(private_key)} bytes")
        print(f"   Array format: [{private_key[0]}, {private_key[1]}, {private_key[2]}, ...]")
        
        # Test balance retrieval
        balance = await wallet.get_sol_balance()
        assert isinstance(balance, float), "Balance should be float"
        assert balance >= 0, "Balance should be non-negative"
        
        print(f"✅ Balance retrieval: SUCCESS")
        print(f"   SOL Balance: {balance:.9f} SOL")
        print(f"   RPC Endpoint: {settings.rpc_endpoint}")
        
        # Test consistency with config system
        config_key_array = eval(settings.private_key)
        assert private_key == config_key_array, "Wallet and config keys should match"
        
        print(f"✅ Config consistency: SUCCESS")
        print(f"   Keys match: {private_key[:3] == config_key_array[:3]}")
        
        # Final summary
        print(f"\n🎉 MNEMONIC INTEGRATION TEST COMPLETE!")
        print(f"   ✅ Mnemonic processing: Working")
        print(f"   ✅ Config integration: Working") 
        print(f"   ✅ Keypair generation: Working")
        print(f"   ✅ Wallet creation: Working")
        print(f"   ✅ Balance retrieval: Working")
        print(f"   📍 Address: {wallet.public_key}")
        print(f"   💰 Balance: {balance:.9f} SOL")
        
    except Exception as e:
        pytest.fail(f"Mnemonic wallet integration failed: {e}")
    finally:
        if wallet:
            await wallet.close()


@pytest.mark.asyncio
async def test_mnemonic_vs_private_key_priority():
    """Test that PRIVATE_KEY takes precedence over MNEMONIC when both are set."""
    
    import tempfile
    import os
    from dotenv import load_dotenv
    
    # Create temporary .env file with both PRIVATE_KEY and MNEMONIC
    test_private_key = "[1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52,53,54,55,56,57,58,59,60,61,62,63,64]"
    test_mnemonic = "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about"
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
        f.write(f'PRIVATE_KEY="{test_private_key}"\n')
        f.write(f'MNEMONIC="{test_mnemonic}"\n')
        f.write(f'RPC_ENDPOINT="https://api.mainnet-beta.solana.com"\n')
        temp_env_file = f.name
    
    try:
        # Load the test environment
        load_dotenv(temp_env_file, override=True)
        
        # Create new settings instance to test
        from src.config import Settings
        test_settings = Settings()
        
        # Should use PRIVATE_KEY, not derive from MNEMONIC
        assert test_settings.private_key == test_private_key, "Should use PRIVATE_KEY when both are present"
        
        print(f"✅ Priority test: PRIVATE_KEY correctly takes precedence over MNEMONIC")
        
    finally:
        # Cleanup
        os.unlink(temp_env_file)
        # Reload original environment and clear variables
        load_dotenv(override=True)
        os.environ.pop("MNEMONIC", None)
        os.environ.pop("PRIVATE_KEY", None)


if __name__ == "__main__":
    # Run tests directly
    asyncio.run(test_mnemonic_processing())
    asyncio.run(test_mnemonic_wallet_integration())