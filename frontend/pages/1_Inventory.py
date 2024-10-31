import streamlit as st
import pandas as pd
from datetime import datetime
from config import make_request

st.set_page_config(
    page_title="Inventory Management",
    page_icon="📊",
    layout="wide",
)

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

def load_items():
    """Load all items with error handling"""
    response = make_request("get", "items/")
    if response and response.status_code == 200:
        try:
            return response.json()
        except Exception as e:
            st.error(f"Error parsing response: {str(e)}")
            return []
    return []

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
            try:
                items_df = pd.DataFrame(
                    [[item["name"], item["description"], 
                      datetime.fromisoformat(item["created_at"]).strftime("%Y-%m-%d %H:%M")] 
                     for item in items],
                    columns=["Name", "Description", "Created At"]
                )
                st.dataframe(items_df, use_container_width=True)
            except Exception as e:
                st.error(f"Error displaying items: {str(e)}")
        else:
            st.info("No items in inventory yet. Create your first item above!")

    with tab2:
        st.header("Update Inventory")
        with st.spinner("Loading items..."):
            items = load_items()
            
        if not items:
            st.warning("No items found. Please add items first.")
        else:
            # Create selection for items
            try:
                item_names = {item["name"]: item["id"] for item in items}
                selected_item_name = st.selectbox(
                    "Select Item",
                    options=list(item_names.keys())
                )
                
                if selected_item_name:
                    selected_item_id = item_names[selected_item_name]
                    quantity = st.number_input("New Quantity", min_value=0.0, step=0.1)
                    user_name = st.text_input("Updated By")
                    
                    if st.button("Update Inventory"):
                        if not user_name:
                            st.error("Please enter your name")
                        else:
                            response = make_request(
                                "post",
                                "inventory/",
                                json={
                                    "item_id": selected_item_id,
                                    "quantity": quantity,
                                    "updated_by": user_name.strip()
                                }
                            )
                            if response and response.status_code == 200:
                                st.success(f"Successfully updated inventory for {selected_item_name}")
                                st.rerun()
            except Exception as e:
                st.error(f"Error processing items: {str(e)}")

if __name__ == "__main__":
    main()