# pylint: disable = missing-module-docstring, missing-function-docstring, missing-final-newline, trailing-whitespace, line-too-long, missing-class-docstring, invalid-name
import os
import json
from datetime import datetime, date
from collections import OrderedDict
import logging
import pandas as pd
import numpy as np
from werkzeug.utils import secure_filename
from .fmp_api_calls import get_10_year_tbill, get_30_year_tbond, get_all_eps, get_industry_pe_values, get_sector_pe_values, get_market_risk_premium
from .mappings import industry_mapping, sector_mapping, dividend_category_mapping

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Call the API once to get the 10-year T-bill rate
tbill_rate = get_10_year_tbill()

# Call the API once to get the 30-year t-bond rate
tbond_rate = get_30_year_tbond()

# Get the industry and sector PE values
industry_pe_dict = get_industry_pe_values()
sector_pe_dict = get_sector_pe_values()

# Get the market risk premium rate
market_risk_premium = get_market_risk_premium()

# Function to safely get PE value
def safe_get_pe(dictionary, exchange, key):
    return dictionary.get((exchange, key), np.nan)

# parse dividend category year ranges into a string range mapping
def parse_range(range_str):
    """Parse a string range into a tuple of integers."""
    if range_str.endswith('+'):
        return (int(range_str[:-1]), float('inf'))
    return tuple(map(int, range_str.split('-')))
    
# get dividend category based on years and a string range mapping
def get_dividend_category(years, category_mapping):
    """Determine the dividend category based on years and a string range mapping."""
    for category, range_str in category_mapping.items():
        start, end = parse_range(range_str)
        if start <= years <= end:
            return category
    return "N/A"  # or any default category you prefer

# Get dividend categories in parsed years
def categorize_dividend(years):
    return get_dividend_category(years, dividend_category_mapping)

# estimate the standard deviation of DGR
def estimate_dgr_std_dev(dgr_1y, dgr_3y, dgr_5y):
    """
    Estimate the standard deviation of DGR using 1-year, 3-year, and 5-year growth rates.
    
    :param dgr_1y: 1-year Dividend Growth Rate
    :param dgr_3y: 3-year Dividend Growth Rate
    :param dgr_5y: 5-year Dividend Growth Rate
    :return: Estimated standard deviation of DGR
    """
    # Convert percentages to decimals if necessary
    dgr_1y = dgr_1y / 100 if dgr_1y > 1 else dgr_1y
    dgr_3y = dgr_3y / 100 if dgr_3y > 1 else dgr_3y
    dgr_5y = dgr_5y / 100 if dgr_5y > 1 else dgr_5y
    
    # Create an estimated series of annual growth rates
    estimated_series = [
        dgr_1y,
        dgr_3y,
        dgr_3y,
        dgr_5y,
        dgr_5y
    ]
    
    # Calculate the standard deviation
    return np.std(estimated_series) * 100

def meets_chowder_criteria(row):
    yield_threshold = 3.0
    high_yield_chowder = 12
    low_yield_chowder = 15
    
    if row['Div Yield'] >= yield_threshold:
        return row['Chowder Number'] >= high_yield_chowder
    return row['Chowder Number'] >= low_yield_chowder

class DateTimeEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, (datetime, date)):
            return o.isoformat()
        return super(DateTimeEncoder, self).default(o)

def dataframe_to_custom_json(df):
    # Use the current DataFrame column order instead of reading from Excel
    column_order = df.columns.tolist()

    # Reset index to make sure we include any index as a column
    df_reset = df.reset_index(drop=True)
    
    # Convert datetime columns to strings
    for col in df_reset.select_dtypes(include=['datetime64', 'datetime64[ns]']).columns:
        df_reset[col] = df_reset[col].dt.date.astype(str)
    
    # Convert to list of OrderedDicts to preserve current column order
    result = []
    for _, row in df_reset.iterrows():
        ordered_row = OrderedDict()
        for col in column_order:
            value = row[col]
            # Convert NaN to null for JSON compatibility
            if pd.isna(value):
                ordered_row[col] = None
            elif isinstance(value, bool):
                ordered_row[col] = bool(value)  # Ensure booleans are correctly serialized
            elif isinstance(value, str) and len(value) == 19 and value[10] == ' ':
                # This checks if the value looks like "YYYY-MM-DD HH:MM:SS"
                ordered_row[col] = value[:10]  # Keep only "YYYY-MM-DD"
            else:
                ordered_row[col] = value
        result.append(ordered_row)
    
    return result

def clean_and_save_file(file, upload_folder):
    if file and file.filename:
        filename = secure_filename(file.filename)
        file_path = os.path.join(upload_folder, filename)
        file.save(file_path)

        if filename.endswith(".xls") or filename.endswith(".xlsx"):
            xls = pd.ExcelFile(file_path)

            if "All" in xls.sheet_names:
                # Read metadata from first two rows
                metadata = pd.read_excel(file_path, sheet_name="All", nrows=2, header=None)
                title = metadata.iloc[0, 0]
                date_time = metadata.iloc[1, 0]
                
                # Format the date_time to remove the timestamp
                if isinstance(date_time, (datetime, pd.Timestamp)):
                    date_time = date_time.date().isoformat()
                elif isinstance(date_time, str):
                    # If it's already a string, try to parse and format it
                    try:
                        parsed_date = datetime.fromisoformat(date_time)
                        date_time = parsed_date.date().isoformat()
                    except ValueError:
                        # If parsing fails, keep the original string
                        pass
                
                # Read the main data, skipping the first two rows
                df = pd.read_excel(file_path, sheet_name="All", header=2, parse_dates=True)
                
                # Convert all company symbols to a comma-separated string
                companies = ','.join(df['Symbol'])
                
                # call bulk API endpoint to retrieve all eps values
                all_eps = get_all_eps(companies)
                
                # drop column with name of "FV"
                if "FV" in df.columns:
                    df = df.drop(columns=["FV"])
                else:
                    print("Warning: 'FV' column not found")

                # Move 'Industry' to the third position
                if 'Industry' in df.columns:
                    industry_col = df.pop('Industry')
                    df.insert(3, 'Industry', industry_col)
                else:
                    print("Warning: 'Industry' column not found")
                
                # drop column with name of "New Member"
                if "New Member" in df.columns:
                    df = df.drop(columns=["New Member"])
                else:
                    print("Warning: 'New Member' column not found")
                
                # Move 'Fair Value' to the fourth position
                if 'Fair Value' in df.columns:
                    fair_value_col = df.pop('Fair Value')
                    df.insert(4, 'Fair Value', fair_value_col)
                else:
                    print("Warning: 'Fair Value' column not found")
                
                # Move 'FV %' to the fifth position
                if 'FV %' in df.columns:
                    fv_percent_col = df.pop('FV %')
                    df.insert(5, 'FV %', fv_percent_col)
                else:
                    print("Warning: 'FV %' column not found")
                
                # Rename column "Price" to "Current Price"
                if "Price" in df.columns:
                    df.rename(columns={"Price": "Current Price"}, inplace=True)
                else:
                    print("Warning: 'Price' column not found")
                
                # drop column with name of "Unnamed: 24"
                if "Unnamed: 24" in df.columns:
                    df = df.drop(columns=["Unnamed: 24"])
                else:
                    print("Warning: 'Unnamed: 24' column not found")
                
                # map column values from excel file to api response for industry and sector
                df['Industry'] = df['Industry'].map(industry_mapping)
                df['Sector'] = df['Sector'].map(sector_mapping)

                # Move "Chowder Number" to the sixth position
                if "Chowder Number" in df.columns:
                    chowder_number_col = df.pop("Chowder Number")
                    df.insert(6, "Chowder Number", chowder_number_col)
                else:
                    print("Warning: 'Chowder Number' column not found")
                
                # Replace null entries in "Chowder Number" column with 0
                df["Chowder Number"] = df["Chowder Number"].fillna(0)
                
                # Add the new "Meets Chowder Criteria" column
                df['Meets Chowder Criteria'] = df.apply(meets_chowder_criteria, axis=1)
                
                # Move "Meets Chowder Criteria" to the seventh position
                if "Meets Chowder Criteria" in df.columns:
                    meets_chowder_criteria_col = df.pop("Meets Chowder Criteria")
                    df.insert(7, "Meets Chowder Criteria", meets_chowder_criteria_col)
                else:
                    print("Warning: 'Meets Chowder Criteria' column not found")
                
                # Add the new "Greater Than 10 Year T-Bill" column
                df["Greater Than 10 Year T-Bill"] = np.nan
                
                # Move "Greater Than 10 Year T-Bill" to the eighth position
                if "Greater Than 10 Year T-Bill" in df.columns:
                    greater_than_10_year_tbill_col = df.pop("Greater Than 10 Year T-Bill")
                    df.insert(8, "Greater Than 10 Year T-Bill", greater_than_10_year_tbill_col)
                else:
                    print("Warning: 'Greater Than 10 Year T-Bill' column not found")
                
                # Set initial value to 0 and then retrieve 10 year t-bill rate and add 1 then conpare to div yield
                df["Greater Than 10 Year T-Bill"] = df.apply(lambda row: 
                    (np.nan_to_num(row["Greater Than 10 Year T-Bill"], nan=tbill_rate) + 1) < row["Div Yield"], 
                    axis=1
                )
                
                # add eps and exchange columns
                df = pd.merge(df, all_eps, on='Symbol', how='left')
                
                # create new columns for IRR and IRR Greater than T-Bond
                df['IRR'] = (df['EPS'] / df['Current Price']) * 100
                df['IRR Greater than T-Bond'] = df['IRR'] > tbond_rate
                
                # Move "IRR" to the ninth position
                if "IRR" in df.columns:
                    irr_col = df.pop("IRR")
                    df.insert(9, "IRR", irr_col)
                else:
                    print("Warning: 'IRR' column not found")
                
                # Move "IRR Greater than T-Bond" to the tenth position
                if "IRR Greater than T-Bond" in df.columns:
                    irr_greater_than_tbond_col = df.pop("IRR Greater than T-Bond")
                    df.insert(10, "IRR Greater than T-Bond", irr_greater_than_tbond_col)
                else:
                    print("Warning: 'IRR Greater than T-Bond' column not found")
                
                # create new column for PE Less Than Half EPS Growth Rate
                df['PE Less Half EPS Growth Rate'] = df['P/E'] < (df['EPS 1Y'] / 2)
                
                # Move "PE Less Half EPS Growth Rate" to the eleventh position
                if "PE Less Half EPS Growth Rate" in df.columns:
                    pe_less_half_eps_growth_rate_col = df.pop("PE Less Half EPS Growth Rate")
                    df.insert(11, "PE Less Half EPS Growth Rate", pe_less_half_eps_growth_rate_col)
                else:
                    print("Warning: 'PE Less Half EPS Growth Rate' column not found")
                
                # create new column for "Growth Plus Yield By PE Less Than 2"
                df['Growth Plus Yield By PE Less Than 2'] = ((df['EPS 1Y'] + df['Div Yield']) / df['P/E']) > 2
                
                # Move "Growth Plus Yield By PE Less Than 2" to the twelfth position
                if "Growth Plus Yield By PE Less Than 2" in df.columns:
                    growth_plus_yield_by_pe_less_than_2_col = df.pop("Growth Plus Yield By PE Less Than 2")
                    df.insert(12, "Growth Plus Yield By PE Less Than 2", growth_plus_yield_by_pe_less_than_2_col)
                else:
                    print("Warning: 'Growth Plus Yield By PE Less Than 2' column not found")
                
                # create new column for "Price to Cash Flow"
                df['Price to Cash Flow'] = df['Current Price'] / df['CF/Share']
                
                # Move "Price to Cash Flow" to the thirteenth position
                if "Price to Cash Flow" in df.columns:
                    price_to_cash_flow_col = df.pop("Price to Cash Flow")
                    df.insert(13, "Price to Cash Flow", price_to_cash_flow_col)
                else:
                    print("Warning: 'Price to Cash Flow' column not found")
                
                # create new colume for "PCF Ratio Less Than 10"
                df['PCF Ratio Less Than 10'] = df['Price to Cash Flow'] < 10
                
                # Move "PCF Ratio Less Than 10" to the fourteenth position
                if "PCF Ratio Less Than 10" in df.columns:
                    pcf_ratio_less_than_10_col = df.pop("PCF Ratio Less Than 10")
                    df.insert(14, "PCF Ratio Less Than 10", pcf_ratio_less_than_10_col)
                else:
                    print("Warning: 'PCF Ratio Less Than 10' column not found")
                
                # Apply the PE values for Sector and Industry
                df['Industry PE'] = df.apply(lambda row: safe_get_pe(industry_pe_dict, row['Exchange'], row['Industry']), axis=1)
                df['Sector PE'] = df.apply(lambda row: safe_get_pe(sector_pe_dict, row['Exchange'], row['Sector']), axis=1)
                
                # Add 'Less Than Industry PE' column
                df['PE Less Than Industry PE'] = df['P/E'] < df['Industry PE']

                # Add 'Less Than Sector PE' column
                df['PE Less Than Sector PE'] = df['P/E'] < df['Sector PE']
                
                # Add 'Weighted DGR' column
                df['Weighted DGR'] = (df['DGR 10Y'] * 0.2) + (df['DGR 5Y'] * 0.4) + (df['DGR 3Y'] * 0.3) + (df['DGR 1Y'] * 0.5)
                
                # Add '3Y DGR Greater Than 10Y DGR'
                df['3Y DGR Greater Than 10Y DGR'] = df['DGR 3Y'] > df['DGR 10Y']
                
                # Add '1Y DGR Less Than 1Y ESP Growth Rate'
                df['1Y DGR Less Than 1Y ESP Growth Rate'] = df['DGR 1Y'] < df['EPS 1Y']
                
                # Add 'Div Yield + Weighted DGR Greater Than Market Risk Rate + 10 Year T-Bill'
                df['Div Yield + Weighted DGR Greater Than Market Risk Rate + 10 Year T-Bill'] = (df['Div Yield'] + df['Weighted DGR']) > (market_risk_premium + tbill_rate)
                
                # 1Y EPS Growth Greater Than Weighted DGR
                df['1Y EPS Growth Greater Than Weighted DGR'] = df['EPS 1Y'] > df['Weighted DGR']
                
                # Div Yield + 1Y EPS Growth Greater Than Market Risk Rate + 10 Year T-Bill
                df['Div Yield + 1Y EPS Growth Greater Than Market Risk Rate + 10 Year T-Bill'] = (df['Div Yield'] + df['EPS 1Y']) > (market_risk_premium + tbill_rate)
                
                # Rename Annualized to Annualized Dividend
                df.rename(columns={"Annualized": "Annualized Dividend"}, inplace=True)
                
                # Calculate Payout Ratio
                df['Payout Ratio'] = (df['Annualized Dividend'] / df['EPS']) * 100
                
                # Calculate FCF Payout Ratio
                df['FCF Payout Ratio'] = (df['Annualized Dividend'] / df['CF/Share']) * 100
                
                # Calculate Dividend Coverage Ratio
                df['Dividend Coverage Ratio'] = df['EPS'] / df['Annualized Dividend']
                
                # Calculate Dividend Growth Acceleration
                df['Dividend Growth Acceleration'] = df['DGR 3Y'] - df['DGR 10Y']
                
                # Calculate Projected Yield on Cost
                df['Projected Yield on Cost'] = (df['Div Yield']/100) * ((1 + (df['DGR 5Y']/100)) ** 5)
                
                # Return Dividend Category
                df['Dividend Category'] = df['No Years'].apply(categorize_dividend)
                
                # Calculating 5-Year EPS CAGR from PEG and P/E
                df['5-Year EPS CAGR'] = df['P/E'] / df['PEG']
                
                # Example usage in a DataFrame
                df['Estimated_DGR_StdDev'] = df.apply(lambda row: estimate_dgr_std_dev(row['DGR 1Y'], row['DGR 3Y'], row['DGR 5Y']), axis=1)
                
                # Convert main data to list of OrderedDicts, passing the Excel file path
                main_data = dataframe_to_custom_json(df)
                
                # Combine metadata and main data
                full_data = OrderedDict([
                    ("metadata", OrderedDict([
                        ("title", title),
                        ("as_of_date", date_time)
                    ])),
                    ("data", main_data)
                ])

                # Convert to JSON string
                full_json = json.dumps(full_data, indent=2, cls=DateTimeEncoder)

                # Save the JSON output
                json_filename = os.path.splitext(filename)[0] + ".json"
                json_path = os.path.join(upload_folder, json_filename)
                with open(json_path, "w", encoding="utf-8") as f:
                    f.write(full_json)

                return full_json  # Return the JSON string
            else:
                raise ValueError("The Excel file does not contain a sheet named 'All'.")
        else:
            raise ValueError("The file is not an Excel file (.xls or .xlsx).")
    return None

def process_file(file, upload_folder):
    try:
        json_output = clean_and_save_file(file, upload_folder)
        if json_output:
            return {
                "success": True,
                "data": json.loads(json_output, object_pairs_hook=OrderedDict),
                "message": "File processed successfully",
            }
        return {"success": False, "message": "Invalid file"}
    except (ValueError, IOError, OSError, pd.errors.ParserError) as e:
        return {"success": False, "message": f"Error processing file: {str(e)}"}