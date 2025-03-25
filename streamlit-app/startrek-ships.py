import streamlit as st

from views.new_ship import new_ship_page

st.set_page_config(page_title="Star Trek Ship Manager", page_icon="🚀", layout="centered")

page = st.sidebar.radio("Go to", ["List Ships", "Edit Ship", "New Ship"])
# list_page = st.Page(page="views/list_ships.py", title="List Ships", icon=":material/account_circle:", default=False)
# edit_page = st.Page(page="views/edit_ship.py", title="Edit Ship", icon=":material/account_circle:", default=False)
# new_page = st.Page(page="views/new_ship.py", title="New Ship", icon=":material/account_circle:", default=True)

# pg = st.navigation(pages=[edit_page])

st.write("# Star Trek Ship Manager")
# st.write("## Managew data about Star Trek ships with ease")
# st.write("And probably learn something on solving problems with python and streamlit.")
# st.navigation(pages=[list_page, edit_page, new_page])
# st.navigation(pages=[new_page, li])

st.logo("https://picsum.photos/400/360")
st.sidebar.text("Sidebar by Volker")
st.sidebar.success("Success Sidebar by Volker")

if page == "New Ship":
    new_ship_page()
