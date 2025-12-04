import pickle
from pyvrp import solve, Model
from pyvrp.stop import FirstFeasible, MaxRuntime
import matplotlib.pyplot as plt
import folium
from folium import Element
from funciones import cargar_geojson
from funciones import clean_name
import pandas as pd
from funciones import agrupar_eventos
import re
#--------------------------------------------
# Modelo
with open('3.3-Modelo.pkl', 'rb') as f:
    m = pickle.load(f)
#--------------------------------------------
# --- Resolver ---
res = m.solve(MaxRuntime(240))
solution = res.best
with open("4.1-Res.pkl", "wb") as f:
    pickle.dump(res, f)
#--------------------------------------------
SCALE = 100
# Mostrar resultado en consola
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
# #--------------------------------------------
# # --- Gráficos ---
mapa = folium.Map(location=[6.1138, -75.3145], zoom_start=11)
for loc in m.clients:
    nombre = clean_name(loc.name)
    folium.Marker(
        location=[loc.y, loc.x],
        popup=nombre,
        tooltip=nombre,
        icon=folium.Icon(color='darkred',icon="location-dot", prefix="fa")
    ).add_to(mapa)
for loc in m.depots:
    nombre = clean_name(loc.name)
    folium.Marker(
        location=[loc.y, loc.x],
        popup=nombre,
        tooltip=nombre,
        icon=folium.Icon(color='darkred',icon="map-pin", prefix="fa")
    ).add_to(mapa)
# Diccionario clientes
original_of = {}
for loc in m.locations:
    name = loc.name
    base = re.sub(r"(d|p)(_?\d+)?$", "", name)
    original_of[name] = base
# print(original_of)
# --- Rutas ---
info_rutas = []
colores = ["#1F77B4", "#2CA02C","#17BECF","#9467BD","#7F7F7F"]
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
    # --- Agrupar visitas --- 
    eventos = agrupar_eventos(visitas_idx, m, original_of, SCALE)
    # secuencia consolidada
    secuencia = [start_depot] + [ev["cliente"] for ev in eventos] + [end_depot]
    # Para tooltips en tramos
    cargas_consolidadas = [ev["carga_despues"] for ev in eventos]
    # --- Información consolidada ---
    detalle = ""
    for ev in eventos:
        detalle += (
            f"<b>{ev['cliente']}</b>: "
            f"↓{ev['entrega']:.2f}  ↑{ev['recogida']:.2f} "
            f"[Actual {ev['carga_despues']:.2f}]<br>"
        )
    texto_panel = f"""
    <b>Ruta {i}</b><br>
    <b>Vehículo:</b> {veh_name}<br>
    <b>Capacidad:</b> {cap_total} m³<br>
    <b>Inicio:</b> {start_depot}<br>
    <b>Fin:</b> {end_depot}<br>
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
    # --- geoJson ---
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
        # extraer distancia y duración
        try:
            summary = gj["features"][0]["properties"]["summary"]
            dist_km = summary["distance"] / 1000
            dur_min = summary["duration"] / 60
        except:
            dist_km = dur_min = 0
        # carga despues de visitar "frm"
        carga_tramo = cargas_consolidadas[k-1] if k > 0 else 0
        if k < len(cargas_consolidadas):
            k += 1
        popup_html = f"""
        <b>Ruta {i} • Tramo {orden}</b><br>
        {frm} → {to}<br>
        <b>Carga veh:</b> {carga_tramo:.2f} m³ / {cap_total} m³<br>
        <b>Distancia:</b> {dist_km:.2f} km<br>
        <b>Duración:</b> {dur_min:.1f} min<br>
        """
        # Estilo de la ruta en el mapa
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
            tooltip=f"{frm} → {to}  |  carga {carga_tramo:.1f} / {cap_total}",
            popup=folium.Popup(popup_html, max_width=350),
        ).add_to(capa_ruta)
# --- Panel lateral ---
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
mapa.save("4.2-Rutas.html")
# #--------------------------------------------

