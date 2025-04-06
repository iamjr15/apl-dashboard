import pandas as pd
import os
import numpy as np

# Define input files
apl6_file = "APL 6.xlsx"
apl7_file = "APL 7.0 data.xlsx"
output_file = "processed_apl_data.csv"

# Function to clean the positions played field
def clean_positions(pos):
    if isinstance(pos, str):
        # Remove brackets and quotes
        pos = pos.replace('[', '').replace(']', '').replace("'", "")
        # Return a comma-separated string of positions
        return pos
    return pos

# Process APL 6 data
def process_apl6():
    print("Processing APL 6 data...")
    
    # Dictionary to store dataframes from each tier
    tier_dfs = {}
    
    # Read each tier sheet
    for tier in range(1, 5):
        sheet_name = f"Tier {tier}"
        df = pd.read_excel(apl6_file, sheet_name=sheet_name)
        
        # Add tier number as a column (easier than extracting from sheet name)
        df['Tier'] = tier
        
        # Add edition column
        df['Edition'] = 'APL 6.0'
        
        # Store the dataframe
        tier_dfs[tier] = df
    
    # Concatenate all tier dataframes
    apl6_df = pd.concat(tier_dfs.values(), ignore_index=True)
    
    # Rename columns for consistency
    apl6_df = apl6_df.rename(columns={
        'Name': 'Player Name',
        'Team Name': 'Team',
        'Positions Played': 'Position'
    })
    
    # Select and reorder columns
    columns_to_keep = ['Player Name', 'Team', 'Position', 'Gender', 'Batch', 'Price', 'Tier', 'Edition']
    apl6_df = apl6_df[columns_to_keep]
    
    # Clean the positions played field
    apl6_df['Position'] = apl6_df['Position'].apply(clean_positions)
    
    return apl6_df

# Process APL 7 data
def process_apl7():
    print("Processing APL 7 data...")
    
    # First, let's try to get the team information from the "Final teams" sheet
    teams_df = pd.read_excel(apl7_file, sheet_name="Final teams", header=None)
    
    # Get the tier list data
    tier_df = pd.read_excel(apl7_file, sheet_name="APL 7 Tier List")
    
    # Extract tier information from APL 7 Tier List
    # This is more complex due to the structure of the sheet
    
    # Initialize a list to store player data
    players_data = []
    
    # Process Men tiers
    men_tier_cols = {
        1: "Men",           # Tier 1
        2: "Unnamed: 1",    # Tier 2
        3: "Unnamed: 7",    # Tier 3 (based on your data output)
        4: "Unnamed: 8"     # Tier 4
    }
    
    # Process Non-Cis Men tiers
    non_cis_tier_cols = {
        1: "Non-Cis Men",   # Tier 1
        2: "Unnamed: 6"     # Tier 2
    }
    
    # Extract tier data for men
    for tier, col_name in men_tier_cols.items():
        # Skip the header row (index 0)
        for player_name in tier_df[col_name].iloc[1:]:
            if pd.notna(player_name):
                players_data.append({
                    'Player Name': player_name,
                    'Gender': 'Man',
                    'Tier': tier,
                    'Edition': 'APL 7.0'
                })
    
    # Extract tier data for non-cis men
    for tier, col_name in non_cis_tier_cols.items():
        # Skip the header row (index 0)
        for player_name in tier_df[col_name].iloc[1:]:
            if pd.notna(player_name):
                players_data.append({
                    'Player Name': player_name,
                    'Gender': 'Non-Cis',
                    'Tier': tier,
                    'Edition': 'APL 7.0'
                })
    
    # Create DataFrame from the players data
    apl7_df = pd.DataFrame(players_data)
    
    # Try to extract team and price information from the Final teams sheet
    # This is complex and may need adjustment based on the exact structure
    
    # Add placeholder columns for data we couldn't extract reliably
    apl7_df['Team'] = np.nan
    apl7_df['Price'] = np.nan
    apl7_df['Position'] = np.nan
    apl7_df['Batch'] = np.nan
    
    # The team data is in a complex format and would need more detailed parsing
    # For now, we'll leave it with placeholders
    
    return apl7_df

# Main processing function
def process_all_data():
    # Process each APL edition
    apl6_df = process_apl6()
    apl7_df = process_apl7()
    
    # Combine the dataframes
    combined_df = pd.concat([apl6_df, apl7_df], ignore_index=True)
    
    # Additional cleaning
    # Fill NaN values appropriately
    combined_df['Team'] = combined_df['Team'].fillna('Unknown')
    combined_df['Position'] = combined_df['Position'].fillna('Unknown')
    combined_df['Batch'] = combined_df['Batch'].fillna('Unknown')
    
    # Convert Price to numeric, replacing NaN with 0
    combined_df['Price'] = pd.to_numeric(combined_df['Price'], errors='coerce').fillna(0)
    
    # Ensure Tier is an integer
    combined_df['Tier'] = combined_df['Tier'].astype(int)
    
    # Clean player names (remove extra whitespace)
    combined_df['Player Name'] = combined_df['Player Name'].str.strip()
    
    # Clean team names
    combined_df['Team'] = combined_df['Team'].str.strip()
    
    # Save to CSV
    combined_df.to_csv(output_file, index=False)
    print(f"Data processing complete. Output saved to {output_file}")
    
    # Return the dataframe for inspection
    return combined_df

# Run the processing
if __name__ == "__main__":
    processed_data = process_all_data()
    
    # Display summary statistics
    print("\nSummary statistics:")
    print(f"Total players: {len(processed_data)}")
    print(f"APL 6.0 players: {len(processed_data[processed_data['Edition'] == 'APL 6.0'])}")
    print(f"APL 7.0 players: {len(processed_data[processed_data['Edition'] == 'APL 7.0'])}")
    
    print("\nPlayers by Tier:")
    tier_counts = processed_data['Tier'].value_counts().sort_index()
    for tier, count in tier_counts.items():
        print(f"Tier {tier}: {count} players")
    
    print("\nPlayers by Gender:")
    for gender, count in processed_data['Gender'].value_counts().items():
        print(f"{gender}: {count} players")
    
    # Display the first few rows of the processed data
    print("\nSample of processed data:")
    print(processed_data.head()) 