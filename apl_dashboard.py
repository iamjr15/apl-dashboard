import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

# Set page config
st.set_page_config(
    page_title="APL Auction Dashboard",
    page_icon="⚽",
    layout="wide"
)

# Load the processed data
@st.cache_data
def load_data():
    return pd.read_csv("processed_apl_data.csv")

# Main function
def main():
    # Title and description
    st.title("⚽ APL Player Auction Dashboard")
    st.markdown("""
    This dashboard provides insights into the APL (Ashoka Premier League) football auction data.
    Analyze player prices, tiers, positions, and more across different editions of the tournament.
    """)
    
    # Load the data
    df = load_data()
    
    # Add a sidebar for filtering
    st.sidebar.title("Filters")
    
    # Filter by Edition
    editions = ['All'] + sorted(df['Edition'].unique().tolist())
    selected_edition = st.sidebar.selectbox("Select Edition", editions)
    
    # Filter by Tier
    tiers = ['All'] + sorted(df['Tier'].unique().tolist())
    selected_tier = st.sidebar.selectbox("Select Tier", tiers)
    
    # Filter by Gender
    genders = ['All'] + sorted(df['Gender'].unique().tolist())
    selected_gender = st.sidebar.selectbox("Select Gender", genders)
    
    # Filter by Team (only show if not 'All' edition)
    if selected_edition != 'All':
        teams = ['All'] + sorted(df[df['Edition'] == selected_edition]['Team'].unique().tolist())
        selected_team = st.sidebar.selectbox("Select Team", teams)
    else:
        teams = ['All'] + sorted(df['Team'].unique().tolist())
        selected_team = st.sidebar.selectbox("Select Team", teams)
    
    # Apply filters to the dataframe
    filtered_df = df.copy()
    
    if selected_edition != 'All':
        filtered_df = filtered_df[filtered_df['Edition'] == selected_edition]
    
    if selected_tier != 'All':
        filtered_df = filtered_df[filtered_df['Tier'] == selected_tier]
    
    if selected_gender != 'All':
        filtered_df = filtered_df[filtered_df['Gender'] == selected_gender]
    
    if selected_team != 'All':
        filtered_df = filtered_df[filtered_df['Team'] == selected_team]

    # Create three columns for the top stats
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Players", len(filtered_df))
    
    with col2:
        avg_price = filtered_df['Price'].mean()
        st.metric("Average Price", f"{avg_price:.2f}")
    
    with col3:
        highest_price = filtered_df['Price'].max()
        highest_player = filtered_df[filtered_df['Price'] == highest_price]['Player Name'].values[0] if len(filtered_df) > 0 else "N/A"
        st.metric("Highest Price", f"{highest_price:.2f}", help=f"Player: {highest_player}")
    
    # Create tabs for different visualization sections
    tab1, tab2, tab3, tab4 = st.tabs(["Player Analysis", "Team Analysis", "Price Distribution", "Data Table"])
    
    # Tab 1: Player Analysis
    with tab1:
        st.header("Player Analysis")
        
        # Price by Tier chart
        st.subheader("Average Price by Tier")
        tier_price = filtered_df.groupby('Tier')['Price'].mean().reset_index()
        
        fig, ax = plt.subplots(figsize=(10, 6))
        sns.barplot(x='Tier', y='Price', data=tier_price, ax=ax)
        ax.set_title('Average Price by Tier')
        ax.set_xlabel('Tier')
        ax.set_ylabel('Average Price')
        st.pyplot(fig)
        
        # Positions analysis
        st.subheader("Players by Position")
        
        # Extract positions from the concatenated string and count occurrences
        position_counts = {}
        for pos_str in filtered_df['Position'].dropna():
            positions = [p.strip() for p in pos_str.split(',')]
            for pos in positions:
                if pos in position_counts:
                    position_counts[pos] += 1
                else:
                    position_counts[pos] = 1
        
        # Convert to DataFrame for plotting
        positions_df = pd.DataFrame({
            'Position': list(position_counts.keys()),
            'Count': list(position_counts.values())
        }).sort_values('Count', ascending=False)
        
        if not positions_df.empty:
            fig, ax = plt.subplots(figsize=(10, 6))
            sns.barplot(x='Position', y='Count', data=positions_df, ax=ax)
            ax.set_title('Player Count by Position')
            ax.set_xlabel('Position')
            ax.set_ylabel('Number of Players')
            plt.xticks(rotation=45)
            st.pyplot(fig)
        else:
            st.info("No position data available for the current selection.")
    
    # Tab 2: Team Analysis
    with tab2:
        st.header("Team Analysis")
        
        # Team composition by tier
        st.subheader("Team Composition by Tier")
        
        team_tier = pd.crosstab(filtered_df['Team'], filtered_df['Tier'])
        
        if not team_tier.empty:
            fig, ax = plt.subplots(figsize=(12, 8))
            team_tier.plot(kind='bar', stacked=True, ax=ax)
            ax.set_title('Team Composition by Tier')
            ax.set_xlabel('Team')
            ax.set_ylabel('Number of Players')
            plt.xticks(rotation=45)
            plt.legend(title='Tier')
            st.pyplot(fig)
        else:
            st.info("No team data available for the current selection.")
        
        # Team spending
        st.subheader("Team Total Spending")
        
        team_spending = filtered_df.groupby('Team')['Price'].sum().reset_index().sort_values('Price', ascending=False)
        
        if not team_spending.empty:
            fig, ax = plt.subplots(figsize=(12, 8))
            sns.barplot(x='Team', y='Price', data=team_spending, ax=ax)
            ax.set_title('Total Spending by Team')
            ax.set_xlabel('Team')
            ax.set_ylabel('Total Price')
            plt.xticks(rotation=45, ha='right')
            st.pyplot(fig)
        else:
            st.info("No spending data available for the current selection.")
    
    # Tab 3: Price Distribution
    with tab3:
        st.header("Price Distribution")
        
        # Price distribution histogram
        st.subheader("Price Distribution Histogram")
        
        fig, ax = plt.subplots(figsize=(10, 6))
        sns.histplot(filtered_df['Price'].dropna(), bins=20, kde=True, ax=ax)
        ax.set_title('Price Distribution')
        ax.set_xlabel('Price')
        ax.set_ylabel('Frequency')
        st.pyplot(fig)
        
        # Price distribution by gender
        st.subheader("Price Distribution by Gender")
        
        fig, ax = plt.subplots(figsize=(10, 6))
        sns.boxplot(x='Gender', y='Price', data=filtered_df, ax=ax)
        ax.set_title('Price Distribution by Gender')
        ax.set_xlabel('Gender')
        ax.set_ylabel('Price')
        st.pyplot(fig)
        
        # Price distribution by edition
        st.subheader("Price Distribution by Edition")
        
        fig, ax = plt.subplots(figsize=(10, 6))
        sns.boxplot(x='Edition', y='Price', data=filtered_df, ax=ax)
        ax.set_title('Price Distribution by Edition')
        ax.set_xlabel('Edition')
        ax.set_ylabel('Price')
        st.pyplot(fig)
    
    # Tab 4: Data Table
    with tab4:
        st.header("Player Data")
        
        # Search box for player name
        search_player = st.text_input("Search Player", "")
        
        # Filter by search term
        if search_player:
            search_results = filtered_df[filtered_df['Player Name'].str.contains(search_player, case=False)]
        else:
            search_results = filtered_df
        
        # Display the data table
        st.dataframe(search_results)
        
        # Option to download the filtered data
        st.download_button(
            label="Download Filtered Data as CSV",
            data=search_results.to_csv(index=False).encode('utf-8'),
            file_name='filtered_apl_data.csv',
            mime='text/csv',
        )

# Run the app
if __name__ == "__main__":
    main() 