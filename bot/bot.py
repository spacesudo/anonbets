from telebot.async_telebot import AsyncTeleBot
import asyncio
from telebot.util import antiflood, extract_arguments, quick_markup
from database import User, Bets
import funcs
import os
from telebot import types
from dotenv import load_dotenv
from telebot import asyncio_filters
from telebot.asyncio_storage import StateMemoryStorage
from tg_states import (
    BroadcastState, ImportWalletState
)


POOL_ADDRESS = 'XRjzqU3rymHiwtDNPujLpGFVGpSFYPmAUGm3NJG2JN5'

load_dotenv()

TOKEN = os.getenv('TOKEN')

POOL_KEY = os.getenv('POOL_KEY')

print(type(POOL_KEY))

bot = AsyncTeleBot(TOKEN, parse_mode='Markdown', disable_web_page_preview=True, state_storage= StateMemoryStorage())

users = {}
freeid = None

db_bet = Bets()
db_bet.setup()

db_user = User('users.db')
db_user.setup()

CHANNEL_USERNAME = '@anonbetsite'

async def check_if_user_is_member(user_id):
    try:
        member_status = await bot.get_chat_member(CHANNEL_USERNAME, user_id)
        if member_status.status in ['member', 'administrator', 'creator']:
            return True
        else:
            return False
    except Exception as e:
        print(f"Error: {e}")
        return False

def coin_toss():
    import random
    
    return random.choice(['Head', 'Tail'])


def rock_game(message, userid1, userid2):
    pass


async def make_bet(message, userid1, userid2):
    wallet1 = db_user.get_wallet(userid1)
    wallet2 = db_user.get_wallet(userid2)
    print(wallet1, wallet2)
    
    user1bet = db_bet.get_last_selection(userid1)
    user2bet = db_bet.get_last_selection(userid2)
    
    choice = coin_toss()
    await bot.send_message(userid1, f"Bet Choice for this round is {choice}")
    await bot.send_message(userid2, f"Bet Choice for this round is {choice}")
    
    if user1bet == user2bet:
        await bot.send_message(userid1, "You both made the same choice...\nBet has been cancelled")
        await bot.send_message(userid2, "You both made the same choice...\nBet has been cancelled")
        db_bet.update_result(userid1, 'Draw')
        db_bet.update_result(userid2, 'Draw')
        amount = funcs.sol_to_lamports(0.1)
        await funcs.send_transaction_with_priority_fee(POOL_KEY, wallet1, amount)
        await funcs.send_transaction_with_priority_fee(POOL_KEY, wallet2, amount)
        
    elif user1bet == choice:
        await bot.send_message(userid1, "You won  the bet!!!")
        await bot.send_message(userid2, "You lost this bet round...")
        db_bet.update_result(userid1, 'Won')
        db_bet.update_result(userid2, 'Lost')
        amount = funcs.sol_to_lamports(0.16)
        await funcs.send_transaction_with_priority_fee(POOL_KEY, wallet1, amount)
    
    elif user2bet == choice:
        await bot.send_message(userid2, "You won  the bet!!!")
        await bot.send_message(userid1, "You lost this bet round...")
        db_bet.update_result(userid1, 'Lost')
        db_bet.update_result(userid2, 'Won')
        amount = funcs.sol_to_lamports(0.16)
        await funcs.send_transaction_with_priority_fee(POOL_KEY, wallet2, amount)
    
    elif user2bet == choice and user1bet == choice:
        await bot.send_message(userid1, "You both made the same choice...\nBet has been cancelled")
        await bot.send_message(userid2, "You both made the same choice...\nBet has been cancelled")
        db_bet.update_result(userid1, 'Draw')
        db_bet.update_result(userid2, 'Draw')
        amount = funcs.sol_to_lamports(0.1)
        await funcs.send_transaction_with_priority_fee(POOL_KEY, wallet1, amount)
        await funcs.send_transaction_with_priority_fee(POOL_KEY, wallet2, amount)
        
    await stop(message)

async def bot_info_():
    return await bot.get_me()


@bot.message_handler(commands=['help'])
async def help(message):
    owner = message.chat.id
    if await check_if_user_is_member(owner):
        await bot.send_message(owner, "update help!!!")
    else:
        await bot.send_message(owner, "You need to join @AnonBetsite to be able to use bot")
          


@bot.message_handler(commands=['broadcast'])
async def broadcast(message):
    print(message.from_user.id)
    messager = message.chat.id
    if str(messager) == "7034272819" or str(messager) == "6219754372":
        await bot.set_state(message.from_user.id, BroadcastState.msg, message.chat.id)

        send = await bot.send_message(message.chat.id,"Enter message to broadcast")
        print("ok")
        
    else:
        await bot.reply_to(message, "You're not allowed to use this command")
        
        
@bot.message_handler(state = BroadcastState.msg)     
async def sendall(message):
    print("ok")
    users = db_user.get_users()
    print(message.text)
    for chatid in users:
        try:
            msg = await antiflood(bot.send_message, chatid, message.text)
        except Exception as e:
            print(e)
        
    await bot.send_message(message.chat.id, "done")
    await bot.delete_state(message.from_user.id, message.chat.id)
    

@bot.message_handler(commands=['userno'])
async def userno(message):
    print(message.from_user.id)
    messager = message.chat.id
    if str(messager) == "7034272819" or str(messager) == "6219754372":
        x = db_user.get_users()
        await bot.reply_to(message,f"Total bot users: {len(x)}")
    else:
        await bot.reply_to(message, "admin command")
        
        
@bot.message_handler(commands=['start'])
async def start(message):
    try:
        owner = message.chat.id
        if await check_if_user_is_member(owner):
            pk= funcs.generate_wallet() if db_user.get_mnemonics(owner) == None else db_user.get_mnemonics(owner)
            wallet = funcs.get_wallet(pk)
            msg = f"""Welcome to AnonBet Bot
            
Bet and earn anonymously with other bot members 

Wallet address 

Bal: {funcs.get_sol_bal(wallet)}

`{wallet}` (tap to copy)
has been generated for you.

You can view your primary from the pk button below  

Use /help command to learn more about bot 

use /find command to search for a new bet session
    """
            markup = quick_markup({
                'Show PK' : {'callback_data': 'show_pk'},
                'Import Wallet' : {'callback_data': 'import'},
                'Start Bet': {'callback_data' : 'find'}
            })
            db_user.add_user(owner, pk, wallet)
            await bot.send_message(owner, msg, reply_markup=markup)
        else:
            await bot.send_message(owner, "You need to join @AnonBetsite to be able to use bot")
            
    except Exception as e:
        print(e)
        


async def show_pk(message):
    owner = message.chat.id
    if await check_if_user_is_member(owner):
        pk = db_user.get_mnemonics(owner)
        wallet = db_user.get_wallet(owner)
        msg = f"Your pk for `{wallet}` \n\n`{pk}` (tap to copy)\nDo not share your PK with anyone!!! \n\nMessage will automatically be deleted"
        b = await bot.send_message(owner, msg)
        await asyncio.sleep(20)
        await bot.delete_message(owner, b.message_id)
    else:
        await bot.send_message(owner, "You need to join @AnonBetsite to be able to use bot")


@bot.message_handler(commands=['import'])
async def impwal(message):
    owner = message.chat.id
    await bot.set_state(owner, ImportWalletState.wallet, owner)
    await bot.send_message(owner, "Enter your primary key")


@bot.message_handler(state = ImportWalletState.wallet)
async def import_wallet(message):
    owner = message.chat.id
    if await check_if_user_is_member(owner):
        try:
            new_pk = message.text
            print(new_pk)
            wallet = funcs.get_wallet(new_pk)
            db_user.update_mnemonics(new_pk, owner)
            db_user.update_wallet(wallet, owner)
            await bot.send_message(owner, "wallet updated")
            await start(message)
            await bot.delete_state(owner)
        except Exception as e:
            print(e)
            await bot.send_message(owner, "Failed to import wallet")
    else:
        await bot.send_message(owner, "You need to join @AnonBetsite to be able to use bot")


@bot.message_handler(commands=['allbet'])
async def all_bet(message):
    owner = message.chat.id
    all = db_bet.get_all(owner)
    msg = f"Bet History\n\n"
    for i in all:
        msg += f"Date: {i[2]}| Opt. {i[1]}| Res. {i[3]}\n"
        
    await bot.send_message(owner, msg)


@bot.message_handler(commands=['find'])
async def find(message: types.Message):
    global freeid
    try:
        owner = message.chat.id
        wallet = db_user.get_wallet(owner)
        bal = funcs.get_sol_bal(wallet)
        print(bal)
        
        if bal > 0.11:
            if message.chat.id not in users:
                await bot.send_message(message.chat.id, 'Search started...')

                if freeid is None:
                    freeid = message.chat.id
                else:
                    mnemonics1 = db_user.get_mnemonics(owner)
                    mnemonics2 = db_user.get_mnemonics(freeid)
                    amount = funcs.sol_to_lamports(0.1)
                    await funcs.send_transaction_with_priority_fee(mnemonics1, POOL_ADDRESS, amount)
                    #await asyncio.sleep(10)
                    await funcs.send_transaction_with_priority_fee(mnemonics2, POOL_ADDRESS, amount)
                    
                    await bot.send_message(message.chat.id, 'Found a new User!')
                    await bot.send_message(freeid, 'Found a new User!')
                    await bot.send_message(message.chat.id, 'New user Found!!!\nYou have 5 minutes to chat and bet against each other\nFor fairplay, each betting session cost 0.1 sol.')
                    await bot.send_message(freeid, 'New user Found!!!\nYou have 5 minutes to chat and bet against each other\nFor fairplay, each betting session cost 0.1 sol.')
                    msg = "Select either Head or Tails and wait for 2 min for the system to decide outcome..."
                    markup = quick_markup({
                        'Head' : {'callback_data' : 'head'},
                        'Tail': {'callback_data' : 'tail'}
                    })
                    await bot.send_message(message.chat.id, msg, reply_markup=markup)
                    await bot.send_message(freeid, msg, reply_markup=markup)
                    users[freeid] = message.chat.id
                    users[message.chat.id] = freeid
                    freeid = None
            else:
                await bot.send_message(message.chat.id, 'You are already in a chat')
                
        else:
            await bot.send_message(owner, "Balance too low to start a new bet fund your wallet and try again...")
    except Exception as e:
        print(e)
    
    
@bot.message_handler(commands=['stop'])
async def stop(message: types.Message):
    global freeid

    if message.chat.id in users:
        await bot.send_message(message.chat.id, 'Stopping...')
        await bot.send_message(users[message.chat.id], 'Your opponent is closing the chat...')

        del users[users[message.chat.id]]
        del users[message.chat.id]
        
    elif message.chat.id == freeid:
        await bot.send_message(message.chat.id, 'Stopping...')
        freeid = None

    else:
        await bot.send_message(message.chat.id, 'You are not in a chat!')
        
        
@bot.message_handler(content_types=['animation', 'audio', 'contact', 'dice', 'document', 'location', 'photo', 'poll', 'sticker', 'text', 'venue', 'video', 'video_note', 'voice'])
async def chatting(message: types.Message):
    if message.chat.id in users:
        await bot.copy_message(users[message.chat.id], users[users[message.chat.id]], message.id)
        await asyncio.sleep(20)
        await make_bet(message, users[message.chat.id], users[users[message.chat.id]])
        
    else:
        await bot.send_message(message.chat.id, 'No one can hear you...')
        
@bot.callback_query_handler(func= lambda call: True)
async def callback(call):
    owner = call.message.chat.id
    if call.data == "show_pk":
        await show_pk(call.message)
        
    elif call.data == 'import':
        await impwal(call.message)  
        
    elif call.data == 'find':
        await find(call.message)   
        
    elif call.data == 'head':
        db_bet.add(owner, 'Head')
        await bot.send_message(owner, f"you have made your choice!\nBet round will be decided in the next 3 min...")
    
    elif call.data == 'tail':
        db_bet.add(owner, 'Tail')
        await bot.send_message(owner, f"you have made your choice!\nBet round will be decided in the next 3 min...")
     
            
bot.add_custom_filter(asyncio_filters.StateFilter(bot))

        
asyncio.run(bot.polling())
