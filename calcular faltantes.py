# ruta = [
#     "CI", "A6", "88", "49", "08", "31", "02", "48",
#     "65", "04", "A5", "19", "42", "49", "70", "49", "CD"
# ]

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
from funciones import matrices
import os
import json
# =========================
# CÁLCULO TOTAL DE LA RUTA
# =========================
resultados = {}

for nombre_ruta, nodos in rutas.items():

    dist_total = 0
    time_total = 0
    tramos_faltantes = []

    for i in range(len(nodos) - 1):
        o, d = nodos[i], nodos[i + 1]
        dist, time = matrices(o, d)

        if dist is None:
            tramos_faltantes.append((o, d))
            continue

        dist_total += dist
        time_total += time

    resultados[nombre_ruta] = {
        "distancia_total": dist_total,
        "tiempo_total": time_total,
        "faltantes": tramos_faltantes
    }

# =========================
# REPORTE EN CONSOLA
# =========================
for ruta, res in resultados.items():
    print(f"\nRUTA: {ruta}")
    print(f"Distancia total: {res['distancia_total']:.2f}")
    print(f"Tiempo total: {res['tiempo_total']:.2f}")

    if res["faltantes"]:
        print("⚠ Tramos sin GeoJSON:")
        for o, d in res["faltantes"]:
            print(f"  - {o} → {d}")