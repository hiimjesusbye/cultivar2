import streamlit as st
import random
import json
import time

# --- 1. CONFIGURATION & DATA ---
st.set_page_config(page_title="Cannabis Tycoon: Hard Mode", page_icon="🌿", layout="wide")

SHOP_ITEMS = {
    "LED Grow Lights": {"cost": 200, "desc": "+20% Yield on all harvests"},
    "Hydroponic System": {"cost": 300, "desc": "+20% Sale Price (Potency boost)"},
    "Auto-Trimmer": {"cost": 500, "desc": "Unlocks a 5th Grow Plot"}
}

TERPENE_INFO = {
    "Myrcene": "Sedative / Relaxing",
    "Limonene": "Energy / Mood Lift",
    "Caryophyllene": "Spicy / Anti-Inflammatory",
    "Pinene": "Piney / Focus",
    "Linalool": "Floral / Calming",
    "Humulene": "Earthy / Appetite Suppressant",
    "Terpinolene": "Fruity / Uplifting",
    "Ocimene": "Sweet / Decongestant"
}

# --- 2. STATE MANAGEMENT ---
default_state = {
    "credits": 100,
    "season": 1,
    "overhead": 50,
    "breed_cost": 50,
    "breeds_left": 1,
    "phase": "PLANNING", 
    "plots_results": [],
    "discovered_terpenes": ["Myrcene", "Limonene"],
    "strains": {
        "Industrial Hemp": {
            "potency": 2, "yield": 10, "resistance": 8, "speed": 4, 
            "terpenes": {"Myrcene": 3} 
        },
        "Wild Sativa": {
            "potency": 8, "yield": 3, "resistance": 3, "speed": 9, 
            "terpenes": {"Limonene": 7}
        }
    },
    "upgrades": [],
    "game_over": False
}

for key, value in default_state.items():
    if key not in st.session_state:
        st.session_state[key] = value

# --- 3. LOGIC FUNCTIONS ---

def mix_terpenes(t1, t2):
    """Breeds two terpene profiles and checks for discoveries"""
    new_terps = {}
    all_keys = set(list(t1.keys()) + list(t2.keys()))
    for key in all_keys:
        val1, val2 = t1.get(key, 0), t2.get(key, 0)
        base = (val1 + val2) / 2 if (val1 > 0 and val2 > 0) else max(val1, val2) * 0.9
        final_val = round(base + random.uniform(-1.5, 1.5), 1)
        if final_val > 0.5: new_terps[key] = final_val

    # Mutation Chance
    mutation_chance = 0.2 + (len(new_terps) * 0.05)
    if random.random() < mutation_chance:
        possible_new = [t for t in TERPENE_INFO.keys() if t not in new_terps]
        if possible_new:
            discovered = random.choice(possible_new)
            new_terps[discovered] = random.randint(1, 4)
            if discovered not in st.session_state.discovered_terpenes:
                st.session_state.discovered_terpenes.append(discovered)
                st.toast(f"🧪 NEW DISCOVERY: {discovered}!", icon="🎉")
    return new_terps

def run_grow_simulation(plot_assignments):
    results = []
    for strain_name in plot_assignments:
        stats = st.session_state.strains[strain_name]
        
        # Variance
        actual_yield = round(stats['yield'] * random.uniform(0.8, 1.2), 2)
        actual_potency = stats['potency']
        
        # Upgrades
        if "LED Grow Lights" in st.session_state.upgrades: actual_yield *= 1.2
        if "Hydroponic System" in st.session_state.upgrades: actual_potency *= 1.2
            
        terp_value = sum(stats['terpenes'].values()) * 0.5
        price_per_unit = (actual_potency * 5) + terp_value
        total_value = round(actual_yield * price_per_unit, 2)
        
        results.append({
            "strain": strain_name,
            "yield": round(actual_yield, 2),
            "value": total_value,
            "terp_bonus": round(terp_value, 2)
        })
    return results

def reset_season(profit):
    # Credits update happens inside the button now, this just handles season reset
    cost = st.session_state.overhead
    
    # Check if they can afford expenses (Profit is already added to credits before this check)
    if st.session_state.credits >= cost:
        st.session_state.credits -= cost
        st.session_state.season += 1
        st.session_state.overhead *= 2 # HARD MODE: Expenses Double
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

st.sidebar.markdown("---")
st.sidebar.metric("Current Breeding Cost", f"${st.session_state.breed_cost}")

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
st.sidebar.caption("Strain Library")

# PREPARE DATA FOR SIDEBAR TABLE
library_data = []
for name, data in st.session_state.strains.items():
    # Format terpenes into a readable string
    t_str = ", ".join([f"{k}({v})" for k,v in data['terpenes'].items()]) if data['terpenes'] else "-"
    library_data.append({
        "Name": name,
        "Pot": data['potency'],
        "Yld": data['yield'],
        "Terps": t_str
    })

st.sidebar.dataframe(
    library_data,
    use_container_width=True, 
    hide_index=True
)

st.sidebar.markdown("---")
st.sidebar.subheader(f"🧪 Terpenes ({len(st.session_state.discovered_terpenes)}/{len(TERPENE_INFO)})")
for t_name in st.session_state.discovered_terpenes:
    desc = TERPENE_INFO.get(t_name, "Unknown Effect")
    st.sidebar.markdown(f"**{t_name}**: _{desc}_")

# --- 5. MAIN UI ---
st.title("Cannabis Tycoon: Hard Mode")

# === BREEDING ===
if st.session_state.phase == "PLANNING":
    cost = st.session_state.breed_cost
    with st.expander(f"🧬 Genetics Lab (Breed - ${cost})", expanded=False):
        if st.session_state.breeds_left > 0:
            c1, c2 = st.columns(2)
            p1 = c1.selectbox("Parent 1", list(st.session_state.strains.keys()))
            p2 = c2.selectbox("Parent 2", list(st.session_state.strains.keys()))
            new_name = st.text_input("New Name:")
            
            if st.button(f"Breed Strain (${cost})"):
                if new_name and st.session_state.credits >= cost:
                    st.session_state.credits -= cost
                    st.session_state.breeds_left -= 1
                    st.session_state.breed_cost += 50 
                    
                    s1, s2 = st.session_state.strains[p1], st.session_state.strains[p2]
                    new_terps = mix_terpenes(s1['terpenes'], s2['terpenes'])
                    new_stats = {
                        "potency": round((s1['potency']+s2['potency'])/2 + random.uniform(-1,2),1),
                        "yield": round((s1['yield']+s2['yield'])/2 + random.uniform(-1,2),1),
                        "resistance": round((s1['resistance']+s2['resistance'])/2, 1),
                        "speed": round((s1['speed']+s2['speed'])/2, 1),
                        "terpenes": new_terps
                    }
                    st.session_state.strains[new_name] = new_stats
                    st.success(f"Bred {new_name}!")
                    st.rerun()
                elif st.session_state.credits < cost:
                    st.error(f"Need ${cost}!")
        else:
            st.info("Breeding finished for this season.")

# === PLOTS ===
st.divider()
st.subheader("🚜 Grow Operations")
num_plots = 5 if "Auto-Trimmer" in st.session_state.upgrades else 4
cols = st.columns(num_plots)

if st.session_state.phase == "PLANNING":
    selected_strains = []
    for i, col in enumerate(cols):
        with col:
            st.markdown(f"**Plot {i+1}**")
            choice = st.selectbox("Select", list(st.session_state.strains.keys()), key=f"p_{i}")
            selected_strains.append(choice)
            
            # SHOW FULL STATS UNDER PLOT
            s_data = st.session_state.strains[choice]
            t_profile = s_data['terpenes']
            t_str = ", ".join([f"{k}({v})" for k,v in t_profile.items()]) if t_profile else "None"
            
            st.caption(f"**Potency:** {s_data['potency']} | **Yield:** {s_data['yield']}")
            st.caption(f"🧬 {t_str}")

    st.markdown("---")
    
    if st.button("🌱 START GROW SEASON", type="primary"):
        # Progress Bar Simulation
        progress_text = "Plants are growing... checking humidity... trimming leaves..."
        my_bar = st.progress(0, text=progress_text)

        for percent_complete in range(100):
            time.sleep(0.04) 
            my_bar.progress(percent_complete + 1, text=progress_text)
            
        my_bar.empty()
        
        results = run_grow_simulation(selected_strains)
        st.session_state.plots_results = results
        st.session_state.phase = "HARVEST"
        st.rerun()

elif st.session_state.phase == "HARVEST":
    st.success("Harvest Ready!")
    total_val = 0
    
    # Display Plot Results
    for i, col in enumerate(cols):
        if i < len(st.session_state.plots_results):
            res = st.session_state.plots_results[i]
            total_val += res['value']
            with col:
                st.markdown(f"### Plot {i+1}")
                st.info(f"**{res['strain']}**")
                st.metric("Yield", f"{res['yield']} oz")
                st.metric("Value", f"${res['value']}")
                if res['terp_bonus'] > 0:
                    st.caption(f"🌟 +${res['terp_bonus']} from Terpenes")

    # FINANCIAL SUMMARY SECTION
    st.markdown("---")
    st.subheader("📊 Season Financials")
    
    overhead = st.session_state.overhead
    net_profit = total_val - overhead
    
    m1, m2, m3 = st.columns(3)
    m1.metric("Gross Harvest", f"${total_val:.2f}")
    m2.metric("Season Expenses", f"-${overhead:.2f}", delta_color="inverse")
    m3.metric("Net Earnings", f"${net_profit:.2f}", delta=round(net_profit, 2))
    
    if st.button("💰 FINALIZE SEASON", type="primary"):
        st.session_state.credits += total_val
        reset_season(total_val)
        st.rerun()
