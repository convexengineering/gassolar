" latitude sweep "
import matplotlib.pyplot as plt
import numpy as np
from gassolar.solar.solar_simple.solarsimple import Mission

fig, ax = plt.subplots()
lat = np.arange(20, 50, 1)
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
        M.cost = M["b"]
        try:
            sol = M.solve("mosek")
            W.append(sol("b").magnitude)
        except RuntimeWarning:
            W.append(np.nan)
    ax.plot(lat, W)

ax.set_ylim([0, 1000])
ax.set_xlim([20, 50])
ax.grid()
labels = ["$\\pm$" + item.get_text() for item in ax.get_xticklabels()]
labels = ["$\\pm$%d" % l for l in np.linspace(20, 50, len(labels))]
ax.set_xticklabels(labels)
ax.set_xlabel("Latitude Requirement [deg]")
ax.set_ylabel("Wing Span [ft]")
ax.legend(["%d Percentile Winds" % a for a in [80, 90, 95]], loc=2, fontsize=15)
fig.savefig("../../../gassolarpaper/spanvslatsolarsimple.pdf",
            bbox_inches="tight")
