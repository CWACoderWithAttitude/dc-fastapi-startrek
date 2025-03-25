from turtle import onclick
import streamlit as st
import requests

from views import list_ships

# FastAPI backend URL
API_BASE_URL = "http://localhost:8000"  # Replace with your FastAPI backend URL

st.title("🚀 Star Trek Ship Manager")

# Tabs for different operations
tab1, tab2, tab3, tab4 = st.tabs(["View Ships", "Add Ship", "Update Ship", "Delete Ship"])


def click():
    print("click")


def get_classifications():
    response = requests.get(f"{API_BASE_URL}/classification/")
    if response.status_code == 200:
        return response.json()
    else:
        return []


# View Ships
with tab1:
    st.header("View Ships")
    skip = st.number_input("Skip", min_value=0, value=0, step=1)
    limit = st.number_input("Limit", min_value=1, value=10, step=1)
    if st.button("Fetch Ships"):
        response = requests.get(f"{API_BASE_URL}/ship/?skip={skip}&limit={limit}")
        if response.status_code == 200:
            ships = response.json()
            # for ship in ships:
            #    st.write(
            #        f"**ID**: {ship['id']}, **Sign**: {ship['sign']}, **Name**: {ship['name']}, **Classification**: {ship['classification']}")
            list_of_ships = []
            for ship in ships:
                list_of_ships.append({"Id": f"{ship['id']}", "Name": f"{ship['name']}", "Sign": f"{ship['sign']}",
                                      "Classification": f"{ship['classification']}"})
            st.table(list_of_ships)
        else:
            st.error(f"Error: {response.status_code} - {response.text}")


# Add Ship
with tab2:
    response = requests.get(f"{API_BASE_URL}/classifications")
    # if response.status_code == 200:
    #    st.write(f"classificatuions: {response.json()}")
    st.header("Add a New Ship")
    name = st.text_input("Name")
    classification = st.text_input("Classification")
    sign = st.text_input("Sign")
    speed = st.text_input("Speed")
    captain = st.text_input("Captain")
    if st.button("Add Ship"):
        payload = {
            "name": name,
            "classification": classification,
            "sign": sign,
            "speed": speed,
            "captain": captain,
        }
        response = requests.post(f"{API_BASE_URL}/ship/", json=payload)
        if response.status_code == 201:
            st.success("Ship added successfully!")
        else:
            st.error(f"Error: {response.status_code} - {response.text}")
# Update Ship
with tab3:
    st.header("Update an Existing Ship")
    ship_id = st.number_input("Ship ID", min_value=1, step=1)
    name = st.text_input("New Name")
    classification = st.text_input("New Classification")
    sign = st.text_input("New Sign")
    speed = st.text_input("New Speed")
    captain = st.text_input("New Captain")
    if st.button("Update Ship"):
        payload = {
            "name": name,
            "classification": classification,
            "sign": sign,
            "speed": speed,
            "captain": captain,
        }
        response = requests.put(f"{API_BASE_URL}/ship/{ship_id}", json=payload)
        if response.status_code == 200:
            st.success("Ship updated successfully!")
        else:
            st.error(f"Error: {response.status_code} - {response.text}")

# Delete Ship
with tab4:
    st.header("Delete a Ship")
    ship_id = st.number_input("Ship ID to Delete", min_value=1, step=1)
    if st.button("Delete Ship"):
        response = requests.delete(f"{API_BASE_URL}/ship/{ship_id}")
        if response.status_code == 204:
            st.success("Ship deleted successfully!")
        else:
            st.error(f"Error: {response.status_code} - {response.text}")
