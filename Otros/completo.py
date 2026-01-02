import pandas as pd
import pickle
from pyvrp import Model
from pyvrp.stop import FirstFeasible, NoImprovement, MaxRuntime
from funciones import split_FF2S
#--------------------------------------------
coords = pd.read_csv("coordenadas.csv")
dist = pd.read_csv("distancias.csv", header=None, index_col=False)
time = pd.read_csv("tiempos.csv", header=None, index_col=False)
dem = pd.read_csv("demanda.csv") 
service = pd.read_csv("service.csv")
#--------------------------------------------
#Modelo
m = Model()
locations = {}
#--------------------------------------------
#Escalar
SCALE = 100
dist = round(dist*SCALE)
time = round(time*SCALE)
#--------------------------------------------
# ====== Depots ======
CI = coords[coords["Nombre"] == "CI"].iloc[0]
CD = coords[coords["Nombre"] == "CD"].iloc[0]
#add depot
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
#Capacidades
VEH_CAPS = {
    "STE138": 31,
    "WCP677": 31,
    "WCP384": 20,
    "PUN354": 15,
    "JYO449": 24,  
}
#add vehicle
for name, cap in VEH_CAPS.items():
    m.add_vehicle_type(
        capacity=[cap*SCALE],
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
# ====== Clients (duplicar pickup/delivery) ======
original_of = {}

for _, row in coords.iterrows():
    planta = str(row["Nombre"])

    # Saltar depots
    if planta in [loc.name for loc in m.depots]:
        continue

    # ======== DEMANDA ========
    d = dem[dem["planta"] == planta]
    s = service[service["planta"] == planta]

    if not d.empty:
        delivery = int(d.iloc[0]["di"] * SCALE)
        pickup   = int(d.iloc[0]["pi"] * SCALE)
    else:
        delivery = pickup = 0

    # ======== TIEMPO DE SERVICIO SEGÚN TIPO ========
    total_srv = int(s.iloc[0]["total"] * SCALE) if not s.empty else 0
    srv_pi    = int(s.iloc[0]["pi"]    * SCALE) if not s.empty else 0
    srv_di    = int(s.iloc[0]["di"]    * SCALE) if not s.empty else 0

    # ========== NODO DELIVERY ==========
    # SPLIT FF2S condicional 
    if delivery > 0:

        # calcular capacidad máxima (real)
        MAX_CAP = max(VEH_CAPS.values()) * SCALE

        # condición para hacer split:
        # delivery debe ser mayor a 0.7 * capacidad máxima
        if delivery > 0.7 * MAX_CAP:
            parts = split_FF2S(delivery)
        else:
            parts = [delivery]   # NO SPLIT

        for k, part in enumerate(parts, start=1):
            # nombre interno
            name_d = f"{planta}d_{k}" if len(parts) > 1 else f"{planta}d"

            # TW especial SOLO delivery
            if planta in ("A6", "42"):
                tw_e = 0
                tw_l = 90 * SCALE
            else:
                tw_e = 0
                tw_l = 1440 * SCALE

            # tiempo servicio SOLO en el último subnodo
            service_k = srv_di if k == len(parts) else 0

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

    # ========== NODO PICKUP ==========
    if pickup > 0:
        name_p = f"{planta}p"

        tw_e = 0
        tw_l = 1440 * SCALE

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
d = [loc.name for loc in m.clients]
print(d)

#--------------------------------------------  
# ====== Edges ======
names = coords["Nombre"].astype(str).tolist()
dist.index = names
dist.columns = names
time.index = names
time.columns = names

for frm_node in list(locations.keys()):
    for to_node in list(locations.keys()):
        frm_orig = original_of.get(frm_node, frm_node)
        to_orig = original_of.get(to_node, to_node)
        if frm_orig in dist.index and to_orig in dist.columns:
            m.add_edge(
                frm=locations[frm_node],
                to=locations[to_node],
                distance=int(dist.loc[frm_orig, to_orig]),
                duration=int(time.loc[frm_orig, to_orig]),
            )

# print([e.duration for e in m._edges[:20]])

#--------------------------------------------  

res = m.solve(MaxRuntime(240))#NoImprovement(9999))
print(res.best)

solution = res.best

#--------------------------------------------  
problem = m.data()
#exportar en .pkl
with open("3.3- ProblemData.pkl", "wb") as f:
    pickle.dump(problem, f)
#--------------------------------------------  

# id -> nombre (m.locations incluye depots + todos los clientes duplicados)
id_to_name = {idx: loc.name for idx, loc in enumerate(m.locations)}
print("\n======= RUTAS SOLUCIÓN =======")
for i, route in enumerate(solution.routes(), start=1):
    veh_type = m.vehicle_types[route.vehicle_type()]
    veh_name = veh_type.name
    start_depot = id_to_name[veh_type.start_depot]
    end_depot = id_to_name[veh_type.end_depot]

    visit_names = [id_to_name[v] for v in route.visits()]

    print(f"\n=== RUTA {i} ===")
    print("Vehículo:", veh_name)
    print("Start depot:", start_depot)
    print("End depot:", end_depot)
    print("Visitas:", " -> ".join(
        [start_depot] + visit_names + [end_depot]
    ))

    print(f"Distancia total: {route.distance()/SCALE:.2f} km")
    print(f"Duración total: {route.duration()/SCALE:.1f} min")
    print("Pickup total:", [p/SCALE for p in route.pickup()])
    print("Delivery total:", [d/SCALE for d in route.delivery()])
    print("Factible:", route.is_feasible())

# mapa
################################
###############################
import folium
from folium import Element
from funciones import cargar_geojson
from funciones import clean_name
mapa = folium.Map(location=[6.1138, -75.3145], zoom_start=11)
for _, row in coords.iterrows():
    folium.Marker(
        location=[float(row["lat"]), float(row["lon"])],
        popup=row["Nombre"],
        tooltip=f"{row['Nombre']}",
        icon=folium.Icon(
            color="blue" if row["Nombre"] in ("CI", "CD") else "green"
        )
    ).add_to(mapa)
info_rutas = []
colores = [
    "#e41a1c", "#377eb8", "#4daf4a", "#984ea3",
    "#ff7f00", "#a65628", "#f781bf", "#999999",
    "#66c2a5", "#fc8d62"
]
for i, route in enumerate(solution.routes(), start=1):
    # Crear capa para esta ruta
    capa_ruta = folium.FeatureGroup(
        name=f"Ruta {i}",       # Esto aparece como checkbox
        show=True               # Mostrar por defecto
    )
    mapa.add_child(capa_ruta)
    color_ruta = colores[(i-1) % len(colores)]
    veh_type = m.vehicle_types[route.vehicle_type()]
    veh_name = veh_type.name
    start_depot = id_to_name[veh_type.start_depot]
    end_depot = id_to_name[veh_type.end_depot] 
    visit_names = [id_to_name[v] for v in route.visits()]
    secuencia = [start_depot] + visit_names + [end_depot]
    for orden, (frm, to) in enumerate(zip(secuencia[:-1], secuencia[1:]), start=1):
        frm_clean = clean_name(frm)
        to_clean = clean_name(to)
        if frm_clean == to_clean:
            continue
        gj = cargar_geojson(frm_clean, to_clean)
        if not gj:
            print(f"⚠ No existe geojson para {frm_clean}→{to_clean} (original: {frm}→{to})")
            continue
        try:
            summary = gj["features"][0]["properties"]["summary"]
            dist_km = summary["distance"] / 1000
            dur_min = summary["duration"] / 60
        except:
            dist_km = dur_min = 0
        popup_html = f"""
        <b>Ruta {i} • Tramo {orden}</b><br>
        {frm} → {to}<br>
        Distancia: {dist_km:.2f} km<br>
        Duración: {dur_min:.1f} min<br>
        """
        # Añadir tramo solo a la capa de esta ruta
        folium.GeoJson(
            gj,
            name=f"{frm}-{to}",
            style_function=lambda x, col=color_ruta: {
                "color": col,
                "weight": 4,
                "opacity": 0.85,
            },
            highlight_function=lambda x: {
                "color": "#00ff00",
                "weight": 7,
                "opacity": 1,
            },
            tooltip=f"{frm} → {to}",
            popup=folium.Popup(popup_html, max_width=350),
        ).add_to(capa_ruta)

folium.LayerControl(collapsed=False).add_to(mapa)
mapa.save("x.html")
