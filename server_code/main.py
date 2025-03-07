import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.secrets
import anvil.server
from . import fetchData

@anvil.server.callable
def fetch_option_data(ticker, strike, option_type, expiration_date):
    """
    Fetches option data from Polygon API
    
    Args:
        ticker (str): Ticker symbol (e.g., "SPY")
        strike (float): Strike price
        option_type (str): "call" or "put"
        expiration_date (str): Date in format "YYYY-MM-DD"
        
    Returns:
        dict: Option metrics (volume, open interest, etc.) or error information
    """
    return fetchData.get_option_data(ticker, strike, option_type, expiration_date)

@anvil.server.callable
def get_all_contract_data():
    """
    Fetches option data for all contracts in the whales table
    and writes the results to the todaysData table
    
    Returns:
        list: List of dictionaries containing option data for each record
    """
    all_whales = app_tables.whales.search()
    results = []
    
    for whale in all_whales:
        trade_id = whale['tradeID']
        ticker = whale['ticker']
        strike = whale['strike']
        side = whale['side']
        expiration = whale['expiration']
        
        option_type = "call" if side == "C" else "put"
        
        print(f"\n{'+'*60}")
        print(f"Fetching data for trade {trade_id}: {ticker} {strike}{side} {expiration}")
        print(f"{'+'*60}")
        
        option_data = fetchData.get_option_data(ticker, strike, option_type, expiration)
        option_data['tradeID'] = trade_id
        
        if option_data['success']:
            print(f"  Volume: {option_data['volume']} | Open Interest: {option_data['open_interest']}")
            print(f"  Delta: {option_data['delta']:.4f} | Gamma: {option_data['gamma']:.6f}")
            print(f"  Theta: {option_data['theta']:.4f} | Vega: {option_data['vega']:.6f}")
            print(f"  IV: {option_data['implied_volatility']:.4f}")
            
            # Write data to todaysData table
            app_tables.todaysData.add_row(
                tradeID=trade_id,
                ticker=ticker,
                strike=strike,
                side=side,
                expiration=expiration,
                volume=option_data['volume'],
                openInterest=option_data['open_interest']
            )
            print(f"  Data saved to todaysData table")
        else:
            print(f"  ERROR: {option_data.get('error', 'Unknown error')}")
        
        results.append(option_data)
    
    print(f"\nCompleted: Retrieved data for {len(results)} contracts\n")
    return results
