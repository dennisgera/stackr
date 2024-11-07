import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from config import make_request

st.set_page_config(
    page_title="Lot Management",
    page_icon="📦",
    layout="wide",
)

def load_items():
    response = make_request("get", "items/")
    if response and response.status_code == 200:
        return response.json()
    return []

def load_lots(item_id=None):
    endpoint = f"lots/?item_id={item_id}" if item_id else "lots/"
    response = make_request("get", endpoint)
    if response and response.status_code == 200:
        return response.json()
    return []

def format_datetime(dt_str: str) -> str:
    dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
    return dt.strftime("%Y-%m-%d %H:%M")

def main():
    st.title("📦 Lot Management")
    
    tab1, tab2 = st.tabs(["Lot Overview", "Expiry Tracking"])
    
    with tab1:
        st.header("Lot Overview")
        
        # Load data
        items = load_items()
        if not items:
            st.warning("No items found.")
            return
            
        # Filter options
        col1, col2 = st.columns(2)
        with col1:
            item_names = {item["name"]: item["id"] for item in items}
            selected_item = st.selectbox(
                "Filter by Item",
                options=["All Items"] + list(item_names.keys())
            )
        
        with col2:
            show_empty = st.checkbox("Show Empty Lots", value=False)
        
        # Load and process lots
        lots = load_lots(
            item_names[selected_item] if selected_item != "All Items" else None
        )
        
        if not lots:
            st.info("No lots found.")
            return
        
        # Process lot data
        processed_lots = []
        for lot in lots:
            if not show_empty and lot["remaining_quantity"] <= 0:
                continue
                
            item_name = next(
                item["name"] for item in items 
                if item["id"] == lot["purchase"]["item_id"]
            )
            
            processed_lots.append({
                "Item": item_name,
                "Lot Number": lot["lot_number"],
                "Remaining Quantity": lot["remaining_quantity"],
                "Manufacturing Date": format_datetime(lot["manufacturing_date"]) if lot["manufacturing_date"] else "N/A",
                "Expiry Date": format_datetime(lot["expiry_date"]) if lot["expiry_date"] else "N/A",
                "Age (Days)": (datetime.now() - datetime.fromisoformat(lot["manufacturing_date"].replace('Z', '+00:00'))).days if lot["manufacturing_date"] else "N/A",
                "Days to Expiry": (datetime.fromisoformat(lot["expiry_date"].replace('Z', '+00:00')) - datetime.now()).days if lot["expiry_date"] else "N/A"
            })
        
        df = pd.DataFrame(processed_lots)
        
        # Lot metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            total_lots = len(df)
            active_lots = len(df[df["Remaining Quantity"] > 0])
            st.metric("Active Lots", active_lots, f"Total: {total_lots}")
        
        with col2:
            avg_remaining = df["Remaining Quantity"].mean()
            st.metric("Average Remaining Quantity", f"{avg_remaining:.1f}")
        
        with col3:
            if "Days to Expiry" in df and df["Days to Expiry"] != "N/A":
                near_expiry = len(df[df["Days to Expiry"] <= 30])
                st.metric("Lots Near Expiry (30 days)", near_expiry)
        
        # Visualizations
        col1, col2 = st.columns(2)
        
        with col1:
            # Remaining quantity by lot
            fig1 = px.bar(
                df,
                x="Lot Number",
                y="Remaining Quantity",
                color="Item",
                title="Remaining Quantity by Lot"
            )
            st.plotly_chart(fig1, use_container_width=True)
        
        with col2:
            # Age distribution
            age_data = df[df["Age (Days)"] != "N/A"].copy()
            if not age_data.empty:
                fig2 = px.histogram(
                    age_data,
                    x="Age (Days)",
                    color="Item",
                    title="Lot Age Distribution"
                )
                st.plotly_chart(fig2, use_container_width=True)
        
        # Detailed lot table
        st.subheader("Lot Details")
        st.dataframe(df, use_container_width=True)
    
    with tab2:
        st.header("Expiry Tracking")
        
        # Filter for expiry tracking
        warning_days = st.slider(
            "Warning Days Before Expiry",
            min_value=1,
            max_value=180,
            value=30
        )
        
        # Filter lots with expiry dates
        expiry_df = pd.DataFrame(processed_lots)
        expiry_df = expiry_df[expiry_df["Days to Expiry"] != "N/A"].copy()
        expiry_df["Days to Expiry"] = pd.to_numeric(expiry_df["Days to Expiry"])
        
        if not expiry_df.empty:
            # Categorize lots by expiry status
            expired = expiry_df[expiry_df["Days to Expiry"] < 0]
            warning = expiry_df[(expiry_df["Days to Expiry"] >= 0) & (expiry_df["Days to Expiry"] <= warning_days)]
            safe = expiry_df[expiry_df["Days to Expiry"] > warning_days]
            
            # Display metrics
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Expired Lots", len(expired))
            with col2:
                st.metric(f"Lots Expiring in {warning_days} days", len(warning))
            with col3:
                st.metric("Safe Lots", len(safe))
            
            # Timeline visualization
            fig = px.timeline(
                expiry_df,
                x_start="Manufacturing Date",
                x_end="Expiry Date",
                y="Lot Number",
                color="Item",
                title="Lot Timeline"
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Display warnings
            if not warning.empty:
                st.warning("⚠️ Lots Requiring Attention")
                st.dataframe(
                    warning[["Item", "Lot Number", "Remaining Quantity", "Days to Expiry"]],
                    use_container_width=True
                )
            
            if not expired.empty:
                st.error("❌ Expired Lots")
                st.dataframe(
                    expired[["Item", "Lot Number", "Remaining Quantity", "Days to Expiry"]],
                    use_container_width=True
                )
        else:
            st.info("No lots with expiry dates found.")

if __name__ == "__main__":
    main()