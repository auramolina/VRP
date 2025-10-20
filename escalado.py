import pandas as pd
from pyvrp import Model
from pyvrp.stop import FirstFeasible
from pyvrp.solve import SolveParams

SCALE = 100  

coords = pd.read_csv("coordenadas.csv")
dist = pd.read_csv("distancias.csv", index_col=0) * SCALE
time = pd.read_csv("tiempos.csv", index_col=0) * SCALE
dem = pd.read_csv("demanda.csv") 
service = pd.read_csv("service.csv", header=None, names=["planta", "service"])

coords["Nombre"] = coords["Nombre"].astype(str).str.strip()
dist.index = dist.index.astype(str).str.strip()
dist.columns = dist.columns.astype(str).str.strip()
time.index = time.index.astype(str).str.strip()
time.columns = time.columns.astype(str).str.strip()
dem["planta"] = dem["planta"].astype(str).str.strip()

m = Model()
locations = {}

depot_row = coords[coords["Nombre"] == "CI"].iloc[0]
locations["CI"] = m.add_depot(
    x=float(depot_row["lon"]),
    y=float(depot_row["lat"]),
    name="CI",
)

depot_row = coords[coords["Nombre"] == "CD"].iloc[0]
locations["CD"] = m.add_depot(
    x=float(depot_row["lon"]),
    y=float(depot_row["lat"]),
    name="CD",
)

for _, row in coords.iterrows():
    planta = str(row["Nombre"])
    if planta in ("CI", "CD"):
        continue

    d = dem[dem["planta"] == planta]
    s = service[service["planta"] == planta]
    service_time = float(s.iloc[0]["service"]) * SCALE if not s.empty else 0

    if not d.empty:
        delivery = float(d.iloc[0]["di"]) * SCALE
        pickup = float(d.iloc[0]["pi"]) * SCALE
    else:
        delivery = pickup = 0.0

    locations[planta] = m.add_client(
        x=float(row["lon"]),
        y=float(row["lat"]),
        delivery=[delivery] if delivery > 0 else [],
        pickup=[pickup] if pickup > 0 else [],
        name=planta,
        service_duration=service_time
    )

for frm in dist.index:
    for to in dist.columns:
        if frm == to:
            continue
        if frm in locations and to in locations:
            m.add_edge(
                locations[frm],
                locations[to],
                distance=float(dist.loc[frm, to]), 
                duration=float(time.loc[frm, to]), 
            )

VEH_CAPS = {
    "STE138": 35.5 * SCALE,
    "WCP677": 35.5 * SCALE,
    "WCP384": 23.0 * SCALE,
    "PUN354": 18.9 * SCALE,
    "JYO449": 29.25 * SCALE,
}

for name, cap in VEH_CAPS.items():
    m.add_vehicle_type(
        capacity=[cap],
        num_available=1,
        name=name,
        start_depot=locations["CI"],
        end_depot=locations["CD"],
        unit_distance_cost=1,  
        unit_duration_cost=1,
    )

res = m.solve(stop=FirstFeasible())
solution = res.best

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

from pyvrp.diversity import broken_pairs_distance
import vrplib

