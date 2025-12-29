import pickle

with open('3.1-ProblemData.pkl', 'rb') as f:
    m = pickle.load(f)
# print(m)

from pyvrp.stop import MaxRuntime, FirstFeasible
from pyvrp import solve
res=solve(m, MaxRuntime(15))
# print(res)

from pyvrp.plotting import *
import matplotlib.pyplot as plt

# plot_runtimes(res)
# plt.savefig("runtime")


# plot_solution(res.best, m)
# plt.savefig("solution")

# plot_diversity(res)
# plot_objectives(res)
# plot_result(res, m)
solution = res.best
routes = solution.routes()
fig, axarr = plt.subplots(2, 2, figsize=(15, 9))
for idx, (ax, route) in enumerate(zip(axarr.flatten(), routes)):
    plot_route_schedule(
        m,
        route,
        title=f"Route {idx}",
        ax=ax,
        legend=idx == 0,
    )

fig.tight_layout()

plt.show()