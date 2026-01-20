import streamlit as st
import random
import uuid
import json
from enum import Enum
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Tuple

# --- SAFE IMPORT FOR GRAPHVIZ ---
try:
    import graphviz
    HAS_GRAPHVIZ = True
except ImportError:
    HAS_GRAPHVIZ = False

# --- 1. CONFIGURATION ---

# The 4 Terpene Alleles
TERPENES = {
    "L": "Limonene (Citrus)",
    "M": "Myrcene (Earth)",
    "P": "Pinene (Pine)",
    "C": "Caryophyllene (Spice)"
}

# Flavor Combo Names (Sorted Tuple -> Name)
FLAVOR_COMBOS = {
    ("L", "L"): "Super Lemon Haze",
    ("M", "M"): "Deep Earth",
    ("P", "P"): "Pure Pine",
    ("C", "C"): "Black Pepper",
    ("L", "M"): "Mango Citrus",
    ("L", "P"): "Lemon Sol",
    ("C", "L"): "Spicy Lemon",
    ("M", "P"): "Forest Floor",
    ("C", "M"): "Musky Spice",
    ("C", "P"): "Peppery Pine"
}

UPGRADES_DB = {
    "hydro": {"name": "Hydroponic System", "cost": 2500, "desc": "+20% Yield on all harvests."},
    "hepa":  {"name": "HEPA Filtration", "cost": 1500, "desc": "Reduces pest/mold risk by 50%."},
    "seq":   {"name": "Genetic Sequencer", "cost": 4000, "desc": "Reveals hidden GENOTYPES."},
    "brand": {"name": "Brand Marketing", "cost": 3000, "desc": "+15% Sale Price."}
}

# --- 2. DATA MODELS ---

@dataclass
class Strain:
    name: str
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    
    # Genetics: 
    # structure: (T, t)
    # resistance: (R, r)
    # aroma: (L, P) <- New Codominant Logic
    genetics: Dict[str, Tuple[str, str]] = field(default_factory=dict)
    
    # Core Stats
    potency: int = 50
    yield_amount: int = 50
    
    # Metadata
    generation: int = 1
    parents_text: str = "Unknown"
    parent_ids: List[str] = field(default_factory=list)
    
    times_grown: int = 0
    inventory_amount: int = 0
    is_sequenced: bool = False

    def recalculate_stats(self):
        base_pot = 50
        base_yld = 50
        
        # Structure Modifier (Mendelian T vs t)
        s_alleles = self.genetics.get("structure", ("t", "t"))
        if "T" in s_alleles: 
            base_pot += 15
            base_yld -= 10
        else: 
            base_pot -= 5
            base_yld += 20
        
        # Aroma Modifier (Complexity Boost)
        # Heterozygous aromas (L, P) are more robust than Homozygous (L, L)
        a_alleles = self.genetics.get("aroma", ("L", "L"))
        if a_alleles[0] != a_alleles[1]:
            base_pot += 5 # Entourage effect bonus
            
        self.potency = max(10, min(100, int(base_pot + random.uniform(-10, 10))))
        self.yield_amount = max(10, min(100, int(base_yld + random.uniform(-10, 10))))

    def get_aroma_label(self) -> str:
        """Returns the fancy name for the terpene combo."""
        alleles = sorted(self.genetics["aroma"])
        key = tuple(alleles)
        return FLAVOR_COMBOS.get(key, "Complex Hybrid")

    def get_structure_label(self) -> str:
        if "T" in self.genetics["structure"]: return "Sativa (Tall)"
        return "Indica (Short)"

    def get_resistance_label(self) -> str:
        if "R" in self.genetics["resistance"]: return "Hardy"
        return "Sensitive"

    def get_growth_speed(self) -> int:
        if "T" in self.genetics["structure"]: return 30
        return 60

    def to_dict(self): return asdict(self)
    @staticmethod
    def from_dict(data):
        s = Strain(**data)
        s.genetics = {k: tuple(v) for k, v in s.genetics.items()}
        return s

# --- 3. LOGIC ENGINES ---

class BreedingEngine:
    @staticmethod
    def breed(parent_a: Strain, parent_b: Strain, name_suggestion: str, upgrades: List[str]) -> Strain:
        child = Strain(name=name_suggestion)
        child.generation = max(parent_a.generation, parent_b.generation) + 1
        child.parents_text = f"{parent_a.name} x {parent_b.name}"
        child.parent_ids = [parent_a.id, parent_b.id]
        
        # Mendelian Genes (Structure/Resistance)
        for key in ["structure", "resistance"]:
            a = random.choice(parent_a.genetics[key])
            b = random.choice(parent_b.genetics[key])
            child.genetics[key] = tuple(sorted((a, b)))
            
        # Codominant Gene (Aroma)
        # Logic: Pick 1 from A, 1 from B. No Dominance, they mix.
        terp_a = random.choice(parent_a.genetics["aroma"])
        terp_b = random.choice(parent_b.genetics["aroma"])
        child.genetics["aroma"] = tuple(sorted((terp_a, terp_b)))
            
        child.recalculate_stats()
        if "seq" in upgrades: child.is_sequenced = True
        return child

class GrowEngine:
    @staticmethod
    def calculate_cost(strain: Strain) -> int:
        days = 100 - strain.get_growth_speed()
        return 500 + (days * 12)

    @staticmethod
    def run_cycle(strain: Strain, current_funds: int, upgrades: List[str]):
        cost = GrowEngine.calculate_cost(strain)
        if current_funds < cost: return {"error": "Insufficient Funds"}

        results = {"yield": 0, "events": [], "cost": cost}
        base_yield = strain.yield_amount * 2.5 
        variance = random.uniform(0.8, 1.2)
        multiplier = 1.2 if "hydro" in upgrades else 1.0
        final_yield = int(base_yield * variance * multiplier)
        results["yield"] = final_yield

        is_hardy = "R" in strain.genetics["resistance"]
        base_risk = 0.05 if is_hardy else 0.30
        if "hepa" in upgrades: base_risk /= 2
        
        if random.random() < base_risk:
            loss = int(final_yield * 0.4)
            final_yield -= loss
            results["yield"] = final_yield
            results["events"].append(f"⚠️ Stress Event! Lost {loss}g.")

        strain.times_grown += 1
        return results

class MarketEngine:
    @staticmethod
    def get_market_state(season: int):
        # Deterministic randomness based on season so it stays consistent per reload if needed
        random.seed(season + 999) 
        
        # Pick a "Trending Terpene"
        trending_code = random.choice(["L", "M", "P", "C"])
        trending_name = TERPENES[trending_code].split(" ")[0]
        
        base = random.uniform(3.0, 7.0)
        
        random.seed() # Reset seed
        return base, trending_code, trending_name

    @staticmethod
    def calculate_value(base_price: float, strain: Strain, trending_code: str) -> float:
        # Quality Base
        val = base_price * (strain.potency / 50.0)
        
        # Trend Bonus
        if trending_code in strain.genetics["aroma"]:
            val *= 1.3 # 30% Bonus for matching trend
            
        # Pure Breed Bonus (Homozygous Aroma)
        # If L,L -> Niche Market premium
        if strain.genetics["aroma"][0] == strain.genetics["aroma"][1]:
            val *= 1.1
            
        return round(val, 2)

# --- 4. VISUALIZATION ---

def get_lineage_text(target_strain: Strain, all_strains: List[Strain], depth=0, max_depth=3) -> str:
    indent = "    " * depth
    prefix = "└── " if depth > 0 else ""
    tree_str = f"{indent}{prefix}{target_strain.name} [{target_strain.get_aroma_label()}]\n"
    if depth >= max_depth: return tree_str
    strain_map = {s.id: s for s in all_strains}
    if target_strain.parent_ids:
        for pid in target_strain.parent_ids:
            if pid in strain_map:
                tree_str += get_lineage_text(strain_map[pid], all_strains, depth + 1, max_depth)
            else:
                tree_str += f"{indent}    └── [Unknown]\n"
    return tree_str

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
        st.error(f"Error: {e}")
        return False

# --- UI ---

if "strains" not in st.session_state:
    # Starter 1: Citrus (L) + Pine (P)
    s1 = Strain(name="Lemon Sol")
    s1.genetics = {"structure": ("T", "T"), "resistance": ("r", "r"), "aroma": ("L", "P")} 
    s1.recalculate_stats()
    
    # Starter 2: Earth (M) + Spice (C)
    s2 = Strain(name="Musky Spice")
    s2.genetics = {"structure": ("t", "t"), "resistance": ("R", "R"), "aroma": ("C", "M")} 
    s2.recalculate_stats()
    
    st.session_state["strains"] = [s1, s2]
    st.session_state["season"] = 1
    st.session_state["funds"] = 3000
    st.session_state["upgrades"] = []

st.set_page_config(page_title="Cultivar Labs", layout="wide")
st.title("🧬 Cultivar Labs: Entourage Edition")
st.markdown("---")

# Get Market State for this Season
base_price, trend_code, trend_name = MarketEngine.get_market_state(st.session_state["season"])

with st.sidebar:
    st.metric("Funds", f"${st.session_state['funds']:,}")
    st.metric("Season", st.session_state['season'])
    st.info(f"📢 **Market Craze:**\n{trend_name} Strains")
    
    st.divider()
    st.download_button("💾 Save", serialize_game_state(), "save.json", "application/json")
    uf = st.file_uploader("📂 Load", type=["json"])
    if uf and st.button("Load"):
        if load_game_state(uf): st.rerun()
    if st.button("Reset"):
        st.session_state.clear()
        st.rerun()

t1, t2, t3, t4, t5 = st.tabs(["🌱 Grow", "💰 Market", "🏗️ Store", "🧬 Breed", "📂 Library"])

with t1:
    st.subheader(f"Active Cultivation")
    c1, c2 = st.columns([1, 2])
    with c1:
        choice = st.selectbox("Strain", [s.name for s in st.session_state["strains"]])
        target = next(s for s in st.session_state["strains"] if s.name == choice)
    with c2:
        cost = GrowEngine.calculate_cost(target)
        st.info(f"**Cost:** ${cost} | **Time:** {100 - target.get_growth_speed()} days")
        st.caption(f"Profile: {target.get_aroma_label()}")
        
    st.divider()
    if st.button("🚀 Start Cycle", type="primary", use_container_width=True):
        res = GrowEngine.run_cycle(target, st.session_state["funds"], st.session_state["upgrades"])
        if "error" in res: st.error(res["error"])
        else:
            st.session_state["funds"] -= res["cost"]
            st.session_state["season"] += 1
            target.inventory_amount += res["yield"]
            st.success("Harvest Complete!")
            c1, c2, c3 = st.columns(3)
            c1.metric("Yield", f"{res['yield']}g")
            c2.metric("Funds", f"${st.session_state['funds']}")
            for e in res["events"]: st.error(e)

with t2:
    st.subheader("Marketplace")
    st.markdown(f"The market is paying a premium for **{trend_name}** ({TERPENES[trend_code]}).")
    
    c1, c2 = st.columns([1, 2])
    c1.metric("Base Price", f"${round(base_price,2)}/g")
    
    with c2:
        for s in st.session_state["strains"]:
            if s.inventory_amount > 0:
                val = MarketEngine.calculate_value(base_price, s, trend_code)
                is_trending = trend_code in s.genetics["aroma"]
                
                with st.container(border=True):
                    cols = st.columns([2, 1, 1])
                    title = f"**{s.name}**"
                    if is_trending: title += " 🔥"
                    cols[0].markdown(title)
                    cols[0].caption(f"{s.get_aroma_label()}")
                    
                    cols[1].caption(f"{s.inventory_amount}g @ ${val}/g")
                    if cols[2].button(f"Sell (${int(s.inventory_amount * val)})", key=f"sell_{s.id}"):
                        st.session_state["funds"] += int(s.inventory_amount * val)
                        s.inventory_amount = 0
                        st.rerun()

with t3:
    st.subheader("Upgrades")
    for uid, data in UPGRADES_DB.items():
        c1, c2 = st.columns([3, 1])
        c1.markdown(f"**{data['name']}** - {data['desc']}")
        if uid in st.session_state["upgrades"]: c2.success("Owned")
        else:
            if c2.button(f"Buy (${data['cost']})", key=uid):
                if st.session_state["funds"] >= data['cost']:
                    st.session_state["funds"] -= data['cost']
                    st.session_state["upgrades"].append(uid)
                    st.rerun()

with t4:
    st.subheader("Breeding Lab")
    c1, c2 = st.columns(2)
    p1 = st.selectbox("Parent A", [s.name for s in st.session_state["strains"]], key="p1")
    p2 = st.selectbox("Parent B", [s.name for s in st.session_state["strains"]], key="p2")
    name = st.text_input("Name", value=f"Strain-{random.randint(100,999)}")
    if st.button("🧬 Cross ($200)"):
        if st.session_state["funds"] < 200: st.error("No Funds")
        else:
            st.session_state["funds"] -= 200
            pa = next(s for s in st.session_state["strains"] if s.name == p1)
            pb = next(s for s in st.session_state["strains"] if s.name == p2)
            child = BreedingEngine.breed(pa, pb, name, st.session_state["upgrades"])
            st.session_state["strains"].append(child)
            st.success(f"Bred {child.name}!")

with t5:
    st.subheader("Strain Library")
    all_names = [s.name for s in st.session_state["strains"]]
    sel_name = st.selectbox("Select Strain", all_names)
    sel = next(s for s in st.session_state["strains"] if s.name == sel_name)
    
    c1, c2 = st.columns(2)
    with c1:
        st.write(f"**Profile:** {sel.get_aroma_label()}")
        st.write(f"**Structure:** {sel.get_structure_label()}")
        st.write(f"**Resistance:** {sel.get_resistance_label()}")
        
        st.caption("Genetics:")
        if "seq" in st.session_state["upgrades"] or sel.is_sequenced:
             st.write(f"- Aroma: `{sel.genetics['aroma']}`")
             st.write(f"- Structure: `{sel.genetics['structure']}`")
             st.write(f"- Resistance: `{sel.genetics['resistance']}`")
        else:
            st.write("🔒 Sequence Hidden")

    with c2:
        st.caption("Ancestry Log")
        st.code(get_lineage_text(sel, st.session_state["strains"]), language="text")
