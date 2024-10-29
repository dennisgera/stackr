import streamlit as st
import requests
import pandas as pd

API_URL = "http://backend:8000"

def load_items():
    try:
        response = requests.get(f"{API_URL}/items/")
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Failed to load items: {response.json().get('detail', 'Unknown error')}")
            return []
    except requests.exceptions.RequestException as e:
        st.error(f"Error connecting to the backend: {str(e)}")
        return []

def update_inventory(item_id: int, quantity: float, updated_by: str):
    try:
        response = requests.post(
            f"{API_URL}/inventory/",
            json={
                "item_id": item_id,
                "quantity": quantity,
                "updated_by": updated_by
            }
        )
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False

st.set_page_config(page_title="Inventory Management", layout="wide")

def main():
    st.title("Inventory Management")
    
    # Create two columns
    left_col, right_col = st.columns([2, 3])
    
    with left_col:
        st.subheader("Update Inventory")
        
        # Load items
        items = load_items()
        
        if not items:
            st.warning("No items found. Please add items from the home page first.")
            return
            
        # Create selection for items
        item_names = {item["name"]: item["id"] for item in items}
        selected_item_name = st.selectbox(
            "Select Item",
            options=list(item_names.keys())
        )
        
        # Only proceed if we have items
        if selected_item_name:
            selected_item_id = item_names[selected_item_name]
            
            # Quantity input
            quantity = st.number_input("New Quantity", min_value=0.0, step=0.1)
            
            # User input
            user_name = st.text_input("Updated By")
            
            # Update button
            if st.button("Update Inventory"):
                if not user_name:
                    st.error("Please enter your name")
                    return
                    
                if update_inventory(selected_item_id, quantity, user_name):
                    st.success(f"Successfully updated inventory for {selected_item_name}")
                else:
                    st.error("Failed to update inventory")
    
    with right_col:
        st.subheader("Current Inventory Status")
        
        if items:
            # Create a status table
            status_data = []
            for item in items:
                try:
                    response = requests.get(f"{API_URL}/inventory/{item['id']}")
                    if response.status_code == 200:
                        records = response.json()
                        latest_quantity = records[0]["quantity"] if records else 0
                        last_updated = records[0]["timestamp"] if records else "Never"
                        status_data.append({
                            "Item": item["name"],
                            "Current Quantity": latest_quantity,
                            "Last Updated": last_updated
                        })
                except requests.exceptions.RequestException:
                    continue
            
            if status_data:
                df = pd.DataFrame(status_data)
                df["Last Updated"] = pd.to_datetime(df["Last Updated"]).dt.strftime("%Y-%m-%d %H:%M")
                st.dataframe(df, use_container_width=True)
            else:
                st.info("No inventory records found")

if __name__ == "__main__":
    main()