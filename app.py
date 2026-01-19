import streamlit as st
import json
import random

# --- 1. INITIALIZE GAME STATE ---
default_state = {
    "credits": 100,
    "season": 1,
    "overhead": 50,
    "breeds_left": 1,
    "sells_left": 4,
    "strains": {
        "Industrial Hemp": {"potency": 2, "yield": 10},
        "Wild Sativa": {"potency": 8, "yield": 3}
        
    },
    "game_over": False
    if "upgrades" not in st.session_state:
    st.session_state.upgrades = []
}

for key, value in default_state.items():
    if key not in st.session_state:
        st.session_state[key] = value

# Helper function to reset actions for next season
def advance_season():
    cost = st.session_state.overhead
    if st.session_state.credits >= cost:
        st.session_state.credits -= cost
        st.session_state.season += 1
        st.session_state.overhead += 50  # Increases by $50 each season
        # Reset Actions
        st.session_state.breeds_left = 1
        st.session_state.sells_left = 4
        st.success(f"Expenses paid! Welcome to Season {st.session_state.season}.")
    else:
        st.session_state.game_over = True

# --- 2. SIDEBAR DASHBOARD ---
st.sidebar.title(f"🍂 Season {st.session_state.season}")

if st.session_state.game_over:
    st.error("GAME OVER: You went bankrupt!")
    if st.sidebar.button("Restart Game"):
        for key in st.session_state.keys():
            del st.session_state[key]
        st.rerun()
    st.stop() # Stops the rest of the app from running

# Stats Display
col1, col2 = st.sidebar.columns(2)
col1.metric("Bank", f"${st.session_state.credits}")
col2.metric("Due End of Season", f"-${st.session_state.overhead}", delta_color="inverse")

st.sidebar.markdown("### ⏳ Season Quota")
st.sidebar.progress((5 - (st.session_state.breeds_left + st.session_state.sells_left)) / 5)
st.sidebar.write(f"🧬 Breeds Left: **{st.session_state.breeds_left}**")
st.sidebar.write(f"💰 Sells Left: **{st.session_state.sells_left}**")

st.sidebar.markdown("---")
st.sidebar.write("### 🌿Strain Catalog")
st.sidebar.table(st.session_state.strains)

st.sidebar.markdown("---")
st.sidebar.write("### 🛠️ Equipment Shop")

# Define available upgrades
shop_items = {
    "LED Lights": {"cost": 150, "effect": "yield_boost", "desc": "+20% Yield on sales"},
    "Hydro System": {"cost": 250, "effect": "potency_boost", "desc": "+20% Price on sales"}
}

for item, data in shop_items.items():
    if item not in st.session_state.upgrades:
        if st.sidebar.button(f"Buy {item} (${data['cost']})"):
            if st.session_state.credits >= data['cost']:
                st.session_state.credits -= data['cost']
                st.session_state.upgrades.append(item)
                st.success(f"Purchased {item}!")
                st.rerun()
            else:
                st.error("Not enough cash!")
    else:
        st.sidebar.info(f"✅ {item} Active")

# --- 3. MAIN GAMEPLAY AREA ---
st.title("Cultivar Labs")

# --- BREEDING SECTION ---
st.subheader("🧬 Genetics Lab")
with st.expander("Breed New Strain (Cost: $50)", expanded=True):
    if st.session_state.breeds_left > 0:
        c1, c2 = st.columns(2)
        p1 = c1.selectbox("Parent 1", list(st.session_state.strains.keys()), key="p1")
        p2 = c2.selectbox("Parent 2", list(st.session_state.strains.keys()), key="p2")
        new_name = st.text_input("Name New Strain:")
        
        if st.button("Breed Strain ($50)"):
            if st.session_state.credits >= 50:
                st.session_state.credits -= 50
                st.session_state.breeds_left -= 1
                
                # Math Logic
                s1, s2 = st.session_state.strains[p1], st.session_state.strains[p2]
                new_potency = round((s1['potency'] + s2['potency']) / 2 + random.uniform(-1, 2), 1)
                new_yield = round((s1['yield'] + s2['yield']) / 2 + random.uniform(-1, 2), 1)
                
                st.session_state.strains[new_name] = {"potency": max(1, new_potency), "yield": max(1, new_yield)}
                st.success(f"Created {new_name}!")
                st.rerun()
            else:
                st.error("Not enough cash!")
    else:
        st.info("⚠️ No breeding slots left this season.")

# --- SELLING SECTION ---
st.subheader("🏪 Marketplace")
if st.button("Sell Batch"):
    strain = st.session_state.strains[sell_target]
    
    # CALCULATE BASE VALUES
    current_yield = strain['yield']
    current_price = strain['potency'] * 5
    
    # APPLY UPGRADES
    if "LED Lights" in st.session_state.upgrades:
        current_yield *= 1.2  # 20% boost
    if "Hydro System" in st.session_state.upgrades:
        current_price *= 1.2  # 20% boost

    profit = round(current_price * current_yield, 2)
    # ... rest of the code
if st.session_state.sells_left > 0:
    sell_target = st.selectbox("Select Batch to Sell", list(st.session_state.strains.keys()))
    if st.button("Sell Batch"):
        strain = st.session_state.strains[sell_target]
        profit = round((strain['potency'] * 5) * strain['yield'], 2)
        
        st.session_state.credits += profit
        st.session_state.sells_left -= 1
        st.balloons()
        st.success(f"Sold for ${profit}")
        st.rerun()
else:
    st.info("⚠️ You have sold your maximum batches for this season.")

# --- END SEASON ---
st.markdown("---")
if st.session_state.breeds_left == 0 and st.session_state.sells_left == 0:
    st.warning("SEASON COMPLETE: All actions used.")
    if st.button(f"Pay ${st.session_state.overhead} & Start Season {st.session_state.season + 1}"):
        advance_season()
        st.rerun()
else:
    # Optional: Allow early advance if they want to skip remaining actions
    if st.button(f"End Season Early (Pay ${st.session_state.overhead})"):
        advance_season()
        st.rerun()


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






