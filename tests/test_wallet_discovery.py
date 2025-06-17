import pytest
import asyncio
import os
from src.wallet import MultiWallet
from src.config import settings


@pytest.mark.asyncio
async def test_wallet_discovery():
    """Test wallet discovery to find the correct account with funds."""
    
    mnemonic = os.getenv('MNEMONIC', '')
    if not mnemonic:
        pytest.skip("MNEMONIC not configured in .env")
    
    target_address = "6mEuN9tSB81o5XAnXzztG2Q9cWvMMeY51mSj4eKE5H8e"
    
    wallet = None
    try:
        print(f"\n🔍 WALLET DISCOVERY TEST")
        print(f"Target address: {target_address}")
        print(f"Expected balance: ~1.48079 SOL")
        print("=" * 60)
        
        # Create multi-wallet instance
        wallet = MultiWallet(mnemonic, settings.rpc_endpoint)
        
        # Try to find account that matches target address
        print("Searching for target address...")
        target_account = await wallet.find_account_with_funds(target_address)
        
        if target_account:
            print(f"\n🎉 FOUND TARGET ACCOUNT!")
            account_info = await wallet.get_account_info(target_account)
            
            print(f"✅ Address: {account_info['address']}")
            print(f"✅ Balance: {account_info['balance_sol']:.9f} SOL")
            print(f"✅ Derivation: {account_info['derivation_method']}")
            print(f"✅ Private key (first 5 bytes): {account_info['private_key_array']}")
            
            # Verify it's the correct address
            assert account_info['address'] == target_address, f"Found address doesn't match target"
            assert account_info['balance_sol'] > 1.0, f"Expected ~1.48 SOL, got {account_info['balance_sol']}"
            
            print(f"\n✅ SUCCESS: Found correct wallet derivation!")
            return target_account
        else:
            print(f"\n❌ Target address not found in any derivation")
            
            # Let's find any accounts with funds as fallback
            print("Searching for any accounts with funds...")
            funded_account = await wallet.find_account_with_funds()
            
            if funded_account:
                account_info = await wallet.get_account_info(funded_account)
                print(f"\n💰 FOUND FUNDED ACCOUNT (not target):")
                print(f"   Address: {account_info['address']}")
                print(f"   Balance: {account_info['balance_sol']:.9f} SOL")
                print(f"   Derivation: {account_info['derivation_method']}")
                
                pytest.fail(f"Target address {target_address} not found. Found funded account: {account_info['address']}")
            else:
                pytest.fail(f"No accounts found with funds using any derivation method")
                
    except Exception as e:
        pytest.fail(f"Wallet discovery failed: {e}")
    finally:
        if wallet:
            await wallet.close()


@pytest.mark.asyncio
async def test_derivation_methods():
    """Test different derivation methods independently."""
    
    mnemonic = os.getenv('MNEMONIC', '')
    if not mnemonic:
        pytest.skip("MNEMONIC not configured in .env")
    
    wallet = None
    try:
        print(f"\n🧪 DERIVATION METHODS TEST")
        print("=" * 50)
        
        wallet = MultiWallet(mnemonic, settings.rpc_endpoint)
        
        # Test standard derivation
        print("1. Standard derivation:")
        standard_account = wallet.derive_standard_account()
        info = await wallet.get_account_info(standard_account)
        print(f"   Address: {info['address']}")
        print(f"   Balance: {info.get('balance_sol', 0):.9f} SOL")
        
        # Test Phantom-style derivations (first 3 accounts)
        print("\n2. Phantom-style derivations:")
        phantom_accounts = wallet.derive_phantom_style_accounts(max_accounts=3)
        for account in phantom_accounts[:6]:  # Show first 6 variations
            info = await wallet.get_account_info(account)
            print(f"   {info['derivation_method']}: {info['address']}")
            if info.get('balance_sol', 0) > 0:
                print(f"   💰 Balance: {info['balance_sol']:.9f} SOL")
        
        # Test passphrase derivations
        print("\n3. Passphrase derivations:")
        passphrase_accounts = wallet.derive_with_passphrases(["", "phantom", "solana"])
        for account in passphrase_accounts:
            info = await wallet.get_account_info(account)
            print(f"   {info['derivation_method']}: {info['address']}")
            if info.get('balance_sol', 0) > 0:
                print(f"   💰 Balance: {info['balance_sol']:.9f} SOL")
        
        print(f"\n✅ Derivation methods test completed")
        
    except Exception as e:
        pytest.fail(f"Derivation methods test failed: {e}")
    finally:
        if wallet:
            await wallet.close()


if __name__ == "__main__":
    # Run tests directly
    asyncio.run(test_derivation_methods())
    asyncio.run(test_wallet_discovery())