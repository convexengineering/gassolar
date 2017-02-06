"latitude sweep"
import matplotlib.pyplot as plt
import numpy as np
from gassolar.gas.gas import Mission
from gassolar.environment.wind_speeds import get_windspeed

plt.rcParams.update({'font.size':15})
fig, ax = plt.subplots()
lat = np.arange(0, 60, 1)
M = Mission()
M.substitutions.update({"W_{pay}": 10})
M.substitutions.update({"t_Mission, Loiter": 7})
# M.cost = M["b_Mission, Aircraft, Wing"]
M.cost = M["MTOW"]
for a in [80, 90, 95]:
    mtow = []
    wind = []
    for l in lat:
        wind.append(get_windspeed(l, a, 15000, 355))
        maxwind = max(wind)
        for v in M.varkeys["V_{wind}"]:
            M.substitutions.update({v: maxwind})
        try:
            sol = M.solve("mosek")
            # mtow.append(sol("b_Mission, Aircraft, Wing").magnitude)
            mtow.append(sol("MTOW").magnitude)
        except RuntimeWarning:
            mtow.append(np.nan)
    ax.plot(lat, mtow, lw=2)

ax.set_ylim([0, 500])
ax.set_xlim([20, 45])
ax.grid()
ax.set_xlabel("Latitude [deg]")
ax.set_ylabel("Max Take Off Weight [lbf]")
labels = ["$\\pm$" + item.get_text() for item in ax.get_xticklabels()]
labels = ["$\\pm$%d" % l for l in np.linspace(20, 45, len(labels))]
ax.set_xticklabels(labels)
ax.legend(["%d Percentile Winds" % a for a in [80, 90, 95]], loc=2, fontsize=15)
fig.savefig("../../gassolarpaper/mtowvslatgas.pdf", bbox_inches="tight")
