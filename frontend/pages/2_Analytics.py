import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from config import make_request

st.set_page_config(
    page_title="Analytics",
    page_icon="📈",
    layout="wide",
)

def load_items():
    response = make_request("get", "items/")
    return response.json() if response and response.status_code == 200 else []

def load_purchases(item_id=None):
    endpoint = f"purchases/?item_id={item_id}" if item_id else "purchases/"
    response = make_request("get", endpoint)
    return response.json() if response and response.status_code == 200 else []

def load_item_history(item_id):
    response = make_request("get", f"inventory/{item_id}")
    return response.json() if response and response.status_code == 200 else []

def load_item_lots(item_id):
    response = make_request("get", f"items/{item_id}/lots")
    return response.json() if response and response.status_code == 200 else []

def format_currency(value):
    return f"${value:,.2f}"

def format_datetime(dt_str: str) -> str:
    return datetime.fromisoformat(dt_str.replace('Z', '+00:00')).strftime("%Y-%m-%d %H:%M")

def main():
    st.title("📈 Enhanced Analytics")
    
    tab1, tab2, tab3 = st.tabs(["Inventory Analytics", "Purchase Analytics", "Lot Analytics"])
    
    items = load_items()
    if not items:
        st.warning("No items found in the system.")
        return
    
    with tab1:
        st.header("Inventory Analytics")
        
        # Item selection
        item_names = {item["name"]: item["id"] for item in items}
        selected_item = st.selectbox(
            "Select Item for Analysis",
            options=list(item_names.keys()),
            key="inventory_analysis"
        )
        selected_item_id = item_names[selected_item]
        
        # Load data
        history = load_item_history(selected_item_id)
        lots = load_item_lots(selected_item_id)
        
        if history:
            df = pd.DataFrame(history)
            df["timestamp"] = pd.to_datetime(df["timestamp"])
            
            # Time range filter
            time_range = st.selectbox(
                "Select Time Range",
                ["Last Week", "Last Month", "Last 3 Months", "All Time"]
            )
            
            now = pd.Timestamp.now(tz=df["timestamp"].iloc[0].tz)
            if time_range == "Last Week":
                df = df[df["timestamp"] > (now - timedelta(days=7))]
            elif time_range == "Last Month":
                df = df[df["timestamp"] > (now - timedelta(days=30))]
            elif time_range == "Last 3 Months":
                df = df[df["timestamp"] > (now - timedelta(days=90))]
            
            # Calculate key metrics
            current_qty = df["quantity"].iloc[0] if not df.empty else 0
            qty_change = df["quantity"].sum()
            
            # Display metrics
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Current Quantity", f"{current_qty:.1f}")
            with col2:
                st.metric("Net Change", f"{qty_change:.1f}")
            with col3:
                total_increases = df[df["quantity"] > 0]["quantity"].sum()
                st.metric("Total Increases", f"{total_increases:.1f}")
            with col4:
                total_decreases = abs(df[df["quantity"] < 0]["quantity"].sum())
                st.metric("Total Decreases", f"{total_decreases:.1f}")
            
            # Inventory movement visualization
            st.subheader("Inventory Movement")
            fig = go.Figure()
            
            # Add increases
            increases = df[df["quantity"] > 0]
            if not increases.empty:
                fig.add_trace(go.Bar(
                    x=increases["timestamp"],
                    y=increases["quantity"],
                    name="Increases",
                    marker_color="green"
                ))
            
            # Add decreases
            decreases = df[df["quantity"] < 0]
            if not decreases.empty:
                fig.add_trace(go.Bar(
                    x=decreases["timestamp"],
                    y=decreases["quantity"],
                    name="Decreases",
                    marker_color="red"
                ))
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Running balance chart
            df["running_balance"] = df["quantity"].cumsum()
            fig2 = px.line(
                df,
                x="timestamp",
                y="running_balance",
                title="Running Balance"
            )
            st.plotly_chart(fig2, use_container_width=True)
    
    with tab2:
        st.header("Purchase Analytics")
        
        # Load purchase data
        all_purchases = load_purchases()
        if all_purchases:
            purchases_df = pd.DataFrame(all_purchases)
            purchases_df["purchase_date"] = pd.to_datetime(purchases_df["purchase_date"])
            purchases_df["total_cost"] = purchases_df["quantity"] * purchases_df["price_per_unit"]
            
            # Add item names
            purchases_df["item_name"] = purchases_df["item_id"].map(
                {item["id"]: item["name"] for item in items}
            )
            
            # Purchase metrics
            col1, col2, col3 = st.columns(3)
            with col1:
                total_spent = purchases_df["total_cost"].sum()
                st.metric("Total Spent", format_currency(total_spent))
            with col2:
                avg_purchase = purchases_df["total_cost"].mean()
                st.metric("Average Purchase", format_currency(avg_purchase))
            with col3:
                total_quantity = purchases_df["quantity"].sum()
                st.metric("Total Quantity Purchased", f"{total_quantity:,.1f}")
            
            # Purchase trends
            st.subheader("Purchase Trends")
            
            fig = px.line(
                purchases_df.groupby(purchases_df["purchase_date"].dt.date)
                ["total_cost"].sum().reset_index(),
                x="purchase_date",
                y="total_cost",
                title="Daily Purchase Costs"
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Purchase distribution
            col1, col2 = st.columns(2)
            
            with col1:
                fig = px.pie(
                    purchases_df,
                    values="total_cost",
                    names="item_name",
                    title="Purchase Cost Distribution by Item"
                )
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                fig = px.pie(
                    purchases_df,
                    values="quantity",
                    names="item_name",
                    title="Purchase Quantity Distribution by Item"
                )
                st.plotly_chart(fig, use_container_width=True)
            
            # Purchase history table
            st.subheader("Purchase History")
            st.dataframe(
                purchases_df[[
                    "purchase_date", "item_name", "quantity",
                    "price_per_unit", "total_cost", "supplier"
                ]].sort_values("purchase_date", ascending=False),
                use_container_width=True
            )
    
    with tab3:
        st.header("Lot Analytics")
        
        # Load lot data for all items
        all_lots_data = []
        for item in items:
            lots = load_item_lots(item["id"])
            if lots:
                for lot in lots:
                    lot_data = {
                        "item_name": item["name"],
                        "lot_number": lot["lot_number"],
                        "remaining_quantity": lot["remaining_quantity"],
                        "manufacturing_date": lot["manufacturing_date"],
                        "expiry_date": lot["expiry_date"]
                    }
                    all_lots_data.append(lot_data)
        
        if all_lots_data:
            lots_df = pd.DataFrame(all_lots_data)
            
            # Convert dates
            for date_col in ["manufacturing_date", "expiry_date"]:
                if date_col in lots_df.columns:
                    lots_df[date_col] = pd.to_datetime(lots_df[date_col])
            
            # Lot metrics
            col1, col2, col3 = st.columns(3)
            with col1:
                total_lots = len(lots_df)
                active_lots = len(lots_df[lots_df["remaining_quantity"] > 0])
                st.metric("Active Lots", active_lots, f"Total: {total_lots}")
            
            with col2:
                avg_remaining = lots_df["remaining_quantity"].mean()
                st.metric("Average Remaining Quantity", f"{avg_remaining:.1f}")
            
            with col3:
                if "expiry_date" in lots_df.columns:
                    expiring_soon = len(lots_df[
                        (lots_df["expiry_date"] - pd.Timestamp.now()).dt.days <= 30
                    ])
                    st.metric("Lots Expiring in 30 Days", expiring_soon)
            
            # Lot visualizations
            st.subheader("Lot Analysis")
            
            col1, col2 = st.columns(2)
            
            with col1:
                fig = px.bar(
                    lots_df,
                    x="lot_number",
                    y="remaining_quantity",
                    color="item_name",
                    title="Remaining Quantity by Lot"
                )
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                if "manufacturing_date" in lots_df.columns:
                    lots_df["age_days"] = (
                        pd.Timestamp.now() - lots_df["manufacturing_date"]
                    ).dt.days
                    
                    fig = px.histogram(
                        lots_df,
                        x="age_days",
                        color="item_name",
                        title="Lot Age Distribution"
                    )
                    st.plotly_chart(fig, use_container_width=True)
            
            # Lot timeline
            if "manufacturing_date" in lots_df.columns and "expiry_date" in lots_df.columns:
                st.subheader("Lot Timeline")
                fig = px.timeline(
                    lots_df,
                    x_start="manufacturing_date",
                    x_end="expiry_date",
                    y="lot_number",
                    color="item_name",
                    title="Lot Lifecycle"
                )
                st.plotly_chart(fig, use_container_width=True)
            
            # Detailed lot table
            st.subheader("Lot Details")
            display_df = lots_df.copy()
            
            # Format dates for display
            if "manufacturing_date" in display_df.columns:
                display_df["manufacturing_date"] = display_df["manufacturing_date"].dt.strftime("%Y-%m-%d")
            if "expiry_date" in display_df.columns:
                display_df["expiry_date"] = display_df["expiry_date"].dt.strftime("%Y-%m-%d")
            
            st.dataframe(display_df.sort_values(
                ["item_name", "lot_number"]), 
                use_container_width=True
            )
        else:
            st.info("No lot data available.")

if __name__ == "__main__":
    main()