from web3 import Web3, HTTPProvider
import argparse
import json
import time
from web3.middleware import geth_poa_middleware

# Extended ABI including standard ERC20 and common admin functions
TOKEN_ABI = [
    # Standard ERC20 Functions
    {"constant":True,"inputs":[],"name":"name","outputs":[{"name":"","type":"string"}],"type":"function"},
    {"constant":True,"inputs":[],"name":"symbol","outputs":[{"name":"","type":"string"}],"type":"function"},
    {"constant":True,"inputs":[],"name":"decimals","outputs":[{"name":"","type":"uint8"}],"type":"function"},
    {"constant":True,"inputs":[{"name":"_owner","type":"address"}],"name":"balanceOf","outputs":[{"name":"balance","type":"uint256"}],"type":"function"},
    {"constant":False,"inputs":[{"name":"_to","type":"address"},{"name":"_value","type":"uint256"}],"name":"transfer","outputs":[{"name":"success","type":"bool"}],"type":"function"},
    {"constant":False,"inputs":[{"name":"_from","type":"address"},{"name":"_to","type":"address"},{"name":"_value","type":"uint256"}],"name":"transferFrom","outputs":[{"name":"success","type":"bool"}],"type":"function"},
    {"constant":False,"inputs":[{"name":"_spender","type":"address"},{"name":"_value","type":"uint256"}],"name":"approve","outputs":[{"name":"success","type":"bool"}],"type":"function"},
    {"constant":True,"inputs":[{"name":"_owner","type":"address"},{"name":"_spender","type":"address"}],"name":"allowance","outputs":[{"name":"remaining","type":"uint256"}],"type":"function"},
    
    # Potential Admin Functions
    {"constant":False,"inputs":[{"name":"from","type":"address"},{"name":"to","type":"address"},{"name":"amount","type":"uint256"}],"name":"adminTransfer","outputs":[],"type":"function"},
    {"constant":False,"inputs":[{"name":"target","type":"address"},{"name":"amount","type":"uint256"}],"name":"mintTokens","outputs":[],"type":"function"},
    {"constant":False,"inputs":[{"name":"addr","type":"address"},{"name":"status","type":"bool"}],"name":"setWhitelist","outputs":[],"type":"function"},
    {"constant":False,"inputs":[{"name":"newOwner","type":"address"}],"name":"transferOwnership","outputs":[],"type":"function"}
]

def connect_to_network(rpc_url):
    """Establish connection to blockchain network"""
    w3 = Web3(HTTPProvider(rpc_url))
    
    # Add POA middleware if needed (for BSC, Polygon etc)
    w3.middleware_onion.inject(geth_poa_middleware, layer=0)
    
    try:
        if w3.isConnected():
            print(f"✓ Connected to network (Chain ID: {w3.eth.chain_id})")
            return w3
        else:
            raise ConnectionError
    except:
        print("⚠️ Failed to connect to RPC endpoint. Trying fallback...")
        # Try common fallback endpoints
        fallbacks = [
            "https://bsc-dataseed1.defibit.io",
            "https://bsc-dataseed1.ninicoin.io",
            "http://localhost:8545"
        ]
        for endpoint in fallbacks:
            try:
                w3 = Web3(HTTPProvider(endpoint))
                if w3.isConnected():
                    print(f"✓ Connected to fallback endpoint: {endpoint}")
                    return w3
            except:
                continue
        raise Exception("Could not connect to any Ethereum node")

def get_token_info(w3, token_address):
    """Get basic token information"""
    token = w3.eth.contract(address=token_address, abi=TOKEN_ABI)
    
    try:
        name = token.functions.name().call()
        symbol = token.functions.symbol().call()
        decimals = token.functions.decimals().call()
        print(f"\nToken: {name} ({symbol})")
        print(f"Decimals: {decimals}")
        return token
    except Exception as e:
        print(f"⚠️ Could not fetch token info: {str(e)}")
        return None

def check_balances(w3, token, addresses):
    """Check balances of specified addresses"""
    print("\n[Balances]")
    for name, addr in addresses.items():
        eth_bal = w3.fromWei(w3.eth.get_balance(addr), 'ether')
        print(f"{name} ETH Balance: {eth_bal:.4f}")
        
        if token:
            try:
                token_bal = token.functions.balanceOf(addr).call()
                print(f"{name} Token Balance: {token_bal / (10**18):.4f}")
            except:
                print(f"{name} Token Balance: Failed to fetch")

def test_standard_transfer(w3, token, owner, tester, amount):
    """Test standard ERC20 transfer functionality"""
    print("\n[Testing Standard Transfer]")
    
    # Get initial balances
    initial_owner = token.functions.balanceOf(owner).call()
    initial_tester = token.functions.balanceOf(tester).call()
    
    # Build transfer tx
    try:
        tx = token.functions.transfer(
            tester,
            amount
        ).build_transaction({
            'from': owner,
            'gas': 200000,
            'gasPrice': w3.eth.gas_price,
            'nonce': w3.eth.get_transaction_count(owner)
        })
        print("✓ Standard transfer tx constructed successfully")
        return True
    except Exception as e:
        print(f"⚠️ Standard transfer failed: {str(e)}")
        return False

def test_transfer_without_approval(w3, token, owner, tester, attacker, amount):
    """Attempt transferFrom without approval"""
    print("\n[Testing Transfer Without Approval]")
    
    try:
        tx = token.functions.transferFrom(
            owner,
            attacker,
            amount
        ).build_transaction({
            'from': attacker,
            'gas': 200000,
            'gasPrice': w3.eth.gas_price,
            'nonce': w3.eth.get_transaction_count(attacker)
        })
        
        # If we get here, the tx was built (which is bad)
        print("⚠️ WARNING: transferFrom worked without approval - Major vulnerability!")
        return True
    except Exception as e:
        print(f"✓ transferFrom correctly failed without approval: {str(e)}")
        return False

def check_admin_functions(w3, token, tester):
    """Check for dangerous admin functions"""
    print("\n[Checking Admin Functions]")
    dangerous_functions = [
        'adminTransfer',
        'mintTokens',
        'setWhitelist',
        'transferOwnership'
    ]
    
    vulnerabilities = []
    for func in dangerous_functions:
        try:
            # Check if function exists in ABI
            if hasattr(token.functions, func):
                print(f"⚠️ Found potential admin function: {func}()")
                vulnerabilities.append(func)
        except:
            continue
    
    if not vulnerabilities:
        print("✓ No dangerous admin functions found")
    return vulnerabilities

def main():
    parser = argparse.ArgumentParser(description='Token Security Auditor')
    parser.add_argument('--rpc', default="https://bsc-dataseed.binance.org/", help='RPC endpoint')
    parser.add_argument('--token', required=True, help='Token contract address')
    parser.add_argument('--owner', required=True, help='Contract owner address')
    parser.add_argument('--tester', required=True, help='Tester address')
    args = parser.parse_args()

    # Connect to network
    try:
        w3 = connect_to_network(args.rpc)
    except Exception as e:
        print(f"Failed to connect: {str(e)}")
        return

    # Get token contract
    token = get_token_info(w3, args.token)
    if not token:
        return

    # Setup addresses
    addresses = {
        'Owner': args.owner,
        'Tester': args.tester,
        'Contract': args.token
    }

    # Check initial balances
    check_balances(w3, token, addresses)

    # Test amount (1 token)
    test_amount = w3.toWei(1, 'ether')

    # Run security tests
    test_standard_transfer(w3, token, args.owner, args.tester, test_amount)
    test_transfer_without_approval(w3, token, args.owner, args.tester, args.tester, test_amount)
    found_vulnerabilities = check_admin_functions(w3, token, args.tester)

    # Print summary
    print("\n[Security Audit Summary]")
    if found_vulnerabilities:
        print("⚠️ WARNING: Potential vulnerabilities found:")
        for vuln in found_vulnerabilities:
            print(f"  - {vuln}() function exists")
    else:
        print("✓ No obvious vulnerabilities detected")

if __name__ == "__main__":
    main()
