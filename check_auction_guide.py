import pandas as pd

# Load the auction guide
file_path = "apl8_auction_guide.csv"
df = pd.read_csv(file_path)

# Display basic info
print(f"File: {file_path}")
print(f"Shape: {df.shape[0]} rows, {df.shape[1]} columns")

# Display column names
print("\nColumns:")
for col in df.columns:
    print(f"  - {col}")

# Display first 5 rows
print("\nFirst 5 rows:")
print(df.head(5).to_string())

# Display some stats about high-value players
high_value = df[df['Value_Score'] > 1.5]
print(f"\nHigh value players (Value_Score > 1.5): {len(high_value)}")

# Display top 10 recommended buys (prioritizing value and tier)
print("\nTop 10 recommended buys:")
top_buys = df.sort_values(['Tier', 'Value_Score'], ascending=[True, False]).head(10)
for i, (_, player) in enumerate(top_buys.iterrows(), 1):
    print(f"{i}. {player['Player']} (Tier {int(player['Tier'])})")
    print(f"   Value: {player['Value_Score']:.2f}, Rec. Price: {player['Recommended']}")
    print(f"   Strategy: {player['Bidding_Strategy']}") 