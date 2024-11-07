# frontend/pages/Home.py
import streamlit as st

st.set_page_config(
    page_title="Stackr",
    page_icon="📦",
    layout="wide",
)

def main():
    st.title("📦 Stackr")

    # Welcome message
    st.markdown("""
        ## Welcome to Stackr, your Inventory Management System!
        
        Navigate using the sidebar to access:
        - 🏠 Home
        - 📦 Inventory
        - 📈 Analytics
        - 🛍️ Purchases
        - 📤 Lots
    """)


if __name__ == "__main__":
    main()