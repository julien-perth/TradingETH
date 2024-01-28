# Importations locales
from constantes import *
from database import Database
from mail import *

# Configurations
import os
from dotenv import load_dotenv

# Librairies
import rel
import atexit
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
import pandas as pd
import websocket, json
from binance.client import Client
from binance.exceptions import BinanceAPIException


load_dotenv()

# Définir une instance de classe 
#db = Database()

##counter##
x = 0
nb = 2

##Data info##
df = pd.DataFrame(columns=["Time", "prices", "Price_variation", "Total_Price_variation","Candle_closed","volume"])
prices = []

# Trading info##
TRADE_SYMBOL = 'ETHUSDT'

user_key = os.getenv("USER_KEY")
secret_key = os.getenv("SECRET_KEY")

client = Client(user_key, secret_key)
number_of_commas = 2

if x == 0:
    in_position = "False"
    side_in_trade = "Empty"
    price_order = 0

##trading indicator
TRADE_QUANTITY = TRADE_QUANTITY
beg_trade_quantity = BEG_TRADE_QUANTITY
share_to_add = SHARE_TO_ADD
total_quantity = beg_trade_quantity + share_to_add


agg_trade_quantity_required = AGG_TRADE_QUANTITY_REQUIRED


ratio_to_add_1 = RATIO_TO_ADD_1
ratio_to_add_2 = RATIO_TO_ADD_2
ratio_to_add_3 = RATIO_TO_ADD_3
ratio_to_add_4 = RATIO_TO_ADD_4
ratio_to_add_5 = RATIO_TO_ADD_5
flag = 0

 
sum_of_variation = SUM_OF_VARIATION
point_before_profit = POINT_BEFORE_PROFIT
point_before_loss = POINT_BEFORE_LOSS

buy_take_loss = 0
buy_take_profit = 0
sell_take_profit = 0
sell_take_loss = 0
new_total_quantity = 0
dollar_before_loss = 0 
dollar_before_profit = 0
beg_share_to_add = 0.35


msg_envoye = False


def on_open(ws):
    print('opened connection')
    msg = "Nous sommes connectés !"
    send_mail( os.getenv("SOURCE_ADDRESS"), os.getenv("DESTINATION_ADDRESS"), msg, os.getenv("PASSWORD"))

# On doit personnalisé le comportement de l'application au cas ou le serveur ferme la connexion, le run_forever ne se relance pas 
# automatiquement si la connexion est fermée par le serveur
def on_close(ws, close_status_code):
    if (close_status_code != 1000 or close_status_code != 1001):
        # Set dispatcher to automatic reconnection
        ws.run_forever(dispatcher=rel)
        rel.dispatch()
    else:
        msg = f"Nous avons une erreur de fermeture : {close_status_code}"
        send_mail( os.getenv("SOURCE_ADDRESS"), os.getenv("DESTINATION_ADDRESS"), msg, os.getenv("PASSWORD"))

def on_error(ws):
    try:
        ws.run_forever(dispatcher=rel)
        rel.dispatch()
    except BinanceAPIException as e:
        msg = f"Nous avons une erreur: {e.message} avec un code de status: {e.status_code} et un code de status Binance : {e.code}"
        send_mail( os.getenv("SOURCE_ADDRESS"), os.getenv("DESTINATION_ADDRESS"), msg, os.getenv("PASSWORD"))
        print(e.message)
        # response status code
        print(e.status_code)
        # Binance error code
        print(e.code)

def on_message(ws, message):
    global df, prices, in_position, x, nb, client, side_in_trade, price_order, TRADE_SYMBOL, TRADE_QUANTITY,beg_trade_quantity, total_quantity
    global buy_take_loss, buy_take_profit, sell_take_profit, sell_take_loss,agg_trade_quantity_required,dollar_before_loss,dollar_before_profit, msg_envoye
    global point_before_profit,point_before_loss,flag,new_total_quantity,ratio_to_add_1,ratio_to_add_2,ratio_to_add_3,ratio_to_add_4,ratio_to_add_5,y,share_to_add,beg_share_to_add


    json_message = json.loads(message)

    candle = json_message['k']

    prices.append(float(candle["c"]))
    y = len(prices)

    #print(candle)
    if candle["x"] == True :
        df.loc[x, "Time"] = datetime.now()
        df.loc[x, "prices"] = float(candle["c"])
        df.loc[x, "volume"] = float(candle["v"])
        df.loc[x, "candle_closed"] = candle["x"]

    x = (len(df))
    print(x)

    if x >2:
        df.loc[x-1, "Price_variation"] =  df.loc[x-1, "prices"]/df.loc[x-2, "prices"]-1
    if x > 3:
        df.loc[x-1, "Total_Price_variation"] =  df.iloc[-nb:, df.columns.get_loc("Price_variation")].sum()
    
    if x > 61 :
        df.loc[x-1, "vol_60"] =  df.iloc[x-60:x, df.columns.get_loc('prices')].std() ** 2
    
    if (x % 60 != 0):
        msg_envoye = False

    if (x % 60 == 0) and (msg_envoye == False) :
        msg = f"Data est peuplé avec {x} données aujourd'hui. flag {flag} last price {df.loc[x-1, 'prices']}"
        send_mail( os.getenv("SOURCE_ADDRESS"), os.getenv("DESTINATION_ADDRESS"), msg, os.getenv("PASSWORD"))
        msg_envoye = True
    
    #if candle["x"] == True:
        #db.insert_data(datetime.now(),candle["c"], candle["v"], candle["x"], df.iloc[x-1, df.columns.get_loc("Price_variation")], df.iloc[x-1, df.columns.get_loc("Total_Price_variation")])

    #### transaction : sell
    if in_position == "True" and side_in_trade == "Sell":
        print("je suis short")
        if df.loc[x-1, "prices"] <= sell_take_profit or df.loc[x-1, "prices"] >= sell_take_loss:
            order_succeeded = order("BUY", TRADE_QUANTITY, TRADE_SYMBOL, prices[y- 1])
            if order_succeeded["orderId"]>0 :
                side_in_trade = "empty"
                in_position = "False"
                price_order = 0
                sell_take_profit = 0
                sell_take_loss = 0
                flag = 0
                TRADE_QUANTITY = beg_trade_quantity
                new_total_quantity = 0
                dollar_before_loss = 0
                dollar_before_profit = 0
                
        else : 
            if (flag == 4) and (df.loc[x-1, "prices"] <= price_order - dollar_before_profit * ratio_to_add_5):
                sell_take_loss = price_order - dollar_before_profit * ratio_to_add_4
                flag = 5

            if (flag == 3) and (df.loc[x-1, "prices"]  <= price_order - dollar_before_profit * ratio_to_add_4):
                sell_take_loss = price_order - dollar_before_profit * ratio_to_add_3
                flag = 4

            if (flag == 2) and (df.loc[x-1, "prices"] <= price_order - dollar_before_profit * ratio_to_add_3) and (TRADE_QUANTITY != new_total_quantity):
                
                #order_succeeded = order("SELL", share_to_add,TRADE_SYMBOL, prices[y- 1])
                #if order_succeeded["orderId"]>0:
                    #price_order = (price_order * TRADE_QUANTITY / (TRADE_QUANTITY+share_to_add)) + (prices[y- 1] * share_to_add /(TRADE_QUANTITY+share_to_add))
                    #new_total_quantity = (TRADE_QUANTITY+share_to_add)
                    #TRADE_QUANTITY = new_total_quantity

                sell_take_loss = price_order - dollar_before_profit * ratio_to_add_2
                flag= 3

            if (flag == 1) and (df.loc[x-1, "prices"] <= price_order - dollar_before_profit * ratio_to_add_2):
                sell_take_loss= price_order - dollar_before_profit * ratio_to_add_1
                flag= 2

            if (flag == 0) and (df.loc[x-1, "prices"]<= price_order - dollar_before_profit * ratio_to_add_1) and (TRADE_QUANTITY !=total_quantity):
                    
                if df.iloc[x-1, df.columns.get_loc("vol_60")]>150:
                    share_to_add = share_to_add*2
                
                order_succeeded = order("SELL", share_to_add,TRADE_SYMBOL, prices[y- 1] )            
                if order_succeeded["orderId"]>0:
                    price_order = (price_order * TRADE_QUANTITY / (TRADE_QUANTITY+share_to_add)) + (prices[y- 1] * share_to_add / (TRADE_QUANTITY+share_to_add))

                    total_quantity = (TRADE_QUANTITY+share_to_add)
                    TRADE_QUANTITY = total_quantity
                    sell_take_loss = price_order
                    flag= 1
                    share_to_add = beg_share_to_add

    #### transaction : buy
    if in_position == "True" and side_in_trade == "Buy":
        print("je suis long")
        if df.loc[x-1, "prices"] <= buy_take_loss or df.loc[x-1, "prices"] >= buy_take_profit:
            order_succeeded = order("SELL", TRADE_QUANTITY, TRADE_SYMBOL, prices[y- 1])
            if order_succeeded["orderId"]>0:
                side_in_trade = "empty"
                in_position = "False"
                price_order = 0
                sell_take_profit = 0
                sell_take_loss = 0
                flag = 0
                TRADE_QUANTITY = beg_trade_quantity
                new_total_quantity = 0
                dollar_before_loss = 0
                dollar_before_profit = 0
               
        else :
           
            if ((df.loc[x-1, "prices"] >= price_order + dollar_before_profit * ratio_to_add_5) and (flag == 4)):

                buy_take_loss = price_order + dollar_before_profit * ratio_to_add_4
                flag = 5

            if ((df.loc[x-1, "prices"] >= price_order + dollar_before_profit * ratio_to_add_4) and (flag == 3)):

                buy_take_loss = price_order + dollar_before_profit * ratio_to_add_3
                flag = 4

            if ((df.loc[x-1, "prices"] >= price_order + dollar_before_profit * ratio_to_add_3) and (flag == 2) and (TRADE_QUANTITY != new_total_quantity)):

                #order_succeeded = order("BUY", share_to_add,TRADE_SYMBOL, prices[y- 1])
                #if order_succeeded["orderId"]>0:
                    #price_order = (price_order * TRADE_QUANTITY / (TRADE_QUANTITY+share_to_add)) + (prices[y- 1] * share_to_add /(TRADE_QUANTITY+share_to_add))
                    #new_total_quantity = (TRADE_QUANTITY+share_to_add)
                    #TRADE_QUANTITY = new_total_quantity
                    
                 buy_take_loss = price_order - dollar_before_profit * ratio_to_add_2
                 flag= 3

            if ((df.loc[x-1, "prices"]  >= price_order + dollar_before_profit * ratio_to_add_2) and (flag == 1)):

                buy_take_loss = price_order + dollar_before_profit * ratio_to_add_1
                flag = 2

            if((TRADE_QUANTITY != total_quantity) and (df.loc[x-1, "prices"] >= price_order + dollar_before_profit*ratio_to_add_1) and (flag ==0)) :

                if df.iloc[x-1, df.columns.get_loc("vol_60")]>150:
                    share_to_add = share_to_add*2
                    
                order_succeeded = order("BUY", share_to_add,TRADE_SYMBOL, prices[y- 1])
                if order_succeeded["orderId"]>0:
                    price_order = (price_order*TRADE_QUANTITY/(TRADE_QUANTITY+share_to_add)) + (prices[y- 1]*share_to_add/(TRADE_QUANTITY+share_to_add))
                    
                    total_quantity = (TRADE_QUANTITY+share_to_add)
                    TRADE_QUANTITY = total_quantity
                    sell_take_loss = price_order
                    flag= 1
                    share_to_add = beg_share_to_add
    if x > 61 :
        print("je regarde")
        print(df.loc[x-2, "Total_Price_variation"])
        print(df.iloc[-nb-1:-nb+1, df.columns.get_loc("volume")].sum() > agg_trade_quantity_required)
    
        if (in_position == "False") and (df.iloc[-nb-1:-nb+1, df.columns.get_loc("volume")].sum() > agg_trade_quantity_required) and (df.iloc[x-1, df.columns.get_loc("vol_60")]>150):
            if (df.loc[x-2, "Total_Price_variation"] <= -sum_of_variation) :

                if df.iloc[x-1, df.columns.get_loc("vol_60")]>150:
                        TRADE_QUANTITY = TRADE_QUANTITY*2

                order_succeeded = order("SELL", TRADE_QUANTITY, TRADE_SYMBOL, prices[y- 1])
                if order_succeeded["orderId"]>0:
                    in_position = "True"
                    side_in_trade = "Sell"

                    price_order = float(prices[y- 1] )
                    dollar_before_profit = point_before_profit * price_order
                    dollar_before_loss = point_before_loss * price_order

                    sell_take_profit = round((float(price_order) - dollar_before_profit), number_of_commas)
                    sell_take_loss = round((float(price_order) + dollar_before_loss), number_of_commas)

                    msg = f"Une transaction a été effectuée. In position:{in_position}, Side in trade :{side_in_trade}, Price order: {price_order}, Dollar before profit: {dollar_before_profit}, Dollar before loss: {dollar_before_loss}, Trade quantity: {TRADE_QUANTITY}, Sell take profit: {sell_take_profit}, Sell take loss: {sell_take_loss}"
                    send_mail( os.getenv("SOURCE_ADDRESS"), os.getenv("DESTINATION_ADDRESS"), msg, os.getenv("PASSWORD"))

            elif (df.loc[x-2, "Total_Price_variation"] >= sum_of_variation) and (in_position=="False") :

                if df.iloc[x-1, df.columns.get_loc("vol_60")]>150:
                        TRADE_QUANTITY = TRADE_QUANTITY*2

                order_succeeded = order("BUY", TRADE_QUANTITY, TRADE_SYMBOL, prices[y- 1])
                if order_succeeded["orderId"]>0:
                    in_position = "True"
                    side_in_trade = "Buy"

                    price_order = float(prices[y- 1])
                    dollar_before_profit = point_before_profit * price_order
                    dollar_before_loss = point_before_loss * price_order
                    buy_take_profit = round((float(price_order) + dollar_before_profit), number_of_commas)
                    buy_take_loss = round((float(price_order) - dollar_before_loss), number_of_commas)

                    msg = f"Une transaction a été effectuée. In position:{in_position}, Side in trade :{side_in_trade}, Price order: {price_order}, Dollar before profit: {dollar_before_profit}, Dollar before loss: {dollar_before_loss}, Trade quantity: {TRADE_QUANTITY}, Buy take profit: {buy_take_profit}, Buy take loss: {buy_take_loss}"
                    send_mail( os.getenv("SOURCE_ADDRESS"), os.getenv("DESTINATION_ADDRESS"), msg, os.getenv("PASSWORD"))

    # Dès que ça dépasse les 1000 on ne garde que les 100 derniers
    if (x > 1000):
        df = df.iloc[len(df)-100:len(df),:].reset_index(drop=True)
        x = (len(df))
        prices = prices[y-100:y].reset_index(drop=True)
        y = len(prices)


def order(side, quantity, symbol, current_price):
    global price_order, client, number_of_commas

    order_market = client.futures_create_order(
    symbol=symbol,
    side=side,
    type="MARKET",
    quantity=quantity,
    isolated=True)

    return order_market


SOCKET = 'wss://fstream.binance.com/ws/ethusdt_perpetual@continuousKline_1m'
ws = websocket.WebSocketApp(SOCKET, on_open=on_open, on_close=on_close, on_message=on_message)
ws.run_forever(dispatcher=rel)
rel.dispatch()
