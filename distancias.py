import openrouteservice as ors
import folium
import pandas as pd
import numpy as np


client = ors.Client(key='eyJvcmciOiI1YjNjZTM1OTc4NTExMTAwMDFjZjYyNDgiLCJpZCI6ImZkMjY1MjRkODk0YTRjNmVhZGMzOWYyZjUyODcwNTRkIiwiaCI6Im11cm11cjY0In0=')

# .csv de coordenadas
# df = pd.read_csv("coordenadas.csv")
df = pd.read_csv("Oriente.csv")
df["lon"] = df["WKT"].apply(lambda x: float(x.split("(")[1].split(" ")[0]))
df["lat"] = df["WKT"].apply(lambda x: float(x.split("(")[1].split(" ")[1].replace(")", "")))
c = df[["lon", "lat"]].values.tolist()

# marcar los puntos en el mapa
m = folium.Map(location=[6.1138, -75.3145], zoom_start=11.3)
for marker in c: 
    folium.Marker(location=list(reversed(marker))).add_to(m)
m.save("puntos.html")

# Crear matrices vacías
n = len(c)
dist_matrix = np.zeros((n, n))
time_matrix = np.zeros((n, n))

def make_avoid_multipolygon(coords, delta=0.001):
    polygons = []
    for lat, lon in coords:
        poly = [[
            [lon - delta, lat - delta],  # SW
            [lon + delta, lat - delta],  # SE
            [lon + delta, lat + delta],  # NE
            [lon - delta, lat + delta],  # NW
            [lon - delta, lat - delta]   # cerrar
        ]]
        polygons.append(poly)
    return {
        "type": "MultiPolygon",
        "coordinates": polygons
    }

avoid = make_avoid_multipolygon([
    (6.140008, -75.518717),
    (6.206873629439695, -75.49034195030447),
    (6.163199, -75.545402),
    (6.094078, -75.498953),
    (6.169535, -75.479657),
    (6.208166, -75.496001),
    (6.168811, -75.484768),
    (6.163921, -75.501829),
    (6.188954, -75.465796)
], delta=0.001)

for i in range(n):
    for j in range(n):
        if i != j:
            try:
                route = client.directions(
                    coordinates=[c[i], c[j]],
                    profile="driving-hgv",
                    format="geojson",
                    preference="recommended",
                    options={
                        "avoid_polygons": avoid,
                        "profile_params": {
                            "restrictions": {
                                "length": 8,
                                "width": 2.5,
                                "height": 2.5,
                                #"axleload": 4,
                                #"weight": 5,
                            }
                        }
                    }
                )

                # Dibujar en mapa
                folium.GeoJson(
                    route,
                    name=f"Ruta {i}-{j}",
                    style_function=lambda x: {"color": "blue", "weight": 5, "opacity": 0.2},
                ).add_to(m)

                # Extraer distancia y duración
                summary = route["features"][0]["properties"]["summary"]
                dist_matrix[i][j] = summary["distance"] / 1000  # km
                time_matrix[i][j] = summary["duration"] / 60    # minutos

            except Exception as e:
                print(f"Error con ruta {i}-{j}: {e}")
                dist_matrix[i][j] = np.inf
                time_matrix[i][j] = np.inf

# Guardar mapa
m.save("rutas(distancia).html")
pd.DataFrame(dist_matrix).to_csv("distancias.csv", index=False, header=False)
pd.DataFrame(time_matrix).to_csv("tiempos.csv", index=False, header=False)