# pylint: disable=missing-module-docstring, missing-function-docstring, missing-final-newline, trailing-whitespace, line-too-long, missing-class-docstring

import json
import os
from urllib.request import urlopen
from datetime import date, timedelta
import pandas as pd
import certifi
from dotenv import load_dotenv

# Get yesterday's date
previous = date.today() - timedelta(days=3)

# Format the date as yyyy-mm-dd
formatted_previous = previous.strftime("%Y-%m-%d")
formatted_today = date.today().strftime("%Y-%m-%d")

# load environment variables
load_dotenv()

# get FMP_API_KEY from .env file
FMP_API_KEY = os.getenv("FMP_API_KEY")

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
    return json.loads(data)

def get_10_year_tbill():
    api_response = get_jsonparsed_data(f"https://financialmodelingprep.com/api/v4/treasury?from={formatted_previous}&to={formatted_today}&apikey={FMP_API_KEY}")
    # Extract the "year10" value and convert it to float
    year10_value = float(api_response[0]["year10"])
    return year10_value

def get_30_year_tbond():
    api_response = get_jsonparsed_data(f"https://financialmodelingprep.com/api/v4/treasury?from={formatted_previous}&to={formatted_today}&apikey={FMP_API_KEY}")
    # Extract the "year30" value and convert it to float
    year30_value = float(api_response[0]["year30"])
    return year30_value

def get_all_eps(companies):
    api_response = get_jsonparsed_data(f"https://financialmodelingprep.com/api/v3/quote/{companies}?apikey={FMP_API_KEY}")
    # Create a DataFrame from the JSON data
    df_json = pd.DataFrame(api_response)
    # Extract the required columns (symbol and eps)
    df_json = df_json[['symbol', 'eps']]
    # Rename the symbol column in the DataFrame
    df_json = df_json.rename(columns={'symbol': 'Symbol'})
    df_json = df_json.rename(columns={'eps': 'EPS'})
    return df_json