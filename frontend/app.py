import streamlit as st
import sys
import os

# Link backend directory
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../backend')))
from agent import search_and_recommend, load_coffee_data

# Page Configuration
st.set_page_config(
    page_title="DeLand Coffee AI Recommendation Engine",
    page_icon="☕",
    layout="centered"
)

st.title("☕ DeLand Coffee AI Recommendation Engine")
st.write("Your intelligent guide to finding the perfect cafe in DeLand, FL.")

# Clean up sidebar status display
with st.sidebar:
    st.header("🏪 Active Coffee Hub")
    st.caption("Successfully connected to your team's JSON database.")
    st.markdown("---")
    
    loaded_files = load_coffee_data()
    if loaded_files:
        for shop_key in loaded_files.keys():
            # Format clean names like "Boston Coffeehouse" instead of raw file names
            clean_name = shop_key.replace('_', ' ').title()
            st.markdown(f"✅ **{clean_name}**")
    else:
        st.error("No JSON files found.")

# Chat Memory
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "👋 Hey! I'm your DeLand coffee assistant. What kind of vibe, drink, or seating are you looking for today?"}
    ]

# Display Chat History
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# User Input
if prompt := st.chat_input("Search menus, vibes, or locations (e.g., 'quiet place with wifi')..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Run backend JSON recommendation engine
    response = search_and_recommend(prompt)

    st.session_state.messages.append({"role": "assistant", "content": response})
    with st.chat_message("assistant"):
        st.markdown(response)
