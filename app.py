import streamlit as st
import random
import json

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="Cannabis Tycoon", page_icon="🌿", layout="wide")

SHOP_ITEMS = {
    "LED Grow Lights": {"cost": 200, "desc": "+20% Yield on all harvests"},
    "Hydroponic System": {"cost": 300, "desc": "+20% Sale Price (Potency boost)"},
    "Auto-Trimmer": {"cost": 500, "desc": "Unlocks a 5th Grow Plot"}
}

POSSIBLE_TERPENES = ["Myrcene", "Limonene", "Caryophyllene", "Pinene", "Linalool", "Humulene"]

# --- 2. STATE MANAGEMENT ---
default_state = {
    "credits": 100,
    "season": 1,
    "overhead": 50,
    "breeds_left": 1,
    "phase": "PLANNING", # New Phase System: PLANNING -> HARVEST -> END
    "plots_results": [], # Stores data about grown crops
    "strains": {
        "Industrial Hemp": {"potency": 2, "yield": 10, "resistance": 8, "speed": 4, "terpenes": {"Myrcene": 3}},
        "Wild Sativa": {"potency": 8, "yield": 3, "resistance": 3, "speed": 9, "terpenes": {"Limonene": 7}}
    },
    "upgrades": [],
    "game_over": False
}

for key, value in default_state.items():
    if key not in st.session_state:
        st.session_state[key] = value

# --- 3. GAME LOGIC FUNCTIONS ---

def mix_terpenes(t1, t2):
    """Combines two terpene dictionaries for breeding"""
    new_terps = {}
    all_keys = set(list(t1.keys()) + list(t2.keys()))
    for key in all_keys:
        val1, val2 = t1.get(key, 0), t2.get(key, 0)
        base = (val1 + val2) / 2 if (val1 > 0 and val2 > 0) else max(val1, val2) * 0.9
        final_val = round(base + random.uniform(-1, 1), 1)
        if final_val > 1.0: new_terps[key] = final_val
    if random.random() < 0.3: # Mutation
        new_terp = random.choice(POSSIBLE_TERPENES)
        if new_terp not in new_terps: new_terps[new_terp] = random.randint(1, 5)
    return new_terps

def run_grow_simulation(plot_assignments):
    """Calculates the results for all assigned plots"""
    results = []
    
    for strain_name in plot_assignments:
        stats = st.session_state.strains[strain_name]
        
        # 1. Base Calcs
        # Random variance based on strain stats
        actual_yield = round(stats['yield'] * random.uniform(0.8, 1.2), 2)
        actual_potency = stats['potency']
        
        # 2. Apply Upgrades
        if "LED Grow Lights" in st.session_state.upgrades:
            actual_yield *= 1.2
        if "Hydroponic System" in st.session_state.upgrades:
            actual_potency *= 1.2 # Simulating higher quality
            
        # 3. Calculate Value
        # Terpene Bonus
        terp_bonus = sum(stats['terpenes'].values()) * 0.5
        price_per_unit = (actual_potency * 5) + terp_bonus
        total_value = round(actual_yield * price_per_unit, 2)
        
        results.append({
            "strain": strain_name,
            "yield": round(actual_yield, 2),
            "value": total_value,
            "desc": "Healthy Harvest" # Placeholder for future random events
        })
        
    return results

def reset_season():
    cost = st.session_state.overhead
    if st.session_state.credits >= cost:
        st.session_state.credits -= cost
        st.session_state.season += 1
        st.session_state.overhead += 50
        st.session_state.breeds_left = 1
        st.session_state.phase = "PLANNING"
        st.session_state.plots_results = []
        st.success("Season Complete!")
    else:
        st.session_state.game_over = True

# --- 4. SIDEBAR ---
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

# Shop
st.sidebar.markdown("---")
with st.sidebar.expander("🛠️ Shop"):
    for item, data in SHOP_ITEMS.items():
        if item in st.session_state.upgrades:
            st.info(f"✅ {item}")
        else:
            if st.button(f"{item} (${data['cost']})"):
                if st.session_state.credits >= data['cost']:
                    st.session_state.credits -= data['cost']
                    st.session_state.upgrades.append(item)
                    st.rerun()

st.sidebar.markdown("---")
st.sidebar.caption("Grow Log")
st.sidebar.dataframe([{"Strain": k, "Potency": v['potency'], "Yield": v['yield']} for k,v in st.session_state.strains.items()], use_container_width=True)


# --- 5. MAIN GAME AREA ---
st.title("Cannabis Tycoon: Farm Manager")

# === PHASE 1: BREEDING (Always visible during Planning) ===
if st.session_state.phase == "PLANNING":
    with st.expander("🧬 Genetics Lab (Breed New Strain - $50)", expanded=False):
        if st.session_state.breeds_left > 0:
            c1, c2 = st.columns(2)
            p1 = c1.selectbox("Parent 1", list(st.session_state.strains.keys()))
            p2 = c2.selectbox("Parent 2", list(st.session_state.strains.keys()))
            new_name = st.text_input("New Name:")
            if st.button("Breed"):
                if new_name and st.session_state.credits >= 50:
                    st.session_state.credits -= 50
                    st.session_state.breeds_left -= 1
                    s1, s2 = st.session_state.strains[p1], st.session_state.strains[p2]
                    
                    new_stats = {
                        "potency": round((s1['potency']+s2['potency'])/2 + random.uniform(-1,2),1),
                        "yield": round((s1['yield']+s2['yield'])/2 + random.uniform(-1,2),1),
                        "resistance": round((s1['resistance']+s2['resistance'])/2, 1),
                        "speed": round((s1['speed']+s2['speed'])/2, 1),
                        "terpenes": mix_terpenes(s1['terpenes'], s2['terpenes'])
                    }
                    st.session_state.strains[new_name] = new_stats
                    st.success(f"Bred {new_name}!")
                    st.rerun()
                elif st.session_state.credits < 50:
                    st.error("Need $50!")
        else:
            st.info("Breeding finished for this season.")

# === PHASE 2: PLOT MANAGEMENT ===
st.divider()
st.subheader("🚜 Grow Operations")

# Determine number of plots (4 base + 1 if upgrade)
num_plots = 5 if "Auto-Trimmer" in st.session_state.upgrades else 4
cols = st.columns(num_plots)

if st.session_state.phase == "PLANNING":
    st.info(f"Select strains for your {num_plots} plots. High Resistance strains are safer!")
    
    # Create a list to capture user choices
    selected_strains = []
    
    for i, col in enumerate(cols):
        with col:
            st.markdown(f"**Plot {i+1}**")
            # Default to first strain to avoid empty errors
            choice = st.selectbox(f"Strain", list(st.session_state.strains.keys()), key=f"plot_{i}")
            selected_strains.append(choice)
            
            # Show quick stats for selection
            stats = st.session_state.strains[choice]
            st.caption(f"Pot: {stats['potency']} | Yld: {stats['yield']}")

    st.markdown("---")
    if st.button("🌱 START GROW SEASON", type="primary"):
        # Run the simulation
        results = run_grow_simulation(selected_strains)
        st.session_state.plots_results = results
        st.session_state.phase = "HARVEST"
        st.rerun()

elif st.session_state.phase == "HARVEST":
    st.success("Harvest Complete! Review your yields below.")
    
    total_season_value = 0
    
    # Display Results in Cards
    for i, col in enumerate(cols):
        # Handle case where user might have fewer results if they just upgraded (safety check)
        if i < len(st.session_state.plots_results):
            res = st.session_state.plots_results[i]
            total_season_value += res['value']
            
            with col:
                st.markdown(f"### Plot {i+1}")
                st.info(f"**{res['strain']}**")
                st.metric("Yield", f"{res['yield']} oz")
                st.metric("Value", f"${res['value']}")
                st.caption(res['desc'])

    st.markdown("---")
    st.subheader(f"Total Harvest Value: ${round(total_season_value, 2)}")
    
    # The Big Payoff Button
    if st.button("💰 SELL HARVEST & PAY RENT", type="primary"):
        st.session_state.credits += total_season_value
        reset_season()
        st.rerun()
