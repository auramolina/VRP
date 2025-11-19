import pandas as pd
import matplotlib.pyplot as plt
from pyvrp import Model
from pyvrp import solve, Result, Client, Route
from pyvrp.stop import FirstFeasible, MultipleCriteria, NoImprovement
from pyvrp.plotting import plot_coordinates, plot_instance, plot_result, plot_route_schedule
#--------------------------------------------
coords = pd.read_csv("coordenadas.csv")
dist = pd.read_csv("distancias.csv", header=None, index_col=False)
time = pd.read_csv("tiempos.csv", header=None, index_col=False)
dem = pd.read_csv("demanda.csv") 
service = pd.read_csv("service.csv")
#--------------------------------------------
#Modelo
m = Model()
locations = {}
#--------------------------------------------
#Escalar
SCALE = 100
dist = round(dist*SCALE)
time = round(time*SCALE)
#--------------------------------------------
# ====== Depots ======
CI = coords[coords["Nombre"] == "CI"].iloc[0]
CD = coords[coords["Nombre"] == "CD"].iloc[0]

#add depot
locations["CI"]=m.add_depot(
    x=float(CI["lon"]),
    y=float(CI["lat"]),
    name=CI["Nombre"]
)
locations["CD"]=m.add_depot(
    x=float(CD["lon"]),
    y=float(CD["lat"]),
    name=CD["Nombre"]
)
# d = [loc.tw_late for loc in m.depots]
# print(d)
#--------------------------------------------
# ====== Clients ======
for _, row in coords.iterrows(): 
    planta = str(row["Nombre"]) 
    if planta in [loc.name for loc in m.depots]: 
        continue 
    #Demanda
    d = dem[dem["planta"] == planta] 
    #Tiempo en planta
    s = service[service["planta"] == planta] 
    service_time = int(s.iloc[0]["total"]* SCALE)  if not s.empty else 0 
    if not d.empty: 
        #Descarga
        delivery = int(d.iloc[0]["di"] * SCALE )
        #Carga
        pickup = int(d.iloc[0]["pi"] * SCALE )
    else: 
        delivery = pickup = 0
    #Ventanas de tiempo
    if planta in ("A6", "42"):
        tw_early = 0
        tw_late = 90 * SCALE 
    else:
        tw_early = 0
        tw_late = 1440 * SCALE
    #add client
    locations[planta] = m.add_client( 
        x=float(row["lon"]), 
        y=float(row["lat"]), 
        delivery=[delivery] if delivery > 0 else [], 
        pickup=[pickup] if pickup > 0 else [],
        service_duration=service_time,
        tw_early=tw_early,
        tw_late=tw_late,
        required=True,
        name=planta,
        )
# d = [loc.name for loc in m.locations]
# print(d)
#--------------------------------------------  
# ====== Edges ======
names = coords["Nombre"].astype(str).tolist()
dist.index = names
dist.columns = names
time.index = names
time.columns = names
#add edges
for frm in dist.index:
    for to in dist.columns:
        # if frm == to:
        #     continue
        if frm in locations and to in locations:
            m.add_edge(
                frm=locations[frm],
                to=locations[to],
                distance=int(dist.loc[frm, to]),
                duration=int(time.loc[frm, to]), 
            )
# print([e.duration for e in m._edges[:20]])
#--------------------------------------------  
# ====== Vehicles ======
#Capacidades
VEH_CAPS = {
    "STE138": 35.5,
    "WCP677": 35.5,
    "WCP384": 23.0,
    "PUN354": 18.9,
    "JYO449": 29.25,  
}
#add vehicle
for name, cap in VEH_CAPS.items():
    m.add_vehicle_type(
        capacity=[cap*SCALE],
        num_available=1,
        start_depot=locations["CI"],
        end_depot=locations["CD"],
        # tw_early=,
        # tw_late=,
        shift_duration=10*60*SCALE,
        unit_distance_cost=1,  
        unit_duration_cost=1,
        # reload_depots=[locations["CI"]], ######
        max_overtime=3*60*SCALE,
        unit_overtime_cost=100000,
        name=name,
    )
#--------------------------------------------  
# ====== Solve ======
res = m.solve(stop=FirstFeasible())
solution = res.best
#-------------------------------------------- 
id_to_name = {idx: loc.name for idx, loc in enumerate(m.locations)}

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
    # --- MÉTRICAS COMPLETAS DEL OBJETO ROUTE ---
    print("\n--- MÉTRICAS DE RUTA ---")
    print("Factible:", route.is_feasible())
    print("Distancia:", route.distance() / SCALE)
    print("Duración:", route.duration() / SCALE)
    print("Duración en viaje:", route.travel_duration() / SCALE)
    print("Duración en servicio:", route.service_duration() / SCALE)
    print("Duración en espera:", route.wait_duration() / SCALE)
    print("Empieza:", route.start_time() / SCALE)
    print("Termina:", route.end_time() / SCALE)
    print("Slack:", route.slack() / SCALE)
    print("Pickup total:", [p / SCALE for p in route.pickup()])
    print("Delivery total:", [d / SCALE for d in route.delivery()])
    # Trip info
    print("\n--- TRIPS ---")
    # print("Num trips:", route.num_trips())
    for t in range(route.num_trips()):
        trip = route.trip(t)
        print(f"Trip {t}: {trip}")
    # Schedule completo (objeto detallado)
    print("\n--- SCHEDULE DETALLADO ---")
    schedule = route.schedule()
    for sv in schedule:
        loc_id = sv.location
        name = id_to_name[loc_id]
        arrival = (sv.start_service - sv.wait_duration) / SCALE
        start = sv.start_service / SCALE
        end = sv.end_service / SCALE
        depart = end  # end_service es cuando el vehículo sale
        wait = sv.wait_duration / SCALE
        service = sv.service_duration / SCALE
        warp = sv.time_warp / SCALE
        print(
            f"{name:>4} | "
            f"arrival={arrival:6.1f} | "
            f"start={start:6.1f} | "
            f"depart={depart:6.1f} | "
            f"wait={wait:5.1f} | "
            f"service={service:5.1f} | "
            f"timewarp={warp:5.1f}"
        )
    print("-" * 60)
#-------------------------------------------- 
data = m.data()
#Gráficos PyVRP
plot_coordinates(data)
plt.title("Coordenadas de los clientes")
plt.tight_layout()
plot_instance(data)
plt.title("Instancia VRP")
plt.tight_layout()
plot_result(res, data)  
plt.title("Rutas encontradas y evolución del algoritmo")
plt.tight_layout()
plt.show()
#-------------------------------------------- 
