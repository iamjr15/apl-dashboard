import pandas as pd
import numpy as np

# File paths
input_file = "apl_historical_data.csv"
output_file = "final_apl_data.csv"

print(f"Loading combined data from {input_file}...")
combined_df = pd.read_csv(input_file)

print(f"Original data shape: {combined_df.shape}")

# Perform any additional formatting or cleaning if needed
# For example, we could:
# 1. Round numeric values
combined_df['Value Rating'] = combined_df['Value Rating'].round(2)
combined_df['Price Tier Ratio'] = combined_df['Price Tier Ratio'].round(2)

# 2. Standardize text fields (convert to title case)
combined_df['Player Name'] = combined_df['Player Name'].str.strip()
combined_df['Team'] = combined_df['Team'].str.strip()

# 3. Ensure boolean columns are actually boolean type
combined_df['In Latest Edition'] = combined_df['In Latest Edition'].astype(bool)

# 4. Add a new column indicating data export date
from datetime import datetime
combined_df['Export Date'] = datetime.now().strftime('%Y-%m-%d')

# 5. Add a unique player identifier that stays consistent across editions
# Create a mapping of player names to unique IDs
unique_players = combined_df['Player Name'].unique()
player_id_map = {player: f"APL{i+1:04d}" for i, player in enumerate(sorted(unique_players))}
combined_df['Unique Player ID'] = combined_df['Player Name'].map(player_id_map)

# Save to the new file
combined_df.to_csv(output_file, index=False)

print(f"Data exported to {output_file}")
print(f"Final data shape: {combined_df.shape}")

# Display summary statistics
print("\nSummary Statistics:")
print(f"Total players: {combined_df['Player Name'].nunique()}")
print(f"Players in APL 6.0: {combined_df[combined_df['Edition'] == 'APL 6.0'].shape[0]}")
print(f"Players in APL 7.0: {combined_df[combined_df['Edition'] == 'APL 7.0'].shape[0]}")
print(f"Players in APL 8.0: {combined_df[combined_df['Edition'] == 'APL 8.0'].shape[0]}")
print(f"Players in multiple editions: {combined_df[combined_df['Edition Count'] > 1]['Player Name'].nunique()}") 