import pandas as pd
import numpy as np

# Read the APL 8 tier list
file_path = "APL 8 Tier list - cis men and non cis.xlsx"

try:
    # First, list all sheets in the file
    xl = pd.ExcelFile(file_path)
    print(f"Sheets in the Excel file: {xl.sheet_names}")
    
    # Examine each sheet
    for sheet_name in xl.sheet_names:
        print(f"\n{'='*80}")
        print(f"Examining sheet: {sheet_name}")
        print(f"{'='*80}")
        
        df = pd.read_excel(file_path, sheet_name=sheet_name)
        
        # Basic info
        print(f"Shape: {df.shape}")
        print("\nFirst 10 rows:")
        print(df.head(10))
        
        # Column names
        print("\nColumn names:")
        for col in df.columns:
            print(f"  - {col}")
        
        # Check for missing values
        missing = df.isnull().sum()
        if missing.sum() > 0:
            print("\nMissing values per column:")
            for col, count in missing.items():
                if count > 0:
                    print(f"  - {col}: {count}")
                    
        # Try to understand the structure
        print("\nUnique values in select columns:")
        for col in df.columns[:10]:  # First 10 columns for brevity
            if df[col].dtype == 'object':  # Only for string/categorical columns
                unique_vals = df[col].dropna().unique()
                if len(unique_vals) < 20:  # Only show if not too many values
                    print(f"  - {col}: {unique_vals}")
        
except Exception as e:
    print(f"Error examining file: {str(e)}") 