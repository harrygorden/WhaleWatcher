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
        # Extract the results from the response - the actual API response is different than initially expected
        results = response_data["data"]["results"]
        
        # Get the day's data
        day_data = results.get("day", {})
        volume = day_data.get("volume", 0)
        open_interest = results.get("open_interest", 0)
        
        # Get details and contract info
        details = results.get("details", {})
        contract_type = details.get("contract_type", "")
        strike_price = details.get("strike_price", 0)
        expiration_date = details.get("expiration_date", "")
        ticker = details.get("ticker", "")
        
        # Get greeks if available
        greeks = results.get("greeks", {})
        delta = greeks.get("delta", 0)
        gamma = greeks.get("gamma", 0)
        theta = greeks.get("theta", 0)
        vega = greeks.get("vega", 0)
        
        # Get implied volatility
        implied_volatility = results.get("implied_volatility", 0)
        
        # Get underlying details
        underlying_asset = results.get("underlying_asset", {})
        underlying_ticker = underlying_asset.get("ticker", "")
        
        return {
            "success": True,
            "symbol": ticker,
            "volume": volume,
            "open_interest": open_interest,
            "contract_type": contract_type,
            "strike_price": strike_price,
            "expiration_date": expiration_date,
            "delta": delta,
            "gamma": gamma,
            "theta": theta,
            "vega": vega,
            "implied_volatility": implied_volatility,
            "underlying_ticker": underlying_ticker,
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
