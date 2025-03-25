import requests
import streamlit as st

# st.title("🚀 List Ships")
API_BASE_URL = "http://localhost:8000"  # Replace with your FastAPI backend URL
#    description="List all ships",
#    layout="wide",


def list_ships_page():
    st.title("List Ships")
    st.write("List Ships")
    print("LIST")
    st.write("cdjcnynsj")  # skip = st.number_input("Skip", min_value=0, value=0, step=1)
    limit = st.number_input("Limit", min_value=1, value=10, step=1)
    if st.button("Fetch Ships"):
        response = requests.get(f"{API_BASE_URL}/ship/?skip={skip}&limit={limit}")
        if response.status_code == 200:
            ships = response.json()
            # for ship in ships:
            #    st.write(
            #        f"**ID**: {ship['id']}, **Sign**: {ship['sign']}, **Name**: {ship['name']}, **Classification**: {ship['classification']}")
        else:
            st.error(f"Error: {response.status_code} - {response.text}")
    ships = [
        {
            "id": "1",
            "name": "USS Cayuga",
            "captain": "Captain Marie Batel",
            "sign": "NCC-1557",
            "classification": "Constitution",
            "details": "https://memory-alpha.fandom.com/wiki/USS_Cayuga"
        },
        {

            "id": "2",
            "name": " USS Talos",
            "captain": "Captain Marie Batel",
            "sign": "NCC-",
            "classification": "",
            "details": "https://memory-alpha.fandom.com/wiki/USS_Talos"
        }
    ]
    list_of_ships = []
    for ship in ships:
        list_of_ships.append({"Id": f"{ship['id']}", "Name": f"{ship['name']}", "Sign": f"{ship['sign']}",
                              "Classification": f"{ship['classification']}"})
    st.table(list_of_ships)
