import pandas as pd
import json
import os
import re
# ---------------------------------------------------------------------------------------
# --- Preprocesado de archivos ---
def procesar_wkt_csv(nombre_archivo_entrada, nombre_archivo_salida):
    """
    .csv exportado de https://www.google.com/maps/d/u/0/edit?mid=1cgAPynNC_zaen6XlQyrnb6DJDkCcNQM&usp=sharing
    Lee un CSV con una columna 'WKT' tipo 'POINT(lon lat)'
    y genera un nuevo CSV con columnas separadas 'lon' y 'lat'.

    Args:
        nombre_archivo_entrada (str): Ruta del CSV original (con columna WKT)
        nombre_archivo_salida (str): Ruta del nuevo CSV con lon | lat
    """
    df = pd.read_csv(nombre_archivo_entrada)

    # Extraer coordenadas de la columna WKT
    df["lon"] = df["WKT"].apply(lambda x: float(x.split("(")[1].split(" ")[0]))
    df["lat"] = df["WKT"].apply(lambda x: float(x.split("(")[1].split(" ")[1].replace(")", "")))

    # Eliminar la columna original WKT
    df = df.drop(columns="WKT")

    # Guardar como nuevo archivo CSV
    df.to_csv(nombre_archivo_salida, index=False, encoding="utf-8-sig")

    return df
# ---------------------------------------------------------------------------------------
# --- Definir los polígonos para el cálculo de distancias ---
def make_avoid_multipolygon(coords, delta=0.001):
    """
    puntos (coordenadas a evitar): para que calcule la distancia entre puntos 
    evitando rutas como santa elena, el túnel, ...
    """
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
# ---------------------------------------------------------------------------------------
# --- Cargar archivos GeoJSON ---
def cargar_geojson(frm, to):
    ruta = f"rutas_geojson/ruta_{frm}_{to}.geojson"
    if os.path.exists(ruta):
        with open(ruta, encoding="utf-8") as f:
            return json.load(f)
    else:
        return None
# ---------------------------------------------------------------------------------------
# --- Quitar sufijos a los nombres de los clientes del ProblemData ---
def clean_name(name: str):
    """
    Quita sufijos 'd', 'p' o 'd_i', 'p_i' para buscar geojson con nombres limpios.
    Ejemplos:
        '42d_3' → '42'
        '42p'   → '42'
        'A4d'   → 'A4'
        'B7p'   → 'B7'
    """
    # 1) Quitar sufijos tipo d_1, d_2, d_15...
    m = re.match(r"^(.*?)[dp]_\d+$", name)
    if m:
        return m.group(1)

    # 2) Quitar sufijos simples: d o p
    m = re.match(r"^(.*?)[dp]$", name)
    if m:
        return m.group(1)

    # 3) Si no coincide ningún patrón, devolver el mismo nombre
    return name
# ---------------------------------------------------------------------------------------
# --- Split delivery ---
def split_FF2S(total_demand):
    """
    Fully-Flexible-2-Splitting (FF2S).
    Retorna una lista de subdemanda que permite cualquier 2-split posible.
    """
    parts = []
    residual = total_demand
    while residual > 0:
        part = (residual + 1) // 2     # ceil(residual / 2)
        parts.append(part)
        residual -= part
    return parts
# ---------------------------------------------------------------------------------------
def agrupar_eventos(visitas_idx, m, original_of, SCALE):
    """
    Une todos los nodos por cliente real (incluye casos como 42d_7, 42p, etc.)
    Y calcula la carga correcta:
        - carga inicial = total_delivery
        - luego resta delivery y suma pickup
    """

    # -----------------------------
    # 1. PRIMER PASO: recolectar entregas/recogidas por cliente
    # -----------------------------
    clientes = {}

    for v in visitas_idx:
        loc = m.locations[v]
        name = loc.name
        orig = original_of.get(name, name)

        entrega = loc.delivery[0] / SCALE if loc.delivery else 0
        recogida = loc.pickup[0] / SCALE if loc.pickup else 0

        if orig not in clientes:
            clientes[orig] = {"entrega": 0, "recogida": 0}

        clientes[orig]["entrega"] += entrega
        clientes[orig]["recogida"] += recogida

    # -----------------------------
    # 2. CARGA INICIAL DEL VEHÍCULO
    # -----------------------------
    carga_inicial = sum(c["entrega"] for c in clientes.values())
    carga = carga_inicial

    # -----------------------------
    # 3. CONSTRUIR EVENTOS EN ORDEN VISITADO
    # -----------------------------
    eventos = []
    vistos = set()

    for v in visitas_idx:
        loc = m.locations[v]
        orig = original_of.get(loc.name, loc.name)

        if orig in vistos:
            continue  # evitar repetir
        vistos.add(orig)

        entrega = clientes[orig]["entrega"]
        recogida = clientes[orig]["recogida"]

        carga_antes = carga
        carga = carga - entrega + recogida
        carga_despues = carga

        eventos.append({
            "cliente": orig,
            "entrega": entrega,
            "recogida": recogida,
            "carga_inicial": carga_inicial,
            "carga_antes": carga_antes,
            "carga_despues": carga_despues,
        })

    return eventos
