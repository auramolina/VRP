import pandas as pd
import openrouteservice as ors
import numpy as np
import sys, os
BASE_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_PATH)
from funciones import make_avoid_multipolygon

df = pd.read_csv("Santuario/santuario.csv", header=0)
print(df)

#API https://account.heigit.org/
client = ors.Client(key='eyJvcmciOiI1YjNjZTM1OTc4NTExMTAwMDFjZjYyNDgiLCJpZCI6ImZkMjY1MjRkODk0YTRjNmVhZGMzOWYyZjUyODcwNTRkIiwiaCI6Im11cm11cjY0In0=')

n = len(df)
dist_matrix = np.zeros((n, n))
time_matrix = np.zeros((n, n))

# Áreas a excluir
avoid = make_avoid_multipolygon(pd.read_csv("avoid.csv")[["lat", "lon"]].values.tolist())

# ORS requiere lon,lat
c = df[["lon","lat"]].values.tolist()
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
                                "height": 3.5,
                            }   
                        }
                    }
                )
                summary = route["features"][0]["properties"]["summary"]
                dist_matrix[i][j] = summary["distance"] / 1000  # km
                time_matrix[i][j] = summary["duration"] / 60    # minutos

            except Exception as e:
                print(f"Error con ruta {i}-{j}: {e}")
                dist_matrix[i][j] = np.inf
                time_matrix[i][j] = np.inf

pd.DataFrame(dist_matrix).to_csv("Santuario/santD.csv", index=False, header=False)
pd.DataFrame(time_matrix).to_csv("Santuario/santT.csv", index=False, header=False)
