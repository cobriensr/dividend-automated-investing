# pylint: disable = missing-module-docstring, missing-function-docstring, missing-final-newline, trailing-whitespace, line-too-long

import os
import pandas as pd
from werkzeug.utils import secure_filename

def clean_and_save_file(file, upload_folder):
    if file and file.filename:
        filename = secure_filename(file.filename)
        file_path = os.path.join(upload_folder, filename)
        file.save(file_path)
        
        # if xls or xlsx file
        if filename.endswith(".xls") or filename.endswith(".xlsx"):
            # load into pandas dataframe
            xls = pd.ExcelFile(file_path)
            # if all in sheet names
            if "All" in xls.sheet_names:
                df = pd.read_excel(xls, sheet_name="All")
                print(f"DataFrame shape: {df.shape}")
                print(f"DataFrame head:\n{df.head()}")
            else:
                raise ValueError("The Excel file does not contain a sheet named 'All'.")