import pandas as pd
import numpy as np

def combine_apl_data():
    """
    Combine APL 6/7 and APL 8 datasets into a comprehensive historical dataset
    """
    # Load the datasets
    apl67_file = "apl_data_cleaned.csv"
    apl8_file = "apl8_players_data.csv"
    
    print("Loading APL 6 & 7 data...")
    apl67_df = pd.read_csv(apl67_file)
    
    print("Loading APL 8 data...")
    apl8_df = pd.read_csv(apl8_file)
    
    print(f"APL 6/7 data: {apl67_df.shape[0]} rows, {apl67_df.shape[1]} columns")
    print(f"APL 8 data: {apl8_df.shape[0]} rows, {apl8_df.shape[1]} columns")
    
    # Step 1: Standardize column names and data types
    # Rename 'Estimated Price' in APL 8 to 'Price' to match APL 6/7
    apl8_df = apl8_df.rename(columns={'Estimated Price': 'Price'})
    
    # Step 2: Handle APL 8 specific columns
    if 'Primary Position' not in apl8_df.columns:
        # Use Position as Primary Position for APL 8
        apl8_df['Primary Position'] = apl8_df['Position']
    
    if 'Team' not in apl8_df.columns:
        # Add Team column for APL 8 (will be filled in later for recurring players)
        apl8_df['Team'] = 'Unknown'
    
    # Step 3: Calculate Value Rating for APL 8 players
    if 'Value Rating' not in apl8_df.columns:
        def calculate_value_rating(row):
            if row['Price'] == 0 or pd.isna(row['Price']):
                return 0
            tier_multiplier = 5 - row['Tier']
            return round((tier_multiplier * 10) / row['Price'], 2)
        
        apl8_df['Value Rating'] = apl8_df.apply(calculate_value_rating, axis=1)
    
    # Step 4: Add missing APL 8 specific columns to APL 6/7 data
    if 'Ranking' not in apl67_df.columns:
        apl67_df['Ranking'] = np.nan  # Will fill with tier-based rankings later
    
    # Step 5: Reset Player IDs to ensure they're unique across combined data
    apl8_df['Original_ID'] = apl8_df['Player ID']  # Preserve original IDs
    max_id_apl67 = apl67_df['Player ID'].max()
    apl8_df['Player ID'] = apl8_df['Player ID'] + max_id_apl67
    
    # Step 6: Create a standardized set of columns for both datasets
    common_columns = [
        'Player ID', 'Player Name', 'Gender', 'Team', 'Position', 'Primary Position',
        'Tier', 'Price', 'Price Category', 'Value Rating', 'Ranking', 'Edition'
    ]
    
    # Step 7: Combine the datasets
    # First ensure all common columns exist in both dataframes
    for col in common_columns:
        if col not in apl67_df.columns:
            apl67_df[col] = np.nan
        if col not in apl8_df.columns:
            apl8_df[col] = np.nan
    
    combined_df = pd.concat([apl67_df[common_columns], apl8_df[common_columns]], ignore_index=True)
    
    # Step 8: Enhance the dataset with additional useful columns
    
    # Add a flag for the latest edition
    combined_df['In Latest Edition'] = (combined_df['Edition'] == 'APL 8.0')
    
    # Count editions per player
    edition_count = combined_df.groupby('Player Name')['Edition'].nunique().reset_index()
    edition_count.columns = ['Player Name', 'Edition Count']
    combined_df = pd.merge(combined_df, edition_count, on='Player Name', how='left')
    
    # Step 9: Add position consistency for recurring players
    # For players who appear in both APL 6/7 and APL 8, use the most recent position info
    recurring_players = combined_df[combined_df['Edition Count'] > 1]['Player Name'].unique()
    
    for player in recurring_players:
        # Get the most recent position data (APL 8.0)
        recent_data = combined_df[(combined_df['Player Name'] == player) & 
                                  (combined_df['Edition'] == 'APL 8.0')]
        
        if not recent_data.empty and not pd.isna(recent_data['Position'].iloc[0]):
            position = recent_data['Position'].iloc[0]
            primary_position = recent_data['Primary Position'].iloc[0]
            
            # Update older entries with the most recent position information
            # Only if the older entries have "Unknown" positions
            older_entries = combined_df[(combined_df['Player Name'] == player) & 
                                        (combined_df['Edition'] != 'APL 8.0') &
                                        (combined_df['Position'] == 'Unknown')]
            
            if not older_entries.empty:
                combined_df.loc[older_entries.index, 'Position'] = position
                combined_df.loc[older_entries.index, 'Primary Position'] = primary_position
    
    # Step 10: Calculate price trends for recurring players
    # Create a pivot table for prices across editions
    price_pivot = combined_df.pivot_table(
        index='Player Name',
        columns='Edition',
        values='Price',
        aggfunc='first'
    ).reset_index()
    
    # Calculate price difference between editions
    if 'APL 8.0' in price_pivot.columns and 'APL 7.0' in price_pivot.columns:
        price_pivot['Price Trend'] = price_pivot['APL 8.0'] - price_pivot['APL 7.0']
    elif 'APL 8.0' in price_pivot.columns and 'APL 6.0' in price_pivot.columns:
        price_pivot['Price Trend'] = price_pivot['APL 8.0'] - price_pivot['APL 6.0']
    else:
        price_pivot['Price Trend'] = 0
    
    # Merge price trend back to main dataframe
    price_trend_df = price_pivot[['Player Name', 'Price Trend']].copy()
    combined_df = pd.merge(combined_df, price_trend_df, on='Player Name', how='left')
    combined_df['Price Trend'] = combined_df['Price Trend'].fillna(0)
    
    # Step 11: Add additional metrics like price/tier ratio
    combined_df['Price Tier Ratio'] = combined_df['Price'] / combined_df['Tier']
    
    # Step 12: Fill any remaining NaN values
    combined_df['Team'] = combined_df['Team'].fillna('Unknown')
    combined_df['Position'] = combined_df['Position'].fillna('Unknown')
    combined_df['Primary Position'] = combined_df['Primary Position'].fillna('Unknown')
    combined_df['Price Trend'] = combined_df['Price Trend'].fillna(0)
    combined_df['Price Tier Ratio'] = combined_df['Price Tier Ratio'].fillna(0)
    
    # Step 13: Save the combined data
    output_file = "apl_historical_data.csv"
    combined_df.to_csv(output_file, index=False)
    
    # Print summary statistics
    print(f"\nCombined data saved to {output_file}")
    print(f"Total rows: {combined_df.shape[0]}")
    print(f"Total columns: {combined_df.shape[1]}")
    print(f"Unique players: {combined_df['Player Name'].nunique()}")
    
    print("\nPlayers by Edition:")
    print(combined_df['Edition'].value_counts())
    
    print("\nPlayers in Multiple Editions:")
    print(combined_df['Edition Count'].value_counts())
    
    # Return the combined dataframe
    return combined_df

if __name__ == "__main__":
    # Combine the data
    combined_df = combine_apl_data()
    
    # Display the first few rows of the combined data
    print("\nSample of combined data:")
    print(combined_df.head()) 