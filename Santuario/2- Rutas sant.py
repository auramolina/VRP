import pandas as pd
from pyvrp import Model
from pyvrp.stop import FirstFeasible, NoImprovement
import folium
from folium import Element
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from funciones import cargar_geojson

#--------------------------------------------
# Lectura de datos
df = pd.read_csv("Santuario\santuario.csv",header=0)
dist = pd.read_csv("Santuario\santD.csv", header=None, index_col=False)
time = pd.read_csv("Santuario\santT.csv", header=None, index_col=False)

coords = df.drop(['pi','di','total'], axis=1)
dem = df.drop(['n','lon','lat','total'], axis=1)
service = df.drop(['n','pi','di','lon','lat'], axis=1)
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
CI = df[df["planta"] == "CI"].iloc[0]
CD = df[df["planta"] == "CD"].iloc[0]
# add depot
locations["CI"]=m.add_depot(
    x=float(CI["lon"]),
    y=float(CI["lat"]),
    name="CI"
)
locations["CD"]=m.add_depot(
    x=float(CD["lon"]),
    y=float(CD["lat"]),
    name="CD"
)
#--------------------------------------------
# ====== Clients ======
for _, row in coords.iterrows(): 
    planta = str(row["planta"]) 
    if planta in [loc.name for loc in m.depots]: 
        continue 
    d = dem[dem["planta"] == planta] 
    s = service[service["planta"] == planta] 
    service_time = int(s.iloc[0]["total"]* SCALE)  if not s.empty else 0 
    if not d.empty: 
        # Descarga
        delivery = int(d.iloc[0]["di"] * SCALE )
        # Carga
        pickup = int(d.iloc[0]["pi"] * SCALE )
    else: 
        delivery = pickup = 0
    # Ventanas de tiempo
    if planta in ("A6", "42"):
        tw_early = 0
        tw_late = 90 * SCALE 
    else:
        tw_early = 0
        tw_late = 1440 * SCALE
    # add client
    locations[planta] = m.add_client( 
        x=float(row["lon"]), 
        y=float(row["lat"]), 
        delivery=[delivery] if delivery > 0 else [], 
        pickup=[pickup] if pickup > 0 else [],
        service_duration=service_time,
        tw_early=tw_early,
        tw_late=tw_late,
        required=True,
        name=planta,
        )
#--------------------------------------------  
# ====== Edges ======
names = coords["planta"].astype(str).tolist()
dist.index = names
dist.columns = names
time.index = names
time.columns = names
# add edges
for frm in dist.index:
    for to in dist.columns:
        if frm in locations and to in locations:
            m.add_edge(
                frm=locations[frm],
                to=locations[to],
                distance=int(dist.loc[frm, to]),
                duration=int(time.loc[frm, to]), 
            )
#--------------------------------------------  
# ====== Vehicles ======
#Capacidades
VEH_CAPS = {
    "STE138": 35.5,
    "WCP677": 35.5,
    "WCP384": 23.0,
    "PUN354": 18.9,
    "JYO449": 29.25,  
}
# add vehicle
for name, cap in VEH_CAPS.items():
    m.add_vehicle_type(
        capacity=[cap*SCALE],
        num_available=1,
        start_depot=locations["CI"],
        end_depot=locations["CD"],
        shift_duration=10*60*SCALE,
        unit_distance_cost=1,  
        unit_duration_cost=1,
        max_overtime=3*60*SCALE,
        unit_overtime_cost=100000,
        name=name,
    )
#--------------------------------------------  
# ====== Solve ======
res = m.solve(stop=NoImprovement(9999))#FirstFeasible())#
solution = res.best
# Imprimir resultado
id_to_name = {idx: loc.name for idx, loc in enumerate(m.locations)}
for i, route in enumerate(solution.routes(), start=1):
    veh_type = m.vehicle_types[route.vehicle_type()]
    veh_name = veh_type.name
    start_depot = id_to_name[veh_type.start_depot]
    end_depot = id_to_name[veh_type.end_depot]
    visit_names = [id_to_name[v] for v in route.visits()]
    print(f"Ruta {i}")
    print(" Vehículo:", veh_name)
    print(" Start depot:", start_depot)
    print(" End depot:", end_depot)
    print(" Visitas:", " -> ".join([start_depot] + visit_names + [end_depot]))
    print(" Distancia:", route.distance() / SCALE, "km")
    print(" Duración:", route.duration() / SCALE, "min")
    print(" Entregas:", [d / SCALE for d in route.delivery()])
    print(" Recogidas:", [p / SCALE for p in route.pickup()])
    print(" ¿Factible?:", route.is_feasible())
    print("-" * 40)
# ====== Mapa ====== 
mapa = folium.Map(location=[6.1138, -75.3145], zoom_start=11)
# Marcar puntos
for _, row in coords.iterrows():
    folium.Marker(
        location=[float(row["lat"]), float(row["lon"])],
        popup=row["planta"],
        tooltip=f"{row["planta"]}: {row["n"]}",
        icon=folium.Icon(color="blue" if row["planta"] in ("CI","CD") else "green")
    ).add_to(mapa)
info_rutas = []
for i, route in enumerate(solution.routes(), start=1):
    veh_type = m.vehicle_types[route.vehicle_type()]
    veh_name = veh_type.name
    start_depot = id_to_name[veh_type.start_depot]
    end_depot = id_to_name[veh_type.end_depot]
    visit_names = [id_to_name[v] for v in route.visits()]
    texto = f"""
    <b>Ruta {i}</b><br>
    <b>Vehículo:</b> {veh_name}<br>
    <b>Visitas:</b> {" → ".join([start_depot] + visit_names + [end_depot])}<br>
    <b>Distancia total:</b> {route.distance()/SCALE:.2f} km<br>
    <b>Duración total:</b> {route.duration()/SCALE:.1f} min<br>
    <b>Entregas:</b> {[d/SCALE for d in route.delivery()]}<br>
    <b>Recogidas:</b> {[p/SCALE for p in route.pickup()]}<br>
    <b>Factible:</b> {route.is_feasible()}<br>
    <hr>
    """
    info_rutas.append(texto)
for i, route in enumerate(solution.routes(), start=1):
    visitas = [id_to_name[v] for v in route.visits()]
    secuencia = ["CI"] + visitas + ["CD"]
    for orden, (frm, to) in enumerate(zip(secuencia[:-1], secuencia[1:]), start=1):
        # Buscar las rutas guardadas
        gj = cargar_geojson(frm, to)
        if not gj:
            print(f"⚠ No existe geojson para tramo {frm}→{to}")
            continue
        # Extraer distancia y duración del GeoJSON
        try:
            summary = gj["features"][0]["properties"]["summary"]
            dist_km = summary["distance"] / 1000
            dur_min = summary["duration"] / 60
        except:
            dist_km = 0
            dur_min = 0
        # Texto al seleccionar ruta
        popup_html = f"""
        <b>Ruta</b><br>
        <b>Tramo:</b> {frm} → {to}<br>
        <b>Orden:</b> {orden}<br>
        <b>Distancia:</b> {dist_km:.2f} km<br>
        <b>Duración:</b> {dur_min:.1f} min<br>
        """
        folium.GeoJson(
            gj,
            name=f"Ruta {i}: {frm}-{to}",
            style_function=lambda x, col="#ff0000": {
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
        ).add_to(mapa)
# Cuadro de información
contenido = "".join(info_rutas)
panel_html = f"""
<div id="panel-rutas" style="
    position: fixed;
    bottom: 20px;
    right: 20px;
    width: 300px;
    height: 290px;
    overflow-y: auto;
    z-index: 999999;
    font-size: 14px;
    background-color: rgba(255,255,255,0.95);
    padding: 10px;
    border: 2px solid gray;
    border-radius: 8px;
    box-shadow: 2px 2px 6px rgba(0,0,0,0.3);
">
<b>Resumen de rutas</b><br><br>
{contenido}
</div>
"""
mapa.get_root().html.add_child(Element(panel_html))
mapa.save("Santuario/Santuario f.html")