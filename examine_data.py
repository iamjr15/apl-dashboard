import pandas as pd
import os

# List of Excel files to examine
excel_files = ["APL 6.xlsx", "APL 7.0 data.xlsx"]

# Examine each file
for file in excel_files:
    print(f"\n{'='*50}")
    print(f"Examining {file}:")
    print(f"{'='*50}")
    
    try:
        # Try to read all sheets in the Excel file
        xl = pd.ExcelFile(file)
        for sheet_name in xl.sheet_names:
            print(f"\nSheet: {sheet_name}")
            df = pd.read_excel(file, sheet_name=sheet_name)
            
            # Print basic info
            print(f"Shape: {df.shape}")
            print("\nFirst 5 rows:")
            print(df.head())
            
            print("\nColumn names:")
            for col in df.columns:
                print(f"  - {col}")
            
            # Check for missing values
            missing_values = df.isnull().sum()
            if missing_values.sum() > 0:
                print("\nMissing values per column:")
                for col, count in missing_values.items():
                    if count > 0:
                        print(f"  - {col}: {count}")
    
    except Exception as e:
        print(f"Error processing {file}: {str(e)}") 