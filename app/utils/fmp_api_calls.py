# pylint: disable=missing-module-docstring, missing-function-docstring, missing-final-newline, trailing-whitespace, line-too-long, missing-class-docstring, missing-timeout

import json
import os
from urllib.request import urlopen
from urllib.error import URLError, HTTPError
from datetime import date, timedelta
import logging
from dotenv import load_dotenv
import pandas as pd
import certifi

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Format the date as yyyy-mm-dd
formatted_today = date.today().strftime("%Y-%m-%d")

# get the most recent business day
def get_most_recent_business_day():
    today = date.today()
    offset = max(1, (today.weekday() + 6) % 7 - 3)
    most_recent = today - timedelta(days=offset)
    return most_recent.strftime("%Y-%m-%d")

# load environment variables
load_dotenv()

# get FMP_API_KEY from .env file
FMP_API_KEY = os.getenv("FMP_API_KEY")

def get_jsonparsed_data(url):
    try:
        response = urlopen(url, cafile=certifi.where())
        data = response.read().decode("utf-8")
        return json.loads(data)
    except HTTPError as e:
        print(f"HTTP Error {e.code}: {e.reason}")
        return None
    except URLError as e:
        print(f"URL Error: {e.reason}")
        return None
    except json.JSONDecodeError:
        print("Error decoding JSON response")
        return None
    except (ValueError, TypeError) as e:
        print(f"An error occurred: {e}")
        return None

def get_10_year_tbill():
    formatted_previous = get_most_recent_business_day()
    api_response = get_jsonparsed_data(f"https://financialmodelingprep.com/api/v4/treasury?from={formatted_previous}&to={formatted_today}&apikey={FMP_API_KEY}")
    # Extract the "year10" value and convert it to float
    year10_value = float(api_response[0]["year10"])
    return year10_value

def get_30_year_tbond():
    formatted_previous = get_most_recent_business_day()
    api_response = get_jsonparsed_data(f"https://financialmodelingprep.com/api/v4/treasury?from={formatted_previous}&to={formatted_today}&apikey={FMP_API_KEY}")
    # Extract the "year30" value and convert it to float
    year30_value = float(api_response[0]["year30"])
    return year30_value

def get_all_eps(companies):
    api_response = get_jsonparsed_data(f"https://financialmodelingprep.com/api/v3/quote/{companies}?apikey={FMP_API_KEY}")
    # Create a DataFrame from the JSON data
    df_json = pd.DataFrame(api_response)
    # Extract the required columns (symbol and eps)
    df_json = df_json[['symbol', 'exchange', 'eps']]
    # Rename the columns in the DataFrame
    df_json = df_json.rename(columns={'symbol': 'Symbol'})
    df_json = df_json.rename(columns={'exchange': 'Exchange'})
    df_json = df_json.rename(columns={'eps': 'EPS'})
    return df_json

def get_industry_pe_values():
    formatted_previous = get_most_recent_business_day()
    nyse_response = get_jsonparsed_data(f"https://financialmodelingprep.com/api/v4/industry_price_earning_ratio?date={formatted_previous}&exchange=NYSE&apikey={FMP_API_KEY}")
    nasdaq_response = get_jsonparsed_data(f"https://financialmodelingprep.com/api/v4/industry_price_earning_ratio?date={formatted_previous}&exchange=NASDAQ&apikey={FMP_API_KEY}")
    
    # Combine responses and create a dataframe
    df = pd.DataFrame(nyse_response + nasdaq_response)
    
    # Convert 'pe' column to numeric type
    df['pe'] = pd.to_numeric(df['pe'])
    
    # Create a multi-index dictionary mapping (exchange, industry) to PE values
    industry_pe_dict = df.set_index(['exchange', 'industry'])['pe'].to_dict()
    
    return industry_pe_dict

def get_sector_pe_values():
    formatted_previous = get_most_recent_business_day()
    nyse_response = get_jsonparsed_data(f"https://financialmodelingprep.com/api/v4/sector_price_earning_ratio?date={formatted_previous}&exchange=NYSE&apikey={FMP_API_KEY}")
    nasdaq_response = get_jsonparsed_data(f"https://financialmodelingprep.com/api/v4/sector_price_earning_ratio?date={formatted_previous}&exchange=NASDAQ&apikey={FMP_API_KEY}")
    
    # Combine responses and create a dataframe
    df = pd.DataFrame(nyse_response + nasdaq_response)
    
    # Convert 'pe' column to numeric type
    df['pe'] = pd.to_numeric(df['pe'])
    
    # Create a multi-index dictionary mapping (exchange, sector) to PE values
    sector_pe_dict = df.set_index(['exchange', 'sector'])['pe'].to_dict()
    
    return sector_pe_dict

def get_market_risk_premium():
    # Get the total equity risk premium
    api_response = get_jsonparsed_data(f"https://financialmodelingprep.com/api/v4/market_risk_premium?apikey={FMP_API_KEY}")
    # Extract the total equity risk premium value and convert it to float
    total_equity_premium = api_response[0]["totalEquityRiskPremium"] / 100
    # Return the total equity risk premium
    return total_equity_premium