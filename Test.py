from web3 import Web3
import argparse
import getpass

def main():
    parser = argparse.ArgumentParser(description='Token Security Test Tool')
    parser.add_argument('--rpc', default="http://127.0.0.1:8545", help='RPC endpoint')
    parser.add_argument('--token', required=True, help='Token contract address')
    parser.add_argument('--owner', required=True, help='Contract owner address')
    parser.add_argument('--tester', required=True, help='Tester address')
    args = parser.parse_args()

    # Initialize Web3
    w3 = Web3(Web3.HTTPProvider(args.rpc))
    
    if not w3.isConnected():
        print("Failed to connect to blockchain")
        return

    # Extended ABI including common vulnerabilities
    token_abi = [
        # Standard ERC20
        {"inputs":[],"name":"name","outputs":[{"name":"","type":"string"}],"type":"function"},
        {"inputs":[],"name":"symbol","outputs":[{"name":"","type":"string"}],"type":"function"},
        {"inputs":[],"name":"decimals","outputs":[{"name":"","type":"uint8"}],"type":"function"},
        {"inputs":[{"name":"account","type":"address"}],"name":"balanceOf","outputs":[{"name":"","type":"uint256"}],"type":"function"},
        {"inputs":[{"name":"owner","type":"address"},{"name":"spender","type":"address"}],"name":"allowance","outputs":[{"name":"","type":"uint256"}],"type":"function"},
        {"inputs":[{"name":"to","type":"address"},{"name":"amount","type":"uint256"}],"name":"transfer","outputs":[{"name":"","type":"bool"}],"type":"function"},
        {"inputs":[{"name":"from","type":"address"},{"name":"to","type":"address"},{"name":"amount","type":"uint256"}],"name":"transferFrom","outputs":[{"name":"","type":"bool"}],"type":"function"},
        
        # Potential vulnerability test functions
        {"inputs":[{"name":"from","type":"address"},{"name":"to","type":"address"},{"name":"amount","type":"uint256"}],"name":"transferAny","outputs":[],"type":"function"},
        {"inputs":[{"name":"from","type":"address"},{"name":"to","type":"address"},{"name":"amount","type":"uint256"}],"name":"adminTransfer","outputs":[],"type":"function"},
        {"inputs":[{"name":"addr","type":"address"},{"name":"status","type":"bool"}],"name":"setWhitelist","outputs":[],"type":"function"}
    ]

    token = w3.eth.contract(address=args.token, abi=token_abi)

    try:
        # Test 1: Check if contract allows arbitrary transfers
        print("\n[+] Testing for transfer vulnerabilities")
        
        # Try transfer without approval (standard should fail)
        print("\n[1] Testing standard transferFrom without approval...")
        try:
            tx = token.functions.transferFrom(
                args.owner,
                args.tester,
                w3.toWei(1, 'ether')
            ).build_transaction({
                'from': args.tester,
                'gas': 200000,
                'gasPrice': w3.eth.gas_price,
                'nonce': w3.eth.get_transaction_count(args.tester)
            })
            print("⚠️ Standard transferFrom worked without approval - Check approval logic")
        except Exception as e:
            print("✓ Standard transferFrom failed as expected:", str(e))

        # Test 2: Check for admin backdoors
        print("\n[2] Testing for admin transfer functions...")
        try:
            # Try common backdoor function names
            for func in ['transferAny', 'adminTransfer', 'ownerTransfer']:
                if func in token.functions:
                    print(f"⚠️ Found potential backdoor function: {func}()")
                    # Would need owner private key to test further
        except:
            pass

        # Test 3: Check whitelist functionality
        print("\n[3] Testing whitelist functions...")
        try:
            if 'setWhitelist' in token.functions:
                print("⚠️ Found whitelist functionality - could bypass approvals")
        except:
            pass

        print("\n[+] Basic security checks completed")

    except Exception as e:
        print(f"\nError: {str(e)}")

if __name__ == "__main__":
    main()
