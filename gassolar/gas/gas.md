# Gas Simple Write Up

# Simple model of a Gas Powered Aircraft
```python
#inPDF: skip
from gas import Mission
from gassolar.environment.wind_speeds import get_windspeed
import matplotlib.pyplot as plt
from gpkit.tools.autosweep import sweep_1d
import numpy as np
plt.rcParams.update({'font.size':19})

""" MTOW vs Endurance """

M = Mission()
M.cost = M["MTOW"]
fig, ax = plt.subplots()
lower = 1
upper = 10 
xmin_ = np.linspace(lower, upper, 100)
tol = 0.05
for p in [85, 90, 95]:
    notpassing = True
    while notpassing:
        wind = get_windspeed(38, p, 15000, 355)
        cwind = get_windspeed(38, p, np.linspace(0, 15000, 11)[1:], 355)
        for vk in M.varkeys["V_{wind}"]:
            if "Climb" in vk.models:
                M.substitutions.update({vk: cwind[vk.idx[0]]})
            else:
                M.substitutions.update({vk: wind})
        try:
            bst = sweep_1d(M, tol, M["t_Mission, Loiter"], [lower, upper], solver="mosek")
            notpassing = False
        except RuntimeWarning:
            notpassing = True
            upper -= 0.1
            xmin_ = np.linspace(lower, upper, 100)

    ax.plot(xmin_, bst["cost"].__call__(xmin_))
ax.grid()
ax.set_ylim([0, 1000])
ax.set_xlabel("Endurance [days]")
ax.set_ylabel("Max Take Off Weight [lbf]")
ax.legend(["%d Percentile Winds" % a for a in [85, 90, 95]], loc=2, fontsize=15)
fig.savefig("mtowvsendurance.pdf", bbox_inches="tight")
```
