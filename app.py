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

# --- 1. CONFIGURATION & ENUMS ---

class GeneType(str, Enum):
    STRUCTURE = "Structure"
    AROMA = "Aroma"
    RESISTANCE = "Resistance"

# --- 2. GENETIC DATABASE ---

@dataclass
class GeneDefinition:
    code: str
    name: str
    dom_label: str
    rec_label: str
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
    
    # Genotype
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
        
        # Structure Modifier
        s_alleles = self.genetics.get("structure", ("t", "t"))
        if "T" in s_alleles: 
            base_pot += 15
            base_yld -= 10
        else: 
            base_pot -= 5
            base_yld += 20
            
        self.potency = max(10, min(100, int(base_pot + random.uniform(-10, 10))))
        self.yield_amount = max(10, min(100, int(base_yld + random.uniform(-10, 10))))

    def get_phenotype_label(self, gene_key: str) -> str:
        gene_def = GENOME_DB[gene_key]
        alleles = self.genetics[gene_key]
        if gene_def.code in alleles:
            return gene_def.dom_label
        return gene_def.rec_label

    def get_growth_speed(self) -> int:
        if "T" in self.genetics["structure"]: return 30
        return 60

    def to_dict(self):
        return asdict(self)

    @staticmethod
    def from_dict(data):
        s = Strain(**data)
        s.genetics = {k: tuple(v) for k, v in s.genetics.items()}
        return s

# --- 4. GAME LOGIC ENGINES ---

class BreedingEngine:
    @staticmethod
    def breed(parent_a: Strain, parent_b: Strain, name_suggestion: str, upgrades: List[str]) -> Strain:
        child = Strain(name=name_suggestion)
        child.generation = max(parent_a.generation, parent_b.generation) + 1
        
        # Lineage Tracking
        child.parents_text = f"{parent_a.name} x {parent_b.name}"
        child.parent_ids = [parent_a.id, parent_b.id]
        
        # Genetics
        for key in GENOME_DB.keys():
            allele_a = random.choice(parent_a.genetics[key])
            allele_b = random.choice(parent_b.genetics[key])
            child.genetics[key] = tuple(sorted((allele_a, allele_b)))
            
        child.recalculate_stats()
        
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
    def get_market_price(upgrades: List[str]):
        base = random.uniform(3.0, 7.0)
        trend = random.choice(["Stable", "Boom", "Crash"])
        if trend == "Boom": base *= 1.4
        elif trend == "Crash": base *= 0.6
        if "brand" in upgrades: base *= 1.15
        return round(base, 2), trend

    @staticmethod
    def calculate_strain_value(base_price: float, strain: Strain) -> float:
        aroma_bonus = 1.1 if "L" in strain.genetics["aroma"] else 1.0
        quality_mod = (strain.potency / 50.0) * aroma_bonus
        return round(base_price * quality_mod, 2)

# --- 5. VISUALIZATION ENGINE ---

def render_lineage(target_strain: Strain, all_strains: List[Strain]):
    """Safe rendering: Returns GraphViz object OR None if missing."""
    if not HAS_GRAPHVIZ:
        return None

    try:
        graph = graphviz.Digraph()
        graph.attr(rankdir='TB') 
        
        strain_map = {s.id: s for s in all_strains}
        visited = set()
        queue = [target_strain]
        
        graph.node(target_strain.id, label=f"{target_strain.name}\n(Gen {target_strain.generation})", shape="box", style="filled", fillcolor="lightblue")
        visited.add(target_strain.id)

        while queue:
            current = queue.pop(0)
            if current.parent_ids:
                for pid in current.parent_ids:
                    if pid in strain_map:
                        parent = strain_map[pid]
                        if pid not in visited:
                            graph.node(pid, label=f"{parent.name}\n(Gen {parent.generation})")
                            visited.add(pid)
                            queue.append(parent)
                        graph.edge(pid, current.id)
                    else:
                        unknown_id = f"unknown_{pid}"
                        if unknown_id not in visited:
                            graph.node(unknown_id, label="Archived", style="dashed")
                            visited.add(unknown_id)
                        graph.edge(unknown_id, current.id)
        return graph
    except Exception:
        return None

# --- 6. STATE & UI ---

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

if "strains" not in st.session_state:
    s1 = Strain(name="Highland Gold")
    s1.genetics = {"structure": ("T", "T"), "aroma": ("L", "L"), "resistance": ("r", "r")} 
    s1.recalculate_stats()
    
    s2 = Strain(name="Deep Chunk")
    s2.genetics = {"structure": ("t", "t"), "aroma": ("l", "l"), "resistance": ("R", "R")} 
    s2.recalculate_stats()
    
    st.session_state["strains"] = [s1, s2]
    st.session_state["season"] = 1
    st.session_state["funds"] = 3000
    st.session_state["upgrades"] = []

st.set_page_config(page_title="Cultivar Labs", layout="wide")

st.title("🧬 Cultivar Labs: Lineage Edition")
st.markdown("---")

with st.sidebar:
    st.metric("Funds", f"${st.session_state['funds']:,}")
    st.metric("Season", st.session_state['season'])
    
    if st.session_state["upgrades"]:
        st.caption("Upgrades:")
        for u in st.session_state["upgrades"]:
            st.write(f"✅ {UPGRADES_DB[u]['name']}")

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
    st.subheader(f"Active Cultivation (Season {st.session_state['season']})")
    c1, c2 = st.columns([1, 2])
    with c1:
        choice = st.selectbox("Strain", [s.name for s in st.session_state["strains"]])
        target = next(s for s in st.session_state["strains"] if s.name == choice)
    with c2:
        cost = GrowEngine.calculate_cost(target)
        st.info(f"**Cost:** ${cost} | **Duration:** {100 - target.get_growth_speed()} days")
        
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
    price, trend = MarketEngine.get_market_price(st.session_state["upgrades"])
    c1, c2 = st.columns([1, 2])
    c1.metric("Base Price", f"${price}/g", delta=trend)
    with c2:
        for s in st.session_state["strains"]:
            if s.inventory_amount > 0:
                val = MarketEngine.calculate_strain_value(price, s)
                with st.container(border=True):
                    cols = st.columns([2, 1, 1])
                    cols[0].write(f"**{s.name}**")
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
    
    # Selection for Visualization
    all_names = [s.name for s in st.session_state["strains"]]
    selected_name = st.selectbox("Select Strain to Inspect", all_names)
    selected_strain = next(s for s in st.session_state["strains"] if s.name == selected_name)
    
    c1, c2 = st.columns(2)
    with c1:
        st.write(f"**Generation:** {selected_strain.generation}")
        st.write(f"**Potency:** {selected_strain.potency}")
        st.write(f"**Yield:** {selected_strain.yield_amount}")
        st.caption("Genetics:")
        if "seq" in st.session_state["upgrades"] or selected_strain.is_sequenced:
             for k, v in selected_strain.genetics.items():
                 st.write(f"- {GENOME_DB[k].name}: `{v}`")
        else:
            st.write("🔒 Sequence Hidden")

    with c2:
        st.caption("Ancestry Tree")
        
        # SAFE GRAPHVIZ CHECK
        if HAS_GRAPHVIZ:
            graph = render_lineage(selected_strain, st.session_state["strains"])
            if graph:
                try:
                    st.graphviz_chart(graph)
                except Exception as e:
                    st.error("Graphviz binary missing. Displaying text fallback.")
                    st.text(f"Lineage: {selected_strain.parents_text}")
            else:
                 st.text("No ancestry data available.")
        else:
            # TEXT FALLBACK
            st.warning("Graphviz library not found. Showing text mode.")
            st.info(f"**Immediate Parents:**\n{selected_strain.parents_text}")
            
            if selected_strain.parent_ids:
                 st.write("Grandparents are in the database but cannot be visualized without Graphviz.")
