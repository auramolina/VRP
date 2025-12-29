import pandas as pd
import openrouteservice as ors
import numpy as np
import sys, os
import folium
from folium import Element
from pyvrp import Model
from pyvrp.stop import MaxRuntime
import pickle
BASE_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_PATH)
from funciones import *
#--------------------------------------------  
# procesar_wkt_csv("Medellín/Oriente- Medellín.csv", "Medellín/med.csv")
# --------------------------------------------  
# client = ors.Client(key='eyJvcmciOiI1YjNjZTM1OTc4NTExMTAwMDFjZjYyNDgiLCJpZCI6ImZkMjY1MjRkODk0YTRjNmVhZGMzOWYyZjUyODcwNTRkIiwiaCI6Im11cm11cjY0In0=')
# df = pd.read_csv("Medellín/med.csv")
# coords = df[["lon", "lat"]].values.tolist()
# n = len(df)
# m = folium.Map(location=[6.1138, -75.3145], zoom_start=11.3)
# for i in range(n):
#     folium.Marker(
#         location=[df.iloc[i]['lat'], df.iloc[i]['lon']],
#         popup=df.iloc[i]['name']
#     ).add_to(m)
# dist_matrix = np.zeros((n, n))
# time_matrix = np.zeros((n, n))
# for i in range(n):
#     for j in range(n):
#         if i == j:
#             continue
#         origen = str(df.iloc[i]["name"]).strip()
#         destino = str(df.iloc[j]["name"]).strip()
#         if origen.lower() == "nan": 
#             origen = f"{i}"
#         if destino.lower() == "nan":
#             destino = f"{j}"
#         origen_id = origen.replace(" ", "_")
#         destino_id = destino.replace(" ", "_")
#         try:
#             route = client.directions(
#                 coordinates=[coords[i], coords[j]],
#                 profile="driving-hgv",
#                 format="geojson",
#                 preference="recommended",
#                 language="es",
#                 instructions=False,
#                 # options={
#                 #     "profile_params": {
#                 #         "restrictions": {
#                 #             "length": 5.3,
#                 #             "width": 2.5,
#                 #             "height": 5.4,
#                         # }
#                     # },
#                 # },
#             )
#             summary = route["features"][0]["properties"]["summary"]
#             dist_km = summary["distance"] / 1000
#             dur_min = summary["duration"] / 60
#             popup_html = f"""
#             <b>Ruta:</b> {origen} → {destino}<br>
#             <b>Distancia:</b> {dist_km:.2f} km<br>
#             <b>Duración:</b> {dur_min:.1f} min
#             """
#             ruta_geojson_path = f"rutas_geojson/ruta_{origen_id}_{destino_id}.geojson"
#             with open(ruta_geojson_path, "w", encoding="utf-8") as f:
#                 json.dump(route, f, ensure_ascii=False, indent=2)
#             fg = folium.FeatureGroup(
#                 name=f"Ruta {origen} → {destino}",
#                 show=True
#             )
#             folium.GeoJson(
#                 route,
#                 style_function=lambda feature: {
#                     "color": "#ff0000",
#                     "weight": 4,
#                     "opacity": 0.85
#                 },
#                 popup=folium.Popup(popup_html, max_width=400),
#                 tooltip=f"{origen} → {destino}"
#             ).add_to(fg)
#             fg.add_to(m)
#             # Matrices
#             dist_matrix[i][j] = summary["distance"] / 1000  # km
#             time_matrix[i][j] = summary["duration"] / 60    # minutos
#         except Exception as e:
#             print(f"ERROR en ruta {origen} → {destino}: {e}")
#             dist_matrix[i][j] = np.inf
#             time_matrix[i][j] = np.inf
# folium.LayerControl(collapsed=False).add_to(m)
# pd.DataFrame(dist_matrix).to_csv("Medellín/distancias.csv", index=False, header=False)
# pd.DataFrame(time_matrix).to_csv("Medellín/tiempos.csv", index=False, header=False)
# m.save("Medellín/Rutas distancias.html")
#-------------------------------------------- 
coords = pd.read_csv("Medellín/med.csv")
dist = pd.read_csv("Medellín/distancias.csv", header=None, index_col=False)
time = pd.read_csv("Medellín/tiempos.csv", header=None, index_col=False)
service = pd.read_csv("Medellín/td.csv")
m = Model()
locations = {}
SCALE = 100
dist = round(dist*SCALE)
time = round(time*SCALE)
A9 = coords[coords["name"] == "A9"].iloc[0]
locations["A9"]=m.add_depot(
    x=float(A9["lon"]),
    y=float(A9["lat"]),
    name=A9["name"]
)
m.add_vehicle_type(
        capacity=[29.256*SCALE],
        num_available=1,
        shift_duration=10*60*SCALE,
        unit_distance_cost=1,  
        unit_duration_cost=1,
        # reload_depots=[locations[""]], ######
        max_overtime=3*60*SCALE,
        unit_overtime_cost=100000,
        name="TLK244",
)
for _, row in coords.iterrows():
    planta = str(row["name"])
    if planta in ("A9"):
        continue
    s = service[service["planta"] == planta]
    service_time = float(s.iloc[0]["total"]) * SCALE if not s.empty else 0
    if not s.empty:
        delivery = float(s.iloc[0]["Volumen"]) * SCALE
    locations[planta] = m.add_client(
        x=float(row["lon"]),
        y=float(row["lat"]),
        delivery=[delivery] if delivery > 0 else [],
        name=planta,
        service_duration=service_time,
        # tw_early=tw_e,
        # tw_late=tw_l
    )
names = coords["name"].astype(str).tolist()
dist.index = names
dist.columns = names
time.index = names
time.columns = names
for frm_node in list(locations.keys()):
    for to_node in list(locations.keys()):
        if frm_node in dist.index and to_node in dist.columns:
            m.add_edge(
                frm=locations[frm_node],
                to=locations[to_node],
                distance=int(dist.loc[frm_node, to_node]),
                duration=int(time.loc[frm_node, to_node]),
            )
# -- --- -- --- --
res = m.solve(MaxRuntime(60))
solution = res.best
print(solution)
with open("Medellín/Res1.pkl", "wb") as f:
    pickle.dump(res, f)
with open("Medellín/M.pkl", "wb") as f:
    pickle.dump(m, f)
#--------------------------------------------  
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
colores = ["#377eb8", "#4daf4a", "#984ea3","#ff7f00"]
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
            f"↓{ev['entrega']:.2f}  "
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
    <b>Delivery total:</b> {[d/SCALE for d in route.delivery()]}<br>
    <hr>
    """
    info_rutas.append(texto_panel)
    k = 0  
    for orden, (frm, to) in enumerate(zip(secuencia[:-1], secuencia[1:]), start=1):
        # frm_clean = clean_name(frm)
        # to_clean  = clean_name(to)
        # if frm_clean == to_clean:
            # continue
        gj = cargar_geojson(frm, to)
        if not gj:
            print(f"No existe geojson para {frm}→{to} (original: {frm}→{to})")
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
mapa.save("Medellín/Ruta2.html")