from pyvrp.plotting import plot_coordinates, plot_instance, plot_result, plot_route_schedule, plot_objectives
import matplotlib.pyplot as plt
import pickle
from pyvrp import Route

# Modelo
with open('4.1-Res.pkl', 'rb') as f:
    res = pickle.load(f)
with open('3.3-ProblemData.pkl', 'rb') as f:
    m = pickle.load(f)

solution = res.best
print(solution)

# plot_coordinates(m)
# plt.title("Coordenadas de los clientes")
# plt.tight_layout()

# plot_instance(m)
# plt.title("Instancia VRP")
# plt.tight_layout()

# plot_result(res, m)  
# plt.title("Rutas encontradas y evolución del algoritmo")
# plt.tight_layout()

# plot_objectives(res)
# for route in solution.routes():
#     plot_route_schedule(m, route)


plt.show()