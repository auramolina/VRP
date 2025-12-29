import pickle
from pyvrp import solve, Result, Client, Route
from pyvrp.stop import FirstFeasible, MultipleCriteria, NoImprovement
import matplotlib.pyplot as plt
from pyvrp.plotting import plot_coordinates, plot_instance, plot_result, plot_route_schedule

SCALE = 100

with open('Escenarios/Instancia1.pkl', 'rb') as f:
    m = pickle.load(f)

#NoImprovement(5000)
res=solve(m, FirstFeasible())
print(res)
# solution = res.best

# print(solution)
# print(solution.num_trips)
# print(solution.is_feasible)

# plot_coordinates(m)
# plt.title("Coordenadas de los clientes")
# plt.tight_layout()

# plot_instance(m)
# plt.title("Instancia VRP")
# plt.tight_layout()

# plot_result(res, m)  
# plt.title("Rutas encontradas y evolución del algoritmo")
# plt.tight_layout()

# plt.show()

# print(m.clients())

# for idx, client in enumerate(m.clients()):
#     print(f"Cliente {idx+1}: {client.name}")

# locations = []

# clientes = [loc.name for loc in m.clients()]
# depots = [loc.name for loc in m.depots()]

# locations = clientes+depots
# # print(locations)

# vehicles = [loc.name for loc in m.vehicle_types()]

# rutas = [loc.visits for loc in solution.routes()]

# print(res.stats)

# for i, route in enumerate(solution.routes(), start=1):
#     veh_type = m.vehicle_types[route.vehicle_type()]
#     veh_name = veh_type.name

#     start_depot = id_to_name[veh_type.start_depot]
#     end_depot = id_to_name[veh_type.end_depot]
#     visit_names = [id_to_name[v] for v in route.visits()]
