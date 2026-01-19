import streamlit as st
import json
import random

# 1. Setup Persistent Data (This keeps your money from resetting on every click)
if 'credits' not in st.session_state:
    st.session_state.credits = 100
if 'strains' not in st.session_state:
    st.session_state.strains = {
        "Industrial Hemp": {"potency": 2, "yield": 10},
        "Wild Sativa": {"potency": 8, "yield": 3}
    }

# 2. Sidebar - Player Stats
st.sidebar.title("🌿 Breeding Lab")
st.sidebar.metric("Bank Balance", f"${st.session_state.credits}")
st.sidebar.write("### Your Stash")
st.sidebar.table(st.session_state.strains)

# 3. Main Area - Breeding
st.title("Strain Laboratory")

with st.expander("🧬 Breed New Strain (Cost: $50)"):
    p1 = st.selectbox("Select Parent 1", list(st.session_state.strains.keys()))
    p2 = st.selectbox("Select Parent 2", list(st.session_state.strains.keys()))
    new_name = st.text_input("Name your new creation:")

    if st.button("Start Breeding"):
        if st.session_state.credits >= 50:
            st.session_state.credits -= 50
            # Breeding Logic
            s1, s2 = st.session_state.strains[p1], st.session_state.strains[p2]
            new_potency = round((s1['potency'] + s2['potency']) / 2 + random.uniform(-1, 2), 1)
            new_yield = round((s1['yield'] + s2['yield']) / 2 + random.uniform(-1, 2), 1)

            st.session_state.strains[new_name] = {"potency": new_potency, "yield": new_yield}
            st.success(f"Successfully bred {new_name}!")
        else:
            st.error("Insufficient funds!")

# 4. Main Area - Marketplace
st.write("### 💰 Marketplace")
sell_target = st.selectbox("What are you selling?", list(st.session_state.strains.keys()))
if st.button("Sell Harvest"):
    strain = st.session_state.strains[sell_target]
    profit = round((strain['potency'] * 5) * strain['yield'], 2)
    st.session_state.credits += profit
    st.balloons()  # Visual celebration!

    st.info(f"Sold for ${profit}")


# 5. Save and Load Functionality
st.sidebar.markdown("---")
st.sidebar.write("### 💾 Game Data")

# --- SAVE GAME ---
# We convert the current game state into a string
game_data = {
    "credits": st.session_state.credits,
    "strains": st.session_state.strains
}
save_string = json.dumps(game_data)

st.sidebar.download_button(
    label="Download Save File",
    data=save_string,
    file_name="breeding_save.json",
    mime="application/json"
)

# --- LOAD GAME ---
uploaded_file = st.sidebar.file_uploader("Upload Save File", type="json")
if uploaded_file is not None:
    loaded_data = json.load(uploaded_file)
    # Update the game state with the loaded data
    st.session_state.credits = loaded_data["credits"]
    st.session_state.strains = loaded_data["strains"]
    st.sidebar.success("Game Loaded!")
