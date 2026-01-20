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
    
    # Inventory Tracking (New in v1.5)
    inventory_amount: int = 0

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

# --- 3. DATABASES ---

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

UPGRADES_DB = {
    "hydro": {"name": "Hydroponic System", "cost": 2500, "desc": "+20% Yield on all harvests."},
    "hepa":  {"name": "HEPA Filtration", "cost": 1500, "desc": "Reduces pest/mold risk by 50%."},
    "seq":   {"name": "Genetic Sequencer", "cost": 5000, "desc": "New breeds start with 2 traits revealed."},
    "brand": {"name": "Brand Marketing", "cost": 3000, "desc": "+15% Sale Price on Marketplace."}
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
    def breed(parent_a: Strain, parent_b: Strain, name_suggestion: str, upgrades: List[str]) -> Strain:
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
        
        reveal_count = 2 if "seq" in upgrades else 1
        if final_traits:
            k = min(len(final_traits), reveal_count)
            child.revealed_traits.extend(random.sample(final_traits, k))

        return child

class GrowEngine:
    @staticmethod
    def calculate_cost(strain: Strain) -> int:
        days_to_harvest = 100 - strain.growth_speed
        # Rebalance: Higher base cost
        return 600 + (days_to_harvest * 12)

    @staticmethod
    def run_cycle(strain: Strain, current_funds: int, upgrades: List[str]):
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

        # Yield Calc: Slightly lower multiplier to tighten margins
        base_yield = strain.yield_amount * 2.5 
        variance = random.uniform(0.8, 1.2)
        
        multiplier = 1.2 if "hydro" in upgrades else 1.0
        final_yield = int(base_yield * variance * multiplier)
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
        risk_threshold = 0.1 if "hepa" in upgrades else 0.2
        if strain.hardiness < 30 and random.random() < risk_threshold:
            loss = int(final_yield * 0.5)
            final_yield -= loss
            results["yield"] = final_yield
            results["events"].append(f"⚠️ Pest infestation! Lost {loss}g.")

        strain.times_grown += 1
        return results

class MarketEngine:
    @staticmethod
    def get_market_price(upgrades: List[str]):
        base = random.uniform(2.5, 7.0) # Lower floor
        trend = random.choice(["Stable", "Boom", "Crash"])
        
        if trend == "Boom": base *= 1.4
        elif trend == "Crash": base *= 0.6
        
        if "brand" in upgrades: base *= 1.15
            
        return round(base, 2), trend

    @staticmethod
    def calculate_strain_value(base_price: float, strain: Strain) -> float:
        # QUALITY MODIFIER: Potency affects price
        # 50 potency = 1.0x (Market Price)
        # 80 potency = 1.6x (Premium)
        # 30 potency = 0.6x (Mids)
        quality_mod = strain.potency / 50.0
        return round(base_price * quality_mod, 2)

# --- 5. SYSTEM FUNCTIONS ---

def serialize_game_state():
    # v1.5 Save Format
    data = {
        "funds": st.session_state["funds"],
        "season": st.session_state["season"],
        "upgrades": st.session_state["upgrades"],
        "strains": [s.to_dict() for s in st.session_state["strains"]]
    }
    return json.dumps(data, indent=2)

def load_game_state(json_file):
    try:
        data = json.load(json_file)
        st.session_state["funds"] = data["funds"]
        st.session_state["season"] = data["season"]
        st.session_state["upgrades"] = data.get("upgrades", [])
        st.session_state["strains"] = [Strain.from_dict(s_data) for s_data in data["strains"]]
        return True
    except Exception as e:
        st.error(f"Corrupt save file: {e}")
        return False

# --- 6. UI & STATE MANAGEMENT ---

if "strains" not in st.session_state:
    s1 = Strain(name="Highland Thai", potency=78, yield_amount=35, growth_speed=25, stability=80)
    s1.traits = ["grow_tall", "chem_limonene"]
    s1.revealed_traits = ["grow_tall"]
    
    s2 = Strain(name="Deep Chunk", potency=55, yield_amount=85, growth_speed=45, stability=90)
    s2.traits = ["neg_mold", "aes_frosty"]
    s2.revealed_traits = ["neg_mold"]
    
    st.session_state["strains"] = [s1, s2]
    st.session_state["season"] = 1
    st.session_state["funds"] = 2000 # HARD START
    st.session_state["upgrades"] = []

st.set_page_config(page_title="Cultivar Labs", layout="wide")

st.title("🧬 Cultivar Labs: Genetic Engineering")
st.markdown("---")

# BANKRUPTCY CHECK
if st.session_state["funds"] < 0:
    st.error("🛑 INSOLVENCY DETECTED. The lab has been seized by creditors.")
    if st.button("Declare Bankruptcy (Restart)"):
        st.session_state.clear()
        st.rerun()
    st.stop()

# Sidebar
with st.sidebar:
    st.header("Lab Status")
    st.metric("Funds", f"${st.session_state['funds']:,}")
    st.metric("Season", st.session_state['season'])
    
    if st.session_state["upgrades"]:
        st.caption("Active Upgrades:")
        for u in st.session_state["upgrades"]:
            st.write(f"✅ {UPGRADES_DB[u]['name']}")

    st.divider()
    
    # SYSTEM
    st.subheader("System")
    json_str = serialize_game_state()
    st.download_button("💾 Save Game", json_str, "cultivar_save.json", "application/json")
    
    uploaded_file = st.file_uploader("📂 Load Game", type=["json"])
    if uploaded_file is not None and st.button("Confirm Load"):
        if load_game_state(uploaded_file):
            st.success("Loaded!")
            st.rerun()

    st.divider()
    if st.button("Reset Simulation", type="secondary"):
        st.session_state.clear()
        st.rerun()

# Tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs(["🌱 Grow Op", "💰 Marketplace", "🏗️ Lab Store", "🧬 Breeding", "📂 Library"])

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
        report = GrowEngine.run_cycle(target_strain, st.session_state["funds"], st.session_state["upgrades"])
        
        if "error" in report:
            st.error(f"Cannot start grow: {report['error']}")
        else:
            st.session_state["funds"] -= report["cost"]
            st.session_state["season"] += 1
            
            # Add to strain inventory
            target_strain.inventory_amount += report["yield"]
            
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
    
    base_price, trend = MarketEngine.get_market_price(st.session_state["upgrades"])
    
    col_tick, col_sell = st.columns([1, 2])
    
    with col_tick:
        st.metric("Base Market Index", f"${base_price}/g")
        st.metric("Trend", trend, delta="Hot" if trend=="Boom" else "Cold" if trend=="Crash" else "Normal")
    
    with col_sell:
        st.write("### Your Inventory")
        # List all strains with inventory
        has_stock = False
        for strain in st.session_state["strains"]:
            if strain.inventory_amount > 0:
                has_stock = True
                # Quality Calculation
                final_price = MarketEngine.calculate_strain_value(base_price, strain)
                quality_tier = "Premium" if strain.potency > 70 else "Mids" if strain.potency > 40 else "Low Grade"
                
                with st.container(border=True):
                    c1, c2, c3 = st.columns([2, 2, 1])
                    c1.write(f"**{strain.name}**")
                    c1.caption(f"{quality_tier} (Potency: {strain.potency})")
                    
                    c2.metric("Stock", f"{strain.inventory_amount}g", delta=f"${final_price}/g")
                    
                    if c3.button(f"Sell All (${int(strain.inventory_amount * final_price)})", key=f"sell_{strain.id}"):
                        revenue = int(strain.inventory_amount * final_price)
                        st.session_state["funds"] += revenue
                        strain.inventory_amount = 0
                        st.success(f"Sold batch for ${revenue}!")
                        st.rerun()
        
        if not has_stock:
            st.info("Inventory is empty. Go to the Grow Op.")

# --- TAB 3: LAB STORE ---
with tab3:
    st.subheader("Facility Upgrades")
    for uid, data in UPGRADES_DB.items():
        col_desc, col_buy = st.columns([3, 1])
        with col_desc:
            st.markdown(f"**{data['name']}**")
            st.write(data['desc'])
        with col_buy:
            if uid in st.session_state["upgrades"]:
                st.success("Owned")
            else:
                if st.button(f"Buy (${data['cost']})", key=f"buy_{uid}"):
                    if st.session_state["funds"] >= data['cost']:
                        st.session_state["funds"] -= data['cost']
                        st.session_state["upgrades"].append(uid)
                        st.rerun()
                    else:
                        st.error("Insufficient Funds")
        st.divider()

# --- TAB 4: BREEDING ---
with tab4:
    st.subheader("Crossbreeding Projects")
    col1, col2 = st.columns(2)
    with col1:
        p1_name = st.selectbox("Parent A (Pollen)", [s.name for s in st.session_state["strains"]], key="p1")
    with col2:
        p2_name = st.selectbox("Parent B (Receiver)", [s.name for s in st.session_state["strains"]], key="p2")
        
    new_name = st.text_input("Project Codename", value=f"Strain-{random.randint(100,999)}")
    breed_cost = 200
    
    if st.button("🧬 Initiate Crossbreed ($200)"):
        if st.session_state["funds"] < breed_cost:
            st.error("Insufficient Funds")
        elif p1_name == p2_name:
            st.error("Selfing not implemented in v1.")
        else:
            st.session_state["funds"] -= breed_cost
            parent_a = next(s for s in st.session_state["strains"] if s.name == p1_name)
            parent_b = next(s for s in st.session_state["strains"] if s.name == p2_name)
            child = BreedingEngine.breed(parent_a, parent_b, new_name, st.session_state["upgrades"])
            st.session_state["strains"].append(child)
            st.success(f"Bred {child.name}!")

# --- TAB 5: LIBRARY ---
with tab5:
    st.subheader("Strain Database")
    for strain in st.session_state["strains"]:
        with st.expander(f"{strain.name} (Gen {strain.generation})"):
            sc1, sc2 = st.columns([1, 2])
            with sc1:
                st.write(f"**Potency:** {strain.get_tier(strain.potency)}")
                st.write(f"**Yield:** {strain.get_tier(strain.yield_amount)}")
                st.write(f"**Speed:** {strain.get_growth_tier()}")
                st.progress(strain.stability / 100, text=f"Stability: {strain.stability}%")
                st.caption(f"In Stock: {strain.inventory_amount}g")
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
