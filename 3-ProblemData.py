import pandas as pd
import pickle
from pyvrp import Model
from funciones import split_FF2S
#--------------------------------------------
coords = pd.read_csv("1.1-coordenadas.csv")
dist = pd.read_csv("2.1-distancias.csv", header=None, index_col=False)
time = pd.read_csv("2.2-tiempos.csv", header=None, index_col=False)
dem = pd.read_csv("demanda.csv") 
service = pd.read_csv("service.csv")
#--------------------------------------------
# Modelo
m = Model()
locations = {}
#--------------------------------------------
# Escalar
SCALE = 100
dist = round(dist*SCALE)
time = round(time*SCALE)
#--------------------------------------------
# ====== Depots ======
CI = coords[coords["Nombre"] == "CI"].iloc[0]
CD = coords[coords["Nombre"] == "CD"].iloc[0]
# Agregar al modelo como depósito
locations["CI"]=m.add_depot(
    x=float(CI["lon"]),
    y=float(CI["lat"]),
    name=CI["Nombre"]
)
locations["CD"]=m.add_depot(
    x=float(CD["lon"]),
    y=float(CD["lat"]),
    name=CD["Nombre"]
)
# d = [loc.tw_late for loc in m.depots]
# print(d)
#--------------------------------------------  
# ====== Vehicles ======
# Capacidades
VEH_CAPS = {
    "STE138": 31,
    "WCP677": 22,
    "WCP384": 20,
    "PUN354": 15,
    "JYO449": 24,  
}
# Agregar al modelo como vehículos
for name, cap in VEH_CAPS.items():
    m.add_vehicle_type(
        capacity=[cap*0.9*SCALE],
        num_available=1,
        start_depot=locations["CI"],
        end_depot=locations["CD"],
        # tw_early=,
        # tw_late=,
        shift_duration=10*60*SCALE,
        unit_distance_cost=1,  
        unit_duration_cost=1,
        # reload_depots=[locations["CI"]], ######
        max_overtime=3*60*SCALE,
        unit_overtime_cost=100000,
        name=name,
    )
#--------------------------------------------
# ====== Clientes ======
original_of = {}
for _, row in coords.iterrows():
    planta = str(row["Nombre"])
    if planta in [loc.name for loc in m.depots]:
        continue    
    d = dem[dem["planta"] == planta]
    s = service[service["planta"] == planta]
    if not d.empty:
        delivery = int(d.iloc[0]["di"] * SCALE)
        pickup   = int(d.iloc[0]["pi"] * SCALE)
    else:
        delivery = pickup = 0
    # tiempo de servicio
    srv_pi    = int(s.iloc[0]["pi"]    * SCALE) if not s.empty else 0
    srv_di    = int(s.iloc[0]["di"]    * SCALE) if not s.empty else 0
    # --- Entregas ---
    # Si la demanda de una planta ocupa más del 70% de la capacidad del vehículo, se divide esta carga
    if delivery > 0:
        MAX_CAP = max(VEH_CAPS.values()) * SCALE 
        if delivery > 0.7 * MAX_CAP:
            parts = split_FF2S(delivery)
        else:
            parts = [delivery]   
        for k, part in enumerate(parts, start=1):
            # Nombrar los puntos
            name_d = f"{planta}d_{k}" if len(parts) > 1 else f"{planta}d"
            # Ventanas de tiempo
            if planta in ("A6", "42"): 
                tw_e = 0
                tw_l = 90 * SCALE
            else:
                tw_e = 0
                tw_l = 1440 * SCALE
            # tiempo servicio SOLO en el último subnodo
            service_k = srv_di if k == len(parts) else 0
            # Agregar al modelo como clientes
            locations[name_d] = m.add_client(
                x=float(row["lon"]),
                y=float(row["lat"]),
                delivery=[part],
                pickup=[],
                service_duration=service_k,
                tw_early=tw_e,
                tw_late=tw_l,
                required=True,
                name=name_d,
            )
            original_of[name_d] = planta
    # --- Recogidas ---
    if pickup > 0:
        # Nombrar los puntos
        name_p = f"{planta}p"
        # Ventanas de tiempo
        tw_e = 0
        tw_l = 1440 * SCALE
        # Agregar al modelo como clientes
        locations[name_p] = m.add_client(
            x=float(row["lon"]),
            y=float(row["lat"]),
            delivery=[],
            pickup=[pickup],
            service_duration=srv_pi,   
            tw_early=tw_e,
            tw_late=tw_l,
            required=True,
            name=name_p,
        )
        original_of[name_p] = planta
# d = [loc.name for loc in m.clients]
# print(d)
#--------------------------------------------  
# ====== Edges ======
names = coords["Nombre"].astype(str).tolist()
dist.index = names
dist.columns = names
time.index = names
time.columns = names
# Establecer relación tiempo, distancia según los clientes agregados
for frm_node in list(locations.keys()):
    for to_node in list(locations.keys()):
        frm_orig = original_of.get(frm_node, frm_node)
        to_orig = original_of.get(to_node, to_node)
        if frm_orig in dist.index and to_orig in dist.columns:
            # Agregar al modelo
            m.add_edge(
                frm=locations[frm_node],
                to=locations[to_node],
                distance=int(dist.loc[frm_orig, to_orig]),
                duration=int(time.loc[frm_orig, to_orig]),
            )
#--------------------------------------------  
# Guardar instancia
# Exportar en .pkl
problem = m.data()
with open("3.3-ProblemData.pkl", "wb") as f:
    pickle.dump(problem, f)
with open("3.3-Modelo.pkl", "wb") as f:
    pickle.dump(m, f)
