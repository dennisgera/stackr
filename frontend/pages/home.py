# frontend/Home.py
import streamlit as st
import requests
import pandas as pd

API_URL = "http://backend:8000"

st.set_page_config(
    page_title="Inventory Management System",
    page_icon="📦",
    layout="wide"
)

def main():
    st.title("📦 Inventory Management System")

    # Welcome message
    st.markdown("""
        ## Welcome to your Inventory Management System!
        
        Use the sidebar to navigate between:
        - 📝 Add/Edit Items
        - 📊 Update Inventory
        - 📈 View Analytics
    """)
    
    # Create tabs
    tab1, tab2, tab3 = st.tabs(["Add Items", "Update Inventory", "Analytics"])
    
    with tab1:
        st.header("Add New Item")
        with st.form("new_item_form"):
            name = st.text_input("Item Name")
            description = st.text_area("Description")
            submitted = st.form_submit_button("Create Item")
            
            if submitted:
                if not name:
                    st.error("Please enter an item name")
                else:
                    try:
                        response = requests.post(
                            f"{API_URL}/items/",
                            json={"name": name, "description": description}
                        )
                        if response.status_code == 200:
                            st.success(f"Item '{name}' created successfully!")
                        else:
                            st.error(f"Failed to create item: {response.json().get('detail', 'Unknown error')}")
                    except requests.exceptions.RequestException as e:
                        st.error(f"Error connecting to the backend: {str(e)}")
        
        # Display existing items
        st.subheader("Existing Items")
        try:
            response = requests.get(f"{API_URL}/items/")
            if response.status_code == 200:
                items = response.json()
                if items:
                    items_df = pd.DataFrame(
                        [[item["name"], item["description"], item["created_at"]] for item in items],
                        columns=["Name", "Description", "Created At"]
                    )
                    st.dataframe(items_df)
                else:
                    st.info("No items in inventory yet. Create your first item above!")
        except requests.exceptions.RequestException as e:
            st.error(f"Error connecting to the backend: {str(e)}")
    
    with tab2:
        def load_items():
            try:
                response = requests.get(f"{API_URL}/items/")
                if response.status_code == 200:
                    return response.json()
                return []
            except Exception:
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
            except Exception:
                return False

        st.header("Update Inventory")
        
        # Load items
        items = load_items()
        if not items:
            st.warning("No items found. Please add items first.")
        else:
            # Create selection for items
            item_names = {item["name"]: item["id"] for item in items}
            selected_item_name = st.selectbox(
                "Select Item",
                options=list(item_names.keys())
            )
            
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
                    else:
                        if update_inventory(selected_item_id, quantity, user_name):
                            st.success(f"Successfully updated inventory for {selected_item_name}")
                        else:
                            st.error("Failed to update inventory")
            
            # Show current status
            st.subheader("Current Inventory Status")
            status_data = []
            for item in items:
                try:
                    response = requests.get(f"{API_URL}/inventory/{item['id']}")
                    if response.status_code == 200:
                        records = response.json()
                        if records:
                            latest_quantity = records[0]["quantity"]
                            last_updated = pd.to_datetime(records[0]["timestamp"]).strftime("%Y-%m-%d %H:%M")
                        else:
                            latest_quantity = 0
                            last_updated = "No records"
                            
                        status_data.append({
                            "Item": item["name"],
                            "Current Quantity": latest_quantity,
                            "Last Updated": last_updated
                        })
                except Exception:
                    continue
            
            if status_data:
                df = pd.DataFrame(status_data)
                st.dataframe(df, use_container_width=True)
            else:
                st.info("No inventory records available")
    
    with tab3:
        st.header("Analytics")
        
        # Load items for analytics
        items = load_items()
        if not items:
            st.warning("No items found. Please add items to view analytics.")
        else:
            # Item selection for analytics
            item_names = {item["name"]: item["id"] for item in items}
            selected_item_name = st.selectbox(
                "Select Item for Analysis",
                options=list(item_names.keys()),
                key="analytics_select"
            )
            
            if selected_item_name:
                selected_item_id = item_names[selected_item_name]
                
                try:
                    response = requests.get(f"{API_URL}/inventory/{selected_item_id}")
                    if response.status_code == 200:
                        records = response.json()
                        if records:
                            df = pd.DataFrame(records)
                            df['timestamp'] = pd.to_datetime(df['timestamp'])
                            
                            # Metrics
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("Current Quantity", f"{df['quantity'].iloc[0]:.1f}")
                            with col2:
                                st.metric("Average Quantity", f"{df['quantity'].mean():.1f}")
                            with col3:
                                st.metric("Min Quantity", f"{df['quantity'].min():.1f}")
                            
                            # Line chart
                            st.line_chart(
                                df.set_index('timestamp')['quantity']
                            )
                            
                            # Detailed history
                            st.subheader("History")
                            history_df = df[['timestamp', 'quantity', 'updated_by']].copy()
                            history_df['timestamp'] = history_df['timestamp'].dt.strftime("%Y-%m-%d %H:%M")
                            st.dataframe(
                                history_df.sort_values('timestamp', ascending=False),
                                use_container_width=True
                            )
                        else:
                            st.info("No inventory records found for this item.")
                except Exception as e:
                    st.error(f"Error loading inventory data: {str(e)}")

if __name__ == "__main__":
    main()