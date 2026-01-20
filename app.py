import streamlit as st
import random
import uuid
import json
from enum import Enum
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional

# --- 1. CONFIGURATION & ENUMS ---

class TraitCategory(str, Enum):
    CHEMICAL = "Chemical Profile"
    GROWTH = "Growth Behavior"
    MARKET = "Market/Consumer"
    AESTHETIC = "Aesthetic/Flavor"
    NEGATIVE = "Negative/Quirk"

class TraitEffect(str, Enum):
    POSITIVE = "Positive"
    NEGATIVE = "Negative"
    MIXED = "Mixed"

class Rarity(str, Enum):
    COMMON = "Common"
    UNCOMMON = "Uncommon"
    RARE = "Rare"
    LEGENDARY = "Legendary"

# --- 2. DATA MODELS ---

@dataclass
class Trait:
    id: str
    name: str
    category: TraitCategory
    effect_type: TraitEffect
    rarity: Rarity
    description: str
    inheritance_weight: float = 1.0

@dataclass
class Strain:
    name: str
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    
    # Core Stats (0-100)
    potency: int = 50
    yield_amount: int = 50
    growth_speed: int = 50 
    stability: int = 50
    hardiness: int = 50
    
    # Genetics
    traits: List[str] = field(default_factory=list)
    revealed_traits: List[str] = field(default_factory=list)
    
    # Metadata
    generation: int = 1
    parents: str = "Unknown"
    times_grown: int = 0

    def get_tier(self, value: int) -> str:
        if value < 20: return "Very Low"
        if value < 40: return "Low"
        if value < 60: return "Average"
        if value < 80: return "High"
        return "Exceptional"

    def get_growth_tier(self) -> str:
        if self.growth_speed < 30: return "Sluggish"
        if self.growth_speed < 60: return "Standard"
        return "Vigorous"

    def to_dict(self):
        return asdict(self)

    @staticmethod
    def from_dict(data):
        return Strain(**data)

# --- 3. TRAIT DATABASE ---
TRAIT_DB = {
    "chem_limonene": Trait("chem_limonene", "Heavy Limonene", TraitCategory.CHEMICAL, TraitEffect.POSITIVE, Rarity.COMMON, "Strong citrus aroma.", 1.2),
    "chem_cbd_rich": Trait("chem_cbd_rich", "CBD Dominant", TraitCategory.CHEMICAL, TraitEffect.MIXED, Rarity.UNCOMMON, "High medicinal value, lower psychoactivity.", 0.8),
    "grow_fast": Trait("grow_fast", "Rapid Rooting", TraitCategory.GROWTH, TraitEffect.POSITIVE, Rarity.UNCOMMON, "Cuttings root 20% faster.", 1.0),
    "grow_tall": Trait("grow_tall", "Sky-High Stretch", TraitCategory.GROWTH, TraitEffect.MIXED, Rarity.COMMON, "Grows very tall, requires vertical space.", 1.5),
    "mkt_purple": Trait("mkt_purple", "Deep Purple", TraitCategory.AESTHETIC, TraitEffect.POSITIVE, Rarity.RARE, "Stunning bag appeal.", 0.5),
    "neg_herm": Trait("neg_herm", "Unstable Sex", TraitCategory.NEGATIVE, TraitEffect.NEGATIVE, Rarity.COMMON, "High risk of hermaphroditism under stress.", 2.0),
    "neg_mold": Trait("neg_mold", "Mold Susceptibility", TraitCategory.NEGATIVE, TraitEffect.NEGATIVE, Rarity.UNCOMMON, "Rot risk in high humidity.", 1.5),
    "aes_frosty": Trait("aes_frosty", "Trichome Blanket", TraitCategory.AESTHETIC, TraitEffect.POSITIVE, Rarity.RARE, "Looks like it was rolled in sugar.", 0.6),
}

# --- 4. GAME LOGIC ENGINES ---

class BreedingEngine:
    @staticmethod
    def blend_stat(val_a: int, val_b: int, parent_stability_avg: int) -> int:
        base = (val_a + val_b) / 2
        variance_range = 25 - (parent_stability_avg * 0.23) 
        variance = random.uniform(-variance_range, variance_range)
        return max(1, min(100, int(base + variance)))

    @staticmethod
    def breed(parent_a: Strain, parent_b: Strain, name_suggestion: str) -> Strain:
        avg_stability = (parent_a.stability + parent_b.stability) / 2
        
        child = Strain(name=name_suggestion)
        child.generation = max(parent_a.generation, parent_b.generation) + 1
        child.parents = f"{parent_a.name} x {parent_b.name}"
        
        child.potency = BreedingEngine.blend_stat(parent_a.potency, parent_b.potency, avg_stability)
        child.yield_amount = BreedingEngine.blend_stat(parent_a.yield_amount, parent_b.yield_amount, avg_stability)
        child.growth_speed = BreedingEngine.blend_stat(parent_a.growth_speed, parent_b.growth_speed, avg_stability)
        child.hardiness = BreedingEngine.blend_stat(parent_a.hardiness, parent_b.hardiness, avg_stability)
        
        decay = random.randint(5, 15)
        child.stability = max(10, int(avg_stability - decay))

        potential_traits = set(parent_a.traits + parent_b.traits)
        child_traits = set()
        
        if potential_traits:
            child_traits.add(random.choice(list(potential_traits)))
        
        for t_id in potential_traits:
            if t_id in child_traits: continue
            trait_data = TRAIT_DB.get(t_id)
            if not trait_data: continue
            chance = 0.4 * trait_data.inheritance_weight
            if trait_data.effect_type == TraitEffect.NEGATIVE: chance *= 1.5 
            if random.random() < chance: child_traits.add(t_id)

        mutation_threshold = (100 - child.stability) / 200
        if random.random() < mutation_threshold:
            available_mutations = [k for k in TRAIT_DB.keys() if k not in child_traits]
            if available_mutations: child_traits.add(random.choice(available_mutations))
        
        final_traits = list(child_traits)
        if len(final_traits) > 4: final_traits = random.sample(final_traits, 4)
        child.traits = final_traits
        
        if final_traits:
            child.revealed_traits.append(random.choice(final_traits))

        return child

class GrowEngine:
    @staticmethod
    def calculate_cost(strain: Strain) -> int:
        days_to_harvest = 100 - strain.growth_speed
        return 500 + (days_to_harvest * 10)

    @staticmethod
    def run_cycle(strain: Strain, current_funds: int):
        cost = GrowEngine.calculate_cost(strain)
        
        if current_funds < cost:
            return {"error": "Insufficient Funds"}

        results = {
            "yield": 0,
            "new_discoveries": [],
            "stability_gain": 0,
            "events": [],
            "cost": cost
        }

        # Yield Calc
        base_yield = strain.yield_amount * 3 
        variance = random.uniform(0.8, 1.2)
        final_yield = int(base_yield * variance)
        results["yield"] = final_yield

        # Discovery Logic
        discovery_chance = 0.3 + (strain.times_grown * 0.1) + (strain.hardiness / 200)
        for t_id in strain.traits:
            if t_id not in strain.revealed_traits:
                if random.random() < discovery_chance:
                    strain.revealed_traits.append(t_id)
                    results["new_discoveries"].append(TRAIT_DB[t_id].name)
        
        # Stability
        if strain.stability < 100:
            gain = random.randint(1, 3)
            strain.stability = min(100, strain.stability + gain)
            results["stability_gain"] = gain

        # Event: Crop Failure Risk
        if strain.hardiness < 30 and random.random() < 0.2:
            loss = int(final_yield * 0.5)
            final_yield -= loss
            results["yield"] = final_yield
            results["events"].append(f"⚠️ Pest infestation! Lost {loss}g.")

        strain.times_grown += 1
        return results

class MarketEngine:
    @staticmethod
    def get_market_price():
        base = random.uniform(3.0, 8.0)
        trend = random.choice(["Stable", "Boom", "Crash"])
        
        if trend == "Boom":
            base *= 1.5
        elif trend == "Crash":
            base *= 0.6
            
        return round(base, 2), trend

# --- 5. SYSTEM FUNCTIONS (SAVE/LOAD) ---

def serialize_game_state():
    """Convert session state to a JSON string."""
    data = {
        "funds": st.session_state["funds"],
        "inventory": st.session_state["inventory"],
        "season": st.session_state["season"],
        "strains": [s.to_dict() for s in st.session_state["strains"]]
    }
    return json.dumps(data, indent=2)

def load_game_state(json_file):
    """Parse JSON and populate session state."""
    try:
        data = json.load(json_file)
        st.session_state["funds"] = data["funds"]
        st.session_state["inventory"] = data["inventory"]
        st.session_state["season"] = data["season"]
        # Reconstruct Strain objects
        st.session_state["strains"] = [Strain.from_dict(s_data) for s_data in data["strains"]]
        return True
    except Exception as e:
        st.error(f"Corrupt save file: {e}")
        return False

# --- 6. UI & STATE MANAGEMENT ---

if "strains" not in st.session_state:
    s1 = Strain(name="Highland Thai", potency=75, yield_amount=40, growth_speed=30, stability=80)
    s1.traits = ["grow_tall", "chem_limonene"]
    s1.revealed_traits = ["grow_tall"]
    
    s2 = Strain(name="Deep Chunk", potency=60, yield_amount=80, growth_speed=40, stability=90)
    s2.traits = ["neg_mold", "aes_frosty"]
    s2.revealed_traits = ["neg_mold"]
    
    st.session_state["strains"] = [s1, s2]
    st.session_state["season"] = 1
    st.session_state["inventory"] = 0 
    st.session_state["funds"] = 5000 

st.set_page_config(page_title="Cultivar Labs", layout="wide")

st.title("🧬 Cultivar Labs: Genetic Engineering")
st.markdown("---")

# Sidebar
with st.sidebar:
    st.header("Lab Status")
    st.metric("Funds", f"${st.session_state['funds']:,}")
    st.metric("Inventory", f"{st.session_state['inventory']}g")
    st.metric("Season", st.session_state['season'])
    
    st.divider()
    
    # SAVE SYSTEM
    st.subheader("System")
    
    # 1. Download (Save)
    json_str = serialize_game_state()
    st.download_button(
        label="💾 Save Game (JSON)",
        data=json_str,
        file_name="cultivar_save.json",
        mime="application/json"
    )
    
    # 2. Upload (Load)
    uploaded_file = st.file_uploader("📂 Load Game", type=["json"])
    if uploaded_file is not None:
        if st.button("Confirm Load"):
            if load_game_state(uploaded_file):
                st.success("Game Loaded!")
                st.rerun()

    st.divider()
    if st.button("Reset Simulation", type="secondary"):
        st.session_state.clear()
        st.rerun()

# Tabs
tab1, tab2, tab3, tab4 = st.tabs(["🌱 Grow Op", "💰 Marketplace", "🧬 Breeding", "📂 Library"])

# --- TAB 1: GROW OP ---
with tab1:
    st.subheader(f"Active Cultivation (Season {st.session_state['season']})")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        grow_choice = st.selectbox("Select Mother Strain", [s.name for s in st.session_state["strains"]])
        target_strain = next(s for s in st.session_state["strains"] if s.name == grow_choice)
        
    with col2:
        est_cost = GrowEngine.calculate_cost(target_strain)
        st.info(f"**Operational Cost:** ${est_cost} | **Est. Time:** {100 - target_strain.growth_speed} days")
        
    st.divider()
    if st.button("🚀 Start Grow Cycle", type="primary", use_container_width=True):
        report = GrowEngine.run_cycle(target_strain, st.session_state["funds"])
        
        if "error" in report:
            st.error(f"Cannot start grow: {report['error']}")
        else:
            st.session_state["funds"] -= report["cost"]
            st.session_state["season"] += 1
            st.session_state["inventory"] += report["yield"]
            
            st.success("Harvest Complete!")
            
            m1, m2, m3 = st.columns(3)
            m1.metric("Yield", f"{report['yield']}g")
            m2.metric("Op Cost", f"-${report['cost']}")
            m3.metric("Net Funds", f"${st.session_state['funds']}")
            
            if report["new_discoveries"]:
                for disc in report["new_discoveries"]:
                    st.warning(f"**New Trait Identified:** {disc}")
            
            if report["events"]:
                for evt in report["events"]:
                    st.error(evt)

# --- TAB 2: MARKETPLACE ---
with tab2:
    st.subheader("Wholesale Market")
    
    price, trend = MarketEngine.get_market_price()
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Current Spot Price", f"${price}/g")
    c2.metric("Market Trend", trend, delta="Hot" if trend=="Boom" else "Cold" if trend=="Crash" else "Normal")
    c3.metric("Inventory Value", f"${int(st.session_state['inventory'] * price):,}")
    
    st.divider()
    
    if st.session_state['inventory'] > 0:
        sc1, sc2 = st.columns([2, 1])
        with sc1:
            sell_amount = st.slider("Amount to Sell (g)", 0, st.session_state['inventory'], st.session_state['inventory'])
        
        with sc2:
            st.write("##") 
            if st.button("Sell Inventory"):
                revenue = int(sell_amount * price)
                st.session_state["funds"] += revenue
                st.session_state["inventory"] -= sell_amount
                st.success(f"Sold {sell_amount}g for ${revenue}!")
                st.rerun()
    else:
        st.info("Inventory is empty. Go to the Grow Op to produce stock.")

# --- TAB 3: BREEDING ---
with tab3:
    st.subheader("Crossbreeding Projects")
    col1, col2 = st.columns(2)
    
    with col1:
        p1_name = st.selectbox("Parent A (Pollen)", [s.name for s in st.session_state["strains"]], key="p1")
    with col2:
        p2_name = st.selectbox("Parent B (Receiver)", [s.name for s in st.session_state["strains"]], key="p2")
        
    new_name = st.text_input("Project Codename", value=f"Strain-{random.randint(100,999)}")
    
    breed_cost = 200
    st.caption(f"Breeding Project Cost: ${breed_cost}")
    
    if st.button("🧬 Initiate Crossbreed"):
        if st.session_state["funds"] < breed_cost:
            st.error("Insufficient Funds for R&D")
        elif p1_name == p2_name:
            st.error("Selfing not implemented in v1.")
        else:
            st.session_state["funds"] -= breed_cost
            parent_a = next(s for s in st.session_state["strains"] if s.name == p1_name)
            parent_b = next(s for s in st.session_state["strains"] if s.name == p2_name)
            
            child = BreedingEngine.breed(parent_a, parent_b, new_name)
            st.session_state["strains"].append(child)
            
            st.success(f"Successfully bred {child.name}!")
            st.info(f"Stats: Potency {child.get_tier(child.potency)} | Stability {child.stability}%")

# --- TAB 4: LIBRARY ---
with tab4:
    st.subheader("Strain Database")
    for strain in st.session_state["strains"]:
        with st.expander(f"{strain.name} (Gen {strain.generation})"):
            sc1, sc2 = st.columns([1, 2])
            with sc1:
                st.write(f"**Potency:** {strain.get_tier(strain.potency)}")
                st.write(f"**Yield:** {strain.get_tier(strain.yield_amount)}")
                st.write(f"**Speed:** {strain.get_growth_tier()}")
                st.progress(strain.stability / 100, text=f"Stability: {strain.stability}%")
            with sc2:
                if not strain.traits:
                    st.write("No distinct traits.")
                else:
                    for t_id in strain.traits:
                        trait_data = TRAIT_DB[t_id]
                        if t_id in strain.revealed_traits:
                            color = "green" if trait_data.effect_type == TraitEffect.POSITIVE else "red" if trait_data.effect_type == TraitEffect.NEGATIVE else "orange"
                            st.markdown(f":{color}[**{trait_data.name}**] - *{trait_data.description}*")
                        else:
                            st.markdown(f"🔒 *Unsequenced Genetic Marker Detected*")
