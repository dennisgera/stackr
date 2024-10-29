# frontend/pages/analytics.py
import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

API_URL = "http://backend:8000"

def load_items():
    response = requests.get(f"{API_URL}/items/")
    if response.status_code == 200:
        return response.json()
    return []

def load_item_history(item_id: int):
    response = requests.get(f"{API_URL}/inventory/{item_id}")
    if response.status_code == 200:
        return response.json()
    return []

st.set_page_config(page_title="Inventory Analytics", layout="wide")

def main():
    st.title("Inventory Analytics")
    
    # Load items
    items = load_items()
    if not items:
        st.warning("No items found. Please add items first.")
        return
    
    # Create tabs for different analytics views
    tab1, tab2 = st.tabs(["Item Analysis", "Overview"])
    
    with tab1:
        st.subheader("Item Analysis")
        
        # Item selection
        item_names = {item["name"]: item["id"] for item in items}
        selected_item_name = st.selectbox(
            "Select Item for Analysis",
            options=list(item_names.keys()),
            key="item_analysis"
        )
        selected_item_id = item_names[selected_item_name]
        
        # Load item history
        history = load_item_history(selected_item_id)
        
        if history:
            # Convert to DataFrame
            df = pd.DataFrame(history)
            df["timestamp"] = pd.to_datetime(df["timestamp"])
            
            # Time range selection
            time_range = st.selectbox(
                "Select Time Range",
                ["Last Week", "Last Month", "Last 3 Months", "All Time"]
            )
            
            # Filter data based on time range
            now = datetime.now()
            if time_range == "Last Week":
                df = df[df["timestamp"] > now - timedelta(days=7)]
            elif time_range == "Last Month":
                df = df[df["timestamp"] > now - timedelta(days=30)]
            elif time_range == "Last 3 Months":
                df = df[df["timestamp"] > now - timedelta(days=90)]
            
            # Create metrics
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric(
                    "Current Quantity",
                    f"{df['quantity'].iloc[0]:.1f}",
                    f"{df['quantity'].iloc[0] - df['quantity'].iloc[-1]:.1f}"
                )
            with col2:
                st.metric(
                    "Average Quantity",
                    f"{df['quantity'].mean():.1f}"
                )
            with col3:
                st.metric(
                    "Min Quantity",
                    f"{df['quantity'].min():.1f}"
                )
            
            # Create time series plot
            fig = px.line(
                df,
                x="timestamp",
                y="quantity",
                title=f"Inventory Level Over Time - {selected_item_name}"
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Show detailed history
            st.subheader("Detailed History")
            detailed_df = df[["timestamp", "quantity", "updated_by"]].copy()
            detailed_df["timestamp"] = detailed_df["timestamp"].dt.strftime("%Y-%m-%d %H:%M")
            st.dataframe(detailed_df, use_container_width=True)
            
    with tab2:
        st.subheader("Overview")
        
        # Create overview metrics
        overview_data = []
        for item in items:
            history = load_item_history(item["id"])
            if history:
                df = pd.DataFrame(history)
                df["timestamp"] = pd.to_datetime(df["timestamp"])
                
                overview_data.append({
                    "Item": item["name"],
                    "Current Stock": df["quantity"].iloc[0],
                    "Average Stock": df["quantity"].mean(),
                    "Min Stock": df["quantity"].min(),
                    "Max Stock": df["quantity"].max(),
                    "Updates Count": len(df),
                    "Last Updated": df["timestamp"].iloc[0]
                })
        
        if overview_data:
            overview_df = pd.DataFrame(overview_data)
            overview_df["Last Updated"] = overview_df["Last Updated"].dt.strftime("%Y-%m-%d %H:%M")
            
            # Create bar chart of current stock levels
            fig = px.bar(
                overview_df,
                x="Item",
                y="Current Stock",
                title="Current Stock Levels"
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Show overview table
            st.dataframe(overview_df, use_container_width=True)

if __name__ == "__main__":
    main()