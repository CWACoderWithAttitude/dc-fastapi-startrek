import requests
import streamlit as st

API_BASE_URL = "http://localhost:8000"


def list_ships_page():
    st.title("🚀 List Ships")

    col1, col2 = st.columns(2, gap="small", vertical_alignment="center")
    with col1:
        limit = st.number_input("Limit", min_value=1, value=10, step=1)
    with col2:
        skip = st.number_input("Skip", min_value=1, value=10, step=1)
    if st.button("Fetch Ships"):
        response = requests.get(f"{API_BASE_URL}/ship/?skip={skip}&limit={limit}")
        if response.status_code == 200:
            ships = response.json()
        else:
            # fetching ships from db failed, so we use some mock ships
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
                                  "Classification": f"{ship['classification']}", "Speed": f"{ship['speed']}",
                                  "Captain": f"{ship['captain']}", "Comment": f"{ship['comment']}", "Book": "[:book:](https://docs.streamlit.io/develop/api-reference/data/st.table)"})
        st.table(list_of_ships)
