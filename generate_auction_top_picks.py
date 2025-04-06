import pandas as pd
import numpy as np
from datetime import datetime

# Load the auction guide
auction_guide_file = "apl8_auction_guide.csv"
output_file = "apl8_auction_top_picks.csv"

print(f"Loading auction guide from {auction_guide_file}...")
df = pd.read_csv(auction_guide_file)

# Create a function to calculate an overall auction score
def calculate_auction_score(row):
    # Base score from value proposition
    base_score = row['Value_Score'] * 5  # Scale up for better differentiation
    
    # Adjust based on tier (Tier 1 most valuable, Tier 4 least)
    tier_factor = (5 - row['Tier']) / 4  # 1.0 for Tier 1, 0.25 for Tier 4
    
    # Adjust for historical data (returning players get bonus)
    history_factor = 1.0
    if row['APL_Editions'] > 1:
        history_factor = 1.1  # 10% bonus for returning players
    
    # Adjust for tier top players
    if row['Top_In_Tier']:
        history_factor *= 1.2  # 20% bonus for top in tier
    
    # Calculate final score and round to 2 decimals
    final_score = base_score * tier_factor * history_factor
    return round(final_score, 1)

# Add auction score column
df['Auction_Score'] = df.apply(calculate_auction_score, axis=1)

# Group players by position
position_groups = {}
if 'Primary_Position' in df.columns:
    # Standardize positions for better grouping
    position_map = {
        'Unknown': 'Other',
        'Reserve Player': 'Reserve',
        'Star Player': 'Star Player',
        'Ball Playing Center Back': 'Defender',
        'Center Back (Sweeper)': 'Defender',
        'Box-to-Box Midfielder': 'Midfielder',
        'Forward/Number 9/CAN': 'Forward',
        'Goalkeeper': 'Goalkeeper'
    }
    
    df['Position_Group'] = df['Primary_Position'].map(position_map)
    position_groups = df.groupby('Position_Group')

# Create the top picks dataframe
top_picks = []

# Overall top 20 players by auction score
top_overall = df.sort_values('Auction_Score', ascending=False).head(20)
top_overall['Category'] = 'Top Overall'
top_picks.append(top_overall)

# Top 5 players by tier
for tier in sorted(df['Tier'].unique()):
    tier_label = f'Tier {int(tier)}'
    top_tier = df[df['Tier'] == tier].sort_values('Auction_Score', ascending=False).head(5)
    top_tier['Category'] = tier_label
    top_picks.append(top_tier)

# Top 5 players by position (if position data is available)
if position_groups:
    for position, group in position_groups:
        if position != 'Other' and len(group) > 0:  # Skip 'Other' and empty groups
            top_position = group.sort_values('Auction_Score', ascending=False).head(5)
            top_position['Category'] = f'Top {position}'
            top_picks.append(top_position)

# Best value picks
best_value = df[df['Value_Score'] > 1.5].sort_values('Auction_Score', ascending=False).head(10)
best_value['Category'] = 'Best Value'
top_picks.append(best_value)

# Combine all categories
combined_picks = pd.concat(top_picks)

# Make sure we have a balanced selection (may have duplicate players across categories)
final_picks = combined_picks.drop_duplicates(subset=['Player', 'Category'])

# Add selection reason field
def selection_reason(row):
    category = row['Category']
    if category == 'Top Overall':
        return "Among top 20 players by overall score"
    elif category.startswith('Tier'):
        return f"Top 5 in {category}"
    elif category.startswith('Top '):
        position = category.replace('Top ', '')
        return f"Top 5 {position} players"
    elif category == 'Best Value':
        return "Exceptional value rating (>1.5)"
    else:
        return ""

final_picks['Selection_Reason'] = final_picks.apply(selection_reason, axis=1)

# Simplify and reorder columns
columns_to_keep = [
    'Player', 'Gender', 'Tier', 'Position_Group', 'Primary_Position',
    'Price', 'Value_Score', 'Auction_Score', 'Recommended',
    'Historical_Avg', 'APL_Editions', 'Bidding_Strategy',
    'Category', 'Selection_Reason'
]

# Use only columns that exist in the dataframe
final_columns = [col for col in columns_to_keep if col in final_picks.columns]
final_picks = final_picks[final_columns]

# Sort by Category then Auction_Score
final_picks = final_picks.sort_values(['Category', 'Auction_Score'], ascending=[True, False])

# Save to CSV
final_picks.to_csv(output_file, index=False)

print(f"Top picks saved to {output_file}")
print(f"Total players in top picks: {len(final_picks)}")

# Display summary
print("\nPlayers by category:")
category_counts = final_picks['Category'].value_counts()
for category, count in category_counts.items():
    print(f"  - {category}: {count} players")

# Display top 5 highest-scoring players
print("\nTop 5 highest scoring players overall:")
top_5 = final_picks.sort_values('Auction_Score', ascending=False).head(5)
for i, (_, player) in enumerate(top_5.iterrows(), 1):
    print(f"{i}. {player['Player']} (Tier {int(player['Tier'])}) - Score: {player['Auction_Score']}, Value: {player['Value_Score']:.2f}, Rec: {player['Recommended']}")
    
# Display best value players
print("\nTop 5 best value players:")
value_5 = final_picks.sort_values('Value_Score', ascending=False).head(5)
for i, (_, player) in enumerate(value_5.iterrows(), 1):
    print(f"{i}. {player['Player']} (Tier {int(player['Tier'])}) - Value: {player['Value_Score']:.2f}, Score: {player['Auction_Score']}, Rec: {player['Recommended']}")
    
# Display example bidding strategies
print("\nExample bidding strategies:")
strategies = final_picks.sample(min(5, len(final_picks)))
for i, (_, player) in enumerate(strategies.iterrows(), 1):
    print(f"{i}. {player['Player']} (Tier {int(player['Tier'])})")
    print(f"   Strategy: {player['Bidding_Strategy']}") 