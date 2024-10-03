import streamlit as st
import HW_Manager.HW1 as HW1
import HW_Manager.HW2 as HW2
import HW_Manager.HW3 as HW3
import HW_Manager.hw5_final as HW5
st.sidebar.title("HW Manager")
page = st.sidebar.selectbox("Choose a HW", ["HW1", "HW2","HW3","HW5"])

if page == "HW1":
    HW1.run()  # Call the HW1 page
elif page == "HW2":
    HW2.run()  # Call the HW2 page
elif page == "HW3":
    HW3.run()  # Call the HW3 page    
elif page == "HW5":
    HW5.run()  # Call the HW5 page