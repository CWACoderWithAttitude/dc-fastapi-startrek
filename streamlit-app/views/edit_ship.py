import streamlit as st

print("EDIRT")
col1, col2 = st.columns(2, gap="small", vertical_alignment="center")
st.title("Edit Ship")
st.write("Edit Ship")
with col1:
    st.write("This is column 1.1")
    st.write("This is column 1.2")
    st.write("This is column 1.3")
with col2:
    st.write("This is column 2.1")
    st.write("This is column 2.2")
    st.write("This is column 2.3")
