import streamlit as st
from ai.pricing_engine import dynamic_price
import logging

logger = logging.getLogger(__name__)

def run_dashboard(calculated_price):
    st.title("Eco-Retail Dynamic Pricing")

    st.metric("Recovered Revenue", "₹1,20,000")

    stock = st.number_input("Stock", value=50)
    days_to_expiry = st.number_input("Days to Expiry", value=2)
    base_price = st.number_input("Base Price", value=60.0)
    day_of_week = st.selectbox("Day of Week", [0,1,2,3,4,5,6])

    logger.info("Dashboard rendered")
    logger.info("\nStock Value: ", stock)
    logger.info("\nDays to Expiry: ", days_to_expiry)
    logger.info("\nBase Price: ",base_price)
    logger.info("\nDay of Week: ",day_of_week)

    if st.button("Calculate Price"):
        price = dynamic_price(
            stock,
            days_to_expiry,
            base_price
        )
        calculated_price = price
        st.success(f"Dynamic Price: ₹{calculated_price}")
    
    return calculated_price