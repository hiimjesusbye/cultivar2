import streamlit as st
import random
import uuid
import json
from enum import Enum
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Tuple

# --- SAFE IMPORT ---
try:
    import graphviz
    HAS_GRAPHVIZ = True
except ImportError:
    HAS_GRAPHVIZ = False

# --- 1. CONFIGURATION ---

TERPENES = {
    "L": "Limonene (Citrus)",
    "M": "Myrcene (Earth)",
    "P": "Pinene (Pine)",
    "C": "Caryophyllene (Spice)"
}

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
    "brand": {"name": "Brand Marketing", "cost": 3000, "desc": "+15% Sale Price."},
    "room":  {"name": "Expand Facility", "cost": 5000, "desc": "Adds 1 Grow Room (Max 4)."}
}

# --- 2. DATA MODELS ---

@dataclass
class Batch:
    id: str
    strain_id: str
    strain_name: str
    amount: int
    harvest_season: int
    status: str  
    target_grade: str 
    seasons_remaining: int
    def to_dict(self): return asdict(self)
    @staticmethod
    def from_dict(data): return Batch(**data)

@dataclass
class Strain:
    name: str
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    genetics: Dict[str, Tuple[str, str]] = field(default_factory=dict)
    potency: int = 50
    yield_amount: int = 50
    generation: int = 1
    parents_text: str = "Unknown"
    parent_ids: List[str] = field(default_factory=list)
    times_grown: int = 0
    is_sequenced: bool = False
    stock_standard: int = 0
    stock_artisanal: int = 0

    def recalculate_stats(self):
        base_pot = 50
        base_yld = 50
        s_alleles = self.genetics.get("structure", ("t", "t"))
        if "T" in s_alleles: 
            base_pot += 15
            base_yld -= 10
        else: 
            base_pot -= 5
            base_yld += 20
        a_alleles = self.genetics.get("aroma", ("L", "L"))
        if a_alleles[0] != a_alleles[1]: base_pot += 5
        self.potency = max(10, min(100, int(base_pot + random.uniform(-10, 10))))
        self.yield_amount = max(10, min(100, int(base_yld + random.uniform(-10, 10))))

    def get_aroma_label(self) -> str:
        alleles = sorted(self.genetics["aroma"])
        return FLAVOR_COMBOS.get(tuple(alleles), "Complex Hybrid")
    def get_structure_label(self) -> str:
        return "Sativa (Tall)" if "T" in self.genetics["structure"] else "Indica (Short)"
    def get_growth_speed(self) -> int:
        return 30 if "T" in self.genetics["structure"] else 60
    def to_dict(self): return asdict(self)
    @staticmethod
    def from_dict(data):
        s = Strain(**data)
        s.genetics = {k: tuple(v) for k, v in s.genetics.items()}
        return s

@dataclass
class GrowRoom:
    id: int
    strain_id: Optional[str] = None # None if empty
    strain_name: Optional[str] = None
    
    def to_dict(self): return asdict(self)
    @staticmethod
    def from_dict(data): return GrowRoom(**data)

# --- 3. LOGIC ENGINES ---

class BreedingEngine:
    @staticmethod
    def breed(parent_a: Strain, parent_b: Strain, name_suggestion: str, upgrades: List[str]) -> Strain:
        child = Strain(name=name_suggestion)
        child.generation = max(parent_a.generation, parent_b.generation) + 1
        child.parents_text = f"{parent_a.name} x {parent_b.name}"
        child.parent_ids = [parent_a.id, parent_b.id]
        for key in ["structure", "resistance"]:
            a = random.choice(parent_a.genetics[key])
            b = random.choice(parent_b.genetics[key])
            child.genetics[key] = tuple(sorted((a, b)))
        terp_a = random.choice(parent_a.genetics["aroma"])
        terp_b = random.choice(parent_b.genetics["aroma"])
        child.genetics["aroma"] = tuple(sorted((terp_a, terp_b)))
        child.recalculate_stats()
        if "seq" in upgrades: child.is_sequenced = True
        return child

class CuringEngine:
    @staticmethod
    def create_batch(strain: Strain, amount: int, season: int) -> Batch:
        return Batch(id=str(uuid.uuid4())[:8], strain_id=strain.id, strain_name=strain.name, amount=amount, harvest_season=season, status="Fresh", target_grade="Standard", seasons_remaining=0)

    @staticmethod
    def process_batches(batches: List[Batch], strains: List[Strain]) -> List[str]:
        events = []
        for b in batches:
            if b.status in ["Curing", "Deep Curing"]:
                b.seasons_remaining -= 1
                if b.seasons_remaining <= 0:
                    if b.status == "Deep Curing":
                        if random.random() < 0.15:
                            events.append(f"❌ Batch {b.id} ({b.strain_name}) rotted! Lost {b.amount}g.")
                            b.status = "Destroyed"
                        else:
                            target_strain = next(s for s in strains if s.id == b.strain_id)
                            target_strain.stock_artisanal += b.amount
                            events.append(f"🏺 Batch {b.id} finished Deep Cure! +{b.amount}g Artisanal.")
                            b.status = "Finished"
                    else:
                        target_strain = next(s for s in strains if s.id == b.strain_id)
                        target_strain.stock_standard += b.amount
                        events.append(f"✅ Batch {b.id} finished curing. +{b.amount}g Standard.")
                        b.status = "Finished"
        st.session_state["batches"] = [b for b in batches if b.status not in ["Finished", "Destroyed"]]
        return events

class FacilityEngine:
    @staticmethod
    def run_facility(rooms: List[GrowRoom], strains: List[Strain], funds: int, upgrades: List[str], season: int):
        occupied = [r for r in rooms if r.strain_id is not None]
        if not occupied:
            return {"error": "No active rooms."}
        
        # Calculate Total Cost
        total_cost = 0
        cycle_results = []
        
        for room in occupied:
            strain = next(s for s in strains if s.id == room.strain_id)
            # Cost based on Speed (Slower = More expensive per season/cycle)
            days = 100 - strain.get_growth_speed()
            cost = 500 + (days * 12)
            total_cost += cost
            
            # Yield Calculation
            base_yield = strain.yield_amount * 2.5 
            variance = random.uniform(0.8, 1.2)
            multiplier = 1.2 if "hydro" in upgrades else 1.0
            final_yield = int(base_yield * variance * multiplier)
            
            # Events
            event_msg = None
            is_hardy = "R" in strain.genetics["resistance"]
            base_risk = 0.05 if is_hardy else 0.30
            if "hepa" in upgrades: base_risk /= 2
            
            if random.random() < base_risk:
                loss = int(final_yield * 0.4)
                final_yield -= loss
                event_msg = f"⚠️ Room {room.id} ({strain.name}): Stress Event! Lost {loss}g."

            strain.times_grown += 1
            
            cycle_results.append({
                "room_id": room.id,
                "strain": strain,
                "yield": final_yield,
                "event": event_msg
            })

        if funds < total_cost:
            return {"error": f"Insufficient funds. Need ${total_cost} to run facility."}

        return {
            "cost": total_cost,
            "results": cycle_results
        }

class MarketEngine:
    @staticmethod
    def get_market_state(season: int):
        random.seed(season + 999) 
        trending_code = random.choice(["L", "M", "P", "C"])
        trending_name = TERPENES[trending_code].split(" ")[0]
        base = random.uniform(3.0, 7.0)
        random.seed()
        return base, trending_code, trending_name

    @staticmethod
    def calculate_value(base_price: float, strain: Strain, trending_code: str, grade: str) -> float:
        val = base_price * (strain.potency / 50.0)
        if trending_code in strain.genetics["aroma"]: val *= 1.3 
        if strain.genetics["aroma"][0] == strain.genetics["aroma"][1]: val *= 1.1
        if grade == "Fresh": val *= 0.7
        elif grade == "Artisanal": val *= 1.4
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
        "strains": [s.to_dict() for s in st.session_state["strains"]],
        "batches": [b.to_dict() for b in st.session_state["batches"]],
        "rooms": [r.to_dict() for r in st.session_state["rooms"]]
    }
    return json.dumps(data, indent=2)

def load_game_state(json_file):
    try:
        data = json.load(json_file)
        st.session_state["funds"] = data["funds"]
        st.session_state["season"] = data["season"]
        st.session_state["upgrades"] = data.get("upgrades", [])
        st.session_state["strains"] = [Strain.from_dict(s_data) for s_data in data["strains"]]
        st.session_state["batches"] = [Batch.from_dict(b) for b in data.get("batches", [])]
        st.session_state["rooms"] = [GrowRoom.from_dict(r) for r in data.get("rooms", [])]
        return True
    except Exception as e:
        st.error(f"Error: {e}")
        return False

# --- UI ---

if "strains" not in st.session_state:
    s1 = Strain(name="Lemon Sol")
    s1.genetics = {"structure": ("T", "T"), "resistance": ("r", "r"), "aroma": ("L", "P")} 
    s1.recalculate_stats()
    s2 = Strain(name="Musky Spice")
    s2.genetics = {"structure": ("t", "t"), "resistance": ("R", "R"), "aroma": ("C", "M")} 
    s2.recalculate_stats()
    
    st.session_state["strains"] = [s1, s2]
    st.session_state["batches"] = [] 
    st.session_state["rooms"] = [GrowRoom(id=1)] # Start with 1 room
    st.session_state["season"] = 1
    st.session_state["funds"] = 5000 # Increased starting funds for facility management
    st.session_state["upgrades"] = []

st.set_page_config(page_title="Cultivar Labs", layout="wide")
st.title("🏭 Cultivar Labs: Facility Manager")
st.markdown("---")

base_price, trend_code, trend_name = MarketEngine.get_market_state(st.session_state["season"])

with st.sidebar:
    st.metric("Funds", f"${st.session_state['funds']:,}")
    st.metric("Season", st.session_state['season'])
    st.metric("Rooms", f"{len(st.session_state['rooms'])}/4")
    st.info(f"📢 **Market Craze:**\n{trend_name} Strains")
    st.divider()
    st.download_button("💾 Save", serialize_game_state(), "save.json", "application/json")
    uf = st.file_uploader("📂 Load", type=["json"])
    if uf and st.button("Load"):
        if load_game_state(uf): st.rerun()
    if st.button("Reset"):
        st.session_state.clear()
        st.rerun()

t1, t2, t3, t4, t5, t6 = st.tabs(["🏭 Facility", "🏺 Curing Room", "💰 Market", "🏗️ Store", "🧬 Breed", "📂 Library"])

with t1:
    st.subheader(f"Grow Operations (Season {st.session_state['season']})")
    
    # Render Rooms
    active_count = 0
    total_est_cost = 0
    
    # Grid Layout for Rooms
    cols = st.columns(4)
    for i, room in enumerate(st.session_state["rooms"]):
        with cols[i]:
            with st.container(border=True):
                st.write(f"**Room {room.id}**")
                
                if room.strain_id is None:
                    # Empty State
                    st.caption("Status: Empty")
                    choice = st.selectbox(f"Assign Strain (R{room.id})", ["-"] + [s.name for s in st.session_state["strains"]], key=f"sel_{room.id}")
                    if choice != "-":
                        selected = next(s for s in st.session_state["strains"] if s.name == choice)
                        if st.button(f"Assign", key=f"btn_{room.id}"):
                            room.strain_id = selected.id
                            room.strain_name = selected.name
                            st.rerun()
                else:
                    # Occupied State
                    st.info(f"Growing: **{room.strain_name}**")
                    strain = next(s for s in st.session_state["strains"] if s.id == room.strain_id)
                    days = 100 - strain.get_growth_speed()
                    cost = 500 + (days * 12)
                    st.caption(f"Cost: ${cost} | Risk: {'Low' if 'R' in strain.genetics['resistance'] else 'High'}")
                    
                    if st.button("Clear Room", key=f"clr_{room.id}"):
                        room.strain_id = None
                        room.strain_name = None
                        st.rerun()
                    
                    active_count += 1
                    total_est_cost += cost

    st.divider()
    
    # Global Controls
    c1, c2 = st.columns([3, 1])
    with c1:
        if active_count == 0:
            st.warning("Facility is idle. Assign strains to rooms to begin.")
        else:
            st.success(f"Ready to run {active_count} room(s). Estimated Cost: ${total_est_cost}")
    
    with c2:
        if st.button("🔴 RUN FACILITY", type="primary", disabled=(active_count==0), use_container_width=True):
            report = FacilityEngine.run_facility(st.session_state["rooms"], st.session_state["strains"], st.session_state["funds"], st.session_state["upgrades"], st.session_state["season"])
            
            if "error" in report:
                st.error(report["error"])
            else:
                # Update Global State
                st.session_state["funds"] -= report["cost"]
                st.session_state["season"] += 1
                
                # Process Results
                for res in report["results"]:
                    # Create Batch
                    new_batch = CuringEngine.create_batch(res["strain"], res["yield"], st.session_state["season"])
                    st.session_state["batches"].append(new_batch)
                    
                    # Clear Room
                    room_obj = next(r for r in st.session_state["rooms"] if r.id == res["room_id"])
                    room_obj.strain_id = None
                    room_obj.strain_name = None
                    
                    # Logs
                    st.toast(f"Room {res['room_id']}: Harvested {res['yield']}g of {res['strain'].name}")
                    if res["event"]: st.error(res["event"])

                # Advance Curing
                cure_logs = CuringEngine.process_batches(st.session_state["batches"], st.session_state["strains"])
                for l in cure_logs: st.info(l)
                
                st.rerun()

with t2:
    st.subheader("Curing & Drying")
    fresh_batches = [b for b in st.session_state["batches"] if b.status == "Fresh"]
    
    if fresh_batches:
        st.markdown("### 🌿 Fresh Harvests")
        for b in fresh_batches:
            with st.container(border=True):
                c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
                c1.write(f"**{b.strain_name}** ({b.amount}g)")
                val_fresh = MarketEngine.calculate_value(base_price, next(s for s in st.session_state["strains"] if s.id == b.strain_id), trend_code, "Fresh")
                if c2.button(f"Sell Fresh (${int(b.amount * val_fresh)})", key=f"sf_{b.id}"):
                    st.session_state["funds"] += int(b.amount * val_fresh)
                    st.session_state["batches"].remove(b)
                    st.rerun()
                if c3.button("Jar Cure (1 S)", key=f"jc_{b.id}"):
                    b.status = "Curing"
                    b.seasons_remaining = 1
                    st.rerun()
                if c4.button("Deep Cure (2 S)", key=f"dc_{b.id}"):
                    b.status = "Deep Curing"
                    b.seasons_remaining = 2
                    st.rerun()

    st.markdown("### ⏳ In Progress")
    aging_batches = [b for b in st.session_state["batches"] if b.status in ["Curing", "Deep Curing"]]
    for b in aging_batches:
        st.info(f"{'🏺' if b.status == 'Curing' else '⚱️'} **{b.strain_name}** | {b.amount}g | Ready in {b.seasons_remaining}")

with t3:
    st.subheader("Marketplace")
    st.markdown(f"Craze: **{trend_name}** | Base: **${round(base_price,2)}/g**")
    for s in st.session_state["strains"]:
        if s.stock_standard > 0 or s.stock_artisanal > 0:
            with st.container(border=True):
                st.write(f"**{s.name}**")
                c1, c2 = st.columns(2)
                if s.stock_standard > 0:
                    val = MarketEngine.calculate_value(base_price, s, trend_code, "Standard")
                    c1.button(f"Sell {s.stock_standard}g Std (${int(s.stock_standard * val)})", key=f"sstd_{s.id}", on_click=lambda s=s, v=val: (setattr(s, 'stock_standard', 0), setattr(st.session_state, 'funds', st.session_state['funds'] + int(s.stock_standard * v))))
                if s.stock_artisanal > 0:
                    val = MarketEngine.calculate_value(base_price, s, trend_code, "Artisanal")
                    c2.button(f"Sell {s.stock_artisanal}g Art (${int(s.stock_artisanal * val)})", key=f"sart_{s.id}", on_click=lambda s=s, v=val: (setattr(s, 'stock_artisanal', 0), setattr(st.session_state, 'funds', st.session_state['funds'] + int(s.stock_artisanal * v))))

with t4:
    st.subheader("Upgrades & Expansion")
    for uid, data in UPGRADES_DB.items():
        c1, c2 = st.columns([3, 1])
        c1.markdown(f"**{data['name']}** - {data['desc']}")
        
        if uid == "room":
            current_rooms = len(st.session_state["rooms"])
            if current_rooms >= 4:
                c2.success("Max Capacity")
            else:
                if c2.button(f"Buy Room ({current_rooms+1}/4) - ${data['cost']}"):
                    if st.session_state["funds"] >= data['cost']:
                        st.session_state["funds"] -= data['cost']
                        st.session_state["rooms"].append(GrowRoom(id=current_rooms + 1))
                        st.rerun()
                    else:
                        st.error("No Funds")
        else:
            if uid in st.session_state["upgrades"]: c2.success("Owned")
            else:
                if c2.button(f"Buy (${data['cost']})", key=uid):
                    if st.session_state["funds"] >= data['cost']:
                        st.session_state["funds"] -= data['cost']
                        st.session_state["upgrades"].append(uid)
                        st.rerun()

with t5:
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

with t6:
    st.subheader("Strain Library")
    sel_name = st.selectbox("Select Strain", [s.name for s in st.session_state["strains"]])
    sel = next(s for s in st.session_state["strains"] if s.name == sel_name)
    c1, c2 = st.columns(2)
    with c1:
        st.write(f"**Profile:** {sel.get_aroma_label()}")
        st.write(f"**Inventory:** {sel.stock_standard}g Std / {sel.stock_artisanal}g Art")
        if "seq" in st.session_state["upgrades"] or sel.is_sequenced:
             st.write(f"- Aroma: `{sel.genetics['aroma']}`")
             st.write(f"- Structure: `{sel.genetics['structure']}`")
             st.write(f"- Resistance: `{sel.genetics['resistance']}`")
        else:
            st.write("🔒 Sequence Hidden")
    with c2:
        st.code(get_lineage_text(sel, st.session_state["strains"]), language="text")
