import streamlit as st
import random
import json

# --- 1. CONFIGURATION & STATE INITIALIZATION ---
st.set_page_config(page_title="Cannabis Tycoon", page_icon="🌿", layout="wide")

SHOP_ITEMS = {
    "LED Grow Lights": {"cost": 200, "desc": "+20% Yield on all harvests"},
    "Hydroponic System": {"cost": 300, "desc": "+20% Sale Price (Potency boost)"},
    "Auto-Trimmer": {"cost": 500, "desc": "+1 Extra Sell Action per season"}
}

# List of possible terpenes for random mutations
POSSIBLE_TERPENES = ["Myrcene", "Limonene", "Caryophyllene", "Pinene", "Linalool", "Humulene"]

default_state = {
    "credits": 100,
    "season": 1,
    "overhead": 50,
    "breeds_left": 1,
    "sells_left": 4,
    "sell_limit": 4,
    "strains": {
        "Industrial Hemp": {
            "potency": 2, "yield": 10, 
            "resistance": 8, "speed": 4,
            "terpenes": {"Myrcene": 3}
        },
        "Wild Sativa": {
            "potency": 8, "yield": 3, 
            "resistance": 3, "speed": 9,
            "terpenes": {"Limonene": 7}
        }
    },
    "upgrades": [],
    "game_over": False
}

for key, value in default_state.items():
    if key not in st.session_state:
        st.session_state[key] = value

# --- 2. HELPER FUNCTIONS ---

def calculate_profit(strain_data):
    """Calculates value based on Yield, Potency, and Terpene Complexity"""
    c_yield = strain_data['yield']
    # Base price derived from potency
    c_price = strain_data['potency'] * 5
    
    # Terpene Bonus: Each unique terpene adds 5% value, high strength adds more
    terp_bonus = 0
    for strength in strain_data['terpenes'].values():
        terp_bonus += strength * 0.5 # $0.50 per point of terpene strength
    c_price += terp_bonus

    # Apply Upgrades
    if "LED Grow Lights" in st.session_state.upgrades:
        c_yield *= 1.2
    if "Hydroponic System" in st.session_state.upgrades:
        c_price *= 1.2
        
    return round(c_price * c_yield, 2)

def mix_terpenes(t1, t2):
    """Combines two terpene dictionaries for breeding"""
    new_terps = {}
    # Get all unique terpene names from both parents
    all_keys = set(list(t1.keys()) + list(t2.keys()))
    
    for key in all_keys:
        val1 = t1.get(key, 0)
        val2 = t2.get(key, 0)
        
        # If both have it, average them. If only one, take it (with slight loss risk)
        if val1 > 0 and val2 > 0:
            base = (val1 + val2) / 2
        else:
            base = max(val1, val2) * 0.9 # Slight penalty if only one parent has it
            
        # Random fluctuation
        final_val = round(base + random.uniform(-1, 1), 1)
        
        # Only keep if strength is significant (> 1.0)
        if final_val > 1.0:
            new_terps[key] = final_val
            
    # Chance to mutate a BRAND NEW terpene
    if random.random() < 0.3: # 30% chance
        new_terp = random.choice(POSSIBLE_TERPENES)
        if new_terp not in new_terps:
            new_terps[new_terp] = random.randint(1, 5)
            
    return new_terps

def advance_season():
    cost = st.session_state.overhead
    if st.session_state.credits >= cost:
        st.session_state.credits -= cost
        st.session_state.season += 1
        st.session_state.overhead += 50
        st.session_state.breeds_left = 1
        base_sells = 5 if "Auto-Trimmer" in st.session_state.upgrades else 4
        st.session_state.sells_left = base_sells
        st.session_state.sell_limit = base_sells
        st.success(f"Expenses paid! Season {st.session_state.season} begins.")
    else:
        st.session_state.game_over = True

# --- 3. SIDEBAR DASHBOARD ---
st.sidebar.title(f"🍂 Season {st.session_state.season}")

if st.session_state.game_over:
    st.error("GAME OVER: Bankrupt!")
    if st.sidebar.button("Restart"):
        st.session_state.clear()
        st.rerun()
    st.stop()

col1, col2 = st.sidebar.columns(2)
col1.metric("Bank", f"${round(st.session_state.credits, 2)}")
col2.metric("Overhead", f"-${st.session_state.overhead}", delta_color="inverse")

# Actions Display
total = 1 + st.session_state.sell_limit
used = total - (st.session_state.breeds_left + st.session_state.sells_left)
st.sidebar.progress(used / total)
st.sidebar.caption(f"Breeds: {st.session_state.breeds_left} | Sells: {st.session_state.sells_left}")

# Upgrade Shop
st.sidebar.markdown("---")
with st.sidebar.expander("🛠️ Shop", expanded=False):
    for item, data in SHOP_ITEMS.items():
        if item in st.session_state.upgrades:
            st.info(f"✅ {item}")
        else:
            if st.button(f"{item} (${data['cost']})"):
                if st.session_state.credits >= data['cost']:
                    st.session_state.credits -= data['cost']
                    st.session_state.upgrades.append(item)
                    st.rerun()

# --- 4. MAIN GAME AREA ---
st.title("Cannabis Tycoon: Genetics Edition")

# --- VISUAL STASH TABLE ---
# We create a 'clean' list for display purposes (formatting the terpenes nicely)
display_data = []
for name, stats in st.session_state.strains.items():
    # Format terpenes as string "Myrcene (5), Linalool (2)"
    terp_str = ", ".join([f"{k} ({v})" for k,v in stats['terpenes'].items()])
    display_data.append({
        "Strain": name,
        "Potency": stats['potency'],
        "Yield": stats['yield'],
        "Resist": stats['resistance'],
        "Speed": stats['speed'],
        "Terpenes": terp_str
    })
st.dataframe(display_data, use_container_width=True)


# --- BREEDING LAB ---
st.subheader("🧬 Genetics Lab")
with st.expander("Breed New Strain (Cost: $50)", expanded=True):
    if st.session_state.breeds_left > 0:
        c1, c2 = st.columns(2)
        p1 = c1.selectbox("Parent 1", list(st.session_state.strains.keys()))
        p2 = c2.selectbox("Parent 2", list(st.session_state.strains.keys()))
        new_name = st.text_input("New Name:")
        
        if st.button("Breed ($50)"):
            if new_name and st.session_state.credits >= 50:
                st.session_state.credits -= 50
                st.session_state.breeds_left -= 1
                
                s1, s2 = st.session_state.strains[p1], st.session_state.strains[p2]
                
                # Standard Stat Inheritance
                new_pot = round((s1['potency'] + s2['potency']) / 2 + random.uniform(-1, 2), 1)
                new_yld = round((s1['yield'] + s2['yield']) / 2 + random.uniform(-1, 2), 1)
                new_res = round((s1['resistance'] + s2['resistance']) / 2 + random.uniform(-1, 2), 1)
                new_spd = round((s1['speed'] + s2['speed']) / 2 + random.uniform(-1, 2), 1)
                
                # Complex Terpene Inheritance
                new_terps = mix_terpenes(s1['terpenes'], s2['terpenes'])
                
                st.session_state.strains[new_name] = {
                    "potency": max(1, new_pot), 
                    "yield": max(1, new_yld),
                    "resistance": max(1, min(10, new_res)), # Cap at 10
                    "speed": max(1, min(10, new_spd)),      # Cap at 10
                    "terpenes": new_terps
                }
                st.success(f"Bred {new_name} with {len(new_terps)} terpenes!")
                st.rerun()
            elif not new_name:
                st.error("Enter a name!")
            else:
                st.error("Not enough cash!")
    else:
        st.info("No breeding slots left.")

# --- MARKETPLACE ---
st.subheader("🏪 Marketplace")
if st.session_state.sells_left > 0:
    sell_target = st.selectbox("Sell Batch", list(st.session_state.strains.keys()))
    val = calculate_profit(st.session_state.strains[sell_target])
    
    st.caption(f"Market Value: ${val}")
    
    if st.button("Sell Batch"):
        st.session_state.credits += val
        st.session_state.sells_left -= 1
        st.success(f"Sold for ${val}")
        st.rerun()
else:
    st.info("Market closed for the season.")

st.markdown("---")
if st.button("End Season & Pay Overhead"):
    advance_season()
    st.rerun()
