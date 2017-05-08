"latitude vs endurance"
import matplotlib.pyplot as plt
import numpy as np
from gassimple import Mission
from gassolar.environment.wind_speeds import get_windspeed

fig, ax = plt.subplots()
lat = np.arange(0, 60, 1)
M = Mission()
M.substitutions.update({"W_{pay}": 10})
for e in M.varkeys["\\eta_{prop}"]:
    M.substitutions.update({e: 0.75})
for cd in M.varkeys["CDA_0"]:
    M.substitutions.update({cd: 0.01})
M.substitutions.update({"t_Mission/Loiter": 7})
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
            mtow.append(sol("MTOW").magnitude)
        except RuntimeWarning:
            mtow.append(np.nan)
    ax.plot(lat, mtow)

ax.set_ylim([0, 1000])
ax.set_xlim([20, 50])
ax.grid()
labels = ["$\\pm$" + item.get_text() for item in ax.get_xticklabels()]
labels = ["$\\pm$%d" % l for l in np.linspace(20, 50, len(labels))]
ax.set_xticklabels(labels)
ax.set_xlabel("Latitude Requirement [deg]")
ax.set_ylabel("Max Take Off Weight [lbf]")
ax.legend(["%d Percentile Winds" % a for a in [80, 90, 95]], loc=2, fontsize=15)
fig.savefig("../../../gassolarpaper/mtowvslatgassimple.pdf",
            bbox_inches="tight")
