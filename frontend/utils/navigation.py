import streamlit as st

def initialize_sidebar():
    with st.sidebar:
        st.title("Navigation")
        pages = {
            "📦 Home": "main.py",
            "📊 Inventory": "pages/1_inventory.py",
            "📈 Analytics": "pages/2_analytics.py"
        }
        
        for page_name, page_id in pages.items():
            if st.button(page_name, use_container_width=True):
                try:
                    st.switch_page(page_id)
                except Exception as e:
                    st.error(f"Could not navigate to {page_id}: {str(e)}")        