from solders.keypair import Keypair
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solana.rpc.api import Client
from solders.system_program import TransferParams, transfer
from solana.transaction import Transaction
import sys
import os
import json
import asyncio
import base58
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solders.system_program import TransferParams, transfer
from solders.instruction import Instruction
from solders.transaction import Transaction
from solders.compute_budget import set_compute_unit_limit, set_compute_unit_price
from solders.transaction_status import TransactionConfirmationStatus
from solders.signature import Signature
from solana.rpc.async_api import AsyncClient
from solana.exceptions import SolanaRpcException

from jito import JitoJsonRpcSDK

def generate_wallet():
    keypair = Keypair()
    return str(keypair)

def get_wallet(pk):
    keypair = Keypair.from_base58_string(pk)
    return str(keypair.pubkey())

async def send_transaction_with_priority_fee(sender_, receiver_, amount, jito_tip_amount = 1_000_000, priority_fee = 1_000_000, compute_unit_limit=100_000):
    try:
        
        solana_client = AsyncClient("https://api.mainnet-beta.solana.com")
        sdk = JitoJsonRpcSDK(url="https://mainnet.block-engine.jito.wtf/api/v1")
        
        sender = Keypair.from_base58_string(sender_)
        receiver = Pubkey.from_string(receiver_)

        recent_blockhash = await solana_client.get_latest_blockhash()

        transfer_ix = transfer(TransferParams(from_pubkey=sender.pubkey(), to_pubkey=receiver, lamports=amount))

        jito_tip_account = Pubkey.from_string(sdk.get_random_tip_account())
        jito_tip_ix = transfer(TransferParams(from_pubkey=sender.pubkey(), to_pubkey=jito_tip_account, lamports=jito_tip_amount))

        priority_fee_ix = set_compute_unit_price(priority_fee)

        transaction = Transaction.new_signed_with_payer(
            [priority_fee_ix, transfer_ix, jito_tip_ix],
            sender.pubkey(),
            [sender],
            recent_blockhash.value.blockhash
        )

        serialized_transaction = base58.b58encode(bytes(transaction)).decode('ascii')
        
        response = sdk.send_txn(params=serialized_transaction, bundleOnly=False)

        if response['success']:
            signature_str = response['data']['result']            
            await solana_client.close()
            
            return signature_str
        
        else:
            print(f"Error sending transaction: {response['error']}")
            return None

    except Exception as e:
        print(f"Exception occurred: {str(e)}")
        return None
    
    
    
def sol_to_lamports(sol: float):
    LAMPORTS_PER_SOL = 1_000_000_000
    return int(sol * LAMPORTS_PER_SOL)



def bot_fees(amount):
    return amount * 0.1

def get_sol_bal(wallet_addr: str):
    client = Client("https://api.mainnet-beta.solana.com")
    
    pub = Pubkey.from_string(wallet_addr)
    
    res = client.get_balance(pub)
    
    return res.value / 1000000000

async def main():
        
    sender = ''

    receiver = ''

    priority_fee = sol_to_lamports(0.001) 
    amount = sol_to_lamports(0.1) 
    jito_tip_amount = sol_to_lamports(0.001) 

    signature = await send_transaction_with_priority_fee(sender, receiver, amount, jito_tip_amount, priority_fee)
    
    if signature:
        print(f"Transaction process completed. Signature: {signature}")

if __name__ == '__main__':
    asyncio.run(main())
    # print(sol_to_lamports(0.001))