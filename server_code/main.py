import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.secrets
import anvil.server
from . import fetchData

# This is a server module. It runs on the Anvil server,
# rather than in the user's browser.
#
# To allow anvil.server.call() to call functions here, we mark
# them with @anvil.server.callable.
# Here is an example - you can replace it with your own:
#
# @anvil.server.callable
# def say_hello(name):
#   print("Hello, " + name + "!")
#   return 42
#

@anvil.server.callable
def fetch_option_data(ticker, strike, option_type, expiration_date):
    """
    Callable function to fetch option data from Polygon API
    
    Args:
        ticker (str): The ticker symbol (e.g., "SPY")
        strike (float): The strike price
        option_type (str): "call" or "put"
        expiration_date (str): Date in format "YYYY-MM-DD"
        
    Returns:
        dict: Dict containing option metrics (volume, open interest, etc.) or error information
    """
    return fetchData.get_option_data(ticker, strike, option_type, expiration_date)

@anvil.server.callable
def get_all_contract_data():
    """
    Fetches option data for all contracts in the whales table
    
    Returns:
        list: List of dictionaries containing option data for each record
    """
    # Get all rows from the whales table
    all_whales = app_tables.whales.search()
    
    results = []
    
    # Process each record
    for whale in all_whales:
        trade_id = whale['tradeID']
        ticker = whale['ticker']
        strike = whale['strike']
        side = whale['side']
        expiration = whale['expiration']
        
        # Convert the side (C/P) to option_type (call/put)
        option_type = "call" if side == "C" else "put"
        
        # Print the message as requested with clear formatting
        print(f"\n{'+'*60}")
        print(f"Fetching data for trade {trade_id}: {ticker} {strike}{side} {expiration}")
        print(f"{'+'*60}")
        
        # Fetch the option data
        option_data = fetchData.get_option_data(ticker, strike, option_type, expiration)
        
        # Add trade ID to the data for reference
        option_data['tradeID'] = trade_id
        
        # Print key metrics for immediate visibility in console
        if option_data['success']:
            print(f"  Volume: {option_data['volume']} | Open Interest: {option_data['open_interest']}")
            print(f"  Delta: {option_data['delta']:.4f} | Gamma: {option_data['gamma']:.6f}")
            print(f"  Theta: {option_data['theta']:.4f} | Vega: {option_data['vega']:.6f}")
            print(f"  IV: {option_data['implied_volatility']:.4f}")
        else:
            print(f"  ERROR: {option_data.get('error', 'Unknown error')}")
        
        # Add to results list
        results.append(option_data)
    
    # Print footer
    print(f"\nCompleted: Retrieved data for {len(results)} contracts\n")
    
    return results
