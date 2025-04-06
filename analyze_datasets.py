import pandas as pd
import numpy as np

def analyze_dataset(file_path, name):
    """
    Analyze a dataset and print key information
    """
    print(f"\n{'='*80}")
    print(f"Analyzing {name} dataset: {file_path}")
    print(f"{'='*80}")
    
    # Load the data
    df = pd.read_csv(file_path)
    
    # Basic info
    print(f"\nShape: {df.shape} (rows, columns)")
    
    # Column names and data types
    print("\nColumns and data types:")
    for col, dtype in df.dtypes.items():
        print(f"  - {col}: {dtype}")
    
    # Missing values
    missing = df.isnull().sum()
    if missing.sum() > 0:
        print("\nMissing values per column:")
        for col, count in missing.items():
            if count > 0:
                print(f"  - {col}: {count} ({count/len(df):.1%})")
    
    # Basic stats for numeric columns
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    if len(numeric_cols) > 0:
        print("\nNumeric column statistics:")
        for col in numeric_cols:
            if col in df.columns:
                stats = df[col].describe()
                print(f"  - {col}:")
                print(f"    Min: {stats['min']}, Max: {stats['max']}, Mean: {stats['mean']:.2f}, Median: {stats['50%']:.2f}")
    
    # Categorical columns
    cat_cols = df.select_dtypes(include=['object']).columns
    if len(cat_cols) > 0:
        print("\nCategorical column values:")
        for col in cat_cols:
            unique_vals = df[col].nunique()
            print(f"  - {col}: {unique_vals} unique values")
            if unique_vals < 20:  # Only show if not too many values
                # Drop NaN values before sorting to avoid type error
                unique_non_null = df[col].dropna().unique()
                print(f"    Values: {sorted(unique_non_null)}")
    
    return df

# Analyze both datasets
apl_67_file = "apl_data_cleaned.csv"
apl_8_file = "apl8_players_data.csv"

# Analyze APL 6 & 7 data
apl67_df = analyze_dataset(apl_67_file, "APL 6 & 7")

# Analyze APL 8 data
apl8_df = analyze_dataset(apl_8_file, "APL 8")

# Compare columns between datasets
print("\n" + "="*80)
print("Comparing columns between datasets")
print("="*80)

apl67_cols = set(apl67_df.columns)
apl8_cols = set(apl8_df.columns)

# Columns in both datasets
common_cols = apl67_cols.intersection(apl8_cols)
print(f"\nColumns in both datasets ({len(common_cols)}):")
for col in sorted(common_cols):
    print(f"  - {col}")

# Columns only in APL 6 & 7
only_apl67_cols = apl67_cols - apl8_cols
print(f"\nColumns only in APL 6 & 7 ({len(only_apl67_cols)}):")
for col in sorted(only_apl67_cols):
    print(f"  - {col}")

# Columns only in APL 8
only_apl8_cols = apl8_cols - apl67_cols
print(f"\nColumns only in APL 8 ({len(only_apl8_cols)}):")
for col in sorted(only_apl8_cols):
    print(f"  - {col}")

# Check for player overlap
apl67_players = set(apl67_df['Player Name'].dropna())
apl8_players = set(apl8_df['Player Name'].dropna())

common_players = apl67_players.intersection(apl8_players)
print(f"\nPlayers in both datasets ({len(common_players)}):")
if common_players:
    print(f"  {sorted(list(common_players))[:10]} {'...' if len(common_players) > 10 else ''}")
else:
    print("  No common players found between datasets")

# Suggestion for combining the datasets
print("\n" + "="*80)
print("Suggested approach for combining datasets")
print("="*80)

print("""
Based on the analysis, here's a suggested approach to combine the datasets:

1. Identify common columns to preserve (Player Name, Gender, Tier, etc.)
2. Handle columns that are unique to each dataset
   - For APL 6 & 7 unique columns: Add to combined dataset with NaN for APL 8 rows
   - For APL 8 unique columns: Add to combined dataset with NaN for APL 6 & 7 rows
3. For common players, ensure consistent data and track their history across editions
4. Add an 'Edition' column to identify which APL edition each row belongs to
5. Add derived columns like:
   - 'Edition Count': Number of editions a player has participated in
   - 'Price Trend': Change in price between editions
   - 'In Latest Edition': Flag to indicate if player is in the latest edition (APL 8)

This approach preserves all data while adding valuable historical information.
""") 