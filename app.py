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
    inheritance_weight: float = 1.0  # Higher = more likely to pass down

@dataclass
class Strain:
    name: str
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    
    # Core Stats (0-100 Integers, displayed as Tiers)
    potency: int = 50
    yield_amount: int = 50
    growth_speed: int = 50  # Higher = Faster
    stability: int = 50     # Higher = Less mutation/variance
    hardiness: int = 50
    
    # Genetics
    traits: List[str] = field(default_factory=list) # List of Trait IDs
    revealed_traits: List[str] = field(default_factory=list) # Subset of traits player can see
    generation: int = 1
    parents: str = "Unknown"

    def get_tier(self, value: int) -> str:
        """Converts raw int to descriptive tier."""
        if value < 20: return "Very Low"
        if value < 40: return "Low"
        if value < 60: return "Average"
        if value < 80: return "High"
        return "Exceptional"

    def get_growth_tier(self) -> str:
        """Special tier text for growth speed."""
        if self.growth_speed < 30: return "Sluggish"
        if self.growth_speed < 60: return "Standard"
        return "Vigorous"

# --- 3. TRAIT DATABASE ---
# A small sample of the full database for v1.0
TRAIT_DB = {
    "chem_limonene": Trait("chem_limonene", "Heavy Limonene", TraitCategory.CHEMICAL, TraitEffect.POSITIVE, Rarity.COMMON, "Strong citrus aroma.", 1.2),
    "chem_cbd_rich": Trait("chem_cbd_rich", "CBD Dominant", TraitCategory.CHEMICAL, TraitEffect.MIXED, Rarity.UNCOMMON, "High medicinal value, lower psychoactivity.", 0.8),
    "grow_fast": Trait("grow_fast", "Rapid Rooting", TraitCategory.GROWTH, TraitEffect.POSITIVE, Rarity.UNCOMMON, "Cuttings root 20% faster.", 1.0),
    "grow_tall": Trait("grow_tall", "Sky-High Stretch", TraitCategory.GROWTH, TraitEffect.MIXED, Rarity.COMMON, "Grows very tall, requires vertical space.", 1.5),
    "mkt_purple": Trait("mkt_purple", "Deep Purple", TraitCategory.AESTHETIC, TraitEffect.POSITIVE, Rarity.RARE, "Stunning bag appeal.", 0.5),
    "neg_herm": Trait("neg_herm", "Unstable Sex", TraitCategory.NEGATIVE, TraitEffect.NEGATIVE, Rarity.COMMON, "High risk of hermaphroditism under stress.", 2.0), # High weight!
    "neg_mold": Trait("neg_mold", "Mold Susceptibility", TraitCategory.NEGATIVE, TraitEffect.NEGATIVE, Rarity.UNCOMMON, "Rot risk in high humidity.", 1.5),
    "aes_frosty": Trait("aes_frosty", "Trichome Blanket", TraitCategory.AESTHETIC, TraitEffect.POSITIVE, Rarity.RARE, "Looks like it was rolled in sugar.", 0.6),
}

# --- 4. BREEDING ENGINE ---

class BreedingEngine:
    @staticmethod
    def blend_stat(val_a: int, val_b: int, parent_stability_avg: int) -> int:
        """
        Blends stats with variance based on parent stability.
        Lower stability = Higher variance (risk/reward).
        """
        base = (val_a + val_b) / 2
        
        # Stability of 100 = +/- 2 variance. Stability of 0 = +/- 25 variance.
        variance_range = 25 - (parent_stability_avg * 0.23) 
        variance = random.uniform(-variance_range, variance_range)
        
        return max(1, min(100, int(base + variance)))

    @staticmethod
    def breed(parent_a: Strain, parent_b: Strain, name_suggestion: str) -> Strain:
        avg_stability = (parent_a.stability + parent_b.stability) / 2
        
        # 1. Create Child Shell
        child = Strain(name=name_suggestion)
        child.generation = max(parent_a.generation, parent_b.generation) + 1
        child.parents = f"{parent_a.name} x {parent_b.name}"
        
        # 2. Blend Core Stats
        child.potency = BreedingEngine.blend_stat(parent_a.potency, parent_b.potency, avg_stability)
        child.yield_amount = BreedingEngine.blend_stat(parent_a.yield_amount, parent_b.yield_amount, avg_stability)
        child.growth_speed = BreedingEngine.blend_stat(parent_a.growth_speed, parent_b.growth_speed, avg_stability)
        child.hardiness = BreedingEngine.blend_stat(parent_a.hardiness, parent_b.hardiness, avg_stability)
        
        # 3. Stability Decay (Entropy)
        # Stability naturally degrades by 5-15 points per gen unless stabilized
        decay = random.randint(5, 15)
        child.stability = max(10, int(avg_stability - decay))

        # 4. Trait Inheritance Logic
        potential_traits = set(parent_a.traits + parent_b.traits)
        child_traits = set()
        
        # Rule: Guaranteed Inheritance (Pick 1 random parent trait)
        if potential_traits:
            guaranteed = random.choice(list(potential_traits))
            child_traits.add(guaranteed)
        
        # Rule: Weighted Rolls for others
        for t_id in potential_traits:
            if t_id in child_traits: continue # Already added
            
            trait_data = TRAIT_DB.get(t_id)
            if not trait_data: continue

            # Calculate chance
            # Base 40% chance + Weight modifier
            chance = 0.4 * trait_data.inheritance_weight
            
            # Rule: Negative Bias (Negative traits stickier)
            if trait_data.effect_type == TraitEffect.NEGATIVE:
                chance *= 1.5 
            
            if random.random() < chance:
                child_traits.add(t_id)

        # Rule: Mutation (Low stability = high mutation chance)
        mutation_threshold = (100 - child.stability) / 200  # 0.5 (50%) at 0 stab, 0% at 100 stab
        if random.random() < mutation_threshold:
            # Pick a random trait from DB not currently on child
            available_mutations = [k for k in TRAIT_DB.keys() if k not in child_traits]
            if available_mutations:
                mutation = random.choice(available_mutations)
                child_traits.add(mutation)
                # Flavor: Mutations are initially hidden
        
        # Enforce max 4 traits
        final_traits = list(child_traits)
        if len(final_traits) > 4:
            final_traits = random.sample(final_traits, 4)
            
        child.traits = final_traits
        
        # Logic: New strains have traits hidden by default, unless they came from parents clearly
        # For gameplay, let's reveal 1 trait immediately
        if final_traits:
            child.revealed_traits.append(random.choice(final_traits))

        return child

# --- 5. UI & STATE MANAGEMENT ---

if "strains" not in st.session_state:
    # Initialize with 2 Starter Strains
    s1 = Strain(name="Highland Thai", potency=75, yield_amount=40, growth_speed=30, stability=80)
    s1.traits = ["grow_tall", "chem_limonene"]
    s1.revealed_traits = ["grow_tall"]
    
    s2 = Strain(name="Deep Chunk", potency=60, yield_amount=80, growth_speed=40, stability=90)
    s2.traits = ["neg_mold", "aes_frosty"]
    s2.revealed_traits = ["neg_mold"] # Player knows it molds, doesn't know it's frosty yet
    
    st.session_state["strains"] = [s1, s2]

st.set_page_config(page_title="Cultivar Labs", layout="wide")

st.title("🧬 Cultivar Labs: Genetic Engineering")
st.markdown("---")

# sidebar
with st.sidebar:
    st.header("Lab Storage")
    st.write(f"Strains in Vault: {len(st.session_state['strains'])}")
    if st.button("Reset Simulation"):
        del st.session_state["strains"]
        st.rerun()

# Tabs
tab1, tab2 = st.tabs(["🧬 Breeding Chamber", "📂 Strain Library"])

with tab1:
    st.subheader("New Project")
    col1, col2 = st.columns(2)
    
    with col1:
        p1_name = st.selectbox("Select Parent A (Pollen)", [s.name for s in st.session_state["strains"]], key="p1")
    with col2:
        p2_name = st.selectbox("Select Parent B (Receiver)", [s.name for s in st.session_state["strains"]], key="p2")
        
    new_name = st.text_input("Project Codename", value=f"Strain-{random.randint(100,999)}")
    
    if st.button("🧬 Initiate Crossbreed"):
        if p1_name == p2_name:
            st.error("Selfing increases mutation risks significantly! (Not implemented in v1)")
        else:
            # Fetch objects
            parent_a = next(s for s in st.session_state["strains"] if s.name == p1_name)
            parent_b = next(s for s in st.session_state["strains"] if s.name == p2_name)
            
            child = BreedingEngine.breed(parent_a, parent_b, new_name)
            st.session_state["strains"].append(child)
            
            st.success(f"Successfully bred {child.name}!")
            
            # Display Result Card
            st.info("🔬 Lab Results Initialized")
            c1, c2, c3 = st.columns(3)
            c1.metric("Est. Potency", child.get_tier(child.potency))
            c2.metric("Growth Vigor", child.get_growth_tier())
            c3.metric("Genetic Stability", f"{child.stability}/100")
            
            st.write("**Detected Traits:**")
            if not child.revealed_traits:
                st.write("*No traits identified yet. Grow out to reveal.*")
            else:
                for t_id in child.revealed_traits:
                    t = TRAIT_DB[t_id]
                    st.markdown(f"- **{t.name}**: {t.description}")

with tab2:
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
            
            with sc2:
                st.caption("Genetic Profile")
                
                # Traits Logic
                if not strain.traits:
                    st.write("No distinct traits.")
                else:
                    for t_id in strain.traits:
                        trait_data = TRAIT_DB[t_id]
                        # Visiblity Check
                        if t_id in strain.revealed_traits:
                            color = "green" if trait_data.effect_type == TraitEffect.POSITIVE else "red" if trait_data.effect_type == TraitEffect.NEGATIVE else "orange"
                            st.markdown(f":{color}[**{trait_data.name}**] - *{trait_data.description}*")
                        else:
                            st.markdown(f"🔒 *Unsequenced Genetic Marker Detected*")
                
                st.caption(f"Lineage: {strain.parents}")
