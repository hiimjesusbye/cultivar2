import streamlit as st
import random
import json

# --- 1. CONFIGURATION & STATE INITIALIZATION ---
st.set_page_config(page_title="Cannabis Tycoon", page_icon="🌿")

# Define available shop items and their effects
SHOP_ITEMS = {
    "LED Grow Lights": {"cost": 200, "desc": "+20% Yield on all harvests"},
    "Hydroponic System": {"cost": 300, "desc": "+20% Sale Price (Potency boost)"},
    "Auto-Trimmer": {"cost": 500, "desc": "+1 Extra Sell Action per season"}
}

default_state = {
    "credits": 100,
    "season": 1,
    "overhead": 50,
    "breeds_left": 1,
    "sells_left": 4,
    "sell_limit": 4, # Base limit, can be upgraded
    "strains": {
        "Industrial Hemp": {"potency": 2, "yield": 10},
        "Wild Sativa": {"potency": 8, "yield": 3}
    },
    "upgrades": [],
    "game_over": False
}

# Load defaults if not present
for key, value in default_state.items():
    if key not in st.session_state:
        st.session_state[key] = value

# --- 2. HELPER FUNCTIONS ---

def calculate_profit(strain_data):
    """Calculates sell value based on stats and active upgrades."""
    # Base Values
    c_yield = strain_data['yield']
    c_price = strain_data['potency'] * 5
    
    # Apply Upgrades
    if "LED Grow Lights" in st.session_state.upgrades:
        c_yield *= 1.2
    if "Hydroponic System" in st.session_state.upgrades:
        c_price *= 1.2
        
    return round(c_price * c_yield, 2)

def advance_season():
    cost = st.session_state.overhead
    if st.session_state.credits >= cost:
        st.session_state.credits -= cost
        st.session_state.season += 1
        st.session_state.overhead += 50
        
        # Reset Actions
        st.session_state.breeds_left = 1
        # Check for Auto-Trimmer upgrade for extra sell slot
        base_sells = 5 if "Auto-Trimmer" in st.session_state.upgrades else 4
        st.session_state.sells_left = base_sells
        st.session_state.sell_limit = base_sells
        
        st.success(f"Expenses paid! Welcome to Season {st.session_state.season}.")
    else:
        st.session_state.game_over = True

# --- 3. SIDEBAR DASHBOARD ---
st.sidebar.title(f"🍂 Season {st.session_state.season}")

# GAME OVER CHECK
if st.session_state.game_over:
    st.error("GAME OVER: Bankrupt!")
    if st.sidebar.button("Restart Game"):
        st.session_state.clear()
        st.rerun()
    st.stop()

# Stats
col1, col2 = st.sidebar.columns(2)
col1.metric("Bank", f"${round(st.session_state.credits, 2)}")
col2.metric("Due Soon", f"-${st.session_state.overhead}", delta_color="inverse")

# Quotas
st.sidebar.markdown("### ⏳ Actions")
total_actions = 1 + st.session_state.sell_limit
used_actions = total_actions - (st.session_state.breeds_left + st.session_state.sells_left)
st.sidebar.progress(used_actions / total_actions)
st.sidebar.write(f"🧬 Breeds: **{st.session_state.breeds_left}**")
st.sidebar.write(f"💰 Sells: **{st.session_state.sells_left}**")

# SHOP SECTION (NEW)
st.sidebar.markdown("---")
st.sidebar.write("### 🛠️ Upgrades")
for item, data in SHOP_ITEMS.items():
    if item in st.session_state.upgrades:
        st.sidebar.info(f"✅ {item}")
    else:
        if st.sidebar.button(f"Buy {item} (${data['cost']})"):
            if st.session_state.credits >= data['cost']:
                st.session_state.credits -= data['cost']
                st.session_state.upgrades.append(item)
                st.success(f"Bought {item}!")
                st.rerun()
            else:
                st.sidebar.error("Need Cash!")
        st.sidebar.caption(data['desc'])

# STASH & SAVE
st.sidebar.markdown("---")
st.sidebar.write("### 🌿 Stash")
st.sidebar.table(st.session_state.strains)

with st.sidebar.expander("💾 Save / Load"):
    # Save
    game_data = {k:v for k,v in st.session_state.items() if k != "game_over"} 
    # (We exclude UI-specific keys usually, but dumping session_state is fine for this scale)
    st.download_button("Download Save", json.dumps(game_data), "save.json", "application/json")
    
    # Load
    uploaded_file = st.file_uploader("Upload Save", type="json")
    if uploaded_file:
        data = json.load(uploaded_file)
        for k, v in data.items():
            st.session_state[k] = v
        st.success("Loaded!")
        st.rerun()

# --- 4. MAIN GAME AREA ---
st.title("Cannabis Tycoon: Text Edition")

# Breeding
st.subheader("🧬 Genetics Lab")
with st.expander("Breed New Strain (Cost: $50)", expanded=True):
    if st.session_state.breeds_left > 0:
        c1, c2 = st.columns(2)
        p1 = c1.selectbox("Parent 1", list(st.session_state.strains.keys()))
        p2 = c2.selectbox("Parent 2", list(st.session_state.strains.keys()))
        new_name = st.text_input("New Strain Name:")
        
        if st.button("Breed ($50)"):
            if not new_name:
                st.error("Please name your strain.")
            elif st.session_state.credits >= 50:
                st.session_state.credits -= 50
                st.session_state.breeds_left -= 1
                
                s1, s2 = st.session_state.strains[p1], st.session_state.strains[p2]
                new_potency = round((s1['potency'] + s2['potency']) / 2 + random.uniform(-1, 2), 1)
                new_yield = round((s1['yield'] + s2['yield']) / 2 + random.uniform(-1, 2), 1)
                
                st.session_state.strains[new_name] = {"potency": max(1, new_potency), "yield": max(1, new_yield)}
                st.balloons()
                st.success(f"Created {new_name}!")
                st.rerun()
            else:
                st.error("Not enough cash!")
    else:
        st.info("⚠️ Breeding slot used for this season.")

# Selling
st.subheader("🏪 Marketplace")
if st.session_state.sells_left > 0:
    sell_target = st.selectbox("Select Batch to Sell", list(st.session_state.strains.keys()))
    
    # Show estimated profit before clicking
    est_profit = calculate_profit(st.session_state.strains[sell_target])
    st.caption(f"Estimated Value: ${est_profit}")
    
    if st.button("Sell Batch"):
        profit = calculate_profit(st.session_state.strains[sell_target])
        st.session_state.credits += profit
        st.session_state.sells_left -= 1
        st.success(f"Sold for ${profit}")
        st.rerun()
else:
    st.info("⚠️ All sell slots used for this season.")

# End Season
st.markdown("---")
if st.button(f"Pay Overhead (${st.session_state.overhead}) & Next Season"):
    advance_season()
    st.rerun()
