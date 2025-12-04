import openrouteservice as ors
import folium
import pandas as pd
import numpy as np
import json
import os
from funciones import make_avoid_multipolygon

# https://account.heigit.org/ 
client = ors.Client(key='eyJvcmciOiI1YjNjZTM1OTc4NTExMTAwMDFjZjYyNDgiLCJpZCI6ImZkMjY1MjRkODk0YTRjNmVhZGMzOWYyZjUyODcwNTRkIiwiaCI6Im11cm11cjY0In0=')

df = pd.read_csv("1.1-coordenadas.csv")
coords = df[["lon", "lat"]].values.tolist()
# Crear los polígonos
avoid = make_avoid_multipolygon(pd.read_csv("1.2-avoid.csv")[["lat", "lon"]].values.tolist())
n = len(df)
# -----------------------------------------------------------

# Mapa de las rutas en las que se calcula la distancia
m = folium.Map(location=[6.1138, -75.3145], zoom_start=11.3)
for i in range(n):
    folium.Marker(
        location=[df.iloc[i]['lat'], df.iloc[i]['lon']],
        popup=df.iloc[i]['Nombre']
    ).add_to(m)

# Carpeta para guardar los archivos geojson
os.makedirs("rutas_geojson", exist_ok=True)

dist_matrix = np.zeros((n, n))
time_matrix = np.zeros((n, n))

# Calcular las distancias y tiempos entre todos los puntos
for i in range(n):
    for j in range(n):
        if i == j:
            continue
        origen = df.iloc[i]["Nombre"]
        destino = df.iloc[j]["Nombre"]
        origen_id = origen.replace(" ", "_")
        destino_id = destino.replace(" ", "_")
        try:
            # openrouteservice
            route = client.directions(
                coordinates=[coords[i], coords[j]],
                profile="driving-hgv",
                format="geojson",
                preference="recommended",
                language="es",
                instructions=False,
                options={
                    "avoid_polygons": avoid,
                    "profile_params": {
                        "restrictions": {
                            "length": 8,
                            "width": 2.5,
                            "height": 3.5,
                        }
                    },
                },
            )
            summary = route["features"][0]["properties"]["summary"]
            dist_km = summary["distance"] / 1000
            dur_min = summary["duration"] / 60
                        # Texto que aparecerá al pasar sobre una ruta
            popup_html = f"""
            <b>Ruta:</b> {origen} → {destino}<br>
            <b>Distancia:</b> {dist_km:.2f} km<br>
            <b>Duración:</b> {dur_min:.1f} min
            """
            ruta_geojson_path = f"rutas_geojson/ruta_{origen_id}_{destino_id}.geojson"
            # Guardar GeoJSON
            with open(ruta_geojson_path, "w", encoding="utf-8") as f:
                json.dump(route, f, ensure_ascii=False, indent=2)
            fg = folium.FeatureGroup(
                name=f"Ruta {origen} → {destino}",
                show=True
            )
            folium.GeoJson(
                route,
                style_function=lambda feature: {
                    "color": "#ff0000",
                    "weight": 4,
                    "opacity": 0.85
                },
                popup=folium.Popup(popup_html, max_width=400),
                tooltip=f"{origen} → {destino}"
            ).add_to(fg)
            fg.add_to(m)
            # Matrices
            dist_matrix[i][j] = summary["distance"] / 1000  # km
            time_matrix[i][j] = summary["duration"] / 60    # minutos
        except Exception as e:
            print(f"ERROR en ruta {origen} → {destino}: {e}")
            dist_matrix[i][j] = np.inf
            time_matrix[i][j] = np.inf
folium.LayerControl(collapsed=False).add_to(m)
# Guardar archivos
pd.DataFrame(dist_matrix).to_csv("2.1-distancias.csv", index=False, header=False)
pd.DataFrame(time_matrix).to_csv("2.2-tiempos.csv", index=False, header=False)
m.save("2.3-Rutas.html")
