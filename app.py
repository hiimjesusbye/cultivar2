import streamlit as st
import random
import uuid
import json
from enum import Enum
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Tuple

# --- 1. CONFIGURATION & ENUMS ---

class GeneType(str, Enum):
    STRUCTURE = "Structure"
    AROMA = "Aroma"
    RESISTANCE = "Resistance"

# --- 2. GENETIC DATABASE (MENDELIAN) ---

@dataclass
class GeneDefinition:
    code: str  # e.g., "T"
    name: str  # e.g., "Structure"
    dom_label: str  # Phenotype if Dominant (T_)
    rec_label: str  # Phenotype if Recessive (tt)
    dom_desc: str
    rec_desc: str

GENOME_DB = {
    "structure": GeneDefinition(
        code="T", 
        name="Structure", 
        dom_label="Sativa (Tall)", 
        rec_label="Indica (Short)",
        dom_desc="Tall growth, longer flowering.",
        rec_desc="Short, stout, fast flowering."
    ),
    "aroma": GeneDefinition(
        code="L", 
        name="Terpene Profile", 
        dom_label="Limonene (Citrus)", 
        rec_label="Myrcene (Berry)",
        dom_desc="Sharp, energetic citrus notes.",
        rec_desc="Deep, relaxing berry/earth notes."
    ),
    "resistance": GeneDefinition(
        code="R", 
        name="Hardiness", 
        dom_label="Hardy", 
        rec_label="Sensitive",
        dom_desc="Resistant to mold and pests.",
        rec_desc="Requires strict environment control."
    )
}

UPGRADES_DB = {
    "hydro": {"name": "Hydroponic System", "cost": 2500, "desc": "+20% Yield on all harvests."},
    "hepa":  {"name": "HEPA Filtration", "cost": 1500, "desc": "Reduces pest/mold risk by 50%."},
    "seq":   {"name": "Genetic Sequencer", "cost": 4000, "desc": "Reveals hidden GENOTYPES (e.g. Tt vs TT)."},
    "brand": {"name": "Brand Marketing", "cost": 3000, "desc": "+15% Sale Price on Marketplace."}
}

# --- 3. DATA MODELS ---

@dataclass
class Strain:
    name: str
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    
    # Genotype: {'structure': ('T', 't'), 'aroma': ('l', 'l')}
    genetics: Dict[str, Tuple[str, str]] = field(default_factory=dict)
    
    # Core Stats (Derived from Genetics + Variance)
    potency: int = 50
    yield_amount: int = 50
    
    # Metadata
    generation: int = 1
    parents: str = "Unknown"
    times_grown: int = 0
    inventory_amount: int = 0
    
    # Discovery
    is_sequenced: bool = False # If true, player sees Tt/TT. If false, player only sees Phenotype.

    def initialize_random_genetics(self):
        """Creates a random genotype for starter strains."""
        for key, gene in GENOME_DB.items():
            # Randomly pick two alleles
            a1 = gene.code if random.random() > 0.5 else gene.code.lower()
            a2 = gene.code if random.random() > 0.5 else gene.code.lower()
            # Sort so Dominant always comes first (Tt not tT) for readability
            self.genetics[key] = tuple(sorted((a1, a2)))
        self.recalculate_stats()

    def recalculate_stats(self):
        """
        Stats are now derived from the Genetics.
        Sativa (T_) = Slower grow, Higher Potency potential
        Indica (tt) = Faster grow, Higher Yield potential
        """
        # Base values
        base_pot = 50
        base_yld = 50
        
        # Structure Modifier
        s_alleles = self.genetics.get("structure", ("t", "t"))
        if "T" in s_alleles: # Sativa Dom
            base_pot += 15
            base_yld -= 10
        else: # Indica Rec
            base_pot -= 5
            base_yld += 20
            
        # Variance
        self.potency = max(10, min(100, int(base_pot + random.uniform(-10, 10))))
        self.yield_amount = max(10, min(100, int(base_yld + random.uniform(-10, 10))))

    def get_phenotype_label(self, gene_key: str) -> str:
        """Returns the visible trait name based on alleles."""
        gene_def = GENOME_DB[gene_key]
        alleles = self.genetics[gene_key]
        
        # If Dominant allele is present
        if gene_def.code in alleles:
            return gene_def.dom_label
        return gene_def.rec_label

    def get_growth_speed(self) -> int:
        # Derived dynamically
        # T_ (Sativa) = Slow (30 speed), tt (Indica) = Fast (60 speed)
        if "T" in self.genetics["structure"]:
            return 30
        return 60

    def to_dict(self):
        return asdict(self)

    @staticmethod
    def from_dict(data):
        # Convert list back to tuple for genetics
        s = Strain(**data)
        s.genetics = {k: tuple(v) for k, v in s.genetics.items()}
        return s

# --- 4. GAME LOGIC ENGINES ---

class BreedingEngine:
    @staticmethod
    def breed(parent_a: Strain, parent_b: Strain, name_suggestion: str, upgrades: List[str]) -> Strain:
        child = Strain(name=name_suggestion)
        child.generation = max(parent_a.generation, parent_b.generation) + 1
        child.parents = f"{parent_a.name} x {parent_b.name}"
        
        # PUNNETT SQUARE LOGIC
        for key in GENOME_DB.keys():
            # Pick one random allele from Parent A
            allele_a = random.choice(parent_a.genetics[key])
            # Pick one random allele from Parent B
            allele_b = random.choice(parent_b.genetics[key])
            
            # Combine and Sort (Capital first)
            child.genetics[key] = tuple(sorted((allele_a, allele_b)))
            
        child.recalculate_stats()
        
        # UPGRADE CHECK: Genetic Sequencer
        if "seq" in upgrades:
            child.is_sequenced = True
            
        return child

class GrowEngine:
    @staticmethod
    def calculate_cost(strain: Strain) -> int:
        days = 100 - strain.get_growth_speed()
        return 500 + (days * 12)

    @staticmethod
    def run_cycle(strain: Strain, current_funds: int, upgrades: List[str]):
        cost = GrowEngine.calculate_cost(strain)
        if current_funds < cost:
            return {"error": "Insufficient Funds"}

        results = {
            "yield": 0,
            "events": [],
            "cost": cost
        }

        base_yield = strain.yield_amount * 2.5 
        variance = random.uniform(0.8, 1.2)
        multiplier = 1.2 if "hydro" in upgrades else 1.0
        final_yield = int(base_yield * variance * multiplier)
        results["yield"] = final_yield

        # Hardiness Check
        # If 'sensitive' (rr), high risk. If 'hardy' (R_), low risk.
        is_hardy = "R" in strain.genetics["resistance"]
        base_risk = 0.05 if is_hardy else 0.30
        
        if "hepa" in upgrades: base_risk /= 2
        
        if random.random() < base_risk:
            loss = int(final_yield * 0.4)
            final_yield -= loss
            results["yield"] = final_yield
            results["events"].append(f"⚠️ Environmental Stress! Lost {loss}g. (Genetics: {'Hardy' if is_hardy else 'Sensitive'})")

        strain.times_grown += 1
        return results

class MarketEngine:
    @staticmethod
    def get_market_price(upgrades: List[str]):
        base = random.uniform(3.0, 7.0)
        trend = random.choice(["Stable", "Boom", "Crash"])
        if trend == "Boom": base *= 1.4
        elif trend == "Crash": base *= 0.6
        if "brand" in upgrades: base *= 1.15
        return round(base, 2), trend

    @staticmethod
    def calculate_strain_value(base_price: float, strain: Strain) -> float:
        # Quality Mod: Potency + Aroma Demand
        # Aroma L (Citrus) currently trendy? (Simplified: L is worth slightly more)
        aroma_bonus = 1.1 if "L" in strain.genetics["aroma"] else 1.0
        quality_mod = (strain.potency / 50.0) * aroma_bonus
        return round(base_price * quality_mod, 2)

# --- 5. STATE MANAGEMENT ---

def serialize_game_state():
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

# --- 6. UI ---

if "strains" not in st.session_state:
    # Initial Strains need explicit genetics to demonstrate the system
    
    # S1: Homozygous Dominant (True Breeding Sativa)
    s1 = Strain(name="Highland Gold")
    s1.genetics = {"structure": ("T", "T"), "aroma": ("L", "L"), "resistance": ("r", "r")} # Tall, Citrus, Weak
    s1.recalculate_stats()
    
    # S2: Homozygous Recessive (True Breeding Indica)
    s2 = Strain(name="Deep Chunk")
    s2.genetics = {"structure": ("t", "t"), "aroma": ("l", "l"), "resistance": ("R", "R")} # Short, Berry, Hardy
    s2.recalculate_stats()
    
    st.session_state["strains"] = [s1, s2]
    st.session_state["season"] = 1
    st.session_state["funds"] = 3000
    st.session_state["upgrades"] = []

st.set_page_config(page_title="Cultivar Labs", layout="wide")

st.title("🧬 Cultivar Labs: Mendelian Genetics")
st.markdown("---")

# Sidebar
with st.sidebar:
    st.metric("Funds", f"${st.session_state['funds']:,}")
    st.metric("Season", st.session_state['season'])
    
    if st.session_state["upgrades"]:
        st.caption("Upgrades:")
        for u in st.session_state["upgrades"]:
            st.write(f"✅ {UPGRADES_DB[u]['name']}")

    st.divider()
    json_str = serialize_game_state()
    st.download_button("💾 Save Game", json_str, "cultivar_save.json", "application/json")
    uploaded_file = st.file_uploader("📂 Load Game", type=["json"])
    if uploaded_file is not None and st.button("Confirm Load"):
        if load_game_state(uploaded_file):
            st.rerun()
            
    st.divider()
    if st.button("Reset Simulation"):
        st.session_state.clear()
        st.rerun()

tab1, tab2, tab3, tab4, tab5 = st.tabs(["🌱 Grow Op", "💰 Marketplace", "🏗️ Lab Store", "🧬 Breeding", "📂 Library"])

# GROW OP
with tab1:
    st.subheader(f"Active Cultivation (Season {st.session_state['season']})")
    col1, col2 = st.columns([1, 2])
    with col1:
        grow_choice = st.selectbox("Select Mother Strain", [s.name for s in st.session_state["strains"]])
        target_strain = next(s for s in st.session_state["strains"] if s.name == grow_choice)
    with col2:
        cost = GrowEngine.calculate_cost(target_strain)
        days = 100 - target_strain.get_growth_speed()
        st.info(f"**Cost:** ${cost} | **Duration:** {days} days")
        
    st.divider()
    if st.button("🚀 Start Grow Cycle", type="primary", use_container_width=True):
        report = GrowEngine.run_cycle(target_strain, st.session_state["funds"], st.session_state["upgrades"])
        if "error" in report:
            st.error(report["error"])
        else:
            st.session_state["funds"] -= report["cost"]
            st.session_state["season"] += 1
            target_strain.inventory_amount += report["yield"]
            
            st.success("Harvest Complete!")
            c1, c2, c3 = st.columns(3)
            c1.metric("Yield", f"{report['yield']}g")
            c2.metric("Op Cost", f"-${report['cost']}")
            c3.metric("Funds", f"${st.session_state['funds']}")
            
            for evt in report["events"]: st.error(evt)

# MARKETPLACE
with tab2:
    st.subheader("Wholesale Market")
    base_price, trend = MarketEngine.get_market_price(st.session_state["upgrades"])
    
    c1, c2 = st.columns([1, 2])
    c1.metric("Market Price", f"${base_price}/g", delta=trend)
    
    with c2:
        for strain in st.session_state["strains"]:
            if strain.inventory_amount > 0:
                val = MarketEngine.calculate_strain_value(base_price, strain)
                with st.container(border=True):
                    cols = st.columns([2, 1, 1])
                    cols[0].write(f"**{strain.name}**")
                    cols[1].caption(f"{strain.inventory_amount}g @ ${val}/g")
                    if cols[2].button(f"Sell (${int(strain.inventory_amount * val)})", key=f"sell_{strain.id}"):
                        st.session_state["funds"] += int(strain.inventory_amount * val)
                        strain.inventory_amount = 0
                        st.rerun()

# STORE
with tab3:
    st.subheader("Lab Equipment")
    for uid, data in UPGRADES_DB.items():
        c1, c2 = st.columns([3, 1])
        c1.markdown(f"**{data['name']}** - {data['desc']}")
        if uid in st.session_state["upgrades"]:
            c2.success("Owned")
        else:
            if c2.button(f"Buy (${data['cost']})", key=uid):
                if st.session_state["funds"] >= data['cost']:
                    st.session_state["funds"] -= data['cost']
                    st.session_state["upgrades"].append(uid)
                    st.rerun()

# BREEDING
with tab4:
    st.subheader("Mendelian Crossbreeding")
    st.info("Breeding combines alleles from parents. (e.g., Tt + tt -> 50% Tt, 50% tt)")
    
    c1, c2 = st.columns(2)
    p1 = st.selectbox("Parent A", [s.name for s in st.session_state["strains"]], key="p1")
    p2 = st.selectbox("Parent B", [s.name for s in st.session_state["strains"]], key="p2")
    name = st.text_input("New Name", value=f"Strain-{random.randint(100,999)}")
    
    if st.button("🧬 Pollinate ($200)"):
        if st.session_state["funds"] < 200:
            st.error("No Funds")
        else:
            st.session_state["funds"] -= 200
            pa = next(s for s in st.session_state["strains"] if s.name == p1)
            pb = next(s for s in st.session_state["strains"] if s.name == p2)
            child = BreedingEngine.breed(pa, pb, name, st.session_state["upgrades"])
            st.session_state["strains"].append(child)
            st.success(f"Bred {child.name}!")

# LIBRARY
with tab5:
    st.subheader("Genetic Database")
    has_sequencer = "seq" in st.session_state["upgrades"]
    
    for strain in st.session_state["strains"]:
        with st.expander(f"{strain.name}"):
            c1, c2 = st.columns(2)
            
            # Phenotype (Visible)
            with c1:
                st.caption("Visible Traits (Phenotype)")
                for key in GENOME_DB.keys():
                    label = strain.get_phenotype_label(key)
                    st.markdown(f"**{GENOME_DB[key].name}:** {label}")
                st.progress(strain.potency/100, f"Potency: {strain.potency}")
            
            # Genotype (Hidden)
            with c2:
                st.caption("Genetic Code (Genotype)")
                if has_sequencer or strain.is_sequenced:
                    for key, alleles in strain.genetics.items():
                        code = "".join(alleles) # e.g. "Tt"
                        color = "green" if alleles[0] == alleles[1] else "orange" # Green if Homozygous (Stable)
                        st.markdown(f"**{GENOME_DB[key].code}:** :{color}[`{code}`]")
                    st.caption(":green[Homozygous (Stable)] | :orange[Heterozygous (Unstable)]")
                else:
                    st.warning("🔒 Sequence Required")
                    st.caption("Buy 'Genetic Sequencer' to view alleles.")
