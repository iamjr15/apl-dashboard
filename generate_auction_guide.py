import pandas as pd
import numpy as np
from datetime import datetime

# File paths
master_data_file = "apl_master_data.csv"
output_file = "apl8_auction_guide.csv"

print("Loading master data...")
df = pd.read_csv(master_data_file)
print(f"Master data: {df.shape[0]} rows, {df.shape[1]} columns")

# Focus only on APL 8.0 players
apl8_players = df[df['Edition'] == 'APL 8.0'].copy()
print(f"APL 8.0 players: {apl8_players.shape[0]}")

# Create a simplified auction guide dataset with the most relevant columns
auction_guide = apl8_players[[
    'Player Name', 'Gender', 'Tier', 'Position', 'Primary Position', 
    'Price', 'Price Category', 'Value Rating', 'Ranking', 
    'Historical_Avg_Price', 'Price_Variance_From_Avg', 'Tier_Movement',
    'Value_Proposition', 'Is_Tier_Top', 'Recommended_Price', 'Edition Count'
]].copy()

# Add additional auction-specific information
auction_guide['Auction_Priority'] = auction_guide.apply(
    lambda row: 'High' if row['Is_Tier_Top'] or row['Value_Proposition'] > 1.5 else 
                ('Medium' if row['Value_Proposition'] > 1.0 else 'Low'),
    axis=1
)

# Generate bidding strategy
def bidding_strategy(row):
    # Base strategy using recommended price
    rec_price = row['Recommended_Price']
    min_bid = max(5, round(rec_price * 0.8))  # Minimum 5, or 80% of recommended
    max_bid = round(rec_price * 1.2)  # 20% over recommended
    
    strategy = f"Target: {rec_price}, Range: {min_bid}-{max_bid}"
    
    # Add special notes based on various factors
    notes = []
    
    # Check if player was in previous editions
    if row['Edition Count'] > 1:
        if row['Tier_Movement'] < 0:
            notes.append("Improved tier")
        elif row['Tier_Movement'] > 0:
            notes.append("Declined tier")
            
        if row['Price_Variance_From_Avg'] < -10:
            notes.append("Significantly cheaper than history")
        elif row['Price_Variance_From_Avg'] > 10:
            notes.append("Significantly more expensive than history")
    
    # Check value proposition
    if row['Value_Proposition'] > 1.5:
        notes.append("Excellent value")
    elif row['Value_Proposition'] < 0.5:
        notes.append("Poor value")
    
    # Top players in tier
    if row['Is_Tier_Top']:
        notes.append("Top in tier")
    
    # Add notes if any
    if notes:
        strategy += f" - Notes: {', '.join(notes)}"
    
    return strategy

auction_guide['Bidding_Strategy'] = auction_guide.apply(bidding_strategy, axis=1)

# Reorder and rename columns for clarity
auction_guide = auction_guide.rename(columns={
    'Player Name': 'Player',
    'Position': 'All_Positions',
    'Primary Position': 'Primary_Position',
    'Historical_Avg_Price': 'Historical_Avg',
    'Price_Variance_From_Avg': 'Price_Variance',
    'Value_Proposition': 'Value_Score',
    'Is_Tier_Top': 'Top_In_Tier',
    'Recommended_Price': 'Recommended',
    'Edition Count': 'APL_Editions'
})

# Sort by Tier and then by Value Score (descending)
auction_guide = auction_guide.sort_values(['Tier', 'Value_Score'], ascending=[True, False])

# Format the numeric columns
auction_guide['Historical_Avg'] = auction_guide['Historical_Avg'].round(1)
auction_guide['Price_Variance'] = auction_guide['Price_Variance'].round(1)
auction_guide['Value_Score'] = auction_guide['Value_Score'].round(2)
auction_guide['Tier_Movement'] = auction_guide['Tier_Movement'].round(1)

# Add metadata
auction_guide['Generated'] = datetime.now().strftime('%Y-%m-%d')
auction_guide['APL_Edition'] = 'APL 8.0'

# Save to CSV
auction_guide.to_csv(output_file, index=False)

print(f"Auction guide saved to {output_file}")
print(f"Auction guide shape: {auction_guide.shape[0]} rows, {auction_guide.shape[1]} columns")

# Display summary statistics
print("\nPlayer distribution by tier:")
print(auction_guide['Tier'].value_counts().sort_index())

print("\nPlayer distribution by auction priority:")
print(auction_guide['Auction_Priority'].value_counts())

print("\nPlayer distribution by gender:")
print(auction_guide['Gender'].value_counts())

print("\nPlayer distribution by primary position:")
print(auction_guide['Primary_Position'].value_counts())

print("\nTop 15 highest value players:")
top_value = auction_guide.sort_values('Value_Score', ascending=False).head(15)
for i, (_, player) in enumerate(top_value.iterrows(), 1):
    print(f"{i}. {player['Player']} (Tier {int(player['Tier'])}) - Value: {player['Value_Score']:.2f}, Rec: {player['Recommended']}")

print("\nTop 5 players in each tier:")
for tier in sorted(auction_guide['Tier'].unique()):
    print(f"\nTier {int(tier)}:")
    tier_players = auction_guide[auction_guide['Tier'] == tier].sort_values('Value_Score', ascending=False).head(5)
    for i, (_, player) in enumerate(tier_players.iterrows(), 1):
        print(f"{i}. {player['Player']} - Value: {player['Value_Score']:.2f}, Rec: {player['Recommended']}") 