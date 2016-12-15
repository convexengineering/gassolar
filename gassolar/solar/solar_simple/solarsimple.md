# Solar Simple Write Up

# Simple model of a Gas Powered Aircraft
```python
#inPDF: skip
from solarsimple import Mission
from gassolar.environment.wind_speeds import get_windspeed
from solar.solar_irradiance import get_Eirr
import matplotlib.pyplot as plt
import numpy as np
plt.rcParams.update({'font.size':19})

""" contour """
# av = 85
# for l in [35, 45]:
#     fig, ax = plt.subplots()
#     S = Mission(latitude=l, percent=av, altitude=60000, day=355)
#     S.substitutions.update({"f_{structures}": ("sweep", np.linspace(0.2, 0.5, 10))})
#     S.substitutions.update({"h_{batt}": ("sweep", np.linspace(250, 400, 10))})
#     S.substitutions.update({"W_{pay}": 10})
#     S.substitutions.update({"\\eta_{prop}": 0.75})
#     S.substitutions.update({"CDA_0": 0.002})
#     S.cost = S["b"]
#     sol = S.solve("mosek", skipsweepfailures=True)
#     x = np.reshape(sol("f_{structures}"), [10, 10])
#     y = np.reshape(sol("h_{batt}"), [10, 10])
#     z = np.reshape(sol("b"), [10, 10])
#     print z
#     levels = np.array(range(50, 2000, 50)+ [2300])
#     if av == 90:
#         v = np.array(range(50, 700, 50)+ [2300])
#     else:
#         v = np.array(range(50, 400, 50)+ [2300])
#     a = ax.contour(x, y, z, levels, colors="k")
#     ax.clabel(a, v, inline=1, fmt="%d [ft]")
#     ax.set_xlabel("Structural Fraction")
#     ax.set_ylabel("Battery Energy Density [Whr/kg]")
#     fig.savefig("bcontourl%da%d.pdf" % (l, 85), bbox_inches="tight")

""" latitutde """
fig, ax = plt.subplots()
lat = np.arange(20, 60, 1)
for a in [80, 90, 95]:
    W = []
    for l in lat:
        M = Mission(latitude=l)
        M.substitutions.update({"W_{pay}": 10})
        for vk in M.varkeys["CDA_0"]:
            M.substitutions.update({vk: 0.002})
        for vk in M.varkeys["p_{wind}"]:
            M.substitutions.update({vk: a/100.0})
        M.substitutions.update({"\\rho_{solar}": 0.25})
        M.cost = M["W"]
        try:
            sol = M.solve("mosek")
            W.append(sol("W").magnitude)
        except RuntimeWarning:
            W.append(np.nan)
    ax.plot(lat, W)

ax.set_ylim([0, 2000])
ax.grid()
ax.set_xlabel("Latitude [deg]")
ax.set_ylabel("Max Take Off Weight [lbs]")
ax.legend(["%d Percentile Winds" % a for a in [80, 90, 95]], loc=2, fontsize=15)
fig.savefig("mtowvslatsolar.pdf", bbox_inches="tight")
