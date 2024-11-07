import streamlit as st
import pandas as pd
from datetime import datetime
from config import make_request
from typing import Optional

st.set_page_config(
    page_title="Purchase Management",
    page_icon="🛍️",
    layout="wide",
)

def load_items():
    """Load all items with error handling"""
    response = make_request("get", "items/")
    if response and response.status_code == 200:
        return response.json()
    return []

def load_purchases(item_id: Optional[int] = None):
    """Load purchases with optional item filtering"""
    endpoint = f"purchases/?item_id={item_id}" if item_id else "purchases/"
    response = make_request("get", endpoint)
    if response and response.status_code == 200:
        return response.json()
    return []

def create_purchase(purchase_data: dict) -> bool:
    """Create a new purchase with error handling"""
    response = make_request("post", "purchases/", json=purchase_data)
    if response and response.status_code == 200:
        st.success("Purchase created successfully!")
        return True
    if response:
        st.error(f"Error creating purchase: {response.text}")
    return False

def format_datetime(dt_str: str) -> str:
    """Format datetime string for display"""
    dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
    return dt.strftime("%Y-%m-%d %H:%M")

def main():
    st.title("🛍️ Purchase Management")
    
    # Create tabs
    tab1, tab2 = st.tabs(["Create Purchase", "View Purchases"])
    
    with tab1:
        st.header("Create New Purchase")
        
        # Load items for selection
        items = load_items()
        if not items:
            st.warning("No items found. Please add items first.")
            return
        
        with st.form("purchase_form"):
            # Item Selection
            item_names = {item["name"]: item["id"] for item in items}
            selected_item = st.selectbox(
                "Select Item",
                options=list(item_names.keys())
            )
            
            # Purchase Type
            purchase_type = st.selectbox(
                "Purchase Type",
                options=["domestic", "imported"]
            )
            
            # Basic Purchase Information
            col1, col2 = st.columns(2)
            with col1:
                quantity = st.number_input("Quantity", min_value=1, step=1)
                price_per_unit = st.number_input("Price per Unit", min_value=0.01, step=0.01)
            
            with col2:
                supplier = st.text_input("Supplier")
                created_by = st.text_input("Created By")
            
            # Lot Information (shown only for imported items or if requested)
            show_lot = purchase_type == "imported" or st.checkbox(
                "Add Lot Information",
                value=purchase_type == "imported"
            )
            
            if show_lot:
                st.subheader("Lot Information")
                col3, col4 = st.columns(2)
                with col3:
                    lot_number = st.text_input(
                        "Lot Number",
                        placeholder="Leave empty for auto-generation"
                    )
                    manufacturing_date = st.date_input(
                        "Manufacturing Date",
                        key="mfg_date"
                    )
                
                with col4:
                    expiry_date = st.date_input(
                        "Expiry Date",
                        key="exp_date"
                    )
            
            submitted = st.form_submit_button("Create Purchase")
            
            if submitted:
                if not supplier or not created_by:
                    st.error("Please fill in all required fields")
                    return
                
                # Prepare purchase data
                purchase_data = {
                    "item_id": item_names[selected_item],
                    "quantity": quantity,
                    "purchase_type": purchase_type,
                    "supplier": supplier,
                    "price_per_unit": price_per_unit,
                    "created_by": created_by
                }
                
                # Add lot information if provided
                if show_lot:
                    purchase_data.update({
                        "lot_number": lot_number if lot_number else None,
                        "manufacturing_date": manufacturing_date.isoformat() if manufacturing_date else None,
                        "expiry_date": expiry_date.isoformat() if expiry_date else None
                    })
                
                if create_purchase(purchase_data):
                    st.rerun()
    
    with tab2:
        st.header("Purchase History")
        
        # Filter options
        col1, col2 = st.columns(2)
        with col1:
            filter_item = st.selectbox(
                "Filter by Item",
                options=["All Items"] + list(item_names.keys()),
                key="filter_item"
            )
        
        # Load and display purchases
        purchases = load_purchases(
            item_names[filter_item] if filter_item != "All Items" else None
        )
        
        if purchases:
            # Process purchase data
            purchases_data = []
            for p in purchases:
                item_name = next(
                    item["name"] for item in items 
                    if item["id"] == p["item_id"]
                )
                
                purchases_data.append({
                    "Item": item_name,
                    "Type": p["purchase_type"],
                    "Quantity": p["quantity"],
                    "Price/Unit": f"${p['price_per_unit']:.2f}",
                    "Total": f"${p['quantity'] * p['price_per_unit']:.2f}",
                    "Supplier": p["supplier"],
                    "Created By": p["created_by"],
                    "Purchase Date": format_datetime(p["purchase_date"])
                })
            
            # Create DataFrame and display
            df = pd.DataFrame(purchases_data)
            st.dataframe(
                df.sort_values("Purchase Date", ascending=False),
                use_container_width=True,
                hide_index=True
            )
            
            # Summary metrics
            col1, col2, col3 = st.columns(3)
            with col1:
                total_value = sum(p["quantity"] * p["price_per_unit"] for p in purchases)
                st.metric("Total Purchase Value", f"${total_value:,.2f}")
            
            with col2:
                total_quantity = sum(p["quantity"] for p in purchases)
                st.metric("Total Quantity", f"{total_quantity:,.1f}")
            
            with col3:
                avg_price = total_value / total_quantity if total_quantity > 0 else 0
                st.metric("Average Price per Unit", f"${avg_price:.2f}")
        
        else:
            st.info("No purchases found.")

if __name__ == "__main__":
    main()