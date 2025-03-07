import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.secrets
import anvil.server

# Database utility functions for WhaleWatcher

# Add server-callable functions here as needed for database operations

def get_all_whales():
    """
    Retrieves all whale contracts from the whales table
    
    Returns:
        list: Search results containing all whale contracts
    """
    return app_tables.whales.search()

def save_option_data_to_table(trade_id, ticker, strike, side, expiration, option_data):
    """
    Writes option data to the todaysdata table
    
    Args:
        trade_id (str): Unique trade identifier
        ticker (str): Stock ticker symbol
        strike (float): Strike price
        side (str): "C" for call or "P" for put
        expiration (str): Expiration date
        option_data (dict): Dictionary containing option metrics
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        app_tables.todaysdata.add_row(
            tradeID=trade_id,
            ticker=ticker,
            strike=strike,
            side=side,
            expiration=expiration,
            volume=option_data['volume'],
            openInterest=option_data['open_interest']
        )
        return True
    except Exception as e:
        print(f"Error saving to todaysdata: {str(e)}")
        return False
