
import streamlit as st
import sys
import os

# Link backend directory
sys.path.append(
    os.path.abspath(
        os.path.join(os.path.dirname(__file__), '../backend')
    )
)

from agent import load_coffee_data
from chatbot import get_chatbot_response


# Page Configuration
st.set_page_config(
    page_title="DeLand Coffee AI Recommendation Engine",
    page_icon="☕",
    layout="centered"
)


# Page Header
st.title("☕ DeLand Coffee AI Recommendation Engine")
st.write(
    "Your intelligent guide to finding the perfect cafe in DeLand, FL."
)


# Load all restaurant JSON files
loaded_files = load_coffee_data()


# Sidebar
with st.sidebar:

    st.header("🏪 Active Coffee Hub")

    st.caption(
        "Connected to your team's restaurant JSON database."
    )

    st.markdown("---")

    if loaded_files:

        st.success(
            f"{len(loaded_files)} restaurants connected"
        )

        for shop_key, shop_data in loaded_files.items():

            if isinstance(shop_data, dict):
                clean_name = shop_data.get(
                    "restaurant",
                    shop_key.replace("_", " ").title()
                )
            else:
                clean_name = shop_key.replace(
                    "_", " "
                ).title()

            st.markdown(f"✅ **{clean_name}**")

    else:
        st.error("No JSON files found.")


# Chat Memory
if "messages" not in st.session_state:

    st.session_state.messages = [
        {
            "role": "assistant",
            "content": (
                "👋 Hey! I'm your DeLand coffee assistant. "
                "What kind of vibe, drink, or seating are "
                "you looking for today?"
            )
        }
    ]


# Display Chat History
for msg in st.session_state.messages:

    with st.chat_message(msg["role"]):

        st.markdown(msg["content"])


# User Input
if prompt := st.chat_input(
    "Search menus, vibes, or locations..."
):

    # Save user message
    st.session_state.messages.append({
        "role": "user",
        "content": prompt
    })

    with st.chat_message("user"):
        st.markdown(prompt)

    # Run integrated chatbot backend
    with st.chat_message("assistant"):

        with st.spinner("Searching all four restaurants..."):

            try:

                result = get_chatbot_response(prompt)

                response = result.get(
                    "response",
                    "I couldn't generate a recommendation."
                )

                # Display chatbot response
                st.markdown(response)

                # Debug information
                st.caption(
                    f"Searching across {len(loaded_files)} "
                    "connected restaurant databases."
                )

            except Exception as e:

                response = (
                    "Sorry, something went wrong while "
                    "searching the restaurant menus."
                )

                st.error(response)

                st.exception(e)

    # Save assistant response
    st.session_state.messages.append({
        "role": "assistant",
        "content": response
    })
