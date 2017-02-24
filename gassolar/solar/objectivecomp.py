" change objective plot "
import matplotlib.pyplot as plt
import numpy as np
from gassolar.solar.solar import Mission

LATITUDE = False
WIND = False
CON = True
COMP = False
SENS = False

plt.rcParams.update({'font.size':15})
fig, ax = plt.subplots()
fig2, ax2 = plt.subplots()
lat = np.arange(20, 40, 1)
l1 = []
l2 = []
for obj in ["b_Mission, Aircraft, Wing", "S_Mission, Aircraft, SolarCells"]:
    W = []
    SS = []
    runagain = True
    for l in lat:
        if runagain:
            M = Mission(latitude=l)
            M.substitutions.update({"W_{pay}": 10})
            for vk in M.varkeys["p_{wind}"]:
                M.substitutions.update({vk: 90/100.0})
            M.cost = M[obj]
            try:
                sol = M.solve("mosek")
                W.append(sol("b_Mission, Aircraft, Wing").magnitude)
                SS.append(sol("S_Mission, Aircraft, SolarCells").magnitude)
            except RuntimeWarning:
                W.append(np.nan)
                SS.append(np.nan)
                runagain = False
        else:
            W.append(np.nan)
            SS.append(np.nan)
    if obj[0] == "b":
        ty = "#4AA9AF"
    else:
        ty = "b--"
    ll = ax.plot(lat, W, "%s" % ty, lw=2)
    ll1 = ax2.plot(lat, SS, '%s' % ty, lw=2)

ax.set_ylim([0, 150])
ax.set_xlim([20, 34])
ax2.set_ylim([0, 300])
ax2.set_xlim([20, 34])
ax.grid()
ax2.grid()
ax.set_xlabel("Latitude Requirement [deg]")
ax2.set_xlabel("Latitude Requirement [deg]")
ax.set_ylabel("Wing Span $b$ [ft]")
ax2.set_ylabel("Solar Cell Area $S_{\\mathrm{solar}}$ [ft$^2$]")
labels = ["$\\pm$%d" % item for item in ax.get_xticks()]
# labels = ["$\\pm$%d" % l for l in np.linspace(20, 34, len(labels))]
ax.set_xticklabels(labels)
ax2.set_xticklabels(labels)
ax.legend(["Objective: min($b$)", "Objective: min($S_{\mathrm{solar}}$)"],
          loc=2, fontsize=15)
ax2.legend(["Objective: min($b$)", "Objective: min($S_{\mathrm{solar}}$)"],
           loc=2, fontsize=15)
fig.savefig("../../gassolarpaper/solarobjcomp.pdf", bbox_inches="tight")
fig2.savefig("../../gassolarpaper/solarobjcomp2.pdf", bbox_inches="tight")
