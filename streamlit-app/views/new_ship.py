import streamlit as st
import requests

API_BASE_URL = "http://localhost:8000"  # Replace with your FastAPI backend URL


def get_classifications():
    print("GET CLASSIFICATIONS1")
    response = requests.get(f"{API_BASE_URL}/classifications")
    print("GET CLASSIFICATIONS2")
    if response.status_code == 200:
        print("GET CLASSIFICATIONS3")

        print(f"response.json(): {response.json()}")
        return response.json()
    else:
        print("GET CLASSIFICATIONS4")
        return ["Pommes", "Apfel", "Banane"]


def new_ship_page():
    classifications = get_classifications()
    st.title("New Ship")
    name = st.text_input("Name")
    classification = st.selectbox("Select Ship Classification",
                                  options=classifications)  # st.text_input("Classification")
    sign = st.text_input("Sign")
    speed = st.text_input("Speed")
    captain = st.text_input("Captain")

    if st.button("Add Ship"):
        if name == None or len(name) < 3:
            print(f"No Namne {name}?!")
            return
        if classification == None or len(classification) < 3:
            print(f"No Classification {classification}?!")
            return
        if sign == None or len(sign) < 3:
            print(f"No Sign {sign}?!")
            return
        if speed == None or len(speed) < 3:
            print(f"No Speede {speed}?!")
            return
        if captain == None or len(captain) < 3:
            print(f"No Captain {captain}?!")
            return
        payload = {
            "name": name,
            "classification": classification,
            "sign": sign,
            "speed": speed,
            "captain": captain,
        }
        response = requests.post(f"{API_BASE_URL}/ship/", json=payload)
        if response.status_code == 201:
            st.success(f"Ship {response.json()} added successfully!")
        else:
            st.error(f"Error: {response.status_code} - {response.text}")
