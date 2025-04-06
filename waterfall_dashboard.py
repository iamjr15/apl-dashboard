import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from PIL import Image
import os
import math
from datetime import datetime

# Set page config with wide layout and a custom title
st.set_page_config(
    page_title="WATERFALL FC Auction Dashboard",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for dashboard
st.markdown("""
<style>
    /* Main page styling */
    .main {
        background-color: #f5f5f5;
    }
    
    /* Header styling */
    .header {
        background-color: #0e1117;
        color: white;
        padding: 1rem;
        border-radius: 5px;
        margin-bottom: 1rem;
        text-align: center;
    }
    
    /* Budget meter styling */
    .budget-meter {
        background-color: #262730;
        border-radius: 10px;
        padding: 1rem;
        color: white;
    }
    
    /* Team builder styling */
    .team-builder {
        background-color: #262730;
        border-radius: 10px;
        padding: 1rem;
        color: white;
        margin-top: 1rem;
    }
    
    /* Player card styling */
    .player-card {
        background-color: white;
        border-radius: 5px;
        padding: 1rem;
        margin-bottom: 0.5rem;
        box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
    }
    
    /* Tier colors */
    .tier-1 {
        background-color: #FF9800;
        padding: 2px 8px;
        border-radius: 3px;
        color: white;
        font-weight: bold;
    }
    
    .tier-2 {
        background-color: #2196F3;
        padding: 2px 8px;
        border-radius: 3px;
        color: white;
        font-weight: bold;
    }
    
    .tier-3 {
        background-color: #4CAF50;
        padding: 2px 8px;
        border-radius: 3px;
        color: white;
        font-weight: bold;
    }
    
    .tier-4 {
        background-color: #9C27B0;
        padding: 2px 8px;
        border-radius: 3px;
        color: white;
        font-weight: bold;
    }
    
    /* Value colors */
    .excellent-value {
        color: #4CAF50;
        font-weight: bold;
    }
    
    .good-value {
        color: #2196F3;
        font-weight: bold;
    }
    
    .fair-value {
        color: #FFC107;
        font-weight: bold;
    }
    
    .poor-value {
        color: #F44336;
        font-weight: bold;
    }
    
    # /* Center logo container */
    # .logo-container {
    #     display: flex;
    #     justify-content: center;
    #     background-color: #0e1117;
    #     padding: 1rem 0;
    #     border-radius: 5px 5px 0 0;
    # }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# Constants
TOTAL_BUDGET = 150  # million
TEAM_SIZE = 10
MIN_NON_CIS = 2

# Function to load data
@st.cache_data
def load_data():
    try:
        # Load all relevant datasets
        auction_guide = pd.read_csv("apl8_auction_guide.csv")
        top_picks = pd.read_csv("apl8_auction_top_picks.csv")
        master_data = pd.read_csv("apl_master_data.csv")
        
        # Debug info
        print(f"Loaded data: auction_guide={auction_guide.shape}, top_picks={top_picks.shape}, master_data={master_data.shape}")
        
        # Ensure data types are correct
        for col in ['Price', 'Value_Score', 'Recommended']:
            if col in auction_guide.columns:
                auction_guide[col] = pd.to_numeric(auction_guide[col], errors='coerce')
            else:
                print(f"Warning: Column {col} not found in auction_guide")
        
        # Ensure all required columns exist
        required_cols = ['Player', 'Gender', 'Tier', 'Price', 'Value_Score', 'Primary_Position', 'Recommended', 'Historical_Avg']
        missing_cols = [col for col in required_cols if col not in auction_guide.columns]
        if missing_cols:
            print(f"Warning: Missing required columns in auction_guide: {missing_cols}")
            # Add missing columns with defaults
            for col in missing_cols:
                auction_guide[col] = None
        
        return auction_guide, top_picks, master_data
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        # Return empty dataframes to avoid errors
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

# Function to get value class
def get_value_class(value_score):
    if value_score >= 2.0:
        return "excellent-value"
    elif value_score >= 1.5:
        return "good-value"
    elif value_score >= 1.0:
        return "fair-value"
    else:
        return "poor-value"

# Function to get max bid
def calculate_max_bid(remaining_budget, players_needed, player_value, is_high_priority):
    # Base calculation based on even distribution
    avg_per_player = remaining_budget / players_needed if players_needed > 0 else 0
    
    # Adjust based on value and priority
    if is_high_priority:
        # High priority players can get up to 1.5-2x the average
        max_bid = avg_per_player * (1.5 + (player_value - 1) * 0.5)
    else:
        # Other players shouldn't go much above average
        max_bid = avg_per_player * (1 + (player_value - 1) * 0.3)
    
    # Cap at remaining budget
    return min(max_bid, remaining_budget)

# Function to display header
def show_header():
    # Dashboard title only - no logo
    st.markdown('<div class="header"><h1>WATERFALL FC Auction Dashboard</h1></div>', unsafe_allow_html=True)
    
    # Dashboard navigation
    tabs = st.tabs(["Team Builder", "Player Search", "Top Targets", "Auction Simulation", "Info"])
    return tabs

# Function to display budget
def show_budget(remaining_budget, players_needed):
    st.markdown('<div class="budget-meter">', unsafe_allow_html=True)
    
    # Budget bar
    budget_pct = (remaining_budget / TOTAL_BUDGET) * 100
    st.progress(budget_pct / 100)
    
    # Budget details
    col1, col2, col3 = st.columns(3)
    col1.metric(label="Budget Remaining", value=f"₹{remaining_budget:.1f}M")
    col2.metric(label="Budget Used", value=f"₹{TOTAL_BUDGET - remaining_budget:.1f}M")
    col3.metric(label="Avg per Remaining Player", value=f"₹{(remaining_budget / players_needed if players_needed > 0 else 0):.1f}M")
    
    st.markdown('</div>', unsafe_allow_html=True)

# Function to initialize session state
def init_session_state():
    if 'team_players' not in st.session_state:
        st.session_state.team_players = []
    if 'remaining_budget' not in st.session_state:
        st.session_state.remaining_budget = TOTAL_BUDGET
    if 'sold_players' not in st.session_state:
        st.session_state.sold_players = []
    if 'search_query' not in st.session_state:
        st.session_state.search_query = ""
    if 'position_filter' not in st.session_state:
        st.session_state.position_filter = "All"
    if 'tier_filter' not in st.session_state:
        st.session_state.tier_filter = "All"
    if 'gender_filter' not in st.session_state:
        st.session_state.gender_filter = "All"
    if 'value_filter' not in st.session_state:
        st.session_state.value_filter = "All"
    if 'price_range_min' not in st.session_state:
        st.session_state.price_range_min = 0.0
    if 'price_range_max' not in st.session_state:
        st.session_state.price_range_max = 100.0
    if 'show_top_picks' not in st.session_state:
        st.session_state.show_top_picks = False
    if 'comparison_player' not in st.session_state:
        st.session_state.comparison_player = None
    if 'compare_list' not in st.session_state:
        st.session_state.compare_list = []
    if 'current_page' not in st.session_state:
        st.session_state.current_page = 1
    # New session state variables for bidding
    if 'bid_history' not in st.session_state:
        st.session_state.bid_history = {}  # Format: {player_name: {'bid': bid_amount, 'final_price': final_price}}
    if 'current_bid_player' not in st.session_state:
        st.session_state.current_bid_player = None
    if 'bid_amount' not in st.session_state:
        st.session_state.bid_amount = 0.0

# Function to display simulation screen
def show_simulation_tab(auction_guide, tab):
    with tab:
        st.header("Auction Simulation")
        
        # Simulation controls
        st.subheader("Simulate Different Budget Allocations")
        
        # Create columns for controls and results
        control_col, results_col = st.columns([1, 1])
        
        with control_col:
            # Set budget allocation by tier or position
            st.write("Allocate your budget to see potential team compositions")
            
            sim_by = st.radio("Allocate budget by:", ["Tier", "Position"])
            
            if sim_by == "Tier":
                # Budget allocation by tier sliders
                t1_budget = st.slider("Tier 1 Budget (₹M)", 0, 100, 40, key="t1_slider")
                t2_budget = st.slider("Tier 2 Budget (₹M)", 0, 80, 40, key="t2_slider")
                t3_budget = st.slider("Tier 3 Budget (₹M)", 0, 60, 40, key="t3_slider")
                t4_budget = st.slider("Tier 4 Budget (₹M)", 0, 40, 30, key="t4_slider")
                
                total_sim_budget = t1_budget + t2_budget + t3_budget + t4_budget
                
                # Show budget visualization
                budget_data = pd.DataFrame({
                    'Tier': ['Tier 1', 'Tier 2', 'Tier 3', 'Tier 4'],
                    'Budget': [t1_budget, t2_budget, t3_budget, t4_budget]
                })
                
                fig = px.bar(
                    budget_data,
                    x='Tier',
                    y='Budget',
                    title=f"Budget Distribution (₹{total_sim_budget}M)",
                    color='Tier',
                    color_discrete_map={
                        'Tier 1': '#FF9800',
                        'Tier 2': '#2196F3',
                        'Tier 3': '#4CAF50',
                        'Tier 4': '#9C27B0'
                    }
                )
                fig.update_layout(height=250)
                st.plotly_chart(fig, use_container_width=True)
                
                # Calculate player counts for each tier
                t1_count = min(2, int(t1_budget/40))
                t2_count = min(3, int(t2_budget/20))
                t3_count = min(3, int(t3_budget/15))
                t4_count = TEAM_SIZE - (t1_count + t2_count + t3_count)
                
                # Ensure we have valid counts
                if t1_count + t2_count + t3_count > TEAM_SIZE:
                    st.warning("Too many players selected. Adjusting counts...")
                    while t1_count + t2_count + t3_count > TEAM_SIZE:
                        if t3_count > 0:
                            t3_count -= 1
                        elif t2_count > 0:
                            t2_count -= 1
                        elif t1_count > 0:
                            t1_count -= 1
                
                if t4_count < 0:
                    t4_count = 0
                
                # Display player count distribution
                count_data = pd.DataFrame({
                    'Tier': ['Tier 1', 'Tier 2', 'Tier 3', 'Tier 4'],
                    'Count': [t1_count, t2_count, t3_count, t4_count]
                })
                
                st.write("### Recommended Player Count")
                count_fig = px.pie(
                    count_data,
                    values='Count',
                    names='Tier',
                    title="Players by Tier",
                    color='Tier',
                    color_discrete_map={
                        'Tier 1': '#FF9800',
                        'Tier 2': '#2196F3',
                        'Tier 3': '#4CAF50',
                        'Tier 4': '#9C27B0'
                    }
                )
                count_fig.update_layout(height=250)
                st.plotly_chart(count_fig, use_container_width=True)
                
            else:  # Position-based allocation
                # Get position categories
                position_categories = {
                    "Forward": ["Forward", "Striker", "Winger", "No. 9", "Forward/Number 9/CAN", "Forward/Number 10"],
                    "Midfielder": ["Midfielder", "Box-to-Box Midfielder", "Central Midfielder", "DM"],
                    "Defender": ["Defender", "Center Back (Sweeper)", "Ball Playing Center Back", "Full Back"],
                    "Goalkeeper": ["Goalkeeper"]
                }
                
                # Budget allocation by position
                fwd_budget = st.slider("Forwards Budget (₹M)", 0, 80, 60, key="fwd_slider")
                mid_budget = st.slider("Midfielders Budget (₹M)", 0, 60, 50, key="mid_slider")
                def_budget = st.slider("Defenders Budget (₹M)", 0, 40, 30, key="def_slider")
                gk_budget = st.slider("Goalkeepers Budget (₹M)", 0, 20, 10, key="gk_slider")
                
                total_sim_budget = fwd_budget + mid_budget + def_budget + gk_budget
                
                # Show budget visualization
                budget_data = pd.DataFrame({
                    'Position': ['Forwards', 'Midfielders', 'Defenders', 'Goalkeepers'],
                    'Budget': [fwd_budget, mid_budget, def_budget, gk_budget]
                })
                
                fig = px.pie(
                    budget_data,
                    values='Budget',
                    names='Position',
                    title=f"Budget Distribution (₹{total_sim_budget}M)",
                    color='Position',
                    color_discrete_map={
                        'Forwards': '#FF5722',
                        'Midfielders': '#2196F3',
                        'Defenders': '#4CAF50',
                        'Goalkeepers': '#9C27B0'
                    }
                )
                fig.update_layout(height=250)
                st.plotly_chart(fig, use_container_width=True)
                
                # Recommended player count by position
                fwd_count = 3
                mid_count = 3
                def_count = 3
                gk_count = 1
                
                # Display player count distribution
                count_data = pd.DataFrame({
                    'Position': ['Forwards', 'Midfielders', 'Defenders', 'Goalkeepers'],
                    'Count': [fwd_count, mid_count, def_count, gk_count]
                })
                
                st.write("### Recommended Player Count")
                count_fig = px.bar(
                    count_data,
                    x='Position',
                    y='Count',
                    title="Players by Position",
                    color='Position',
                    color_discrete_map={
                        'Forwards': '#FF5722',
                        'Midfielders': '#2196F3',
                        'Defenders': '#4CAF50',
                        'Goalkeepers': '#9C27B0'
                    }
                )
                count_fig.update_layout(height=250)
                st.plotly_chart(count_fig, use_container_width=True)
            
            # Show budget status
            if total_sim_budget > TOTAL_BUDGET:
                st.error(f"⚠️ Over budget by ₹{total_sim_budget - TOTAL_BUDGET}M")
            elif total_sim_budget < TOTAL_BUDGET:
                st.info(f"Under budget by ₹{TOTAL_BUDGET - total_sim_budget}M")
            else:
                st.success("✅ Budget perfectly allocated")
        
        with results_col:
            st.write("### Recommended Team")
            
            try:
                # Create simulated team based on budget allocation
                simulated_team = pd.DataFrame()
                
                if sim_by == "Tier":
                    # Get best players from each tier
                    t1_players = auction_guide[
                        (auction_guide['Tier'] == 1) & 
                        (auction_guide['Price'] <= t1_budget) &
                        (~auction_guide['Player'].isin(st.session_state.sold_players))
                    ].sort_values(['Value_Score'], ascending=[False]).head(t1_count)
                    
                    t2_players = auction_guide[
                        (auction_guide['Tier'] == 2) & 
                        (auction_guide['Price'] <= t2_budget) &
                        (~auction_guide['Player'].isin(st.session_state.sold_players))
                    ].sort_values(['Value_Score'], ascending=[False]).head(t2_count)
                    
                    t3_players = auction_guide[
                        (auction_guide['Tier'] == 3) & 
                        (auction_guide['Price'] <= t3_budget) &
                        (~auction_guide['Player'].isin(st.session_state.sold_players))
                    ].sort_values(['Value_Score'], ascending=[False]).head(t3_count)
                    
                    t4_players = auction_guide[
                        (auction_guide['Tier'] == 4) & 
                        (auction_guide['Price'] <= t4_budget) &
                        (~auction_guide['Player'].isin(st.session_state.sold_players))
                    ].sort_values(['Value_Score'], ascending=[False]).head(t4_count)
                    
                    # Make sure we have at least 2 non-cis players
                    combined_team = pd.concat([t1_players, t2_players, t3_players, t4_players])
                    non_cis_count = len(combined_team[combined_team['Gender'] == 'Women'])
                    
                    if non_cis_count < MIN_NON_CIS:
                        st.warning(f"Only {non_cis_count} non-cis players in simulated team. Adjusting...")
                        
                        # Find non-cis players to add
                        non_cis_players = auction_guide[
                            (auction_guide['Gender'] == 'Women') & 
                            (~auction_guide['Player'].isin(combined_team['Player'])) &
                            (~auction_guide['Player'].isin(st.session_state.sold_players))
                        ].sort_values(['Value_Score'], ascending=[False])
                        
                        # Try to add enough non-cis players
                        for i in range(MIN_NON_CIS - non_cis_count):
                            if i < len(non_cis_players):
                                # Remove the lowest value player from our team
                                combined_team = combined_team.sort_values(['Value_Score'], ascending=[True])
                                combined_team = combined_team.iloc[1:]
                                
                                # Add the non-cis player
                                combined_team = pd.concat([combined_team, non_cis_players.iloc[[i]]])
                    
                    simulated_team = combined_team
                    
                else:  # Position-based simulation
                    # Helper function to get players by position
                    def get_position_players(categories, budget, count):
                        # Flatten position categories
                        positions = []
                        for cat in categories:
                            positions.extend(position_categories.get(cat, []))
                        
                        players = auction_guide[
                            (auction_guide['Primary_Position'].isin(positions)) & 
                            (auction_guide['Price'] <= budget) &
                            (~auction_guide['Player'].isin(st.session_state.sold_players))
                        ].sort_values(['Value_Score'], ascending=[False]).head(count)
                        
                        return players
                    
                    # Get players for each position
                    forwards = get_position_players(['Forward'], fwd_budget, fwd_count)
                    midfielders = get_position_players(['Midfielder'], mid_budget, mid_count)
                    defenders = get_position_players(['Defender'], def_budget, def_count)
                    goalkeepers = get_position_players(['Goalkeeper'], gk_budget, gk_count)
                    
                    # Combine into one team
                    simulated_team = pd.concat([forwards, midfielders, defenders, goalkeepers])
                    
                    # Check for non-cis requirement
                    non_cis_count = len(simulated_team[simulated_team['Gender'] == 'Women'])
                    
                    if non_cis_count < MIN_NON_CIS:
                        st.warning(f"Only {non_cis_count} non-cis players in simulated team. Adjusting...")
                        
                        # Find non-cis players to add
                        non_cis_players = auction_guide[
                            (auction_guide['Gender'] == 'Women') & 
                            (~auction_guide['Player'].isin(simulated_team['Player'])) &
                            (~auction_guide['Player'].isin(st.session_state.sold_players))
                        ].sort_values(['Value_Score'], ascending=[False])
                        
                        # Try to add enough non-cis players
                        for i in range(MIN_NON_CIS - non_cis_count):
                            if i < len(non_cis_players):
                                # Remove the lowest value player from our team who is not a goalkeeper
                                non_gk_team = simulated_team[~simulated_team['Primary_Position'].isin(['Goalkeeper'])]
                                non_gk_team = non_gk_team.sort_values(['Value_Score'], ascending=[True])
                                
                                if len(non_gk_team) > 0:
                                    player_to_remove = non_gk_team.iloc[0]['Player']
                                    simulated_team = simulated_team[simulated_team['Player'] != player_to_remove]
                                    
                                    # Add the non-cis player
                                    simulated_team = pd.concat([simulated_team, non_cis_players.iloc[[i]]])
                
                # Display team stats
                if len(simulated_team) > 0:
                    # Calculate team metrics
                    total_cost = simulated_team['Price'].sum()
                    avg_value = simulated_team['Value_Score'].mean()
                    non_cis_count = len(simulated_team[simulated_team['Gender'] == 'Women'])
                    
                    # Display metrics
                    st.metric("Team Cost", f"₹{total_cost:.1f}M", f"{(total_cost/TOTAL_BUDGET)*100:.1f}% of budget")
                    
                    # Create two columns for metrics
                    metric_col1, metric_col2 = st.columns(2)
                    with metric_col1:
                        st.metric("Avg Value", f"{avg_value:.2f}")
                    with metric_col2:
                        non_cis_status = "✅" if non_cis_count >= MIN_NON_CIS else "❌"
                        st.metric("Non-CIS Players", f"{non_cis_count}/{MIN_NON_CIS}", f"{non_cis_status}")
                    
                    # Display team composition
                    display_cols = ['Player', 'Gender', 'Tier', 'Primary_Position', 'Price', 'Value_Score']
                    team_display = simulated_team[display_cols].copy() if all(col in simulated_team.columns for col in display_cols) else simulated_team
                    
                    # Sort by tier and value score
                    team_display = team_display.sort_values(['Tier', 'Value_Score'], ascending=[True, False])
                    
                    st.dataframe(team_display, use_container_width=True)
                    
                    # Button to add all players to team
                    if st.button("Add Team to My Roster", key="add_team_btn"):
                        # Check if we can afford the team
                        if total_cost <= st.session_state.remaining_budget:
                            # Check for duplicates
                            current_players = [p['Player'] for p in st.session_state.team_players]
                            new_players_added = 0
                            
                            for _, player in simulated_team.iterrows():
                                if player['Player'] not in current_players:
                                    st.session_state.team_players.append({
                                        'Player': player['Player'],
                                        'Tier': player['Tier'],
                                        'Price': player['Price'],
                                        'Gender': player['Gender'],
                                        'Position': player['Primary_Position'],
                                        'Value_Score': player['Value_Score']
                                    })
                                    new_players_added += 1
                            
                            if new_players_added > 0:
                                st.session_state.remaining_budget -= total_cost
                                st.success(f"Added {new_players_added} players to your team!")
                                st.rerun()
                            else:
                                st.info("All these players are already in your team.")
                        else:
                            st.error(f"Not enough budget! This team costs ₹{total_cost}M but you only have ₹{st.session_state.remaining_budget}M.")
                    
                else:
                    st.error("Could not create a valid team with the current budget allocation.")
            
            except Exception as e:
                st.error(f"Error creating simulated team: {str(e)}")
            
            # Simulation tips
            with st.expander("Simulation Tips", expanded=False):
                st.write("""
                ### Effective Budget Allocation:
                
                1. **Tier-Based Allocation**:
                   - Tier 1 players: ₹60-90M
                   - Tier 2 players: ₹30-60M
                   - Tier 3 players: ₹10-30M
                   - Tier 4 players: ₹5-15M
                
                2. **Position-Based Allocation**:
                   - Forwards: ₹40-70M
                   - Midfielders: ₹30-60M  
                   - Defenders: ₹20-40M
                   - Goalkeeper: ₹10-20M
                
                3. **Remember the requirements**:
                   - Total 10 players
                   - At least 2 non-cis players
                   - Total budget of ₹150M
                """)
            
            # Quick player lookup
            with st.expander("Quick Player Search", expanded=False):
                quick_search = st.text_input("Search for player:", key="quick_search")
                
                if quick_search:
                    search_results = auction_guide[
                        auction_guide['Player'].str.contains(quick_search, case=False)
                    ].sort_values(['Tier', 'Value_Score'], ascending=[True, False])
                    
                    if len(search_results) > 0:
                        st.dataframe(
                            search_results[['Player', 'Gender', 'Tier', 'Primary_Position', 'Price', 'Value_Score']],
                            use_container_width=True
                        )
                    else:
                        st.info(f"No players found matching '{quick_search}'")
                
                # Top value players section
                st.subheader("Top Value Players")
                value_tier = st.selectbox("Select Tier:", [1, 2, 3, 4], key="value_tier")
                
                value_players = auction_guide[
                    (auction_guide['Tier'] == value_tier) &
                    (~auction_guide['Player'].isin(st.session_state.sold_players))
                ].sort_values('Value_Score', ascending=False).head(5)
                
                if len(value_players) > 0:
                    st.dataframe(
                        value_players[['Player', 'Gender', 'Primary_Position', 'Price', 'Value_Score', 'Recommended']],
                        use_container_width=True
                    )

# Function to display top targets tab
def show_top_targets_tab(top_picks, tab):
    with tab:
        st.header("Top Targets")
        
        # Create tabs for different player categories
        category_tabs = st.tabs(["All Players", "Tier 1", "Tier 2", "Tier 3", "Tier 4", "Best Value"])
        
        # Group players by category for easier filtering
        categories = {
            "All Players": top_picks,
            "Tier 1": top_picks[top_picks["Tier"] == 1],
            "Tier 2": top_picks[top_picks["Tier"] == 2],
            "Tier 3": top_picks[top_picks["Tier"] == 3],
            "Tier 4": top_picks[top_picks["Tier"] == 4],
            "Best Value": top_picks[top_picks["Selection_Reason"].str.contains("value", case=False, na=False)]
        }
        
        # Display players in each category tab
        for i, (category, players) in enumerate(categories.items()):
            with category_tabs[i]:
                st.subheader(f"{category} ({len(players)} players)")
                
                # Sort players by auction score (descending)
                if not players.empty and "Auction_Score" in players.columns:
                    players = players.sort_values("Auction_Score", ascending=False)
                
                # Create expandable sections for each player
                for idx, (_, player) in enumerate(players.iterrows()):
                    # Create a unique key based on player name, category and index
                    unique_key = f"{player['Player']}_{category}_{idx}"
                    
                    # Check if player exists in data
                    if pd.isna(player['Player']):
                        continue
                    
                    # Check if player is already in team
                    player_name = player['Player']
                    player_bought = player_name in [p['Player'] for p in st.session_state.team_players]
                    player_sold = player_name in st.session_state.sold_players
                    
                    # Format the expander title
                    expander_title = f"{player['Player']} (Tier {int(player['Tier'])}) - {player['Category']}"
                    
                    # Create expander without key parameter
                    with st.expander(expander_title):
                        col1, col2 = st.columns([2, 1])
                        
                        with col1:
                            # Player basic info
                            st.markdown(f"**Position:** {player['Primary_Position']}")
                            st.markdown(f"**Gender:** {player['Gender']}")
                            st.markdown(f"**Value Score:** {player['Value_Score']:.2f}")
                            st.markdown(f"**Auction Score:** {player['Auction_Score']:.1f}")
                            
                            # Show recommendation reason
                            if pd.notna(player['Selection_Reason']):
                                st.markdown(f"**Selection Reason:** {player['Selection_Reason']}")
                            
                            # Show bidding strategy if available
                            if pd.notna(player['Bidding_Strategy']):
                                st.markdown(f"**Bidding Strategy:** {player['Bidding_Strategy']}")
                            
                            # Price recommendation
                            if pd.notna(player['Price']) and pd.notna(player['Recommended']):
                                st.markdown(f"**Price:** ₹{player['Price']}M (Recommended: ₹{player['Recommended']}M)")
                            elif pd.notna(player['Price']):
                                st.markdown(f"**Price:** ₹{player['Price']}M")
                        
                        with col2:
                            # Action buttons with unique keys
                            if not player_bought and not player_sold:
                                # Add to team button with unique key
                                add_btn_key = f"add_{unique_key}"
                                if st.button(f"Add to Team", key=add_btn_key):
                                    # Check if we can afford the player
                                    if player['Price'] <= st.session_state.remaining_budget:
                                        st.session_state.team_players.append({
                                            'Player': player['Player'],
                                            'Tier': player['Tier'],
                                            'Price': player['Price'],
                                            'Gender': player['Gender'],
                                            'Position': player['Primary_Position'],
                                            'Value_Score': player['Value_Score']
                                        })
                                        st.session_state.remaining_budget -= player['Price']
                                        st.success(f"Added {player['Player']} to your team!")
                                    else:
                                        st.error(f"Not enough budget to add this player (₹{player['Price']}M)!")
                                    
                                    # Force rerun to update the UI
                                    st.rerun()
                            elif player_bought:
                                st.markdown("<div style='text-align:center; padding:5px; background-color:#4CAF50; color:white; border-radius:3px; font-weight:bold;'>IN TEAM</div>", unsafe_allow_html=True)
                            else:
                                st.markdown("<div style='text-align:center; padding:5px; background-color:#9E9E9E; color:white; border-radius:3px; font-weight:bold;'>SOLD</div>", unsafe_allow_html=True)
                            
                            # Mark as sold button (if not in team)
                            if not player_bought:
                                if not player_sold:
                                    sold_btn_key = f"sold_{unique_key}"
                                    if st.button("Mark as Sold", key=sold_btn_key):
                                        st.session_state.sold_players.append(player['Player'])
                                        st.info(f"Marked {player['Player']} as sold to another team.")
                                        st.rerun()
                                else:
                                    avail_btn_key = f"avail_{unique_key}"
                                    if st.button("Mark as Available", key=avail_btn_key):
                                        st.session_state.sold_players.remove(player['Player'])
                                        st.info(f"Marked {player['Player']} as available again.")
                                        st.rerun()
                            
                            # Bid button with unique key
                            bid_btn_key = f"bid_{unique_key}"
                            if not player_bought and not player_sold:
                                if st.button("Bid", key=bid_btn_key):
                                    st.session_state.current_bid_player = player_name
                                    st.rerun()
                            
                            # Compare button
                            compare_btn_key = f"compare_{unique_key}"
                            if st.button("Compare", key=compare_btn_key):
                                st.success(f"Added {player['Player']} to comparison. Feature coming soon.")
                
                    # Show bid modal if this is the current bid player
                    if st.session_state.current_bid_player == player_name:
                        st.markdown("### Place Bid")
                        
                        # Get values for bidding
                        recommended = float(player['Recommended']) if pd.notna(player['Recommended']) else None
                        value_score = float(player['Value_Score']) if pd.notna(player['Value_Score']) else 1.0
                        is_high_priority = True if 'Selection_Reason' in player and pd.notna(player['Selection_Reason']) and 'top player' in str(player['Selection_Reason']).lower() else False
                        current_budget = st.session_state.remaining_budget
                        
                        # Display bidding information
                        st.info(f"Remaining Budget: ₹{current_budget}M")
                        if recommended:
                            st.write(f"Recommended Price: ₹{recommended}M")
                        
                        # Calculate max bid if we can
                        try:
                            max_bid = calculate_max_bid(current_budget, 
                                                      TEAM_SIZE - len(st.session_state.team_players), 
                                                      value_score, is_high_priority)
                            st.write(f"Maximum Bid: ₹{max_bid}M")
                        except:
                            max_bid = None
                        
                        # Bid slider
                        min_bid = 0.5
                        max_possible_bid = min(100.0, current_budget or 100.0) 
                        
                        # Initialize bid amount
                        initial_bid = recommended or max_bid or min_bid
                        if initial_bid > max_possible_bid:
                            initial_bid = max_possible_bid
                            
                        bid_amount = st.slider(
                            "Your Bid (₹M)", 
                            min_value=min_bid, 
                            max_value=max_possible_bid,
                            value=float(initial_bid),
                            step=0.5,
                            key=f"bid_slider_{unique_key}"
                        )
                        
                        # Final price input
                        final_price = st.number_input(
                            "Final Price Paid (₹M)",
                            min_value=0.0,
                            max_value=max_possible_bid,
                            value=bid_amount,
                            step=0.5,
                            key=f"final_price_{unique_key}"
                        )
                        
                        # Buttons
                        confirm_col, cancel_col = st.columns(2)
                        with confirm_col:
                            confirm_key = f"confirm_bid_{unique_key}"
                            if st.button("Confirm and Add to Team", key=confirm_key):
                                # Check if we can afford the player
                                if final_price <= current_budget:
                                    # Add to team with bid information
                                    st.session_state.team_players.append({
                                        'Player': player_name,
                                        'Tier': player['Tier'],
                                        'Price': player['Price'],
                                        'Gender': player['Gender'],
                                        'Position': player['Primary_Position'],
                                        'Value_Score': player['Value_Score'],
                                        'Bid': bid_amount,
                                        'Final_Price': final_price
                                    })
                                    # Update budget based on final price
                                    st.session_state.remaining_budget -= final_price
                                    # Add to bid history
                                    st.session_state.bid_history[player_name] = {
                                        'bid': bid_amount,
                                        'final_price': final_price
                                    }
                                    # Clear current bid player
                                    st.session_state.current_bid_player = None
                                    st.success(f"Successfully bid ₹{bid_amount}M and acquired {player_name} for ₹{final_price}M!")
                                    st.rerun()
                                else:
                                    st.error(f"Not enough budget to pay ₹{final_price}M for this player!")
                                    
                        with cancel_col:
                            cancel_key = f"cancel_bid_{unique_key}"
                            if st.button("Cancel", key=cancel_key):
                                # Clear current bid player
                                st.session_state.current_bid_player = None
                                st.rerun()

# Function to display player search tab
def show_player_search_tab(auction_guide, tab):
    with tab:
        st.header("Player Search")
        
        # Add data debugging expander
        with st.expander("Data Information", expanded=False):
            st.write(f"Total players in dataset: {len(auction_guide)}")
            st.write(f"Columns available: {', '.join(auction_guide.columns)}")
            st.write("Sample player data:")
            if not auction_guide.empty:
                st.dataframe(auction_guide.head(3))
            else:
                st.error("No player data loaded")
        
        # Search and filter controls
        col1, col2 = st.columns([1, 3])
        
        with col1:
            st.session_state.search_query = st.text_input("Search by Player Name", st.session_state.search_query)
        
        # Advanced filters
        with st.expander("Advanced Filters", expanded=True):
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                position_options = ["All"]
                if 'Primary_Position' in auction_guide.columns:
                    unique_positions = auction_guide["Primary_Position"].dropna().unique().tolist()
                    position_options += sorted(unique_positions)
                
                position_index = 0
                if st.session_state.position_filter in position_options:
                    position_index = position_options.index(st.session_state.position_filter)
                st.session_state.position_filter = st.selectbox("Position", position_options, index=position_index)
            
            with col2:
                tier_options = ["All"]
                if 'Tier' in auction_guide.columns:
                    unique_tiers = sorted(auction_guide["Tier"].dropna().unique().tolist())
                    tier_options += [int(t) for t in unique_tiers if pd.notna(t)]
                
                tier_index = 0
                if st.session_state.tier_filter in tier_options:
                    tier_index = tier_options.index(st.session_state.tier_filter)
                else:
                    tier_index = 0
                
                st.session_state.tier_filter = st.selectbox("Tier", tier_options, index=tier_index)
            
            with col3:
                gender_options = ["All"]
                if 'Gender' in auction_guide.columns:
                    gender_options += sorted(auction_guide["Gender"].dropna().unique().tolist())
                
                gender_index = 0
                if st.session_state.gender_filter in gender_options:
                    gender_index = gender_options.index(st.session_state.gender_filter)
                st.session_state.gender_filter = st.selectbox("Gender", gender_options, index=gender_index)
            
            with col4:
                st.session_state.value_filter = st.selectbox("Value", ["All", "Excellent (>=2.0)", "Good (>=1.5)", "Fair (>=1.0)", "Poor (<1.0)"], index=0)
            
            col1, col2 = st.columns(2)
            
            with col1:
                min_price = 0.0
                max_price = 100.0
                if 'Price' in auction_guide.columns and not auction_guide.empty:
                    min_price = float(auction_guide['Price'].min() if not pd.isna(auction_guide['Price'].min()) else 0.0)
                    max_price = float(auction_guide['Price'].max() if not pd.isna(auction_guide['Price'].max()) else 100.0)
                
                # Use two separate sliders for min and max price
                price_col1, price_col2 = st.columns(2)
                with price_col1:
                    st.session_state.price_range_min = st.slider(
                        "Min Price (₹M)", 
                        min_value=min_price,
                        max_value=max_price,
                        value=st.session_state.price_range_min,
                        step=1.0
                    )
                with price_col2:
                    st.session_state.price_range_max = st.slider(
                        "Max Price (₹M)", 
                        min_value=min_price,
                        max_value=max_price,
                        value=max(st.session_state.price_range_max, st.session_state.price_range_min),
                        step=1.0
                    )
                
                # Ensure min <= max
                if st.session_state.price_range_min > st.session_state.price_range_max:
                    st.session_state.price_range_min = st.session_state.price_range_max
            
            with col2:
                availability_options = ["All Players", "Available Only", "Sold Players Only"]
                availability = st.radio("Availability", availability_options, horizontal=True)
                st.session_state.show_top_picks = st.checkbox("Only Show Top Picks", st.session_state.show_top_picks)
        
        # Apply filters
        try:
            filtered_players = auction_guide.copy()
            
            # Ensure required columns exist for filtering
            required_columns = ['Player', 'Gender', 'Tier', 'Price', 'Value_Score', 'Primary_Position']
            for col in required_columns:
                if col not in filtered_players.columns:
                    filtered_players[col] = None
            
            # Apply text search filter
            if st.session_state.search_query != "":
                if 'Player' in filtered_players.columns:
                    # Make search more flexible by allowing partial matches
                    filtered_players = filtered_players[filtered_players["Player"].str.contains(
                        st.session_state.search_query, case=False, na=False)]
            
            # Apply tier filter with NA handling
            if st.session_state.tier_filter != "All" and 'Tier' in filtered_players.columns:
                # Only filter on rows where Tier is not NA
                filtered_players = filtered_players[
                    (filtered_players["Tier"] == st.session_state.tier_filter) | 
                    (filtered_players["Tier"].isna() & (st.session_state.tier_filter == "All"))
                ]
            
            # Apply position filter with more lenient matching
            if st.session_state.position_filter != "All" and 'Primary_Position' in filtered_players.columns:
                # Case-insensitive position matching, allowing NA positions to pass through when filter is "All"
                filtered_players = filtered_players[
                    (filtered_players["Primary_Position"].str.contains(
                        st.session_state.position_filter, case=False, na=False)) | 
                    (filtered_players["Primary_Position"].isna() & (st.session_state.position_filter == "All"))
                ]
            
            # Apply gender filter, preserving NA when filter is "All"
            if st.session_state.gender_filter != "All" and 'Gender' in filtered_players.columns:
                filtered_players = filtered_players[
                    (filtered_players["Gender"] == st.session_state.gender_filter) | 
                    (filtered_players["Gender"].isna() & (st.session_state.gender_filter == "All"))
                ]
            
            # Apply value filter, ignoring NA values when filter is "All"
            if st.session_state.value_filter != "All" and 'Value_Score' in filtered_players.columns:
                if st.session_state.value_filter == "Excellent (>=2.0)":
                    filtered_players = filtered_players[
                        (filtered_players["Value_Score"] >= 2.0) | 
                        (filtered_players["Value_Score"].isna() & (st.session_state.value_filter == "All"))
                    ]
                elif st.session_state.value_filter == "Good (>=1.5)":
                    filtered_players = filtered_players[
                        (filtered_players["Value_Score"] >= 1.5) | 
                        (filtered_players["Value_Score"].isna() & (st.session_state.value_filter == "All"))
                    ]
                elif st.session_state.value_filter == "Fair (>=1.0)":
                    filtered_players = filtered_players[
                        (filtered_players["Value_Score"] >= 1.0) | 
                        (filtered_players["Value_Score"].isna() & (st.session_state.value_filter == "All"))
                    ]
                elif st.session_state.value_filter == "Poor (<1.0)":
                    filtered_players = filtered_players[
                        (filtered_players["Value_Score"] < 1.0) | 
                        (filtered_players["Value_Score"].isna() & (st.session_state.value_filter == "All"))
                    ]
            
            # Apply price range filter, handling NA values
            if 'Price' in filtered_players.columns:
                # Include both players within price range and players with no price data when using "All"
                filtered_players = filtered_players[
                    ((filtered_players["Price"] >= st.session_state.price_range_min) & 
                    (filtered_players["Price"] <= st.session_state.price_range_max)) | 
                    (filtered_players["Price"].isna())
                ]
            
            # Apply availability filter
            if availability == "Available Only":
                filtered_players = filtered_players[~filtered_players["Player"].isin(st.session_state.sold_players)]
            elif availability == "Sold Players Only":
                filtered_players = filtered_players[filtered_players["Player"].isin(st.session_state.sold_players)]
            
            # Apply top picks filter with NA handling
            if st.session_state.show_top_picks and 'Auction_Priority' in filtered_players.columns:
                filtered_players = filtered_players[
                    (filtered_players["Auction_Priority"] == "High") | 
                    (filtered_players["Auction_Priority"].isna() & st.session_state.show_top_picks == False)
                ]
            
            # Calculate players to display and handle pagination
            player_count = len(filtered_players)
            page_size = 5  # Reduced to show more details per player
            total_pages = max(1, math.ceil(player_count / page_size))
            
            # Initialize current_page first
            if 'current_page' not in st.session_state:
                st.session_state.current_page = 1
            
            current_page = st.session_state.current_page
            
            if player_count == 0:
                st.warning("No players match your search criteria. Try broadening your filters.")
                # Display all filter settings for debugging
                st.write("Current filter settings:")
                st.write(f"- Search query: '{st.session_state.search_query}'")
                st.write(f"- Tier: {st.session_state.tier_filter}")
                st.write(f"- Position: {st.session_state.position_filter}")
                st.write(f"- Gender: {st.session_state.gender_filter}")
                st.write(f"- Value: {st.session_state.value_filter}")
                st.write(f"- Price range: ₹{st.session_state.price_range_min}M - ₹{st.session_state.price_range_max}M")
                st.write(f"- Show top picks only: {st.session_state.show_top_picks}")
            else:
                # Sort options
                sort_col1, sort_col2 = st.columns([3, 1])
                with sort_col1:
                    st.write(f"Found {player_count} players matching your criteria.")
                with sort_col2:
                    sort_option = st.selectbox(
                        "Sort by:", 
                        ["Tier (Asc)", "Value (Desc)", "Price (Asc)", "Price (Desc)", "Name (A-Z)"],
                        index=0,
                        key="sort_option"
                    )
                
                # Apply sorting with NA handling
                try:
                    if sort_option == "Tier (Asc)" and 'Tier' in filtered_players.columns:
                        # Sort tier first (NAs last), then value score (NAs last)
                        filtered_players = filtered_players.sort_values(
                            ["Tier", "Value_Score"], 
                            ascending=[True, False],
                            na_position='last'
                        )
                    elif sort_option == "Value (Desc)" and 'Value_Score' in filtered_players.columns:
                        filtered_players = filtered_players.sort_values(
                            "Value_Score", 
                            ascending=False,
                            na_position='last'
                        )
                    elif sort_option == "Price (Asc)" and 'Price' in filtered_players.columns:
                        filtered_players = filtered_players.sort_values(
                            "Price", 
                            ascending=True,
                            na_position='last'
                        )
                    elif sort_option == "Price (Desc)" and 'Price' in filtered_players.columns:
                        filtered_players = filtered_players.sort_values(
                            "Price", 
                            ascending=False,
                            na_position='last'
                        )
                    elif sort_option == "Name (A-Z)" and 'Player' in filtered_players.columns:
                        filtered_players = filtered_players.sort_values(
                            "Player", 
                            ascending=True,
                            na_position='last'
                        )
                except Exception as e:
                    st.error(f"Error sorting players: {str(e)}")
                
                # Pagination
                col1, col2, col3 = st.columns([1, 2, 1])
                with col2:
                    # Better pagination controls
                    if total_pages > 1:
                        page_cols = st.columns([1, 3, 1])
                        with page_cols[0]:
                            if st.button("← Prev", key="prev_btn", disabled=(current_page == 1)):
                                st.session_state.current_page = max(1, current_page - 1)
                                st.rerun()
                        
                        with page_cols[1]:
                            st.session_state.current_page = st.number_input(
                                "Page", 
                                min_value=1, 
                                max_value=total_pages, 
                                value=current_page, 
                                key="page_number"
                            )
                            st.write(f"Page {current_page} of {total_pages}")
                        
                        with page_cols[2]:
                            if st.button("Next →", key="next_btn", disabled=(current_page == total_pages)):
                                st.session_state.current_page = min(total_pages, current_page + 1)
                                st.rerun()
                
                # Update current_page from session state
                current_page = st.session_state.current_page
                
                # Calculate page start and end
                page_start = (current_page - 1) * page_size
                page_end = min(page_start + page_size, player_count)
                
                # Display players
                players_to_display = filtered_players.iloc[page_start:page_end].copy()
                
                # Ensure all fields exist with empty defaults
                default_fields = {
                    'Auction_Priority': None,
                    'APL_Editions': 0,
                    'Auction_Score': 0,
                    'Bidding_Strategy': "No strategy available",
                    'Selection_Reason': "No reason available",
                    'Secondary_Position': "Not specified",
                    'Historical_Avg': 0,
                    'Recommended': None
                }
                
                for field, default in default_fields.items():
                    if field not in players_to_display.columns:
                        players_to_display[field] = default
                
                for idx, (_, player) in enumerate(players_to_display.iterrows()):
                    # Generate a unique ID for each player card
                    player_id = f"player_{player['Player']}_{idx}_{current_page}"
                    
                    # Check if the player is already in sold list
                    player_sold = player['Player'] in st.session_state.sold_players
                    player_bought = player['Player'] in [p['Player'] for p in st.session_state.team_players]
                    
                    # Apply gray overlay for sold players
                    if player_sold and not player_bought:
                        st.markdown(f'<div class="player-card" style="opacity: 0.5;">', unsafe_allow_html=True)
                    else:
                        st.markdown('<div class="player-card">', unsafe_allow_html=True)
                    
                    # Player Name and Basic Info - safely access all fields with defaults
                    player_name = player['Player'] if pd.notna(player['Player']) else "Unknown Player"
                    st.markdown(f"## {player_name}")
                    
                    # Basic info in columns
                    col1, col2, col3 = st.columns([1, 1, 1])
                    
                    with col1:
                        if pd.notna(player['Tier']):
                            try:
                                tier_value = int(player['Tier'])
                                st.markdown(f"<span class='tier-{tier_value}'>Tier {tier_value}</span>", unsafe_allow_html=True)
                            except (ValueError, TypeError):
                                st.write("**Tier:** Unknown")
                        else:
                            st.write("**Tier:** Not specified")
                            
                        gender = player['Gender'] if pd.notna(player['Gender']) else "Not specified"
                        st.write(f"**Gender:** {gender}")
                        
                        position = player['Primary_Position'] if pd.notna(player['Primary_Position']) else "Not specified"
                        st.write(f"**Position:** {position}")
                    
                    with col2:
                        if pd.notna(player['Price']):
                            st.write(f"**Price:** ₹{player['Price']}M")
                        else:
                            st.write("**Price:** Not specified")
                            
                        if pd.notna(player['Recommended']):
                            st.write(f"**Recommended:** ₹{player['Recommended']}M")
                        else:
                            st.write("**Recommended:** Not available")
                            
                        if pd.notna(player['Value_Score']):
                            value_class = get_value_class(player['Value_Score'])
                            st.markdown(f"**Value:** <span class='{value_class}'>{player['Value_Score']:.2f}</span>", unsafe_allow_html=True)
                        else:
                            st.write("**Value:** Not calculated")
                    
                    with col3:
                        if pd.notna(player['Historical_Avg']):
                            st.write(f"**Historical Avg:** ₹{player['Historical_Avg']}M")
                        else:
                            st.write("**Historical Avg:** No data")
                            
                        if pd.notna(player['APL_Editions']):
                            st.write(f"**APL Editions:** {player['APL_Editions']}")
                        else:
                            st.write("**APL Editions:** 0")
                            
                        if pd.notna(player['Auction_Score']):
                            st.write(f"**Auction Score:** {player['Auction_Score']}")
                        else:
                            st.write("**Auction Score:** Not calculated")
                        
                        # Auction priority if available
                        if pd.notna(player['Auction_Priority']):
                            priority = player['Auction_Priority']
                            priority_color = "#4CAF50" if priority == "High" else "#FFC107" if priority == "Medium" else "#F44336"
                            st.markdown(f"**Priority:** <span style='color:{priority_color};font-weight:bold;'>{priority}</span>", unsafe_allow_html=True)
                        else:
                            st.write("**Priority:** Not assigned")
                    
                    # Only show Player Analysis section if we have some data
                    if (pd.notna(player['Bidding_Strategy']) or 
                        pd.notna(player['Selection_Reason']) or 
                        pd.notna(player['Secondary_Position']) or
                        pd.notna(player['Value_Score'])):
                        
                        st.markdown("### Player Analysis")
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            # Bidding strategy
                            if pd.notna(player['Bidding_Strategy']):
                                st.write(f"**Bidding Strategy:** {player['Bidding_Strategy']}")
                            
                            # Selection reason if available
                            if pd.notna(player['Selection_Reason']):
                                st.write(f"**Selection Reason:** {player['Selection_Reason']}")
                            
                            # Other player details
                            if pd.notna(player['Secondary_Position']):
                                st.write(f"**Secondary Position:** {player['Secondary_Position']}")
                        
                        with col2:
                            # Default to showing recommend actions even with incomplete data
                            remaining_budget = st.session_state.remaining_budget
                            players_needed = TEAM_SIZE - len(st.session_state.team_players)
                            
                            # Set defaults for calculation
                            value_score = player['Value_Score'] if pd.notna(player['Value_Score']) else 1.0
                            is_high_priority = (player['Auction_Priority'] == "High") if pd.notna(player['Auction_Priority']) else False
                            
                            # Calculate max bid using available data or defaults
                            try:
                                player_price = float(player['Price']) if pd.notna(player['Price']) else 0
                                max_bid = calculate_max_bid(remaining_budget, players_needed, value_score, is_high_priority)
                                st.markdown(f"**Maximum Bid:** ₹{max_bid:.1f}M")
                                
                                # Buy/Pass recommendation - more lenient with incomplete data
                                if pd.isna(player['Price']) or player_price <= max_bid:
                                    rec = "BUY" if is_high_priority else "Consider"
                                    rec_color = "#4CAF50" if is_high_priority else "#2196F3"
                                else:
                                    rec = "PASS"
                                    rec_color = "#F44336"
                                
                                st.markdown(f"<div style='text-align:center; padding:5px; background-color:{rec_color}; color:white; border-radius:3px; font-weight:bold;'>{rec}</div>", unsafe_allow_html=True)
                            except Exception as e:
                                st.write("**Recommendation:** Insufficient data")
                    
                    # Action buttons row
                    button_col1, button_col2, button_col3 = st.columns(3)
                    
                    with button_col1:
                        if not player_sold and not player_bought:
                            # Add to team button with unique key
                            button_key = f"add_search_{player_name}_{idx}_{current_page}"
                            if st.button(f"Add to Team", key=button_key):
                                # Get default values for required fields
                                player_price = float(player['Price']) if pd.notna(player['Price']) else 0
                                player_tier = int(player['Tier']) if pd.notna(player['Tier']) else 4
                                player_gender = player['Gender'] if pd.notna(player['Gender']) else "Not specified"
                                player_position = player['Primary_Position'] if pd.notna(player['Primary_Position']) else "Not specified"
                                player_value = float(player['Value_Score']) if pd.notna(player['Value_Score']) else 1.0
                                
                                # Check if we can afford the player
                                if player_price <= st.session_state.remaining_budget:
                                    st.session_state.team_players.append({
                                        'Player': player_name,
                                        'Tier': player_tier,
                                        'Price': player_price,
                                        'Gender': player_gender,
                                        'Position': player_position,
                                        'Value_Score': player_value,
                                        'Bid': None,
                                        'Final_Price': player_price
                                    })
                                    st.session_state.remaining_budget -= player_price
                                    st.success(f"Added {player_name} to your team!")
                                    st.rerun()
                                else:
                                    st.error(f"Not enough budget to add this player (₹{player_price}M)!")
                        elif player_bought:
                            st.markdown("<div style='text-align:center; padding:5px; background-color:#4CAF50; color:white; border-radius:3px; font-weight:bold;'>IN TEAM</div>", unsafe_allow_html=True)
                            
                            # Remove from team button with unique key
                            remove_key = f"remove_{player_name}_{idx}_{current_page}"
                            if st.button(f"Remove", key=remove_key):
                                # Get player's info
                                for i, team_player in enumerate(st.session_state.team_players):
                                    if team_player['Player'] == player_name:
                                        st.session_state.remaining_budget += team_player['Final_Price'] or team_player['Price']
                                        st.session_state.team_players.pop(i)
                                        st.success(f"Removed {player_name} from your team.")
                                        st.rerun()
                                        break
                        else:
                            st.markdown("<div style='text-align:center; padding:5px; background-color:#9E9E9E; color:white; border-radius:3px; font-weight:bold;'>SOLD</div>", unsafe_allow_html=True)
                    
                    with button_col2:
                        if not player_sold and not player_bought:
                            # Replace the bid button with direct bid options
                            st.markdown("### Bid Options")
                            
                            # Get values for bidding
                            recommended = float(player['Recommended']) if pd.notna(player['Recommended']) else None
                            value_score = float(player['Value_Score']) if pd.notna(player['Value_Score']) else 1.0
                            is_high_priority = (player['Auction_Priority'] == "High") if pd.notna(player['Auction_Priority']) and 'Auction_Priority' in player else False
                            current_budget = st.session_state.remaining_budget
                            
                            # Calculate max bid
                            try:
                                max_bid = calculate_max_bid(current_budget, 
                                                                 TEAM_SIZE - len(st.session_state.team_players), 
                                                                 value_score, is_high_priority)
                                st.write(f"Max bid: ₹{max_bid}M")
                            except:
                                max_bid = None
                            
                            # Recommended price
                            if recommended:
                                st.write(f"Rec: ₹{recommended}M")
                            
                            # Bid slider
                            min_bid = 0.5
                            max_possible_bid = min(50.0, current_budget or 50.0) 
                            
                            # Initialize bid amount
                            initial_bid = recommended or max_bid or min_bid
                            if initial_bid > max_possible_bid:
                                initial_bid = max_possible_bid
                                
                            bid_amount = st.slider(
                                "Bid (₹M)", 
                                min_value=min_bid, 
                                max_value=max_possible_bid,
                                value=float(initial_bid),
                                step=0.5,
                                key=f"bid_slider_{player_name}_{idx}"
                            )
                            
                            # Final price input
                            final_price = st.number_input(
                                "Final Price (₹M)",
                                min_value=0.0,
                                max_value=max_possible_bid,
                                value=bid_amount,
                                step=0.5,
                                key=f"final_price_{player_name}_{idx}"
                            )
                            
                            # Confirm bid button
                            confirm_key = f"confirm_bid_{player_name}_{idx}"
                            if st.button("Confirm Bid", key=confirm_key):
                                # Get default values for required fields
                                player_price = float(player['Price']) if pd.notna(player['Price']) else 0
                                player_tier = int(player['Tier']) if pd.notna(player['Tier']) else 4
                                player_gender = player['Gender'] if pd.notna(player['Gender']) else "Not specified"
                                player_position = player['Primary_Position'] if pd.notna(player['Primary_Position']) else "Not specified"
                                player_value = float(player['Value_Score']) if pd.notna(player['Value_Score']) else 1.0
                                
                                # Check if we can afford the player
                                if final_price <= st.session_state.remaining_budget:
                                    # Add to team with bid information
                                    st.session_state.team_players.append({
                                        'Player': player_name,
                                        'Tier': player_tier,
                                        'Price': player_price,
                                        'Gender': player_gender,
                                        'Position': player_position,
                                        'Value_Score': player_value,
                                        'Bid': bid_amount,
                                        'Final_Price': final_price
                                    })
                                    # Update budget based on final price
                                    st.session_state.remaining_budget -= final_price
                                    # Add to bid history
                                    st.session_state.bid_history[player_name] = {
                                        'bid': bid_amount,
                                        'final_price': final_price
                                    }
                                    st.success(f"Acquired {player_name} for ₹{final_price}M!")
                                    st.rerun()
                                else:
                                    st.error(f"Not enough budget to pay ₹{final_price}M!")
                        
                        elif player_sold:
                            # Mark as available button with unique key
                            avail_key = f"avail_{player_name}_{idx}_{current_page}"
                            if st.button(f"Mark Available", key=avail_key):
                                st.session_state.sold_players.remove(player_name)
                                st.success(f"Marked {player_name} as available.")
                                st.rerun()
                        elif player_bought:
                            # Show bid info if available
                            for team_player in st.session_state.team_players:
                                if team_player['Player'] == player_name:
                                    if 'Bid' in team_player and team_player['Bid'] is not None:
                                        st.write(f"Bid: ₹{team_player['Bid']}M")
                                        st.write(f"Final: ₹{team_player['Final_Price']}M")
                                    break
                    
                    with button_col3:
                        # Button to mark player as sold to another team
                        if not player_sold and not player_bought:
                            sold_key = f"sold_{player_name}_{idx}_{current_page}"
                            if st.button(f"Mark as Sold", key=sold_key):
                                st.session_state.sold_players.append(player_name)
                                st.info(f"Marked {player_name} as sold to another team.")
                                st.rerun()
                        
                        # Add comparison button
                        compare_key = f"compare_{player_name}_{idx}_{current_page}"
                        if st.button("Compare", key=compare_key):
                            st.session_state.comparison_player = player_name
                            st.success(f"Added {player_name} to comparison.")
                    
                    st.markdown('</div>', unsafe_allow_html=True)
                    
        except Exception as e:
            st.error(f"Error displaying players: {str(e)}")
            import traceback
            st.code(traceback.format_exc())

# Function to display team builder tab
def show_team_builder_tab(tab, auction_guide):
    with tab:
        st.header("Team Builder")
        
        # Budget summary at the very top
        total_team_price = sum([p.get('Final_Price', p.get('Price', 0)) for p in st.session_state.team_players])
        remaining_budget = st.session_state.remaining_budget
        players_needed = TEAM_SIZE - len(st.session_state.team_players)
        avg_per_player = remaining_budget / players_needed if players_needed > 0 else 0
        
        # Display budget metrics in a prominent way at the top
        budget_cols = st.columns(3)
        with budget_cols[0]:
            st.metric("Budget Remaining", f"₹{remaining_budget:.1f}M", f"{(remaining_budget/TOTAL_BUDGET)*100:.1f}% left")
        with budget_cols[1]:
            st.metric("Budget Used", f"₹{total_team_price:.1f}M", f"{(total_team_price/TOTAL_BUDGET)*100:.1f}% used")
        with budget_cols[2]:
            st.metric("Avg. Per Remaining Player", f"₹{avg_per_player:.1f}M", f"{players_needed} players needed")
        
        st.markdown("---")
        
        # Team summary and budget in a single column layout
        st.subheader("Current Team")
        
        if len(st.session_state.team_players) == 0:
            st.info("No players added to your team yet.")
        else:
            # Team table
            team_df = pd.DataFrame(st.session_state.team_players)
            
            # Calculate stats
            avg_team_value = team_df['Value_Score'].mean()
            non_cis_count = len(team_df[team_df['Gender'] == 'Women'])
            
            # Display team table with sortable columns and bid information
            if 'Bid' in team_df.columns and 'Final_Price' in team_df.columns:
                # Create a better display format with bid information
                display_df = team_df.copy()
                # Format bid and final price for display
                display_df['Price Info'] = display_df.apply(
                    lambda row: f"₹{row['Final_Price']}M (Bid: ₹{row['Bid']}M)" if pd.notna(row['Bid']) else f"₹{row['Price']}M", 
                    axis=1
                )
                # Select columns to display
                display_cols = ['Player', 'Tier', 'Position', 'Gender', 'Value_Score', 'Price Info']
                display_df = display_df[display_cols] if all(col in display_df.columns for col in display_cols) else display_df
                st.dataframe(display_df.style.background_gradient(subset=['Value_Score'], cmap='RdYlGn'), use_container_width=True)
            else:
                st.dataframe(team_df.style.background_gradient(subset=['Value_Score'], cmap='RdYlGn'), use_container_width=True)
            
            # Performance metrics with visual indicators - removed budget metric which is now at the top
            st.markdown("### Team Performance Metrics")
            metrics_col1, metrics_col2 = st.columns(2)
            
            with metrics_col1:
                value_status = "Excellent" if avg_team_value >= 1.5 else "Good" if avg_team_value >= 1.2 else "Average" if avg_team_value >= 1.0 else "Poor"
                st.metric("Value Efficiency", f"{avg_team_value:.2f}", value_status)
            
            with metrics_col2:
                non_cis_status = f"{non_cis_count}/{MIN_NON_CIS}" + (" ✅" if non_cis_count >= MIN_NON_CIS else " ❌")
                st.metric("Non-CIS Count", non_cis_count, non_cis_status)
            
            # Team completeness  
            st.progress((len(team_df)/TEAM_SIZE), text=f"Team Completion: {len(team_df)}/{TEAM_SIZE} players")
            
            # Display warning if non-cis requirement not met
            if non_cis_count < MIN_NON_CIS and len(team_df) >= TEAM_SIZE:
                st.warning(f"⚠️ You need at least {MIN_NON_CIS} non-cis players in your team!")

        # Team actions
        st.subheader("Team Actions")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Reset Team", key="reset_team_builder"):
                st.session_state.team_players = []
                st.session_state.remaining_budget = TOTAL_BUDGET
                st.success("Team reset successfully.")
                st.rerun()
        
        # Player search section in team builder
        st.markdown("---")
        st.subheader("Player Search")
        
        # Simple search box
        search_col1, search_col2 = st.columns([3, 1])
        with search_col1:
            search_query = st.text_input("Search for players to add", key="team_builder_search")
        with search_col2:
            search_button = st.button("Search", key="team_builder_search_btn")
        
        # Filter options
        filter_col1, filter_col2, filter_col3 = st.columns(3)
        with filter_col1:
            position_options = ["All"]
            if 'Primary_Position' in auction_guide.columns:
                unique_positions = auction_guide["Primary_Position"].dropna().unique().tolist()
                position_options += sorted(unique_positions)
            position_filter = st.selectbox("Position", position_options, key="team_builder_position")
        
        with filter_col2:
            tier_options = ["All"]
            if 'Tier' in auction_guide.columns:
                unique_tiers = sorted(auction_guide["Tier"].dropna().unique().tolist())
                tier_options += [int(t) for t in unique_tiers if pd.notna(t)]
            tier_filter = st.selectbox("Tier", tier_options, key="team_builder_tier")
        
        with filter_col3:
            gender_options = ["All"]
            if 'Gender' in auction_guide.columns:
                gender_options += sorted(auction_guide["Gender"].dropna().unique().tolist())
            gender_filter = st.selectbox("Gender", gender_options, key="team_builder_gender")
        
        # Search results
        if search_query or search_button:
            # Filter available players
            filtered_players = auction_guide.copy()
            
            # Apply search filter
            if search_query:
                filtered_players = filtered_players[filtered_players["Player"].str.contains(search_query, case=False, na=False)]
            
            # Apply other filters
            if position_filter != "All" and 'Primary_Position' in filtered_players.columns:
                filtered_players = filtered_players[
                    (filtered_players["Primary_Position"].str.contains(position_filter, case=False, na=False)) | 
                    (filtered_players["Primary_Position"].isna() & (position_filter == "All"))
                ]
            
            if tier_filter != "All" and 'Tier' in filtered_players.columns:
                filtered_players = filtered_players[
                    (filtered_players["Tier"] == tier_filter) | 
                    (filtered_players["Tier"].isna() & (tier_filter == "All"))
                ]
            
            if gender_filter != "All" and 'Gender' in filtered_players.columns:
                filtered_players = filtered_players[
                    (filtered_players["Gender"] == gender_filter) | 
                    (filtered_players["Gender"].isna() & (gender_filter == "All"))
                ]
            
            # Show only available players (not in sold list or team)
            existing_players = [p['Player'] for p in st.session_state.team_players]
            filtered_players = filtered_players[~filtered_players["Player"].isin(st.session_state.sold_players + existing_players)]
            
            # Display search results
            if not filtered_players.empty:
                st.write(f"Found {len(filtered_players)} players")
                
                # Limit display to top 10 players
                display_players = filtered_players.head(10)
                
                # Display in a grid of cards
                cols_per_row = 2
                for i in range(0, len(display_players), cols_per_row):
                    row_cols = st.columns(cols_per_row)
                    for j in range(cols_per_row):
                        idx = i + j
                        if idx < len(display_players):
                            player = display_players.iloc[idx]
                            player_name = player['Player'] if pd.notna(player['Player']) else "Unknown Player"
                            
                            with row_cols[j]:
                                with st.container():
                                    st.markdown(f"### {player_name}")
                                    
                                    # Player details - enhanced with more information
                                    col1, col2 = st.columns(2)
                                    with col1:
                                        if pd.notna(player['Tier']):
                                            try:
                                                tier_value = int(player['Tier'])
                                                st.markdown(f"**Tier:** {tier_value}")
                                            except:
                                                st.write("**Tier:** Unknown")
                                        
                                        gender = player['Gender'] if pd.notna(player['Gender']) else "Not specified"
                                        st.write(f"**Gender:** {gender}")
                                        
                                        position = player['Primary_Position'] if pd.notna(player['Primary_Position']) else "Not specified"
                                        st.write(f"**Position:** {position}")
                                        
                                        if 'APL_Editions' in player and pd.notna(player['APL_Editions']):
                                            st.write(f"**APL Editions:** {player['APL_Editions']}")
                                        
                                        if 'Secondary_Position' in player and pd.notna(player['Secondary_Position']):
                                            st.write(f"**Secondary Position:** {player['Secondary_Position']}")
                                    
                                    with col2:
                                        if pd.notna(player['Price']):
                                            st.write(f"**Price:** ₹{player['Price']}M")
                                        
                                        if pd.notna(player['Value_Score']):
                                            value_class = get_value_class(player['Value_Score'])
                                            st.markdown(f"**Value:** {player['Value_Score']:.2f}")
                                        
                                        if pd.notna(player['Recommended']):
                                            st.write(f"**Recommended:** ₹{player['Recommended']}M")
                                            
                                        if 'Historical_Avg' in player and pd.notna(player['Historical_Avg']):
                                            st.write(f"**Historical Avg:** ₹{player['Historical_Avg']}M")
                                            
                                        if 'Auction_Score' in player and pd.notna(player['Auction_Score']):
                                            st.write(f"**Auction Score:** {player['Auction_Score']}")
                                    
                                    # Additional player details if available
                                    if ('Bidding_Strategy' in player and pd.notna(player['Bidding_Strategy'])) or \
                                       ('Selection_Reason' in player and pd.notna(player['Selection_Reason'])):
                                        st.markdown("---")
                                        
                                        if 'Bidding_Strategy' in player and pd.notna(player['Bidding_Strategy']):
                                            st.write(f"**Bidding Strategy:** {player['Bidding_Strategy']}")
                                            
                                        if 'Selection_Reason' in player and pd.notna(player['Selection_Reason']):
                                            st.write(f"**Selection Reason:** {player['Selection_Reason']}")
                                    
                                    # Action buttons - now in 3 columns to include Mark as Sold
                                    st.markdown("---")
                                    button_col1, button_col2, button_col3 = st.columns(3)
                                    with button_col1:
                                        # Add to team button
                                        add_key = f"add_team_{player_name}_{idx}"
                                        if st.button("Add to Team", key=add_key):
                                            # Get default values for required fields
                                            player_price = float(player['Price']) if pd.notna(player['Price']) else 0
                                            player_tier = int(player['Tier']) if pd.notna(player['Tier']) else 4
                                            player_gender = player['Gender'] if pd.notna(player['Gender']) else "Not specified"
                                            player_position = player['Primary_Position'] if pd.notna(player['Primary_Position']) else "Not specified"
                                            player_value = float(player['Value_Score']) if pd.notna(player['Value_Score']) else 1.0
                                            
                                            # Check if we can afford the player
                                            if player_price <= st.session_state.remaining_budget:
                                                st.session_state.team_players.append({
                                                    'Player': player_name,
                                                    'Tier': player_tier,
                                                    'Price': player_price,
                                                    'Gender': player_gender,
                                                    'Position': player_position,
                                                    'Value_Score': player_value,
                                                    'Bid': None,
                                                    'Final_Price': player_price
                                                })
                                                st.session_state.remaining_budget -= player_price
                                                st.success(f"Added {player_name} to your team!")
                                                st.rerun()
                                            else:
                                                st.error(f"Not enough budget to add this player (₹{player_price}M)!")
                                    
                                    with button_col2:
                                        # Bid button
                                        bid_key = f"bid_team_{player_name}_{idx}"
                                        if st.button("Bid", key=bid_key):
                                            st.session_state.current_bid_player = player_name
                                            st.rerun()
                                    
                                    with button_col3:
                                        # Mark as Sold button
                                        sold_key = f"sold_team_{player_name}_{idx}"
                                        if st.button("Mark as Sold", key=sold_key):
                                            st.session_state.sold_players.append(player_name)
                                            st.info(f"Marked {player_name} as sold to another team.")
                                            st.rerun()
                                        
                                    # Show bid modal if this is the current bid player
                                    if st.session_state.current_bid_player == player_name:
                                        # Get values for the bid modal
                                        recommended = float(player['Recommended']) if pd.notna(player['Recommended']) else None
                                        value_score = float(player['Value_Score']) if pd.notna(player['Value_Score']) else 1.0
                                        is_high_priority = (player['Auction_Priority'] == "High") if pd.notna(player['Auction_Priority']) and 'Auction_Priority' in player else False
                                        
                                        try:
                                            max_bid = calculate_max_bid(st.session_state.remaining_budget, 
                                                                     TEAM_SIZE - len(st.session_state.team_players), 
                                                                     value_score, is_high_priority)
                                        except:
                                            max_bid = None
                                        
                                        # Show bid modal and get result
                                        bid_result = show_bid_modal(
                                            player_name, 
                                            recommended_price=recommended, 
                                            max_bid=max_bid,
                                            current_budget=st.session_state.remaining_budget
                                        )
                                        
                                        # Process bid result
                                        if bid_result["action"] == "confirm":
                                            # Get default values for required fields
                                            player_price = float(player['Price']) if pd.notna(player['Price']) else 0
                                            player_tier = int(player['Tier']) if pd.notna(player['Tier']) else 4
                                            player_gender = player['Gender'] if pd.notna(player['Gender']) else "Not specified"
                                            player_position = player['Primary_Position'] if pd.notna(player['Primary_Position']) else "Not specified"
                                            player_value = float(player['Value_Score']) if pd.notna(player['Value_Score']) else 1.0
                                            
                                            # Check if we can afford the player
                                            if bid_result["final_price"] <= st.session_state.remaining_budget:
                                                # Add to team with bid information
                                                st.session_state.team_players.append({
                                                    'Player': player_name,
                                                    'Tier': player_tier,
                                                    'Price': player_price,
                                                    'Gender': player_gender,
                                                    'Position': player_position,
                                                    'Value_Score': player_value,
                                                    'Bid': bid_result["bid"],
                                                    'Final_Price': bid_result["final_price"]
                                                })
                                                # Update budget based on final price
                                                st.session_state.remaining_budget -= bid_result["final_price"]
                                                # Add to bid history
                                                st.session_state.bid_history[player_name] = {
                                                    'bid': bid_result["bid"],
                                                    'final_price': bid_result["final_price"]
                                                }
                                                # Clear current bid player
                                                st.session_state.current_bid_player = None
                                                st.success(f"Successfully bid ₹{bid_result['bid']}M and acquired {player_name} for ₹{bid_result['final_price']}M!")
                                                st.rerun()
                                            else:
                                                st.error(f"Not enough budget to pay ₹{bid_result['final_price']}M for this player!")
                                        elif bid_result["action"] == "cancel":
                                            # Clear current bid player
                                            st.session_state.current_bid_player = None
                                            st.rerun()
                                    
                                    st.markdown("---")
            else:
                st.info("No players found matching your search criteria.")
        
        # Team composition section - moved to be a separate section
        st.markdown("---")
        st.subheader("Team Composition")
        
        if len(st.session_state.team_players) > 0:
            team_df = pd.DataFrame(st.session_state.team_players)
            
            # Create a row of charts
            chart_cols = st.columns(3)
            
            # Tier distribution pie chart in first column
            with chart_cols[0]:
                tier_counts = team_df['Tier'].value_counts().reset_index()
                tier_counts.columns = ['Tier', 'Count']
                
                fig = px.pie(
                    tier_counts, 
                    values='Count', 
                    names='Tier', 
                    title='Players by Tier',
                    color='Tier',
                    color_discrete_map={
                        1: '#FF9800',
                        2: '#2196F3',
                        3: '#4CAF50',
                        4: '#9C27B0'
                    }
                )
                fig.update_traces(textinfo='percent+label')
                fig.update_layout(height=250)
                st.plotly_chart(fig, use_container_width=True)
            
            # Budget allocation by position in second column
            with chart_cols[1]:
                if 'Position' in team_df.columns:
                    # Get actual price paid (final price or regular price)
                    team_df['Actual_Price'] = team_df.apply(
                        lambda row: row.get('Final_Price', row.get('Price', 0)), 
                        axis=1
                    )
                    position_budget = team_df.groupby('Position')['Actual_Price'].sum().reset_index()
                    position_budget = position_budget.sort_values('Actual_Price', ascending=False)
                    
                    fig = px.bar(
                        position_budget,
                        x='Position',
                        y='Actual_Price',
                        title='Budget by Position (₹M)',
                        color='Position',
                    )
                    fig.update_layout(height=250)
                    st.plotly_chart(fig, use_container_width=True)
            
            # Gender distribution in third column
            with chart_cols[2]:
                gender_counts = team_df['Gender'].value_counts().reset_index()
                gender_counts.columns = ['Gender', 'Count']
                
                fig = px.bar(
                    gender_counts,
                    x='Gender',
                    y='Count',
                    title='Gender Distribution',
                    color='Gender',
                    color_discrete_map={
                        'Men': '#2196F3',
                        'Women': '#E91E63'
                    }
                )
                fig.update_layout(height=250)
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Add players to see team composition.")
        
        # Team optimization suggestions
        st.markdown("---")
        st.subheader("Team Optimization Suggestions")
        
        if len(st.session_state.team_players) > 0:
            team_df = pd.DataFrame(st.session_state.team_players)
            remaining_budget = st.session_state.remaining_budget
            remaining_slots = TEAM_SIZE - len(team_df)
            non_cis_count = len(team_df[team_df['Gender'] == 'Women'])
            non_cis_needed = max(0, MIN_NON_CIS - non_cis_count)
            
            # Team balance analysis
            st.markdown("### Team Balance Analysis")
            
            # Position analysis if we have position data
            if 'Position' in team_df.columns:
                # Count players by position
                position_counts = team_df['Position'].value_counts().to_dict()
                
                # Define ideal counts
                ideal_counts = {
                    'Forward': 3,
                    'Midfielder': 3,
                    'Defender': 3, 
                    'Goalkeeper': 1
                }
                
                # Check position balance
                position_advice = []
                for position, ideal in ideal_counts.items():
                    current = position_counts.get(position, 0)
                    if current < ideal and remaining_slots > 0:
                        position_advice.append(f"Need {ideal - current} more {position}s")
                    elif current > ideal:
                        position_advice.append(f"Have {current - ideal} extra {position}s")
                
                if position_advice:
                    st.info("📊 **Position Balance:** " + " | ".join(position_advice))
            
            # Suggestions based on team composition
            if remaining_slots > 0:
                st.write(f"You need {remaining_slots} more players with ₹{remaining_budget:.1f}M remaining (₹{remaining_budget/remaining_slots:.1f}M per player).")
                
                # Gender requirement suggestion
                if non_cis_needed > 0:
                    st.warning(f"⚠️ **Priority Alert:** You need {non_cis_needed} more non-cis players to meet the requirement.")
                    
                    # Get top non-cis players within budget
                    avg_budget_per_player = remaining_budget / remaining_slots
                    affordable_non_cis = auction_guide[
                        (auction_guide['Gender'] == 'Women') & 
                        (auction_guide['Price'] <= remaining_budget) &
                        (~auction_guide['Player'].isin([p['Player'] for p in st.session_state.team_players])) &
                        (~auction_guide['Player'].isin(st.session_state.sold_players))
                    ].sort_values('Value_Score', ascending=False)
                    
                    if len(affordable_non_cis) > 0:
                        st.markdown("#### Top Non-CIS Recommendations:")
                        
                        # Create a clean table of recommendations
                        non_cis_display = affordable_non_cis.head(3)[['Player', 'Tier', 'Primary_Position', 'Price', 'Value_Score']].copy()
                        non_cis_display.columns = ['Player', 'Tier', 'Position', 'Price (₹M)', 'Value']
                        st.table(non_cis_display)
                    else:
                        st.error("No affordable non-cis players found within your remaining budget!")
                
                # Value analysis
                if len(team_df) > 0:
                    avg_value = team_df['Value_Score'].mean()
                    if avg_value < 1.2 and remaining_slots > 0:
                        st.warning("⚠️ **Value Alert:** Your team's average value is below optimal. Consider targeting higher value players.")
                
                # Best value picks with remaining budget
                st.subheader("Best Available Players Within Budget")
                
                affordable_players = auction_guide[
                    (auction_guide['Price'] <= remaining_budget) &
                    (~auction_guide['Player'].isin([p['Player'] for p in st.session_state.team_players])) &
                    (~auction_guide['Player'].isin(st.session_state.sold_players))
                ].sort_values('Value_Score', ascending=False)
                
                if len(affordable_players) > 0:
                    # Create tabs for different recommendation types
                    pick_tabs = st.tabs(["Best Value", "Budget Picks", "Premium Options"])
                    
                    with pick_tabs[0]:
                        # Best value regardless of price
                        best_value = affordable_players.head(5)
                        st.dataframe(
                            best_value[['Player', 'Gender', 'Tier', 'Primary_Position', 'Price', 'Value_Score', 'Recommended']],
                            use_container_width=True
                        )
                    
                    with pick_tabs[1]:
                        # Budget picks (lower price)
                        budget_picks = affordable_players[affordable_players['Price'] <= remaining_budget/remaining_slots].sort_values('Value_Score', ascending=False).head(5)
                        st.dataframe(
                            budget_picks[['Player', 'Gender', 'Tier', 'Primary_Position', 'Price', 'Value_Score', 'Recommended']],
                            use_container_width=True
                        )
                        
                    with pick_tabs[2]:
                        # Premium options (higher price)
                        premium_picks = affordable_players[affordable_players['Tier'] <= 2].sort_values('Value_Score', ascending=False).head(5)
                        st.dataframe(
                            premium_picks[['Player', 'Gender', 'Tier', 'Primary_Position', 'Price', 'Value_Score', 'Recommended']],
                            use_container_width=True
                        )
                        
                    # Button to view all affordable players
                    if st.button("View All Affordable Players"):
                        st.session_state.price_range_min = 0.0
                        st.session_state.price_range_max = float(remaining_budget)
                        st.session_state.search_query = ""
                        st.session_state.show_top_picks = False
                        st.rerun()
                else:
                    st.error("No affordable players found within your remaining budget!")
            else:
                # Team is complete
                st.success("✅ Your team is complete!")
                
                # Team quality assessment
                team_df = pd.DataFrame(st.session_state.team_players)
                avg_value = team_df['Value_Score'].mean()
                value_rating = "Excellent" if avg_value >= 1.5 else "Good" if avg_value >= 1.2 else "Average" if avg_value >= 1.0 else "Poor"
                
                st.markdown(f"### Team Quality Assessment: **{value_rating}**")
                
                # More detailed analysis
                tier1_count = len(team_df[team_df['Tier'] == 1])
                tier2_count = len(team_df[team_df['Tier'] == 2])
                
                if tier1_count == 0:
                    st.info("📝 **Note:** Your team has no Tier 1 players. This can work if you have strong Tier 2 players.")
                
                if tier1_count + tier2_count < 3:
                    st.info("📝 **Note:** Your team is weighted toward lower-tier players, which may lack star power.")
                
                # Check for non-cis requirement
                if non_cis_count < MIN_NON_CIS:
                    st.error(f"❌ Your team doesn't meet the non-cis requirement ({non_cis_count}/{MIN_NON_CIS})!")
                    
                    # Suggestions to fix
                    st.write("Consider replacing a male player with a female player:")
                    
                    # Get male players in team
                    male_players = team_df[team_df['Gender'] == 'Men']
                    
                    # Get affordable female players
                    for _, male_player in male_players.iterrows():
                        budget_with_swap = remaining_budget + male_player['Price']
                        
                        affordable_females = auction_guide[
                            (auction_guide['Gender'] == 'Women') & 
                            (auction_guide['Price'] <= budget_with_swap) &
                            (~auction_guide['Player'].isin([p['Player'] for p in st.session_state.team_players])) &
                            (~auction_guide['Player'].isin(st.session_state.sold_players))
                        ].sort_values('Value_Score', ascending=False)
                        
                        if len(affordable_females) > 0:
                            st.write(f"Replace {male_player['Player']} (₹{male_player['Price']}M) with:")
                            for _, female_player in affordable_females.head(2).iterrows():
                                net_change = female_player['Price'] - male_player['Price']
                                st.write(f"- {female_player['Player']} (Tier {int(female_player['Tier'])}) - ₹{female_player['Price']}M, Net Budget Change: ₹{net_change:.1f}M")
                        
                        if len(affordable_females) == 0:
                            st.write(f"No affordable female players found to replace {male_player['Player']} (₹{male_player['Price']}M)")
        else:
            st.info("Add players to your team to see optimization suggestions.")

# Function to display info tab with detailed metrics explanation
def show_info_tab(tab):
    with tab:
        st.header("APL Auction Metrics Guide")
        
        st.markdown("""
        ## Understanding Auction Metrics
        
        This comprehensive guide explains how all key metrics and scores are calculated
        for the APL 8 auction. Use this information to make more informed decisions about
        player valuation and team building.
        """)
        
        # Create tabs for different metric categories
        metric_tabs = st.tabs(["Value Score", "Auction Score", "Price Calculations", "Team Building", "Glossary"])
        
        with metric_tabs[0]:
            st.markdown("""
            # Value Score Explained
            
            ## What is Value Score?
            
            The Value Score is a metric ranging from 0 to 3+ that indicates how much value a player provides at their price point.
            This is the most important metric for auction strategy as it helps identify undervalued players.
            
            ## Score Interpretation
            
            - **Excellent Value (≥2.0)**: Player is significantly underpriced and provides exceptional value
            - **Good Value (1.5-1.99)**: Player is underpriced and provides above-average value
            - **Fair Value (1.0-1.49)**: Player is appropriately priced
            - **Poor Value (<1.0)**: Player is overpriced relative to their expected contribution
            
            ## Calculation Formula
            
            ```
            Value_Score = (Player_Adjusted_Rating / Player_Price) × Price_Scaling_Factor
            ```
            
            Where:
            - **Player_Adjusted_Rating**: A composite score based on:
              - Historical performance in previous APL editions
              - Performance consistency across editions
              - Tier rating (inherent skill level)
              - Positional impact assessment
            
            - **Price_Scaling_Factor**: Adjusts for the different price ranges across tiers:
              - Tier 1: 1.0x
              - Tier 2: 1.2x
              - Tier 3: 1.4x
              - Tier 4: 1.6x
            
            This scaling acknowledges that lower tier players are expected to provide less absolute value,
            but can still be valuable relative to their lower price points.
            
            ## Example Calculation
            
            For a Tier 3 player with:
            - Adjusted Rating: 30
            - Price: ₹20M
            - Tier Scaling Factor: 1.4
            
            ```
            Value_Score = (30 / 20) × 1.4 = 2.1
            ```
            
            This would be considered an excellent value at 2.1.
            """)
            
        with metric_tabs[1]:
            st.markdown("""
            # Auction Score Explained
            
            ## What is Auction Score?
            
            The Auction Score is a comprehensive rating from 0-10 that combines multiple factors to indicate 
            a player's overall desirability during an auction. It helps prioritize players when making bidding decisions.
            
            ## Score Components
            
            The Auction Score is calculated as a weighted combination of:
            
            1. **Value Score (40%)**: The player's value rating
            2. **Player Quality (25%)**: Absolute player skill level (primarily based on tier)
            3. **Team Fit (15%)**: How well the player matches positional needs
            4. **Historical Consistency (10%)**: Reliability across APL editions
            5. **Budget Fit (10%)**: How well the player fits within budget constraints
            
            ## Formula Breakdown
            
            ```
            Auction_Score = (0.4 × Value_Component) + 
                           (0.25 × Quality_Component) + 
                           (0.15 × Team_Fit_Component) + 
                           (0.1 × Historical_Component) + 
                           (0.1 × Budget_Component)
            ```
            
            Each component is normalized to a 0-10 scale before being combined.
            
            ## Example Interpretation
            
            - **8-10**: Must-have players, worth aggressive bidding
            - **6-8**: Strong targets, bid confidently up to recommended price
            - **4-6**: Solid options, good value at or below recommended price
            - **2-4**: Consider only if price falls well below recommendations
            - **0-2**: Avoid unless extremely underpriced
            """)
            
        with metric_tabs[2]:
            st.markdown("""
            # Price Calculations
            
            ## Historical Average Price
            
            The historical average price is calculated from previous APL editions where the player participated:
            
            ```
            Historical_Avg = Sum of prices across APL editions / Number of editions
            ```
            
            ## Recommended Price
            
            The recommended price builds on historical average with adjustments:
            
            ```
            Recommended_Price = Historical_Avg × Value_Factor × Inflation_Adjustment
            ```
            
            Where:
            - **Value_Factor**: Adjustment based on performance trend (0.8-1.2)
            - **Inflation_Adjustment**: APL price inflation factor (1.1 for this edition)
            
            For new players without historical data:
            ```
            Recommended_Price = Tier_Base_Price × Performance_Adjustment
            ```
            
            Where tier base prices are:
            - Tier 1: ₹75M
            - Tier 2: ₹40M
            - Tier 3: ₹15M
            - Tier 4: ₹5M
            
            ## Maximum Bid Calculation
            
            The maximum bid calculation is dynamic based on team needs:
            
            ```
            Max_Bid = (Remaining_Budget / Players_Needed) × Value_Adjustment
            ```
            
            Where Value_Adjustment is:
            - For high priority players: 1.5 + (Value_Score - 1) × 0.5
            - For other players: 1 + (Value_Score - 1) × 0.3
            
            This ensures you can bid more aggressively on high-value players while maintaining budget discipline.
            """)
            
        with metric_tabs[3]:
            st.markdown("""
            # Team Building Guidelines
            
            ## Team Composition Requirements
            
            - **Total Players**: 10 players per team
            - **Gender Requirement**: Minimum 2 non-CIS (women) players
            - **Budget**: ₹150M total
            
            ## Recommended Position Distribution
            
            - **Forwards**: 3 players (30-40% of budget)
            - **Midfielders**: 3 players (25-35% of budget)
            - **Defenders**: 3 players (15-25% of budget)
            - **Goalkeeper**: 1 player (5-15% of budget)
            
            ## Tier Distribution Strategies
            
            ### Balanced Approach
            - 1-2 Tier 1 players
            - 2-3 Tier 2 players
            - 3-4 Tier 3 players
            - 2-3 Tier 4 players
            
            ### Star Power Approach
            - 2-3 Tier 1 players
            - 1-2 Tier 2 players
            - 2-3 Tier 3 players
            - 3-4 Tier 4 players
            
            ### Value Maximization Approach
            - 0-1 Tier 1 players
            - 3-4 Tier 2 players
            - 4-5 Tier 3 players
            - 1-2 Tier 4 players
            
            ## Budget Allocation Principles
            
            1. **Core vs. Support**: Allocate 60-70% to core players (4-5 players)
            2. **Positional Weighting**: Premium on forwards and creative midfielders
            3. **Value Targeting**: Prioritize players with Value Score > 1.5
            4. **Reserve Flexibility**: Keep 5-10% in reserve for opportunities
            """)
            
        with metric_tabs[4]:
            st.markdown("""
            # Glossary of Terms
            
            ## Player Categories
            
            - **Tier**: Fundamental skill classification (1-4, with 1 being highest)
            - **Primary Position**: Player's main playing position
            - **Secondary Position**: Alternative position capability
            - **Gender**: Men or Women (minimum 2 women required per team)
            
            ## Value Metrics
            
            - **Value Score**: Measure of player's value relative to price (higher is better)
            - **Auction Score**: Overall auction desirability on 0-10 scale
            - **Auction Priority**: High/Medium/Low classification for auction targeting
            
            ## Price Components
            
            - **Price**: Listed auction price in millions (₹M)
            - **Historical Average**: Average price from previous APL editions
            - **Recommended Price**: Suggested maximum bid amount
            - **Maximum Bid**: Dynamic calculation of highest justifiable bid based on team situation
            
            ## Strategic Terms
            
            - **Bidding Strategy**: Specific auction approach for each player
            - **Selection Reason**: Justification for player's inclusion in top picks
            - **Value Tier**: Classification based on Value Score (Excellent/Good/Fair/Poor)
            - **Budget Fit**: How well a player fits within remaining team budget
            """)

# Add this function after the calculate_max_bid function
def show_bid_modal(player_name, recommended_price=None, max_bid=None, current_budget=None):
    """Display bid modal with slider for bid amount and input for final price"""
    # Show budget and recommendation
    st.subheader(f"Place Bid for {player_name}")
    
    if current_budget:
        st.info(f"Remaining Budget: ₹{current_budget}M")
    
    if recommended_price:
        st.write(f"Recommended Price: ₹{recommended_price}M")
    
    if max_bid:
        st.write(f"Maximum Bid: ₹{max_bid}M")
    
    # Bid slider
    min_bid = 0.5
    max_possible_bid = min(100.0, current_budget or 100.0) 
    
    # Initialize bid amount
    initial_bid = recommended_price or max_bid or min_bid
    if initial_bid > max_possible_bid:
        initial_bid = max_possible_bid
        
    bid_amount = st.slider(
        "Your Bid (₹M)", 
        min_value=min_bid, 
        max_value=max_possible_bid,
        value=float(initial_bid),
        step=0.5
    )

    # Final price input
    final_price = st.number_input(
        "Final Price Paid (₹M)",
        min_value=0.0,
        max_value=max_possible_bid,
        value=bid_amount,
        step=0.5
    )
    
    # Buttons - without using columns
    if st.button("Confirm and Add to Team", key=f"confirm_bid_{player_name}"):
        return {"bid": bid_amount, "final_price": final_price, "action": "confirm"}
    
    if st.button("Cancel", key=f"cancel_bid_{player_name}"):
        return {"action": "cancel"}
    
    return {"action": "pending"}

# Main function
def main():
    # Initialize session state
    init_session_state()
    
    # Load data
    auction_guide, top_picks, master_data = load_data()
    
    # Display header
    tabs = show_header()
    
    # Display budget meter
    remaining_budget = st.session_state.remaining_budget
    players_needed = TEAM_SIZE - len(st.session_state.team_players)
    show_budget(remaining_budget, players_needed)
    
    # Display tabs
    show_team_builder_tab(tabs[0], auction_guide)
    show_player_search_tab(auction_guide, tabs[1])
    show_top_targets_tab(top_picks, tabs[2])
    show_simulation_tab(auction_guide, tabs[3])
    show_info_tab(tabs[4])

if __name__ == "__main__":
    main() 