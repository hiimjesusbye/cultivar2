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

# --- 1. CONFIGURATION & DATABASES ---

TERPENES = {
    "L": "Limonene (Citrus)",
    "M": "Myrcene (Earth)",
    "P": "Pinene (Pine)",
    "C": "Caryophyllene (Spice)"
}

FLAVOR_COMBOS = {
    ("L", "L"): {"name": "Super Lemon Haze", "icon": "🍋⚡"},
    ("M", "M"): {"name": "Deep Earth", "icon": "🌍🍄"},
    ("P", "P"): {"name": "Pure Pine", "icon": "🌲🏔️"},
    ("C", "C"): {"name": "Black Pepper", "icon": "🌶️🔥"},
    ("L", "M"): {"name": "Mango Citrus", "icon": "🥭🍹"},
    ("L", "P"): {"name": "Lemon Sol", "icon": "🍋🌲"},
    ("C", "L"): {"name": "Spicy Lemon", "icon": "🍋🌶️"},
    ("M", "P"): {"name": "Forest Floor", "icon": "🌲🍂"},
    ("C", "M"): {"name": "Musky Spice", "icon": "🧉🌶️"},
    ("C", "P"): {"name": "Peppery Pine", "icon": "🌲🔥"}
}

# NEW: Cultivation Inputs
SUBSTRATES = {
    "soil": {"name": "Living Soil", "cost_mult": 1.0, "yield_mult": 0.9, "value_mult": 1.25, "desc": "Lower yield, Premium price."},
    "hydro": {"name": "Deep Water Hydro", "cost_mult": 1.5, "yield_mult": 1.3, "value_mult": 1.0, "desc": "Max yield, Standard price."},
    "coco": {"name": "Coco Coir", "cost_mult": 1.2, "yield_mult": 1.1, "value_mult": 1.05, "desc": "Balanced approach."}
}

NUTRIENTS = {
    "syn": {"name": "Synthetic Salts", "cost": 100, "yield_bonus": 0.15, "risk": 0.10, "desc": "Pushes growth, risk of burn."},
    "org": {"name": "Organic Teas", "cost": 300, "yield_bonus": 0.0, "risk": -0.05, "desc": "Safe, improves terpene profile (+Value)."}
}

UPGRADES_DB = {
    "hepa":  {"name": "HEPA Filtration", "cost": 1500, "desc": "Reduces pest/mold risk by 50%."},
    "seq":   {"name": "Genetic Sequencer", "cost": 4000, "desc": "Reveals Genotypes immediately."},
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
    seasons_remaining: int
    # Track how it was grown for history
    method: str = "Unknown"
    
    def to_dict(self): return asdict(self)
    @staticmethod
    def from_dict(data): return Batch(**data)

@dataclass
class Strain:
    name: str
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    genetics: Dict[str, Tuple[str, str]] = field(default_factory=dict)
    
    # Stats
    potency: int = 0
    yield_amount: int = 0
    
    # Metadata
    generation: int = 1
    parents_text: str = "Unknown"
    parent_ids: List[str] = field(default_factory=list)
    
    # State
    is_proven: bool = True # If False, stats are hidden (Seed)
    is_sequenced: bool = False
    
    # Inventory
    stock_standard: int = 0
    stock_artisanal: int = 0

    def generate_random_stats(self):
        """Called when seed is first harvested to 'roll' the phenotype."""
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
        
        # Aroma Modifier
        a_alleles = self.genetics.get("aroma", ("L", "L"))
        if a_alleles[0] != a_alleles[1]: base_pot += 5
        
        self.potency = max(10, min(100, int(base_pot + random.uniform(-10, 10))))
        self.yield_amount = max(10, min(100, int(base_yld + random.uniform(-10, 10))))
        self.is_proven = True

    def get_aroma_data(self):
        alleles = sorted(self.genetics["aroma"])
        return FLAVOR_COMBOS.get(tuple(alleles), {"name": "Complex Hybrid", "icon": "🧬❓"})

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
    strain_id: Optional[str] = None 
    strain_name: Optional[str] = None
    # Configuration
    substrate: Optional[str] = None
    nutrient: Optional[str] = None
    
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
        
        # Genetics
        for key in ["structure", "resistance"]:
            a = random.choice(parent_a.genetics[key])
            b = random.choice(parent_b.genetics[key])
            child.genetics[key] = tuple(sorted((a, b)))
        terp_a = random.choice(parent_a.genetics["aroma"])
        terp_b = random.choice(parent_b.genetics["aroma"])
        child.genetics["aroma"] = tuple(sorted((terp_a, terp_b)))
        
        # NEW: It starts unproven (stats not calculated yet)
        child.is_proven = False 
        child.potency = 0
        child.yield_amount = 0
        
        if "seq" in upgrades: child.is_sequenced = True
        return child

class FacilityEngine:
    @staticmethod
    def run_facility(rooms: List[GrowRoom], strains: List[Strain], funds: int, upgrades: List[str], season: int):
        occupied = [r for r in rooms if r.strain_id is not None]
        if not occupied: return {"error": "No active rooms."}
        
        total_cost = 0
        cycle_results = []
        
        for room in occupied:
            strain = next(s for s in strains if s.id == room.strain_id)
            
            # 1. Config Data
            sub_data = SUBSTRATES[room.substrate]
            nut_data = NUTRIENTS[room.nutrient]
            
            # 2. Cost Calculation
            # Base cost depends on speed
            days = 100 - strain.get_growth_speed()
            base_run_cost = 500 + (days * 12)
            
            # Apply Config Multipliers
            run_cost = (base_run_cost * sub_data["cost_mult"]) + nut_data["cost"]
            total_cost += int(run_cost)
            
            # 3. Pheno Hunt Check (Reveal Stats if Seed)
            newly_proven = False
            if not strain.is_proven:
                strain.generate_random_stats()
                newly_proven = True
            
            # 4. Yield Calculation
            # Base Yield (Strain Stat) * Substrate Mult * Nutrient Bonus
            base_yield = strain.yield_amount * 2.5 
            variance = random.uniform(0.9, 1.1)
            
            yield_mult = sub_data["yield_mult"] + nut_data["yield_bonus"]
            final_yield = int(base_yield * variance * yield_mult)
            
            # 5. Risk Calculation
            event_msg = None
            is_hardy = "R" in strain.genetics["resistance"]
            base_risk = 0.05 if is_hardy else 0.25
            
            # Modifiers
            risk_mod = nut_data["risk"]
            if "hepa" in upgrades: risk_mod -= 0.10
            
            total_risk = max(0.01, base_risk + risk_mod)
            
            if random.random() < total_risk:
                loss = int(final_yield * 0.4)
                final_yield -= loss
                event_msg = f"⚠️ Room {room.id} ({strain.name}): Stress/Burn! Lost {loss}g."

            strain.times_grown += 1
            
            cycle_results.append({
                "room_id": room.id,
                "strain": strain,
                "yield": final_yield,
                "event": event_msg,
                "proven_now": newly_proven
            })

        if funds < total_cost: return {"error": f"Need ${total_cost} to run facility."}
        return {"cost": total_cost, "results": cycle_results}

class CuringEngine:
    @staticmethod
    def create_batch(strain: Strain, amount: int, season: int, room: GrowRoom) -> Batch:
        # Determine method string for flavor text
        sub_name = SUBSTRATES[room.substrate]['name']
        return Batch(
            id=str(uuid.uuid4())[:8],
            strain_id=strain.id,
            strain_name=strain.name,
            amount=amount,
            harvest_season=season,
            status="Fresh",
            seasons_remaining=0,
            method=sub_name
        )

    @staticmethod
    def process_batches(batches: List[Batch], strains: List[Strain]) -> List[str]:
        events = []
        for b in batches:
            if b.status in ["Curing", "Deep Curing"]:
                b.seasons_remaining -= 1
                if b.seasons_remaining <= 0:
                    target = next(s for s in strains if s.id == b.strain_id)
                    if b.status == "Deep Curing":
                        if random.random() < 0.15:
                            events.append(f"❌ Batch {b.id} rotted.")
                            b.status = "Destroyed"
                        else:
                            target.stock_artisanal += b.amount
                            b.status = "Finished"
                    else:
                        target.stock_standard += b.amount
                        b.status = "Finished"
        st.session_state["batches"] = [b for b in batches if b.status not in ["Finished", "Destroyed"]]
        return events

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
    tree_str = f"{indent}{prefix}{target_strain.name}\n"
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
    s1.generate_random_stats() # Starters are proven
    
    s2 = Strain(name="Musky Spice")
    s2.genetics = {"structure": ("t", "t"), "resistance": ("R", "R"), "aroma": ("C", "M")} 
    s2.generate_random_stats()
    
    st.session_state["strains"] = [s1, s2]
    st.session_state["batches"] = [] 
    st.session_state["rooms"] = [GrowRoom(id=1)] 
    st.session_state["season"] = 1
    st.session_state["funds"] = 6000 
    st.session_state["upgrades"] = []

st.set_page_config(page_title="Cultivar Labs", layout="wide")
st.title("🧪 Cultivar Labs: Master Grower")
st.markdown("---")

base_price, trend_code, trend_name = MarketEngine.get_market_state(st.session_state["season"])

with st.sidebar:
    st.metric("Funds", f"${st.session_state['funds']:,}")
    st.metric("Season", st.session_state['season'])
    st.metric("Rooms", f"{len(st.session_state['rooms'])}/4")
    st.info(f"📢 **Trend:** {trend_name}")
    st.divider()
    st.download_button("💾 Save", serialize_game_state(), "save.json", "application/json")
    uf = st.file_uploader("📂 Load", type=["json"])
    if uf and st.button("Load"):
        if load_game_state(uf): st.rerun()
    if st.button("Reset"):
        st.session_state.clear()
        st.rerun()

t1, t2, t3, t4, t5, t6 = st.tabs(["🏭 Facility", "🏺 Curing", "💰 Market", "🏗️ Store", "🧬 Breed", "📂 Library"])

with t1:
    st.subheader(f"Grow Operations")
    active_count = 0
    total_est_cost = 0
    cols = st.columns(4)
    for i, room in enumerate(st.session_state["rooms"]):
        with cols[i]:
            with st.container(border=True):
                st.write(f"**Room {room.id}**")
                
                if room.strain_id is None:
                    # CONFIGURATION PHASE
                    choice = st.selectbox(f"Strain", ["-"] + [s.name for s in st.session_state["strains"]], key=f"s_{room.id}")
                    sub_c = st.selectbox("Substrate", list(SUBSTRATES.keys()), format_func=lambda x: SUBSTRATES[x]['name'], key=f"sub_{room.id}")
                    nut_c = st.selectbox("Nutrients", list(NUTRIENTS.keys()), format_func=lambda x: NUTRIENTS[x]['name'], key=f"nut_{room.id}")
                    
                    if choice != "-":
                        # Cost Preview
                        sel_strain = next(s for s in st.session_state["strains"] if s.name == choice)
                        days = 100 - sel_strain.get_growth_speed()
                        base = 500 + (days * 12)
                        
                        sub_mult = SUBSTRATES[sub_c]["cost_mult"]
                        nut_cost = NUTRIENTS[nut_c]["cost"]
                        final_est = int((base * sub_mult) + nut_cost)
                        
                        st.caption(f"Est Cost: ${final_est}")
                        
                        if st.button("Assign", key=f"btn_{room.id}"):
                            room.strain_id = sel_strain.id
                            room.strain_name = sel_strain.name
                            room.substrate = sub_c
                            room.nutrient = nut_c
                            st.rerun()
                else:
                    # OCCUPIED STATE
                    st.info(f"Growing: **{room.strain_name}**")
                    strain = next(s for s in st.session_state["strains"] if s.id == room.strain_id)
                    
                    if not strain.is_proven:
                        st.warning("🌱 Pheno Hunting (Seed)")
                    
                    st.caption(f"Method: {SUBSTRATES[room.substrate]['name']}")
                    
                    if st.button("Clear", key=f"clr_{room.id}"):
                        room.strain_id = None
                        st.rerun()
                    active_count += 1
                    
                    # Recalculate cost for Total display
                    days = 100 - strain.get_growth_speed()
                    base = 500 + (days * 12)
                    sub_mult = SUBSTRATES[room.substrate]["cost_mult"]
                    nut_cost = NUTRIENTS[room.nutrient]["cost"]
                    total_est_cost += int((base * sub_mult) + nut_cost)

    st.divider()
    if st.button("🔴 RUN FACILITY", type="primary", disabled=(active_count==0), use_container_width=True):
        report = FacilityEngine.run_facility(st.session_state["rooms"], st.session_state["strains"], st.session_state["funds"], st.session_state["upgrades"], st.session_state["season"])
        if "error" in report: st.error(report["error"])
        else:
            st.session_state["funds"] -= report["cost"]
            st.session_state["season"] += 1
            
            for res in report["results"]:
                # Create batch
                room_obj = next(r for r in st.session_state["rooms"] if r.id == res["room_id"])
                new_batch = CuringEngine.create_batch(res["strain"], res["yield"], st.session_state["season"], room_obj)
                st.session_state["batches"].append(new_batch)
                
                # Logs
                st.toast(f"R{res['room_id']} Harvest: {res['yield']}g")
                if res["proven_now"]:
                    st.toast(f"🧬 Analysis Complete: {res['strain'].name} stats revealed!", icon="🔎")
                
                # Clear Room
                room_obj.strain_id = None
                
            # Process Curing
            CuringEngine.process_batches(st.session_state["batches"], st.session_state["strains"])
            st.rerun()

with t2:
    st.subheader("Curing Room")
    fresh_batches = [b for b in st.session_state["batches"] if b.status == "Fresh"]
    if fresh_batches:
        st.markdown("### 🌿 Fresh")
        for b in fresh_batches:
            with st.container(border=True):
                c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
                c1.write(f"**{b.strain_name}** ({b.amount}g)")
                c1.caption(f"Grown in: {b.method}")
                
                # Dynamic Pricing based on how it was grown? 
                # For now, substrates boost YIELD or COST. We could add a value mult here later.
                # Currently value mult is applied at sale time implicitly if we wanted, 
                # but let's stick to the MarketEngine logic which uses genetics.
                
                val_fresh = MarketEngine.calculate_value(base_price, next(s for s in st.session_state["strains"] if s.id == b.strain_id), trend_code, "Fresh")
                if c2.button(f"Sell Fresh (${int(b.amount * val_fresh)})", key=f"sf_{b.id}"):
                    st.session_state["funds"] += int(b.amount * val_fresh)
                    st.session_state["batches"].remove(b)
                    st.rerun()
                if c3.button("Jar Cure (1S)", key=f"jc_{b.id}"):
                    b.status = "Curing"
                    b.seasons_remaining = 1
                    st.rerun()
                if c4.button("Deep Cure (2S)", key=f"dc_{b.id}"):
                    b.status = "Deep Curing"
                    b.seasons_remaining = 2
                    st.rerun()
    
    st.markdown("### ⏳ Curing")
    aging = [b for b in st.session_state["batches"] if b.status in ["Curing", "Deep Curing"]]
    for b in aging:
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
    st.subheader("Store")
    for uid, data in UPGRADES_DB.items():
        c1, c2 = st.columns([3, 1])
        c1.markdown(f"**{data['name']}** - {data['desc']}")
        if uid == "room":
            cur = len(st.session_state["rooms"])
            if cur >= 4: c2.success("Max")
            else:
                if c2.button(f"Expand ($5000)"):
                    if st.session_state["funds"] >= 5000:
                        st.session_state["funds"] -= 5000
                        st.session_state["rooms"].append(GrowRoom(id=cur + 1))
                        st.rerun()
        elif uid in st.session_state["upgrades"]: c2.success("Owned")
        else:
            if c2.button(f"Buy (${data['cost']})", key=uid):
                if st.session_state["funds"] >= data['cost']:
                    st.session_state["funds"] -= data['cost']
                    st.session_state["upgrades"].append(uid)
                    st.rerun()

with t5:
    st.subheader("Breeding Lab")
    c1, c2 = st.columns(2)
    # Filter only PROVEN strains for breeding parents (can't breed a mystery seed)
    proven_strains = [s.name for s in st.session_state["strains"] if s.is_proven]
    
    if len(proven_strains) < 2:
        st.warning("You need at least 2 Proven Strains to breed.")
    else:
        p1 = st.selectbox("Parent A", proven_strains, key="p1")
        p2 = st.selectbox("Parent B", proven_strains, key="p2")
        name = st.text_input("Project Name", value=f"Seed-{random.randint(100,999)}")
        
        st.caption("Breeding produces a **Mystery Seed**. You must grow it to see its traits!")
        
        if st.button("🧬 Cross ($200)"):
            if st.session_state["funds"] < 200: st.error("No Funds")
            else:
                st.session_state["funds"] -= 200
                pa = next(s for s in st.session_state["strains"] if s.name == p1)
                pb = next(s for s in st.session_state["strains"] if s.name == p2)
                child = BreedingEngine.breed(pa, pb, name, st.session_state["upgrades"])
                st.session_state["strains"].append(child)
                st.success(f"Created Seed Pack: {child.name}")

with t6:
    st.subheader("Strain Library")
    sel_name = st.selectbox("Inspect Strain", [s.name for s in st.session_state["strains"]])
    sel = next(s for s in st.session_state["strains"] if s.name == sel_name)
    aroma_data = sel.get_aroma_data()
    
    if not sel.is_proven:
        st.info(f"🌱 **{sel.name}** (Unproven Seed)")
        st.write("Grow this strain to reveal its stats!")
        st.caption(f"Parents: {sel.parents_text}")
    else:
        st.markdown(f"### {sel.name} {aroma_data['icon']}")
        col_vis, col_dna, col_hist = st.columns([1, 1, 1])
        
        with col_vis:
            st.caption("Potency")
            st.progress(sel.potency/100, text=f"{sel.potency}/100")
            st.caption("Yield")
            st.progress(sel.yield_amount/100, text=f"{sel.yield_amount}/100")
            st.write(f"📦 **{sel.stock_standard}g** Std | ⭐ **{sel.stock_artisanal}g** Art")

        with col_dna:
            if "seq" in st.session_state["upgrades"] or sel.is_sequenced:
                s_pair = sel.genetics['structure']
                st.markdown(f"**Structure:** `{s_pair}`")
                r_pair = sel.genetics['resistance']
                st.markdown(f"**Hardiness:** `{r_pair}`")
                a_pair = sel.genetics['aroma']
                st.markdown(f"**Aroma:** `{a_pair}`")
            else:
                st.warning("🔒 Sequence Hidden")

        with col_hist:
            st.code(get_lineage_text(sel, st.session_state["strains"]), language="text")
