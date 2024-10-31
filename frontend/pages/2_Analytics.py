# frontend/pages/2_Analytics.py
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import timedelta
from config import make_request

st.set_page_config(
    page_title="Analytics",
    page_icon="📈",
    layout="wide",
)

def load_items():
    """Load items with error handling"""
    response = make_request("get", "items/")
    if response and response.status_code == 200:
        return response.json()
    return []

def load_item_history(item_id: int):
    """Load item history with error handling"""
    response = make_request("get", f"inventory/{item_id}")
    if response and response.status_code == 200:
        return response.json()
    return []

def create_metrics(df: pd.DataFrame):
    """Create and display metrics with error handling"""
    col1, col2, col3 = st.columns(3)
    
    with col1:
        try:
            current = df['quantity'].iloc[0]
            change = current - df['quantity'].iloc[-1]
            st.metric(
                "Current Quantity",
                f"{current:.1f}",
                f"{change:.1f}"
            )
        except (IndexError, AttributeError):
            st.metric("Current Quantity", "No data", "0")
    
    with col2:
        try:
            average = df['quantity'].mean()
            st.metric(
                "Average Quantity",
                f"{average:.1f}" if not df.empty else "No data"
            )
        except (AttributeError, ValueError):
            st.metric("Average Quantity", "No data")
    
    with col3:
        try:
            minimum = df['quantity'].min()
            st.metric(
                "Min Quantity",
                f"{minimum:.1f}" if not df.empty else "No data"
            )
        except (AttributeError, ValueError):
            st.metric("Min Quantity", "No data")

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
            try:
                # Convert to DataFrame
                df = pd.DataFrame(history)
                df["timestamp"] = pd.to_datetime(df["timestamp"])
                
                # Time range selection
                time_range = st.selectbox(
                    "Select Time Range",
                    ["Last Week", "Last Month", "Last 3 Months", "All Time"]
                )
                
                # Filter data based on time range
                now = pd.Timestamp.now(tz=df["timestamp"].iloc[0].tz)
                if time_range == "Last Week":
                    df = df[df["timestamp"] > (now - timedelta(days=7))]
                elif time_range == "Last Month":
                    df = df[df["timestamp"] > (now - timedelta(days=30))]
                elif time_range == "Last 3 Months":
                    df = df[df["timestamp"] > (now - timedelta(days=90))]
                
                # Display metrics
                create_metrics(df)
                
                if not df.empty:
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
                    st.dataframe(
                        detailed_df.sort_values('timestamp', ascending=False),
                        use_container_width=True
                    )
                else:
                    st.info("No data available for the selected time range.")
            
            except Exception as e:
                st.error(f"Error processing data: {str(e)}")
        else:
            st.info("No inventory records found for this item.")
            
    with tab2:
        st.subheader("Overview")
        
        try:
            # Create overview metrics
            overview_data = []
            for item in items:
                history = load_item_history(item["id"])
                if history:
                    df = pd.DataFrame(history)
                    df["timestamp"] = pd.to_datetime(df["timestamp"])
                    
                    if not df.empty:
                        overview_data.append({
                            "Item": item["name"],
                            "Current Stock": df["quantity"].iloc[0],
                            "Average Stock": round(df["quantity"].mean(), 1),
                            "Min Stock": df["quantity"].min(),
                            "Max Stock": df["quantity"].max(),
                            "Updates Count": len(df),
                            "Last Updated": df["timestamp"].iloc[0]
                        })
            
            if overview_data:
                overview_df = pd.DataFrame(overview_data)
                
                # Format timestamp for display
                overview_df["Last Updated"] = pd.to_datetime(overview_df["Last Updated"]).dt.strftime("%Y-%m-%d %H:%M")
                
                # Create bar chart of current stock levels
                fig = px.bar(
                    overview_df,
                    x="Item",
                    y="Current Stock",
                    title="Current Stock Levels"
                )
                st.plotly_chart(fig, use_container_width=True)
                
                # Show overview table
                st.dataframe(
                    overview_df.sort_values('Current Stock', ascending=False),
                    use_container_width=True
                )
            else:
                st.info("No inventory data available for any items.")
                
        except Exception as e:
            st.error(f"Error generating overview: {str(e)}")

if __name__ == "__main__":
    main()