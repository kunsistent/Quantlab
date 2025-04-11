import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import warnings
warnings.filterwarnings("ignore")

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
def get_stats(df, initial_aum, cost=0):
    """
    Extended backtest function that calculates key performance metrics
    Parameters
    ----------
    df : pandas.DataFrame
        DataFrame containing trades with columns:
          'entry_time', 'exit_time', 'entry_price', 'exit_price',
          'position', 'quantity'
    initial_aum : float
        Initial assets under management.
    cost : float, optional (default=0)
        Transaction cost per trade as a percentage (applied on both entry and exit legs).

    Returns
    -------
    - "metrics_df": DataFrame of key performance metrics.
    """
    # --- Validate Columns ---
    required_cols = ['entry_time', 'exit_time', 'entry_price', 'exit_price', 'position', 'quantity']
    if not all(col in df.columns for col in required_cols):
        raise ValueError(f"DataFrame must contain columns: {', '.join(required_cols)}")

    df = df.copy()
    df['entry_time'] = pd.to_datetime(df['entry_time'])
    df['exit_time']  = pd.to_datetime(df['exit_time'])

    # --- Calculate Trade PnL with Cost ---
    # cost_amount = (cost% of (entry_price + exit_price)) * quantity
    df['cost_amount'] = (cost / 100.0) * ((df['entry_price'] + df['exit_price']) * df['quantity'])
    df['pnl'] = ((df['exit_price'] - df['entry_price'])
                 * df['position']
                 * df['quantity']) - df['cost_amount']

    # --- Cumulative PnL & Returns ---
    df['cumulative_pnl'] = df['pnl'].cumsum()
    df['cumulative_returns'] = (df['cumulative_pnl'] / initial_aum) + 1
    df['daily_return'] = df['cumulative_returns'].pct_change().fillna(0)

    # --- Key Metrics ---
    final_pnl     = df['cumulative_pnl'].iloc[-1]
    total_return  = (final_pnl / initial_aum) * 100
    daily_ret_std = df['daily_return'].std()
    risk_free_rate = 0.07/252
    sharpe_ratio = (np.sqrt(252) * (df['daily_return'].mean() - risk_free_rate) / daily_ret_std) if daily_ret_std != 0 else np.nan

    start_date = df['entry_time'].min()
    end_date   = df['exit_time'].max()
    total_days = (end_date - start_date).days
    num_years  = total_days / 365.25 if total_days > 0 else np.nan
    num_weeks  = total_days / 7.0 if total_days > 0 else np.nan
    num_months = total_days / 30.4375 if total_days > 0 else np.nan

    cagr = (df['cumulative_returns'].iloc[-1])**(1 / num_years) - 1 if num_years and num_years > 0 else np.nan

    df['peak']     = df['cumulative_returns'].cummax()
    df['drawdown'] = (df['cumulative_returns'] - df['peak']) / df['peak']
    max_drawdown   = df['drawdown'].min()
    yearly_roi     = (final_pnl / initial_aum) / num_years * 100 if num_years and num_years > 0 else np.nan
    calmar_ratio   = (yearly_roi/100) / abs(max_drawdown) if abs(max_drawdown) != 0 else np.nan

    df['trade_outcome'] = np.where(df['pnl'] > 0, 1, 0)
    hit_ratio      = df['trade_outcome'].mean() * 100
    avg_profit     = df.loc[df['pnl'] > 0, 'pnl'].mean()
    avg_loss       = df.loc[df['pnl'] < 0, 'pnl'].mean()
    pnl_ratio      = avg_profit / abs(avg_loss) if avg_loss else np.nan

    overall_profit = final_pnl
    avg_day_profit = final_pnl / total_days if total_days > 0 else np.nan

    # --- Monthly PnL Breakup ---
    df['year']  = df['exit_time'].dt.year
    df['month'] = df['exit_time'].dt.month_name()
    monthly_group = df.groupby(['year', 'month'])['pnl'].sum().reset_index()
    monthly_pnl = monthly_group.pivot(index='year', columns='month', values='pnl').fillna(0)
    months_order = ["January","February","March","April","May","June",
                    "July","August","September","October","November","December"]
    monthly_pnl = monthly_pnl.reindex(columns=months_order)

    # Compute additional monthly stats for median calculation
    flattened_monthly = monthly_group['pnl']
    median_monthly_profit = flattened_monthly.median() if not flattened_monthly.empty else np.nan
    avg_monthly_profit = final_pnl / num_months if num_months else np.nan
    avg_yearly_profit = final_pnl / num_years if num_years else np.nan
    avg_weekly_profit = final_pnl / num_weeks if num_weeks else np.nan
    total_trades = len(df)
    avg_trades_per_day = total_trades / total_days if total_days > 0 else np.nan

    # --- Compile All Stats into a Metrics DataFrame ---
    metrics_data = [
        ["Overall Profit",          overall_profit],
        ["Total Return (%)",        total_return],
        ["Average Day Profit",      avg_day_profit],
        ["Average Monthly Profit",  avg_monthly_profit],
        ["Average Yearly Profit",   avg_yearly_profit],
        ["Median Monthly Profit",   median_monthly_profit],
        ["Average Weekly Profit",   avg_weekly_profit],
        ["Average Trades Per Day",  avg_trades_per_day],
        ["Sharpe Ratio",            sharpe_ratio],
        ["CAGR (%)",                cagr * 100 if not np.isnan(cagr) else np.nan],
        ["Calmar Ratio",            calmar_ratio],
        ["Max Drawdown (%)",        max_drawdown * 100 if not np.isnan(max_drawdown) else np.nan],
        ["Yearly ROI (%)",          yearly_roi],
        ["Hit Ratio (%)",           hit_ratio],
        ["Average Profit",          avg_profit],
        ["Average Loss",            avg_loss],
        ["PnL Ratio (Profit/Loss)", pnl_ratio]
    ]
    metrics_df = pd.DataFrame(metrics_data, columns=["Metric", "Value"])
    return metrics_df





def color_profit(val):
    """
    Return a CSS style to color the cell green if val is >= 0, else red.
    """
    try:
        color = 'green' if val >= 0 else 'red'
    except Exception:
        color = ''
    return f'background-color: {color}'

def get_monthly_pnl(df, initial_aum, cost=0):
    """
    Compute monthly PnL for each month in each year and style it using only red (loss) and green (profit).
    Adds a 'Total' column indicating the total PnL for that year.

    Parameters:
      df : pandas.DataFrame
          DataFrame with columns: 'entry_price', 'exit_price', 'quantity', 'position', 'exit_time'
      initial_aum : float
          (Unused here but kept for consistency)
      cost : float
          Transaction cost per trade as a percentage.

    Returns:
      styled : pandas.io.formats.style.Styler
          Pivot table (Year x Month with extra 'Total' column) with cells colored green for profit and red for loss.
    """
    df = df.copy()
    # Calculate cost amount and pnl per trade
    df['cost_amount'] = (cost / 100) * ((df['entry_price'] + df['exit_price']) * df['quantity'])
    df['pnl'] = ((df['exit_price'] - df['entry_price']) * df['position'] * df['quantity']) - df['cost_amount']

    # Convert exit_time to datetime
    df['exit_time'] = pd.to_datetime(df['exit_time'])

    # Extract year and month name from exit_time
    df['year'] = df['exit_time'].dt.year
    df['month'] = df['exit_time'].dt.month_name()

    # Group by year and month and sum the pnl
    monthly_grouped = df.groupby(['year', 'month'])['pnl'].sum().reset_index()
    monthly_pnl = monthly_grouped.pivot(index='year', columns='month', values='pnl').fillna(0)

    # Reorder columns to reflect calendar months
    months_order = ["January", "February", "March", "April", "May", "June",
                    "July", "August", "September", "October", "November", "December"]
    monthly_pnl = monthly_pnl.reindex(columns=months_order, fill_value=0)

    # Add a 'Total' column for each year
    monthly_pnl['Total'] = monthly_pnl.sum(axis=1)

    # Apply the custom coloring function
    styled = monthly_pnl.style.applymap(color_profit)
    return styled

def get_weekly_pnl(df, initial_aum, cost=0):
    """
    Compute weekly PnL aggregated by weekday and style it using only red (loss) and green (profit).

    Parameters:
      df : pandas.DataFrame
          DataFrame with columns: 'entry_price', 'exit_price', 'quantity', 'position', 'exit_time'
      initial_aum : float
          (Unused here but kept for consistency)
      cost : float
          Transaction cost per trade as a percentage.

    Returns:
      styled : pandas.io.formats.style.Styler
          DataFrame with weekdays as index (ordered Monday to Sunday) and total PnL, styled with green for profit and red for loss.
    """
    df = df.copy()
    # Calculate cost amount and pnl per trade
    df['cost_amount'] = (cost / 100) * ((df['entry_price'] + df['exit_price']) * df['quantity'])
    df['pnl'] = ((df['exit_price'] - df['entry_price']) * df['position'] * df['quantity']) - df['cost_amount']

    # Convert exit_time to datetime
    df['exit_time'] = pd.to_datetime(df['exit_time'])

    # Extract weekday name from exit_time
    df['weekday'] = df['exit_time'].dt.day_name()

    # Group by weekday and sum the pnl
    weekly_grouped = df.groupby('weekday')['pnl'].sum().reset_index()
    weekly_pnl = weekly_grouped.set_index('weekday')

    # Ensure natural weekday order
    day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    weekly_pnl = weekly_pnl.reindex(day_order, fill_value=0)

    # Apply custom coloring
    styled = weekly_pnl.style.applymap(color_profit)
    return styled



def plot_pnl_and_trades(df, cost=0):
    """
    Plot two charts side-by-side:
    1. Cumulative PnL over time
    2. Monthly number of trades with color gradient

    Parameters:
    - df : pd.DataFrame
        Must contain 'entry_price', 'exit_price', 'position', 'quantity', 'exit_time'
    - cost : float
        Transaction cost percentage (default is 0)

    Returns:
    - dict with 'chart': matplotlib figure object
    """
    df = df.copy()
    df['exit_time'] = pd.to_datetime(df['exit_time'])
    df.sort_values('exit_time', inplace=True)

    # Calculate PnL with cost
    df['cost_amount'] = (cost / 100) * ((df['entry_price'] + df['exit_price']) * df['quantity'])
    df['pnl'] = ((df['exit_price'] - df['entry_price']) * df['position'] * df['quantity']) - df['cost_amount']

    # --- Cumulative PnL Chart ---
    df['cumulative_pnl'] = df['pnl'].cumsum()

    # --- Monthly Trade Count ---
    df['month'] = df['exit_time'].dt.to_period('M').dt.to_timestamp()
    monthly_trades = df.groupby('month').size()

    # Normalize values for color mapping
    norm = plt.Normalize(monthly_trades.min(), monthly_trades.max())
    colors = plt.cm.viridis(norm(monthly_trades.values))

    # --- Plotting ---
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    # Plot 1: Cumulative PnL
    axes[0].plot(df['exit_time'], df['cumulative_pnl'], color='green', linewidth=2)
    axes[0].set_title("Cumulative PnL Over Time", fontsize=13)
    axes[0].set_xlabel("Exit Time")
    axes[0].set_ylabel("Cumulative PnL")
    axes[0].grid(True)

    # Plot 2: Monthly Number of Trades
    axes[1].bar(monthly_trades.index, monthly_trades.values, color=colors, edgecolor='black')
    axes[1].set_title("Monthly Number of Trades", fontsize=13)
    axes[1].set_xlabel("Month")
    axes[1].set_ylabel("Number of Trades")
    axes[1].grid(True)
    axes[1].tick_params(axis='x', rotation=45)

    plt.tight_layout()

    return {"chart": fig}
