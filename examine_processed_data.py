import pandas as pd

# Read the processed data
df = pd.read_csv("processed_apl_data.csv")

# Show basic info
print("DataFrame Info:")
print(df.info())

print("\nFirst 10 rows:")
print(df.head(10))

print("\nColumn unique values:")
for col in df.columns:
    if col in ['Player Name', 'Price']:
        continue  # Skip columns with many unique values
    print(f"\n{col} unique values:")
    print(df[col].unique())

print("\nMissing values:")
print(df.isnull().sum())

print("\nPotential data quality issues:")
# Check for inconsistent gender values
print("\nGender values:")
print(df['Gender'].value_counts())

# Check for position format consistency
print("\nSample of Position values:")
print(df['Position'].value_counts().head(10))

# Check for issues with team names
print("\nSample of Team values:")
print(df['Team'].value_counts().head(10)) 