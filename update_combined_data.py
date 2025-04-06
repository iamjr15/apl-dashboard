import pandas as pd
import numpy as np
import os
from datetime import datetime

# File paths
combined_data_file = "apl_historical_data.csv"
apl8_tier_list_file = "APL 8 Tier list - cis men and non cis.xlsx"
apl8_processed_file = "apl8_players_data.csv"
output_file = "apl_master_data.csv"

print("Loading data files...")
# Load the combined historical data
combined_df = pd.read_csv(combined_data_file)
print(f"Combined data: {combined_df.shape[0]} rows, {combined_df.shape[1]} columns")

# Load APL 8 processed data (for price categories and estimated prices)
apl8_df = pd.read_csv(apl8_processed_file)
print(f"APL 8 processed data: {apl8_df.shape[0]} rows, {apl8_df.shape[1]} columns")

# Create a copy of the combined data to update
updated_df = combined_df.copy()

# Step 1: Ensure 'In Latest Edition' flag is correctly set for all APL 8 players
updated_df['In Latest Edition'] = updated_df['Edition'] == 'APL 8.0'

# Step 2: Calculate historical price averages for each player
print("\nCalculating historical price averages...")
player_price_history = updated_df.groupby('Player Name').agg({
    'Price': ['mean', 'min', 'max', 'count'],
    'Tier': ['mean', 'min', 'max'],
    'Edition Count': 'first'
}).reset_index()

# Flatten the multi-level column names
player_price_history.columns = [
    '_'.join(col).strip('_') for col in player_price_history.columns.values
]

# Rename columns to be more descriptive
player_price_history = player_price_history.rename(columns={
    'Price_mean': 'Historical_Avg_Price',
    'Price_min': 'Historical_Min_Price',
    'Price_max': 'Historical_Max_Price',
    'Price_count': 'Price_Data_Points',
    'Tier_mean': 'Historical_Avg_Tier',
    'Tier_min': 'Historical_Min_Tier',
    'Tier_max': 'Historical_Max_Tier'
})

# Round the average values
player_price_history['Historical_Avg_Price'] = player_price_history['Historical_Avg_Price'].round(1)
player_price_history['Historical_Avg_Tier'] = player_price_history['Historical_Avg_Tier'].round(1)

# Step 3: Merge the historical averages back to the main dataframe
updated_df = pd.merge(
    updated_df,
    player_price_history[['Player Name', 'Historical_Avg_Price', 'Historical_Min_Price', 
                         'Historical_Max_Price', 'Historical_Avg_Tier']],
    on='Player Name',
    how='left'
)

# Step 4: Calculate price variance from historical average for current edition
updated_df['Price_Variance_From_Avg'] = updated_df.apply(
    lambda row: row['Price'] - row['Historical_Avg_Price'] if row['Edition Count'] > 1 else 0,
    axis=1
)

# Step 5: Create a tier movement indicator for returning players
def calculate_tier_movement(row):
    if row['Edition Count'] <= 1:
        return 0  # New player, no movement
    
    if row['Edition'] == 'APL 8.0':
        prev_tier = row['Historical_Avg_Tier']
        current_tier = row['Tier']
        # Negative means improvement (moved to lower tier number), positive means decline
        return current_tier - prev_tier
    return 0  # Not current edition

updated_df['Tier_Movement'] = updated_df.apply(calculate_tier_movement, axis=1)

# Step 6: Calculate a value proposition score
# For APL 8.0 players: higher score = better value based on tier and price history
def calculate_value_proposition(row):
    if row['Edition'] != 'APL 8.0':
        return None
    
    # Base score from Value Rating
    base_score = row['Value Rating']
    
    # Adjust for tier movement
    tier_factor = 1.0
    if row['Tier_Movement'] < 0:  # Improved tier
        tier_factor = 1.2  # Bonus for improving
    elif row['Tier_Movement'] > 0:  # Declined tier
        tier_factor = 0.8  # Penalty for declining
    
    # Adjust for price variance
    price_factor = 1.0
    if row['Edition Count'] > 1:
        if row['Price_Variance_From_Avg'] < 0:  # Price lower than historical average
            price_factor = 1.2  # Bonus for being cheaper
        elif row['Price_Variance_From_Avg'] > 0:  # Price higher than historical average
            price_factor = 0.8  # Penalty for being more expensive
    
    # Calculate final score and round to 2 decimals
    value_prop = base_score * tier_factor * price_factor
    return round(value_prop, 2)

updated_df['Value_Proposition'] = updated_df.apply(calculate_value_proposition, axis=1)

# Step 7: Add a column indicating whether the player is a tier top (in top 3 of their tier)
tier_rankings = updated_df[updated_df['Edition'] == 'APL 8.0'].groupby('Tier')['Ranking'].min().reset_index()
tier_rankings = tier_rankings.rename(columns={'Ranking': 'Tier_Min_Ranking'})
updated_df = pd.merge(updated_df, tier_rankings, on='Tier', how='left')
updated_df['Is_Tier_Top'] = updated_df.apply(
    lambda row: row['Ranking'] <= row['Tier_Min_Ranking'] + 2 if row['Edition'] == 'APL 8.0' else False,
    axis=1
)

# Step 8: Add export metadata
updated_df['Export_Date'] = datetime.now().strftime('%Y-%m-%d')
updated_df['Data_Version'] = '1.0'

# Step 9: Create a recommended price column for APL 8 players
def recommend_price(row):
    if row['Edition'] != 'APL 8.0':
        return None
    
    base_price = row['Price']
    
    # Adjust price based on historical data
    if row['Edition Count'] > 1:
        # Blend current price with historical average
        historical_weight = min(0.3, 0.1 * row['Edition Count'])  # Cap at 30% influence
        current_weight = 1 - historical_weight
        blended_price = (current_weight * base_price) + (historical_weight * row['Historical_Avg_Price'])
        
        # Adjust for tier movement
        if row['Tier_Movement'] < 0:  # Improved tier (moved to lower number)
            tier_bonus = abs(row['Tier_Movement']) * 5  # 5% increase per tier improvement
            blended_price *= (1 + tier_bonus/100)
        elif row['Tier_Movement'] > 0:  # Declined tier (moved to higher number)
            tier_penalty = row['Tier_Movement'] * 5  # 5% decrease per tier decline
            blended_price *= (1 - tier_penalty/100)
        
        # Round to nearest whole number
        return round(blended_price)
    
    # For new players, just use the current price
    return base_price

updated_df['Recommended_Price'] = updated_df.apply(recommend_price, axis=1)

# Step 10: Save the updated data
updated_df.to_csv(output_file, index=False)

print(f"Updated data saved to {output_file}")
print(f"Final data shape: {updated_df.shape[0]} rows, {updated_df.shape[1]} columns")

# Display summary statistics for APL 8 players
apl8_players = updated_df[updated_df['Edition'] == 'APL 8.0']
print(f"\nAPL 8.0 players: {len(apl8_players)}")
print(f"Players with historical data: {len(apl8_players[apl8_players['Edition Count'] > 1])}")

# Show distribution of Value Proposition scores for APL 8 players
value_prop_stats = apl8_players['Value_Proposition'].describe()
print("\nValue Proposition Score Statistics:")
print(f"Min: {value_prop_stats['min']:.2f}")
print(f"Max: {value_prop_stats['max']:.2f}")
print(f"Mean: {value_prop_stats['mean']:.2f}")
print(f"25th Percentile: {value_prop_stats['25%']:.2f}")
print(f"Median: {value_prop_stats['50%']:.2f}")
print(f"75th Percentile: {value_prop_stats['75%']:.2f}")

# Show top 10 value proposition players
print("\nTop 10 players by Value Proposition Score:")
top_value_players = apl8_players.sort_values('Value_Proposition', ascending=False).head(10)
for i, (_, player) in enumerate(top_value_players.iterrows(), 1):
    print(f"{i}. {player['Player Name']} (Tier {int(player['Tier'])}) - Value: {player['Value_Proposition']:.2f}, Rec. Price: {player['Recommended_Price']}")

# Show players with significant price changes from their historical average
print("\nPlayers with significant price changes from historical average:")
significant_change = apl8_players[abs(apl8_players['Price_Variance_From_Avg']) > 10].sort_values('Price_Variance_From_Avg')
for i, (_, player) in enumerate(significant_change.iterrows(), 1):
    direction = "increase" if player['Price_Variance_From_Avg'] > 0 else "decrease"
    print(f"{i}. {player['Player Name']} - {abs(player['Price_Variance_From_Avg']):.1f} {direction} from historical avg of {player['Historical_Avg_Price']:.1f}") 