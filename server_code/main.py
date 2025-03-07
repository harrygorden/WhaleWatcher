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
