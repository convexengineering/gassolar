"solar latitude sweep"
import matplotlib.pyplot as plt
import numpy as np
from gassolar.solar.solar import Mission
from gassolar.solar.plotting import windalt_plot

plt.rcParams.update({'font.size':15})
fig, ax = plt.subplots()
lat = np.arange(21, 40, 1)
for a in [80, 90, 95]:
    W = []
    runagain = True
    for l in lat:
        if runagain:
            M = Mission(latitude=l)
            for vk in M.varkeys["p_{wind}"]:
                M.substitutions.update({vk: a/100.0})
            # M.cost = M["b_Mission, Aircraft, Wing"]
            M.cost = M["W_{total}"]
            try:
                sol = M.solve("mosek")
                # W.append(sol("b_Mission, Aircraft, Wing").magnitude)
                W.append(sol("W_{total}").magnitude)
            except RuntimeWarning:
                W.append(np.nan)
                runagain = False
        else:
            W.append(np.nan)
    ax.plot(lat, W, lw=2)

ax.set_ylim([0, 500])
ax.set_xlim([20, 45])
ax.grid()
ax.set_xlabel("Latitude Requirement [deg]")
ax.set_ylabel("Max Take Off Weight [lbf]")
labels = ["$\\pm$" + item.get_text() for item in ax.get_xticklabels()]
labels = ["$\\pm$%d" % l for l in np.linspace(20, 45, len(labels))]
ax.set_xticklabels(labels)
ax.legend(["%d Percentile Winds" % a for a in [80, 90, 95]], loc=2, fontsize=15)
fig.savefig("../../gassolarpaper/mtowvslatsolar.pdf", bbox_inches="tight")
