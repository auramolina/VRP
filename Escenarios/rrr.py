import pickle
import pyvrp
from pyvrp.stop import *
from pyvrp import solve

with open('edges/modelo-g.pkl', 'rb') as f:
    g = pickle.load(f)
with open('edges/modelo-m.pkl', 'rb') as f:
    m = pickle.load(f)

res_g = g.solve(MaxRuntime(60))
res_m = m.solve(MaxRuntime(60))

print(res_g)
print(res_m)