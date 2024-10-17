# pylint: disable=missing-module-docstring, missing-function-docstring, invalid-name, line-too-long, missing-final-newline, trailing-whitespace

import os
import json
from typing import Dict, Any, Union, List
from urllib.request import urlopen
from urllib.error import URLError, HTTPError
import logging
from dotenv import load_dotenv
import certifi

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

def generate_schema(sample_data: Union[Dict[str, Any], List[Dict[str, Any]]]) -> Dict[str, Any]:
    if isinstance(sample_data, list):
        return generate_array_schema(sample_data)
    return generate_object_schema(sample_data)

def generate_array_schema(sample_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    schema = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "array",
        "items": generate_object_schema(sample_data[0])
    }
    return schema

def generate_object_schema(sample_data: Dict[str, Any]) -> Dict[str, Any]:
    schema = {
        "type": "object",
        "properties": {},
        "required": [],
        "additionalProperties": False
    }
    
    for key, value in sample_data.items():
        schema["properties"][key] = infer_type(value)
        schema["required"].append(key)
    
    return schema

def infer_type(value: Any) -> Dict[str, Any]:
    if isinstance(value, str):
        return {"type": "string"}
    elif isinstance(value, int):
        return {"type": "integer"}
    elif isinstance(value, float):
        return {"type": "number"}
    elif isinstance(value, bool):
        return {"type": "boolean"}
    elif isinstance(value, list):
        if value:
            return {
                "type": "array",
                "items": infer_type(value[0])
            }
        return {"type": "array"}
    elif isinstance(value, dict):
        return generate_object_schema(value)
    elif value is None:
        return {"type": "null"}
    return {"type": "object"}

def main():
    endpoints = {
        "Income Statements": f"https://financialmodelingprep.com/api/v3/income-statement/AAPL?period=annual&apikey={FMP_API_KEY}",
        "Balance Sheet Statements": f"https://financialmodelingprep.com/api/v3/balance-sheet-statement/AAPL?period=annual&apikey={FMP_API_KEY}",
        "Cashflow Statements": f"https://financialmodelingprep.com/api/v3/cash-flow-statement/AAPL?period=annual&apikey={FMP_API_KEY}",
        "Ratios": f"https://financialmodelingprep.com/api/v3/ratios/AAPL?apikey={FMP_API_KEY}",
        "Key Metrics": f"https://financialmodelingprep.com/api/v3/key-metrics/AAPL?apikey={FMP_API_KEY}",
        "DCFs": f"https://financialmodelingprep.com/api/v3/discounted-cash-flow/AAPL?apikey={FMP_API_KEY}",
        "Key Metrics TTM": f"https://financialmodelingprep.com/api/v3/key-metrics-ttm/AAPL?apikey={FMP_API_KEY}",
        "Ratios TTM": f"https://financialmodelingprep.com/api/v3/ratios-ttm/AAPL?apikey={FMP_API_KEY}",
        "Financial Scores": f"https://financialmodelingprep.com/api/v4/score?symbol=AAPL&apikey={FMP_API_KEY}",
        "Financials Growth": f"https://financialmodelingprep.com/api/v3/financial-growth/AAPL?period=annual&apikey={FMP_API_KEY}",
        "Income Statement Growth": f"https://financialmodelingprep.com/api/v3/income-statement-growth/AAPL?period=annual&apikey={FMP_API_KEY}",
        "Balance Sheet Growth": f"https://financialmodelingprep.com/api/v3/balance-sheet-statement-growth/AAPL?period=annual&apikey={FMP_API_KEY}",
        "Cashflow Statement Growth": f"https://financialmodelingprep.com/api/v3/cash-flow-statement-growth/AAPL?period=annual&apikey={FMP_API_KEY}",
    }

    # Create a directory to store the schema files
    os.makedirs("schemas", exist_ok=True)

    for name, url in endpoints.items():
        print(f"Fetching data for {name}...")
        sample_data = get_jsonparsed_data(url)
        print(f"Generating schema for {name}...")
        schema = generate_schema(sample_data)
        
        # Create individual JSON schema file for each endpoint
        file_name = f"schemas/{name}.json"
        with open(file_name, "w", encoding='utf-8') as f:
            json.dump(schema, f, indent=2)
        print(f"Schema saved to {file_name}")

    print("All schemas have been generated and saved.")

if __name__ == "__main__":
    main()