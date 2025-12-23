import pandas as pd
import pickle
from pyvrp import Model
from pyvrp.stop import MaxRuntime
import folium
from folium import Element
import re
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from funciones import split_FF2S, cargar_geojson, clean_name, agrupar_eventos
#--------------------------------------------
coords = pd.read_csv("1.1-coordenadas.csv")
dist = pd.read_csv("2.1-distancias.csv", header=None, index_col=False)
time = pd.read_csv("2.2-tiempos.csv", header=None, index_col=False)
dem = pd.read_csv("demanda.csv") 
service = pd.read_csv("service.csv")
#--------------------------------------------
E2 = Model()
locations2 = {}
#--------------------------------------------
SCALE = 100
dist = round(dist*SCALE)
time = round(time*SCALE)
#--------------------------------------------
# ====== Depots ======
CI = coords[coords["Nombre"] == "CI"].iloc[0]
CD = coords[coords["Nombre"] == "CD"].iloc[0]
locations2["CI"]=E2.add_depot(
    x=float(CI["lon"]),
    y=float(CI["lat"]),
    name=CI["Nombre"]
)
locations2["CD"]=E2.add_depot(
    x=float(CD["lon"]),
    y=float(CD["lat"]),
    name=CD["Nombre"]
)
#--------------------------------------------  
# ====== Vehicles ======
VEH_CAPS = {
    "STE138": 35.5,
    "WCP677": 35.5,
    "WCP384": 23,
    "PUN354": 19.8,
    "JYO449": 29.25,  
}
for name, cap in VEH_CAPS.items():
    E2.add_vehicle_type(
        capacity=[cap*SCALE],
        num_available=1,
        start_depot=locations2["CI"],
        end_depot=locations2["CD"],
        shift_duration=10*60*SCALE,
        unit_distance_cost=1,  
        unit_duration_cost=1,
        max_overtime=3*60*SCALE,
        unit_overtime_cost=100000,
        name=name,
    )
#--------------------------------------------
# ====== Clientes ======
original_of = {}
for _, row in coords.iterrows():
    planta = str(row["Nombre"])
    if planta in [loc.name for loc in E2.depots]:
        continue    
    d = dem[dem["planta"] == planta]
    s = service[service["planta"] == planta]
    if not d.empty:
        delivery = int(d.iloc[0]["di"] * SCALE)
        pickup   = int(d.iloc[0]["pi"] * SCALE)
    else:
        delivery = pickup = 0
    srv_pi = int(s.iloc[0]["pi"] * SCALE) if not s.empty else 0
    srv_di = int(s.iloc[0]["di"] * SCALE) if not s.empty else 0
    if delivery > 0:
        MAX_CAP = max(VEH_CAPS.values()) * SCALE 
        if delivery > 0.7 * MAX_CAP:
            parts = split_FF2S(delivery)
        else:
            parts = [delivery]   
        for k, part in enumerate(parts, start=1):
            name_d = f"{planta}d_{k}" if len(parts) > 1 else f"{planta}d"
            if planta in ("A6", "42"): 
                tw_e = 0
                tw_l = 90 * SCALE
            else:
                tw_e = 0
                tw_l = 1440 * SCALE
            service_k = srv_di if k == len(parts) else 0
            locations2[name_d] = E2.add_client(
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
    if pickup > 0:
        name_p = f"{planta}p"
        tw_e = 0
        tw_l = 1440 * SCALE
        locations2[name_p] = E2.add_client(
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
#--------------------------------------------  
# ====== Edges ======
names = coords["Nombre"].astype(str).tolist()
dist.index = names
dist.columns = names
time.index = names
time.columns = names
for frm_node in list(locations2.keys()):
    for to_node in list(locations2.keys()):
        frm_orig = original_of.get(frm_node, frm_node)
        to_orig = original_of.get(to_node, to_node)
        if frm_orig in dist.index and to_orig in dist.columns:
            E2.add_edge(
                frm=locations2[frm_node],
                to=locations2[to_node],
                distance=int(dist.loc[frm_orig, to_orig]),
                duration=int(time.loc[frm_orig, to_orig]),
            )
#--------------------------------------------  
# Guardar instancia
# with open("Escenarios/Escenario_2.pkl", "wb") as f:
#     pickle.dump(E2, f)
#--------------------------------------------  
# ====== Solución ======
res = E2.solve(MaxRuntime(300))
print(res.best)
solution = res.best
with open("Escenarios/Res2.pkl", "wb") as f:
    pickle.dump(res, f)
#--------------------------------------------  
# ====== Mapa Rutas ======
m = E2
id_to_name = {idx: loc.name for idx, loc in enumerate(m.locations)}
mapa = folium.Map(location=[6.1138, -75.3145], zoom_start=11)
for loc in m.clients:
    nombre = clean_name(loc.name)
    folium.Marker(
        location=[loc.y, loc.x],
        popup=nombre,
        tooltip=nombre,
        icon=folium.Icon(color='red',icon="location-dot", prefix="fa")
    ).add_to(mapa)
for loc in m.depots:
    nombre = clean_name(loc.name)
    folium.Marker(
        location=[loc.y, loc.x],
        popup=nombre,
        tooltip=nombre,
        icon=folium.Icon(color='red',icon="map-pin", prefix="fa")
    ).add_to(mapa)
original_of = {}
for loc in m.locations:
    name = loc.name
    base = re.sub(r"(d|p)(_?\d+)?$", "", name)
    original_of[name] = base
info_rutas = []
colores = ["#e41a1c", "#377eb8", "#4daf4a", "#984ea3","#ff7f00"]
for i, route in enumerate(solution.routes(), start=1):
    capa_ruta = folium.FeatureGroup(name=f"Ruta {i}", show=True)
    mapa.add_child(capa_ruta)
    color_ruta = colores[(i-1) % len(colores)]
    veh_type = m.vehicle_types[route.vehicle_type()]
    veh_name = veh_type.name
    cap_total = veh_type.capacity[0] / SCALE
    start_depot = id_to_name[veh_type.start_depot]
    end_depot   = id_to_name[veh_type.end_depot]
    visitas_idx = list(route.visits())
    visit_names = [id_to_name[v] for v in visitas_idx]
    eventos = agrupar_eventos(visitas_idx, m, original_of, SCALE)
    secuencia = [start_depot] + [ev["cliente"] for ev in eventos] + [end_depot]
    cargas_consolidadas = [ev["carga_despues"] for ev in eventos]
    detalle = ""
    for ev in eventos:
        detalle += (
            f"<b>{ev['cliente']}</b> : "
            f"↓{ev['entrega']:.2f}  ↑{ev['recogida']:.2f}   "
        )
    texto_panel = f"""
    <b>Ruta {i}</b><br>
    <b>Vehículo:</b> {veh_name}<br>
    <b>Capacidad:</b> {cap_total} m³<br>
    <b>Visitas:</b> {" → ".join(secuencia)}<br>
    <b>Detalle por cliente:</b><br>
    {detalle}<br>
    <b>Distancia total:</b> {route.distance()/SCALE:.2f} km<br>
    <b>Duración total:</b> {route.duration()/SCALE:.1f} min<br>
    <b>Carga máxima:</b> {max(cargas_consolidadas):.2f} m³<br>
    <b>Pickup total:</b> {[p/SCALE for p in route.pickup()]}<br>
    <b>Delivery total:</b> {[d/SCALE for d in route.delivery()]}<br>
    <hr>
    """
    info_rutas.append(texto_panel)
    k = 0  
    for orden, (frm, to) in enumerate(zip(secuencia[:-1], secuencia[1:]), start=1):
        frm_clean = clean_name(frm)
        to_clean  = clean_name(to)
        if frm_clean == to_clean:
            continue
        gj = cargar_geojson(frm_clean, to_clean)
        if not gj:
            print(f"No existe geojson para {frm_clean}→{to_clean} (original: {frm}→{to})")
            continue
        try:
            summary = gj["features"][0]["properties"]["summary"]
            dist_km = summary["distance"] / 1000
            dur_min = summary["duration"] / 60
        except:
            dist_km = dur_min = 0
        carga_tramo = cargas_consolidadas[k-1] if k > 0 else 0
        if k < len(cargas_consolidadas):
            k += 1
        popup_html = f"""
        <b>Ruta {i} • Tramo {orden}</b><br>
        {frm} → {to}<br>
        <b>Ocupación:</b> {round((carga_tramo / cap_total),2)*100} %<br>
        <b>Distancia:</b> {dist_km:.2f} km<br>
        <b>Duración:</b> {dur_min:.1f} min<br>
        """
        folium.GeoJson(
            gj,
            name=f"{frm}-{to}",
            style_function=lambda x, col=color_ruta: {
                "color": col,
                "weight": 4,
                "opacity": 0.85,
            },
            highlight_function=lambda x: {
                "color": "#ADFF2F",
                "weight": 7,
                "opacity": 1,
            },
            tooltip=f"{frm} → {to}  |  carga {carga_tramo:.1f}m³ / {cap_total}m³",
            popup=folium.Popup(popup_html, max_width=350),
        ).add_to(capa_ruta)
contenido = "".join(info_rutas)
panel_html = f"""
<div id="panel-rutas" style="
    position: fixed;
    bottom: 20px;
    right: 20px;
    width: 330px;
    height: 300px;
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
folium.LayerControl(collapsed=False).add_to(mapa)
mapa.save("Escenarios/E2.html")
#--------------------------------------------  
