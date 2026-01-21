import pandas as pd
import folium
import json
import os

# df = pd.read_csv(
#     "datos.csv",
#     sep=";",
#     encoding="latin1",
#     low_memory=False
# )

# df["Fecha"] = pd.to_datetime(df["Fecha"],dayfirst=True)
# import re

# df["Hora Llegada"] = (
#     df["Hora Llegada"]
#     .str.lower()
#     .str.replace(r"[^0-9apm:\s]", "", regex=True)  # elimina ÿ, puntos raros, etc.
#     .str.replace(r"\ba\s*m\b", "AM", regex=True)
#     .str.replace(r"\bp\s*m\b", "PM", regex=True)
#     .str.strip()
# )

# df["Hora Llegada"] = pd.to_datetime(
#     df["Hora Llegada"],
#     format="%I:%M:%S %p"
# )
# df["Hora Salida"] = pd.to_datetime(
#     df["Hora Salida"],
#     format="%H:%M:%S"
# )
# df = df.dropna()

# df = df.sort_values(["Vehiculo", "Fecha", "Hora Llegada"])
# # print(df)

# df["Orden"] = (
#     df.groupby(["Ruta", "Vehiculo", "Fecha"])
#       .cumcount() + 1
# )
# df["Orden"] = df["Orden"].astype("Int64")

# secuencias = (
#     df.sort_values(["Ruta", "Vehiculo", "Fecha", "Hora Llegada"])
#       .groupby(["Ruta", "Vehiculo", "Fecha"])["Planta"]
#       .apply(list)
#       .reset_index(name="Secuencia")
# )

# secuencia_tipica = (
#     secuencias
#     .groupby(["Ruta", "Vehiculo"])["Secuencia"]
#     .agg(lambda x: x.value_counts().idxmax())
#     .reset_index(name="Secuencia_Tipica")
# )

# comparacion = secuencias.merge(
#     secuencia_tipica,
#     on=["Ruta", "Vehiculo"],
#     how="left"
# )

# comparacion["Coincide"] = (
#     comparacion["Secuencia"] == comparacion["Secuencia_Tipica"]
# )

# variabilidad = (
#     comparacion
#     .groupby(["Ruta", "Vehiculo"])["Coincide"]
#     .agg(
#         Total_Dias="count",
#         Dias_Correctos="sum"
#     )
# )

# variabilidad["Porc_Correcto"] = (
#     variabilidad["Dias_Correctos"] / variabilidad["Total_Dias"]
# )

# variabilidad = variabilidad.sort_values("Porc_Correcto")
# # print(variabilidad)


# variabilidad["Nivel"] = pd.cut(
#     variabilidad["Porc_Correcto"],
#     bins=[0, 0.3, 0.6, 0.9, 1.01],
#     labels=["Muy variable", "Variable", "Semi-estable", "Estable"]
# )

# variabilidad.sort_values("Porc_Correcto")

# seq_long = (
#     secuencias
#     .explode("Secuencia")
#     .rename(columns={"Secuencia": "Planta"})
# )

# seq_long["Posicion"] = (
#     seq_long
#     .groupby(["Ruta", "Vehiculo", "Fecha"])
#     .cumcount() + 1
# )
# # print(seq_long)

# secuencia_representativa = (
#     secuencias
#     .groupby(["Ruta", "Vehiculo"])["Secuencia"]
#     .agg(lambda x: x.value_counts().idxmax())
#     .reset_index()
# )

# # print(secuencia_representativa)


# secuencia_por_ruta = (
#     secuencias
#     .groupby("Ruta")["Secuencia"]
#     .agg(lambda x: x.value_counts().idxmax())
#     .reset_index(name="Secuencia_Representativa")
# )

# secuencia_por_ruta
# secuencia_por_ruta["Secuencia_str"] = (
#     secuencia_por_ruta["Secuencia_Representativa"]
#     .apply(lambda x: " → ".join(x))
# )

# secuencia_por_ruta[["Ruta", "Secuencia_str"]]
# # 
# # print(secuencia_por_ruta)

# # for _, row in secuencia_por_ruta.iterrows():
# #     print(f"Ruta {row['Ruta']}:")
# #     for i, planta in enumerate(row["Secuencia_Representativa"], 1):
# #         print(f"  {i}. {planta}")
# #     print()

# clientes_por_ruta = (
#     df.groupby("Ruta")["Planta"]
#       .apply(set)
#       .reset_index(name="Clientes_Ruta")
# )
# secuencias_full = secuencias.merge(
#     clientes_por_ruta,
#     on="Ruta",
#     how="left"
# )

# secuencias_full["Completa"] = secuencias_full.apply(
#     lambda r: set(r["Secuencia"]) == r["Clientes_Ruta"],
#     axis=1
# )
# secuencias_completas = secuencias_full[
#     secuencias_full["Completa"]
# ]
# secuencia_completa_por_ruta = (
#     secuencias_completas
#     .groupby("Ruta")["Secuencia"]
#     .agg(lambda x: x.value_counts().idxmax())
#     .reset_index(name="Secuencia_Representativa")
# )
# rutas_sin_completa = (
#     clientes_por_ruta[~clientes_por_ruta["Ruta"].isin(
#         secuencia_completa_por_ruta["Ruta"]
#     )]
# )

# rutas_sin_completa
# secuencia_completa_por_ruta["Secuencia_str"] = (
#     secuencia_completa_por_ruta["Secuencia_Representativa"]
#     .apply(lambda x: " → ".join(x))
# )

# rutas_sin_completa = clientes_por_ruta[
#     ~clientes_por_ruta["Ruta"].isin(
#         secuencia_completa_por_ruta["Ruta"]
#     )
# ]["Ruta"]
# secuencias_sin_completa = secuencias[
#     secuencias["Ruta"].isin(rutas_sin_completa)
# ]
# for ruta in rutas_sin_completa:
#     print(f"\nRuta {ruta} (sin secuencia completa):")

#     dias = secuencias_sin_completa[
#         secuencias_sin_completa["Ruta"] == ruta
#     ]

#     for _, row in dias.iterrows():
#         print(f"  Fecha {row['Fecha']}:")
#         for i, planta in enumerate(row["Secuencia"], 1):
#             print(f"    {i}. {planta}")


# # print(rutas_sin_completa)
# duracion_diaria = (
#     df.groupby(["Ruta", "Fecha"])
#       .agg(
#           Inicio=("Hora Llegada", "min"),
#           Fin=("Hora Llegada", "max")
#       )
#       .reset_index()
# )

# duracion_diaria["Duracion_Min"] = (
#     duracion_diaria["Fin"] - duracion_diaria["Inicio"]
# ).dt.total_seconds() / 60

# tiempo_promedio_ruta = (
#     duracion_diaria
#     .groupby("Ruta")["Duracion_Min"]
#     .agg(
#         Promedio_Min="mean",
#         Mediana_Min="median",
#         Minimo="min",
#         Maximo="max",
#         Dias="count"
#     )
#     .sort_values("Promedio_Min", ascending=False)
# )

# print(tiempo_promedio_ruta)



















# df = pd.read_csv("1.1-coordenadas.csv")
# coord_dict = {
#     row["Nombre"]: (row["lat"], row["lon"])
#     for _, row in df.iterrows()
# }

# rutas = {
#     "Plantas Propias - Oriente": [
#         "CI", "A6", "69", "36", "42", "RE","CD"
#     ],
#     "Marinilla - Santuario": [
#         "CI", "42", "36", "69",
#         "24",  "B7", "46", "42", "46",
#         "32", "39", "06", "40", "13", "49",
#         "B3", "A4", "56", "D2", "D4",
#         "D7", "RE", "CD"
#     ],
#     "Coopimar - Renacer": [
#         "CI", "42", "RE", "CD"
#     ],
#     "Rionegro - La Ceja - Marinilla": [
#         "CI" "A6", "88", "49", "08", "31",
#         "02", "48", "65", "04", "A5", "19",
#         "42", "49", "70", "49", "CD"
#     ],
#     "Plantas Prym - Oriente": [
#         "CI", "36", "24", "42", "32", "19", "69", "39", "46", "CD"
#     ]
# }

# # =========================
# # 3. CARGAR MÉTRICAS REALES
# # =========================
# edge_metrics = {}

# for file in os.listdir("rutas_geojson"):
#     if not file.endswith(".geojson"):
#         continue

#     name = file.replace("ruta_", "").replace(".geojson", "")
#     origen, destino = name.split("_", 1)
#     origen = origen.replace("_", " ")
#     destino = destino.replace("_", " ")

#     with open(os.path.join("rutas_geojson", file), "r", encoding="utf-8") as f:
#         data = json.load(f)

#     summary = data["features"][0]["properties"]["summary"]

#     edge_metrics[(origen, destino)] = {
#         "dist_km": summary["distance"] / 1000,
#         "time_min": summary["duration"] / 60
#     }

# # =========================
# # 4. MAPA BASE
# # =========================
# m = folium.Map(
#     location=[df["lat"].mean(), df["lon"].mean()],
#     zoom_start=11
#     # tiles="OpenStreetMap"
# )

# # =========================
# # 5. DIBUJAR RUTAS + PUNTOS
# # =========================
# colors = ["red", "blue", "green", "purple", "orange"]

# for (ruta_nombre, nodos), color in zip(rutas.items(), colors):

#     fg = folium.FeatureGroup(name=ruta_nombre, show=False)

#     route_coords = []
#     total_dist = 0
#     total_time = 0

#     for i in range(len(nodos) - 1):
#         o, d = nodos[i], nodos[i + 1]

#         if o in coord_dict and d in coord_dict:
#             route_coords.append(coord_dict[o])

#             if (o, d) in edge_metrics:
#                 total_dist += edge_metrics[(o, d)]["dist_km"]
#                 total_time += edge_metrics[(o, d)]["time_min"]

#     # Último nodo
#     if nodos[-1] in coord_dict:
#         route_coords.append(coord_dict[nodos[-1]])

#     # Línea recta de la ruta
#     popup_html = f"""
#     <b>{ruta_nombre}</b><br>
#     Distancia total (red vial): {total_dist:.2f} km<br>
#     Tiempo total (red vial): {total_time:.1f} min
#     """

#     folium.PolyLine(
#         locations=route_coords,
#         color=color,
#         weight=4,
#         opacity=0.8,
#         popup=popup_html
#     ).add_to(fg)

#     # Puntos SOLO de esta ruta
#     for n in nodos:
#         if n in coord_dict:
#             folium.CircleMarker(
#                 location=coord_dict[n],
#                 radius=4,
#                 color=color,
#                 fill=True,
#                 fill_opacity=1,
#                 popup=n
#             ).add_to(fg)

#     fg.add_to(m)

# # =========================
# # 6. CONTROL Y GUARDADO
# # =========================
# folium.LayerControl(collapsed=False).add_to(m)
# m.save("Rutas_operativas_rectas_metricas_reales.html")



import pandas as pd
import folium

# =========================
# 1. COORDENADAS
# =========================
df = pd.read_csv("1.1-coordenadas.csv")

coord_dict = {
    row["Nombre"]: (row["lat"], row["lon"])
    for _, row in df.iterrows()
}

# =========================
# 2. RUTAS (SECUENCIAS)
# =========================
rutas = {
    "Plantas Propias - Oriente": [
        "CI", "A6", "69", "36", "42", "RE","CD"
    ],
    "Marinilla - Santuario": [
        "CI", "42", "36", "69",
        "24",  "B7", "46", "42", "46",
        "32", "39", "06", "40", "13", "49",
        "B3", "A4", "56", "D2", "D4",
        "D7", "RE", "CD"
    ],
    "Coopimar - Renacer": [
        "CI", "42", "RE", "CD"
    ],
    "Rionegro - La Ceja - Marinilla": [
        "CI", "A6", "88", "49", "08", "31",
        "02", "48", "65", "04", "A5", "19",
        "42", "49", "70", "49", "CD"
    ],
    "Plantas Prym - Oriente": [
        "CI", "36", "24", "42", "32", "19", "69", "39", "46", "CD"
    ]
}

# =========================
# 3. MAPA BASE
# =========================
m = folium.Map(
    location=[df["lat"].mean(), df["lon"].mean()],
    zoom_start=11,
    tiles="OpenStreetMap"
)

# =========================
# 4. DIBUJAR SECUENCIAS
# =========================
colors = ["red", "blue", "green", "purple", "orange"]

for (ruta_nombre, nodos), color in zip(rutas.items(), colors):

    fg = folium.FeatureGroup(name=ruta_nombre, show=False)

    # Coordenadas en orden
    route_coords = [
        coord_dict[n] for n in nodos if n in coord_dict
    ]

    # Línea recta
    folium.PolyLine(
        locations=route_coords,
        color=color,
        weight=4,
        opacity=0.8
    ).add_to(fg)

    # Puntos de la ruta
    for n in nodos:
        if n in coord_dict:
            folium.CircleMarker(
                location=coord_dict[n],
                radius=4,
                color=color,
                fill=True,
                fill_opacity=1,
                popup=n
            ).add_to(fg)

    fg.add_to(m)

# =========================
# 5. CONTROL Y GUARDADO
# =========================
folium.LayerControl(collapsed=False).add_to(m)
m.save("Secuencias_rectas_folium.html")
