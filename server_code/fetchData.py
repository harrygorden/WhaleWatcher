import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.secrets
import anvil.server
import requests
from datetime import datetime

def build_option_symbol(ticker, expiration_date, option_type, strike):
    """
    Builds the OCC option symbol for Polygon API (e.g., O:SPY250307C00575000)
    
    Args:
        ticker (str): Ticker symbol
        expiration_date (str or date): YYYY-MM-DD or datetime.date
        option_type (str): "call" or "put"
        strike (float): Strike price
        
    Returns:
        str: Formatted OCC option symbol
    """
    # Convert string to date object if needed
    if isinstance(expiration_date, str):
        exp_date = datetime.strptime(expiration_date, "%Y-%m-%d")
    else:
        exp_date = expiration_date
    
    exp_formatted = exp_date.strftime("%y%m%d")
    opt_type = "C" if option_type.lower() == "call" else "P"
    strike_formatted = f"{float(strike) * 1000:08.0f}"
    
    return f"O:{ticker}{exp_formatted}{opt_type}{strike_formatted}"

def fetch_from_polygon(ticker, option_symbol):
    """
    Makes a request to Polygon's API to get option data
    
    Args:
        ticker (str): Ticker symbol
        option_symbol (str): OCC option symbol
        
    Returns:
        dict: Response data or error information
    """
    api_key = anvil.secrets.get_secret("Polygon_APIKey")
    url = f"https://api.polygon.io/v3/snapshot/options/{ticker}/{option_symbol}?apiKey={api_key}"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        
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
    Extracts relevant metrics from the Polygon API response
    
    Args:
        response_data (dict): Polygon API response
        
    Returns:
        dict: Volume, open interest, and other option data
    """
    if not response_data.get("success", False):
        return {
            "success": False,
            "error": response_data.get("error", "Unknown error occurred")
        }
    
    try:
        results = response_data["data"]["results"]
        
        # Extract metrics from various sections of the response
        day_data = results.get("day", {})
        details = results.get("details", {})
        greeks = results.get("greeks", {})
        underlying_asset = results.get("underlying_asset", {})
        
        return {
            "success": True,
            "symbol": details.get("ticker", ""),
            "volume": day_data.get("volume", 0),
            "open_interest": results.get("open_interest", 0),
            "strike_price": details.get("strike_price", 0),
            "contract_type": details.get("contract_type", ""),
            "expiration_date": details.get("expiration_date", ""),
            "implied_volatility": results.get("implied_volatility", 0),
            "delta": greeks.get("delta", 0),
            "gamma": greeks.get("gamma", 0),
            "theta": greeks.get("theta", 0),
            "vega": greeks.get("vega", 0),
            "underlying_ticker": underlying_asset.get("ticker", ""),
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
        ticker (str): Ticker symbol
        strike (float): Strike price
        option_type (str): "call" or "put"
        expiration_date (str): Date in format "YYYY-MM-DD"
        
    Returns:
        dict: Option metrics or error information
    """
    option_symbol = build_option_symbol(ticker, expiration_date, option_type, strike)
    response_data = fetch_from_polygon(ticker, option_symbol)
    return extract_option_metrics(response_data)
