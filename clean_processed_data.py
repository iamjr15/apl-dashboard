import pandas as pd
import numpy as np

# Read the processed data
df = pd.read_csv("processed_apl_data.csv")
print(f"Original data: {df.shape[0]} rows, {df.shape[1]} columns")

# ---- Data Cleaning ----

# 1. Handle missing player names
# There are 30 rows with missing player names - we'll filter these out
df_clean = df.dropna(subset=['Player Name'])
print(f"After removing rows with missing player names: {df_clean.shape[0]} rows")

# 2. Fix inconsistent gender values - standardize the format
# Standardize to: 'Man', 'Non-Cis Man', 'Woman', 'Non-Binary'
gender_mapping = {
    'Man': 'Man',
    'Non-Cis Man': 'Non-Cis',  # Simplify to just 'Non-Cis'
    'Non-Cis': 'Non-Cis'
}
df_clean['Gender'] = df_clean['Gender'].map(gender_mapping).fillna('Unknown')

# 3. Standardize position formats
# Remove 'Unknown' positions and standardize the position names
df_clean['Position'] = df_clean['Position'].apply(
    lambda x: "Unknown" if x == "Unknown" else ", ".join(sorted([p.strip().title() for p in x.split(',')]))
)

# Create a list of primary positions based on the positions played
def get_primary_position(pos_str):
    if pos_str == "Unknown":
        return "Unknown"
    
    positions = [p.strip() for p in pos_str.split(',')]
    # Define position priority: Goalkeeper, Defender, Midfielder, Attacker
    priority = {'Goalkeeper': 1, 'Defender': 2, 'Midfielder': 3, 'Attacker': 4}
    
    # Sort positions by priority
    sorted_positions = sorted(positions, key=lambda p: priority.get(p, 5))
    if sorted_positions:
        return sorted_positions[0]
    return "Unknown"

# Add primary position column
df_clean['Primary Position'] = df_clean['Position'].apply(get_primary_position)

# 4. Clean team names
# Remove special characters and standardize
df_clean['Team'] = df_clean['Team'].apply(
    lambda x: x.strip() if x != "Unknown" else x
)

# 5. Add a new column for price category
def get_price_category(price):
    if price == 0:
        return "N/A"
    elif price < 10:
        return "Low"
    elif price < 30:
        return "Medium"
    elif price < 60:
        return "High"
    else:
        return "Premium"

df_clean['Price Category'] = df_clean['Price'].apply(get_price_category)

# 6. Create a player value metric
# Formula: Value = Tier-based multiplier / Price
# Tier 1: 4x, Tier 2: 3x, Tier 3: 2x, Tier 4: 1x
def calculate_value(row):
    if row['Price'] == 0:
        return 0
    
    tier_multiplier = 5 - row['Tier']  # 4 for Tier 1, 3 for Tier 2, etc.
    return round((tier_multiplier * 10) / row['Price'], 2)

df_clean['Value Rating'] = df_clean.apply(calculate_value, axis=1)

# 7. Add a player ID column for easier reference
df_clean['Player ID'] = range(1, len(df_clean) + 1)

# 8. Round Price to integers (assuming these are whole number prices)
df_clean['Price'] = df_clean['Price'].round().astype(int)

# 9. Ensure proper column order
columns_order = [
    'Player ID', 'Player Name', 'Team', 'Position', 'Primary Position', 
    'Gender', 'Price', 'Price Category', 'Tier', 'Value Rating', 'Edition'
]
df_clean = df_clean[columns_order]

# Save the cleaned data
output_file = "apl_data_cleaned.csv"
df_clean.to_csv(output_file, index=False)

print(f"\nCleaning complete! Data saved to {output_file}")
print(f"Cleaned data: {df_clean.shape[0]} rows, {df_clean.shape[1]} columns")

# Print a sample of the cleaned data
print("\nSample of cleaned data:")
print(df_clean.head())

# Print summary statistics
print("\nPlayers by Gender:")
print(df_clean['Gender'].value_counts())

print("\nPlayers by Primary Position:")
print(df_clean['Primary Position'].value_counts())

print("\nPlayers by Price Category:")
print(df_clean['Price Category'].value_counts())

print("\nPlayers by Tier:")
print(df_clean['Tier'].value_counts().sort_index()) 