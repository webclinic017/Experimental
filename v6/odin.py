import pandas as pd
import requests
import datetime
from datetime import date, datetime
import time
from pathlib import Path
import pandas_ta as ta
from Pytrader_API_V1_06 import *
MT = Pytrader_API()
ports = [1122, 1125, 1127]
port_dict = {1122:'FTMO', 1125:'FXCM', 1127:'GP'}

list_symbols = ['AUDCAD', 'AUDCHF', 'AUDJPY', 'AUDNZD', 'AUDUSD', 'CADCHF', 'CADJPY', 'EURAUD', 'EURCAD', 'EURCHF', 'EURGBP', 'EURJPY', 'EURUSD', 'CHFJPY', 'GBPAUD', 'GBPCAD','GBPCHF', 'GBPJPY', 'GBPUSD', 'NZDCAD', 'NZDJPY', 'NZDUSD', 'USDCAD', 'USDCHF', 'USDJPY']
symbols = {}
for pair in list_symbols:
    symbols[pair] = pair
con = MT.Connect(server='127.0.0.1', port=1125, instrument_lookup=symbols)

home = str(Path.home())
t_gram_creds = open((home+'/Desktop/t_gram.txt'), 'r')
bot_token = t_gram_creds.readline().split('\n')[0]
bot_chatID = t_gram_creds.readline()
t_gram_creds.close()

def telegram_bot_sendtext(bot_message):
    send_text = 'https://api.telegram.org/bot' + bot_token + '/sendMessage?chat_id=' + bot_chatID + '&parse_mode=Markdown&text=' + bot_message
    response = requests.get(send_text)
    return response.json()

def telegram_bot_sendfile(filename, location):
    url = "https://api.telegram.org/bot" + bot_token + "/sendDocument"
    files = {'document': open((location+filename), 'rb')}
    data = {'chat_id' : bot_chatID}
    r= requests.post(url, files=files, data=data)
    print(r.status_code, r.reason, r.content)

all_curr = pd.DataFrame(columns=['Currency', 'mon_open', 'wed_open', 'rsi'])

for currency in list_symbols:
    bars = pd.DataFrame(MT.Get_last_x_bars_from_now(instrument = currency, timeframe = MT.get_timeframe_value('D1'), nbrofbars=300))
    rsi_trend_raw = ta.rsi(bars['close'], length = 100)
    bars['rsi trend'] = rsi_trend_raw
    to_all_curr = []
    to_all_curr.append(currency)
    mon_open = bars['open'].loc[len(bars)-3]
    to_all_curr.append(mon_open)
    wed_open = bars['open'].loc[len(bars)-1]
    to_all_curr.append(wed_open)
    tues_rsi_raw = bars['rsi trend'].loc[len(bars)-2]
    if tues_rsi_raw > 50:
        to_all_curr.append('buy')
    elif tues_rsi_raw < 50:
        to_all_curr.append('sell')
    else:
        to_all_curr.append('ignore')
    all_curr.loc[len(all_curr)] = to_all_curr

action = []

action_raw = []
for line in range(0, len(all_curr)):
    if (all_curr['mon_open'].loc[line] > all_curr['wed_open'].loc[line]) and all_curr['rsi'].loc[line] == 'sell': #og = all_curr['rsi trend'].loc[line] == 'sell'
        action_raw.append('buy')
    elif (all_curr['mon_open'].loc[line] < all_curr['wed_open'].loc[line]) and all_curr['rsi'].loc[line] == 'buy':  #og = all_curr['rsi trend'].loc[line] == 'buy'
        action_raw.append('sell')
    else:
        action_raw.append('ignore')
all_curr['Action'] = action_raw

to_trade_final_raw = all_curr[all_curr['Action'] != 'ignore']
to_trade_final_raw.reset_index(inplace = True)
to_trade_final_raw.drop(columns = 'index', inplace = True)

print(to_trade_final_raw)

for currency in to_trade_final_raw['Currency']:
    dirxn = to_trade_final_raw['Action'][to_trade_final_raw['Currency'] == currency].values[0]
    coms = 'ODN_v1'
    vol = round((MT.Get_dynamic_account_info()['balance']*0.000010), 2)
    order = MT.Open_order(instrument=currency, ordertype=dirxn, volume=vol, openprice = 0.0, slippage = 10, magicnumber=41, stoploss=0, takeprofit=0, comment =coms)
    if order != -1:
        telegram_bot_sendtext('ODIN - ERROR opening order for ', currency, '-',dirxn.upper())