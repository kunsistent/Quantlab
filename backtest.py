##################    RUN STRATEGY     ##################
def run_strat(data, entry_conditions, TP_conditions, SL_conditions):
    if (data['signal'].iloc[-2] > 0): # condition for sell
        data = sell(data, TP_conditions, SL_conditions)
    elif data['signal'].iloc[-1] == 0: # condition for buy
        data = buy(data, entry_conditions)
    return data

##################    BUY CONDITIONS    ##################
def buy(data, entry_conditions):
    
    # buy conditions
#     if ((data['9EMA'].iloc[-2] < data.vwap.iloc[-2]) & 
#         (data['9EMA'].iloc[-1] > data.vwap.iloc[-1])
#         ):
    if entry_conditions(data):
        data['signal'].iloc[-1] = 1 
        data['SL'].iloc[-1] = data['close'].iloc[-1] - 10    
        data['TP'].iloc[-1] = data['close'].iloc[-1] + 15
        data['transact_time'].iloc[-1] = data.index[-1]
        data['transact_price'].iloc[-1] = data['close'].iloc[-1]
        data['squareoff_criteria'].iloc[-1] = 'BUY' 
        data['margin_used'].iloc[-1] = 0 # will be updated later
        data['margin_available'].iloc[-1] = 0 # will be updated later
        data['aum'].iloc[-1] = 0 # will be updated later
        print('\n BUY', '\t time: ', data.index[-1], '\t Close: ', data.close.iloc[-1], \
              '\t iSL: ', data['SL'].iloc[-1], '\t iTP: ', data['TP'].iloc[-1])
        # place buy order    

    # if buy conditions do not satisfy
    else:
        data['signal'].iloc[-1] = data['signal'].iloc[-2]
        data['transact_time'].iloc[-1] = 0
        data['transact_price'].iloc[-1] = 0
        data['squareoff_criteria'].iloc[-1] = 0
        data['margin_used'] = 0 # will be updated later
        data['margin_available'] = 0 # will be updated later
        data['aum'].iloc[-1] = 0 # will be updated later
        data['SL'].iloc[-1] = 0
        data['TP'].iloc[-1] = 0
    
    return data

##################    SELL CONDITIONS    ##################
def sell(data, TP_conditions, SL_conditions):
    # update signal, SL & TP for last instant
    data['signal'].iloc[-1] = data['signal'].iloc[-2]
    data['SL'].iloc[-1] = data['SL'].iloc[-2]
    data['TP'].iloc[-1] = data['TP'].iloc[-2]
    
    # SL - Sell condition
    if SL_conditions(data): 
        data['signal'].iloc[-1] = 0 # order quantity becomes signal - signal.shift(1) i.e. -1 (sell)
        data['transact_time'].iloc[-1] = data.index[-1]
        data['transact_price'].iloc[-1] = data[['close', 'SL']].max(axis = 1).iloc[-1]
        data['squareoff_criteria'].iloc[-1] = 'SL'
        data['margin_used'] = 0 # will be updated later
        data['margin_available'] = 0 # will be updated later
        data['aum'].iloc[-1] = 0 # will be updated later
        data['SL'].iloc[-1] = 0
        data['TP'].iloc[-1] = 0

        print('\n SELL', '\t time: ', data.index[-1], '\t Close: ', data.close.iloc[-1], \
              '\t SellPrice: ', data['transact_price'].iloc[-1]) 
        # place sell order

    # TP - sell condition
    elif TP_conditions(data): 
        data['signal'].iloc[-1] = 0 # order quantity becomes signal - signal.shift(1) i.e. -1 (sell)
        data['transact_time'].iloc[-1] = data.index[-1]
        data['transact_price'].iloc[-1] = data[['close', 'TP']].min(axis = 1).iloc[-1]
        data['squareoff_criteria'].iloc[-1] = 'TP'
        data['margin_used'] = 0 # will be updated later
        data['margin_available'] = 0 # will be updated later
        data['aum'].iloc[-1] = 0 # will be updated later
        data['SL'].iloc[-1] = 0
        data['TP'].iloc[-1] = 0

        print('\n SELL', '\t time: ', data.index[-1], '\t Close: ', data.close.iloc[-1], \
              '\t SellPrice: ', data['transact_price'].iloc[-1]) 
        # place sell order

    else:
        # if both SL & TP conditions do not satisfy - update data columns
        data['transact_time'].iloc[-1] = data['transact_time'].iloc[-2]
        data['transact_price'].iloc[-1] = data['transact_price'].iloc[-2]
        data['squareoff_criteria'].iloc[-1] = 0
        data['margin_used'] = 0 # will be updated later
        data['margin_available'] = 0 # will be updated later
        data['aum'].iloc[-1] = 0 # will be updated later
            
    return data
