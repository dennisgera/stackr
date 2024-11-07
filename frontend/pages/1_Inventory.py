import logging
import streamlit as st
import pandas as pd
from datetime import datetime
from config import make_request

st.set_page_config(
    page_title="Inventory Management",
    page_icon="📊",
    layout="wide",
)

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def load_items():
    """Load all items with error handling"""
    response = make_request("get", "items/")
    if response and response.status_code == 200:
        return response.json()
    return []

def load_item_lots(item_id: int, include_empty: bool = False):
    """Load available lots for an item"""
    response = make_request(
        "get", 
        f"items/{item_id}/lots?exclude_empty={not include_empty}"
    )
    if response and response.status_code == 200:
        return response.json()
    return []

def create_item(name: str, description: str) -> bool:
    """Create a new item with error handling"""
    if not name:
        st.error("Please enter an item name")
        return False
    
    response = make_request(
        "post",
        "items/",
        json={
            "name": name.strip(),
            "description": description.strip() if description else None
        }
    )
    
    if response and response.status_code == 200:
        st.success(f"Item '{name}' created successfully!")
        return True
    return False

def update_inventory(record_data: dict) -> bool:
    """Update inventory with lot handling"""
    response = make_request("post", "inventory/", json=record_data)
    if response and response.status_code == 200:
        st.success("Inventory updated successfully!")
        return True
    if response:
        st.error(f"Error updating inventory: {response.text}")
    return False

def main():
    st.title("📊 Inventory Management")
    
    # Create tabs
    tab1, tab2 = st.tabs(["Add Items", "Update Inventory"])
    
    with tab1:
        st.header("Add New Item")
        with st.form("new_item_form"):
            name = st.text_input("Item Name")
            description = st.text_area("Description")
            submitted = st.form_submit_button("Create Item")
            
            if submitted:
                if create_item(name, description):
                    st.rerun()
        
        # Display existing items
        st.subheader("Existing Items")
        with st.spinner("Loading items..."):
            items = load_items()
        
        if items:
            items_df = pd.DataFrame(
                [[item["name"], item["description"], 
                  datetime.fromisoformat(item["created_at"]).strftime("%Y-%m-%d %H:%M")]
                 for item in items],
                columns=["Name", "Description", "Created At"]
            )
            st.dataframe(items_df, use_container_width=True)
        else:
            st.info("No items in inventory yet. Create your first item above!")
    
    with tab2:
        st.header("Update Inventory")
        items = load_items()
        
        if not items:
            st.warning("No items found. Please add items first.")
            return
        
        # Create selection for items
        item_names = {item["name"]: item["id"] for item in items}
        selected_item_name = st.selectbox(
            "Select Item",
            options=list(item_names.keys())
        )
        
        if selected_item_name:
            selected_item_id = item_names[selected_item_name]
            
            # Load available lots
            lots = load_item_lots(selected_item_id, include_empty=True)
            
            col1, col2 = st.columns(2)
            with col1:
                quantity = st.number_input(
                    "Quantity Change (negative for reduction)",
                    step=1
                )
            
            with col2:
                user_name = st.text_input("Updated By")
            
            # Show lot selection for reductions or if lots exist
            show_lots = quantity < 0 or lots
            if show_lots:
                st.subheader("Lot Information")
                
                if quantity < 0:
                    st.info(
                        "Reduction will automatically use oldest lots first. "
                        "Select a specific lot below to override this behavior."
                    )
                
                if lots:
                    lot_options = {
                        f"{lot['lot_number']} (Remaining: {lot['remaining_quantity']:.1f})": lot["id"]
                        for lot in lots
                    }
                    selected_lot = st.selectbox(
                        "Select Lot (Optional)",
                        options=["Auto-select (FIFO)"] + list(lot_options.keys())
                    )
                    
                    lot_id = lot_options[selected_lot] if selected_lot != "Auto-select (FIFO)" else None
                else:
                    st.info("No lots available for this item.")
                    lot_id = None
            else:
                lot_id = None
            
            if st.button("Update Inventory"):
                if not user_name:
                    st.error("Please enter your name")
                    return
                
                record_data = {
                    "item_id": selected_item_id,
                    "quantity": quantity,
                    "updated_by": user_name.strip(),
                    "lot_id": lot_id
                }
                
                if update_inventory(record_data):
                    st.rerun()

if __name__ == "__main__":
    main()