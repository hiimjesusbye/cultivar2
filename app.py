import streamlit as st
import random
import uuid
from enum import Enum
from dataclasses import dataclass, field
from typing import List, Dict, Optional

# --- 1. CONFIGURATION & ENUMS ---

class TraitCategory(Enum):
    CHEMICAL = "Chemical Profile"
    GROWTH = "Growth Behavior"
    MARKET = "Market/Consumer"
    AESTHETIC = "Aesthetic/Flavor"
    NEGATIVE = "Negative/Quirk"

class TraitEffect(Enum):
    POSITIVE = "Positive"
    NEGATIVE = "Negative"
    MIXED = "Mixed"

class Rarity(Enum):
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
    times_grown: int = 0  # New: Tracks experience with strain

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
        
        # New strains start with 1 random trait revealed
        if final_traits:
            child.revealed_traits.append(random.choice(final_traits))

        return child

class GrowEngine:
    @staticmethod
    def run_cycle(strain: Strain):
        """
        Simulates one season of growing a specific strain.
        Returns a result dictionary.
        """
        results = {
            "yield": 0,
            "new_discoveries": [],
            "stability_gain": 0,
            "events": []
        }

        # 1. Calculate Yield (Based on stats + randomness)
        base_yield = strain.yield_amount * 2  # Arbitrary "grams per plant" multiplier
        variance = random.uniform(0.8, 1.2)
        final_yield = int(base_yield * variance)
        results["yield"] = final_yield

        # 2. Trait Discovery Logic
        # Chance to reveal hidden traits increases with Hardiness and Times Grown
        discovery_chance = 0.3 + (strain.times_grown * 0.1) + (strain.hardiness / 200)
        
        for t_id in strain.traits:
            if t_id not in strain.revealed_traits:
                if random.random() < discovery_chance:
                    strain.revealed_traits.append(t_id)
                    trait_name = TRAIT_DB[t_id].name
                    results["new_discoveries"].append(trait_name)
        
        # 3. Stabilization Mechanic
        # Successfully growing a strain helps dial it in, improving stability slightly
        if strain.stability < 100:
            gain = random.randint(1, 3)
            strain.stability = min(100, strain.stability + gain)
            results["stability_gain"] = gain

        # 4. Hardiness Check (Event)
        # Low hardiness strains might suffer issues
        if strain.hardiness < 30 and random.random() < 0.3:
            loss = int(final_yield * 0.4)
            final_yield -= loss
            results["yield"] = final_yield
            results["events"].append(f"⚠️ Crop struggled with environmental stress. Lost {loss}g.")

        strain.times_grown += 1
        return results

# --- 5. UI & STATE MANAGEMENT ---

if "strains" not in st.session_state:
    s1 = Strain(name="Highland Thai", potency=75, yield_amount=40, growth_speed=30, stability=80)
    s1.traits = ["grow_tall", "chem_limonene"]
    s1.revealed_traits = ["grow_tall"]
    
    s2 = Strain(name="Deep Chunk", potency=60, yield_amount=80, growth_speed=40, stability=90)
    s2.traits = ["neg_mold", "aes_frosty"]
    s2.revealed_traits = ["neg_mold"]
    
    st.session_state["strains"] = [s1, s2]
    st.session_state["season"] = 1
    st.session_state["inventory"] = 0 # Total Yield

st.set_page_config(page_title="Cultivar Labs", layout="wide")

st.title("🧬 Cultivar Labs: Genetic Engineering")
st.markdown("---")

# Sidebar
with st.sidebar:
    st.metric("Current Season", f"Season {st.session_state['season']}")
    st.metric("Total Harvest", f"{st.session_state['inventory']}g")
    
    st.divider()
    st.write(f"Strains in Vault: {len(st.session_state['strains'])}")
    if st.button("Reset Simulation"):
        st.session_state.clear()
        st.rerun()

# Tabs
tab1, tab2, tab3 = st.tabs(["🌱 Grow Op", "🧬 Breeding Chamber", "📂 Strain Library"])

# --- TAB 1: GROW OP ---
with tab1:
    st.subheader(f"Season {st.session_state['season']} - Active Cultivation")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.info("Select a strain to fill the grow room for this season.")
        grow_choice = st.selectbox("Select Mother Strain", [s.name for s in st.session_state["strains"]])
        
    with col2:
        if st.button("🚀 Start Grow Cycle", type="primary"):
            # Find the object
            target_strain = next(s for s in st.session_state["strains"] if s.name == grow_choice)
            
            # Run Engine
            report = GrowEngine.run_cycle(target_strain)
            
            # Update Global State
            st.session_state["season"] += 1
            st.session_state["inventory"] += report["yield"]
            
            # Render Report
            st.success("Harvest Complete!")
            
            # Metrics
            m1, m2, m3 = st.columns(3)
            m1.metric("Yield", f"{report['yield']}g")
            m2.metric("Stability", f"+{report['stability_gain']}", delta_color="normal")
            m3.metric("Experience", f"Run #{target_strain.times_grown}")
            
            # Events / Discovery
            if report["new_discoveries"]:
                st.markdown("### 🧬 Genetic Breakthrough!")
                for disc in report["new_discoveries"]:
                    st.warning(f"**New Trait Identified:** {disc}")
            
            if report["events"]:
                for evt in report["events"]:
                    st.error(evt)
                    
            if not report["new_discoveries"] and not report["events"]:
                st.caption("A standard, uneventful grow cycle. Data collected.")

# --- TAB 2: BREEDING ---
with tab2:
    st.subheader("Crossbreeding Projects")
    col1, col2 = st.columns(2)
    
    with col1:
        p1_name = st.selectbox("Parent A (Pollen)", [s.name for s in st.session_state["strains"]], key="p1")
    with col2:
        p2_name = st.selectbox("Parent B (Receiver)", [s.name for s in st.session_state["strains"]], key="p2")
        
    new_name = st.text_input("Project Codename", value=f"Strain-{random.randint(100,999)}")
    
    if st.button("🧬 Initiate Crossbreed"):
        if p1_name == p2_name:
            st.error("Selfing not implemented in v1.")
        else:
            parent_a = next(s for s in st.session_state["strains"] if s.name == p1_name)
            parent_b = next(s for s in st.session_state["strains"] if s.name == p2_name)
            
            child = BreedingEngine.breed(parent_a, parent_b, new_name)
            st.session_state["strains"].append(child)
            
            st.success(f"Successfully bred {child.name}!")
            st.info(f"Stats: Potency {child.get_tier(child.potency)} | Stability {child.stability}%")

# --- TAB 3: LIBRARY ---
with tab3:
    st.subheader("Strain Database")
    
    for strain in st.session_state["strains"]:
        with st.expander(f"{strain.name} (Gen {strain.generation})"):
            sc1, sc2 = st.columns([1, 2])
            
            with sc1:
                st.caption("Morphology")
                st.write(f"**Potency:** {strain.get_tier(strain.potency)}")
                st.write(f"**Yield:** {strain.get_tier(strain.yield_amount)}")
                st.write(f"**Hardiness:** {strain.get_tier(strain.hardiness)}")
                st.progress(strain.stability / 100, text=f"Stability: {strain.stability}%")
                st.caption(f"Times Grown: {strain.times_grown}")
            
            with sc2:
                st.caption("Genetic Profile")
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
                
                st.caption(f"Lineage: {strain.parents}")
