import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.secrets
import anvil.server
import requests
import json
from datetime import datetime

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

def build_option_symbol(ticker, expiration_date, option_type, strike):
    """
    Builds the OCC option symbol for Polygon API.
    Example: O:SPY250307C00575000
    
    Args:
        ticker (str): The ticker symbol (e.g., "SPY")
        expiration_date (str): Date in format "YYYY-MM-DD"
        option_type (str): "call" or "put"
        strike (float): The strike price
        
    Returns:
        str: Formatted OCC option symbol
    """
    # Convert expiration date from YYYY-MM-DD to YYMMDD
    exp_date = datetime.strptime(expiration_date, "%Y-%m-%d")
    exp_formatted = exp_date.strftime("%y%m%d")
    
    # Format the option type (C for call, P for put)
    opt_type = "C" if option_type.lower() == "call" else "P"
    
    # Format the strike price (8 digits with 3 decimal places)
    strike_formatted = f"{float(strike) * 1000:08.0f}"
    
    # Build the full OCC symbol
    occ_symbol = f"O:{ticker}{exp_formatted}{opt_type}{strike_formatted}"
    
    return occ_symbol

def fetch_from_polygon(option_symbol):
    """
    Makes a request to Polygon's API to get option data
    
    Args:
        option_symbol (str): The OCC option symbol
        
    Returns:
        dict: The response data or error information
    """
    api_key = anvil.secrets.get_secret("Polygon_APIKey")
    url = f"https://api.polygon.io/v3/snapshot/options/{option_symbol}?apiKey={api_key}"
    
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise exception for non-200 status codes
        
        return {
            "success": True,
            "data": response.json(),
            "status_code": response.status_code
        }
    except requests.exceptions.RequestException as e:
        return {
            "success": False,
            "error": str(e),
            "status_code": getattr(e.response, 'status_code', None) if hasattr(e, 'response') else None
        }

def extract_option_metrics(response_data):
    """
    Extracts the relevant metrics from the Polygon API response
    
    Args:
        response_data (dict): The Polygon API response
        
    Returns:
        dict: Dict containing volume, open interest, and other relevant data
    """
    if not response_data.get("success", False):
        return {
            "success": False,
            "error": response_data.get("error", "Unknown error occurred")
        }
    
    try:
        # Extract the results from the response
        results = response_data["data"]["results"]
        
        # Get the day's data
        day_data = results.get("day", {})
        volume = day_data.get("volume", 0)
        open_interest = results.get("open_interest", 0)
        
        # Get current price data
        last_price = results.get("last_trade", {}).get("price", 0)
        bid = results.get("last_quote", {}).get("bid", 0)
        ask = results.get("last_quote", {}).get("ask", 0)
        
        # Get underlying details
        underlying_price = results.get("underlying_asset", {}).get("price", 0)
        
        return {
            "success": True,
            "symbol": results.get("symbol", ""),
            "volume": volume,
            "open_interest": open_interest,
            "last_price": last_price,
            "bid": bid,
            "ask": ask,
            "underlying_price": underlying_price,
            "raw_data": results  # Including raw data for potential future use
        }
    except (KeyError, TypeError) as e:
        return {
            "success": False,
            "error": f"Error parsing response: {str(e)}"
        }

def get_option_data(ticker, strike, option_type, expiration_date):
    """
    Main function to get option data from Polygon
    
    Args:
        ticker (str): The ticker symbol (e.g., "SPY")
        strike (float): The strike price
        option_type (str): "call" or "put"
        expiration_date (str): Date in format "YYYY-MM-DD"
        
    Returns:
        dict: Dict containing option metrics or error information
    """
    # Build the OCC option symbol
    option_symbol = build_option_symbol(ticker, expiration_date, option_type, strike)
    
    # Fetch data from Polygon
    response_data = fetch_from_polygon(option_symbol)
    
    # Extract and return the metrics
    return extract_option_metrics(response_data)
