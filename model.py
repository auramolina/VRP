import pandas as pd
from pyvrp import Model
from pyvrp.stop import MaxRuntime, MultipleCriteria, FirstFeasible, NoImprovement
import numpy as np
from pyvrp.solve import SolveParams
from pyvrp import CostEvaluator


coords = pd.read_csv("coordenadas.csv")
nombres = coords["Nombre"].astype(str).tolist() 
dist = pd.read_csv("distancias.csv", index_col=0)
time = pd.read_csv("tiempos.csv", index_col=0)
dem = pd.read_csv("demanda.csv")

coords.index = coords.index.astype(str).str.strip()
dist.index = dist.index.astype(str).str.strip()
dist.columns = dist.columns.astype(str).str.strip()
time.index = dist.index.astype(str).str.strip()
time.columns = dist.columns.astype(str).str.strip()

m = Model()

locations = {}

depot_row = coords[coords["Nombre"] == "CI"].iloc[0]
locations["CI"] = m.add_depot(
    x = float(depot_row["lon"]),
    y = float(depot_row["lat"]),
    name = "CI",
)
depot_row=coords[coords["Nombre"]=="CD"].iloc[0] 
locations["CD"] = m.add_depot(
    x = float(depot_row["lon"]),
    y = float(depot_row["lat"]),
    name = "CD",
)

for _, row in coords.iterrows():
    planta = str(row["Nombre"])  
    if planta in ("CI", "CD"): 
        continue
    d = dem[dem["planta"] == planta]
    if not d.empty:
        delivery = float(d.iloc[0]["di"])
        pickup = float(d.iloc[0]["pi"])
    else:
        delivery = pickup = 0.0
    locations[planta] = m.add_client(
        x=float(row["lon"]),
        y=float(row["lat"]),
        delivery=[float(delivery)] if delivery > 0 else [],
        pickup=[float(pickup)] if pickup > 0 else [],
        name=planta,
        # service_duration=
    )

for frm in dist.index:
    for to in dist.columns:
        if frm == to:
            continue
        m.add_edge(
            locations[frm],
            locations[to],
            distance=float(dist.loc[frm, to]),
            duration=float(time.loc[frm, to]) 
        )

m.add_vehicle_type(capacity=[float(35.5)], num_available=1, name="STE138", start_depot=locations["CI"], end_depot=locations["CD"], unit_distance_cost=1, unit_duration_cost=1)
m.add_vehicle_type(capacity=[float(35.5)], num_available=1, name="WCP677", start_depot=locations["CI"], end_depot=locations["CD"], unit_distance_cost=1, unit_duration_cost=1) 
m.add_vehicle_type(capacity=[float(23)], num_available=1, name="WCP384", start_depot=locations["CI"], end_depot=locations["CD"], unit_distance_cost=1, unit_duration_cost=1) 
m.add_vehicle_type(capacity=[float(18.9)], num_available=1, name="PUN354", start_depot=locations["CI"], end_depot=locations["CD"], unit_distance_cost=1, unit_duration_cost=1) 
m.add_vehicle_type(capacity=[float(29.25)], num_available=1, name="JYO449", start_depot=locations["CI"], end_depot=locations["CD"], unit_distance_cost=1, unit_duration_cost=1) 




#solve
res = m.solve(
    stop = FirstFeasible()#NoImprovement(55500))##MaxRuntime(500)([NoImprovement(500), FirstFeasible]), 
    # seed= ,
    # collect_stats = True, 
    # display = False, 
    # params = SolveParams(
    #     genetic = GeneticAlgorithmParams(), 
    #     penalty = PenaltyParams(), 
    #     population = PopulationParams(), 
    #     neighbourhood = NeighbourhoodParams(), 
    #     node_ops: list[type[NodeOperator]] = NODE_OPERATORS, 
    #     route_ops: list[type[RouteOperator]] = ROUTE_OPERATORS, 
    #     display_interval = 5.0
    # ), 
    # missing_value = MAX_VALUE
    )
# print(res)

solution = res.best  
    
id_to_name = {idx: loc.name for idx, loc in enumerate(m.locations)}

for i, route in enumerate(solution.routes(), start=1):
    veh_type = m.vehicle_types[route.vehicle_type()]  # el tipo de vehículo
    veh_name = veh_type.name
    
    # depots de inicio y fin
    start_depot = id_to_name[veh_type.start_depot]
    end_depot = id_to_name[veh_type.end_depot]
    
    # visitas intermedias
    visit_names = [id_to_name[v] for v in route.visits()]
    
    print(f"Ruta {i}")
    print(" Vehículo:", veh_name)
    print(" Start depot:", start_depot)
    print(" End depot:", end_depot)
    print(" Visitas:", " -> ".join([start_depot] + visit_names + [end_depot]))
    print(" Distancia:", route.distance(), "km")
    print(" Duración:", route.duration(), "min")
    print(" Entregas:", route.delivery())
    print(" Recogidas:", route.pickup())
    print(" ¿Factible?:", route.is_feasible())
    print("-" * 40)


# from pyvrp import diversity

# res1 = m.solve(stop=MaxRuntime(30), seed=1)
# res2 = m.solve(stop=MaxRuntime(30), seed=2)

# sol1 = res1.best
# sol2 = res2.best

# print("Costo sol1:", res1.cost())
# print("Costo sol2:", res2.cost())
# print("Diversidad (BPD):", diversity.broken_pairs_distance(sol1, sol2))

# for i, route in enumerate(sol1.routes(), start=1):
#     print(f"Ruta {i}: distancia={route.distance()}, duración={route.duration()}, entregas={route.delivery()}, recogidas={route.pickup()}")

# # Mapeo de IDs a nombres (para leer las visitas en texto)

# id_to_name = {idx: loc.name for idx, loc in enumerate(m.locations)}
# veh_type_to_name = {idx: vt.name for idx, vt in enumerate(m.vehicle_types)}
# def print_solution(solution, result, label="Solución"):
#     print("=" * 60)
#     print(label)
#     print(f"Costo total: {result.cost()}")
#     print(f"Número de rutas: {len(solution.routes())}")
#     print("-" * 60)
    
#     for i, route in enumerate(solution.routes(), start=1):
#         veh_name = veh_type_to_name[route.vehicle_type()]
#         visits = [id_to_name[v] for v in route.visits()]
        
#         try:
#             start_depot = id_to_name[route.start_depot()]
#             end_depot = id_to_name[route.end_depot()]
#         except Exception:
#             start_depot = "?"
#             end_depot = "?"
        
#         print(f"Ruta #{i}")
#         print(" Vehículo:", veh_name)
#         print(" Camino :", " -> ".join([start_depot] + visits + [end_depot]))
#         print(" Distancia:", route.distance())
#         print(" Duración:", route.duration())
#         print(" Entregas:", route.delivery())
#         print(" Recogidas:", route.pickup())
#         print(" ¿Factible?:", route.is_feasible())
#         print("-" * 60)

# # Usar así:
# print_solution(sol1, res1, "Solución 1")
# print_solution(sol2, res2, "Solución 2")




# res2 = m.solve(stop=MultipleCriteria([MaxRuntime(60), NoImprovement(5000)]), display=True)
# sol2 = res2.best

# # res3 = m.solve(MultipleCriteria([MaxRuntime(10), NoImprovement(500)]), display=False)
# # sol3 = res3.best

# bpd = diversity.broken_pairs_distance(sol1, sol2)
# # bpd2 = diversity.broken_pairs_distance(sol3, sol2)
# # bpd3 = diversity.broken_pairs_distance(sol3, sol1)

# print(bpd)
# # print(bpd2)
# # print(bpd3)

# print(res2.cost)

