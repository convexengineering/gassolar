" contour plots "
import matplotlib.pyplot as plt
import numpy as np
from solar import Mission
from plotting import windalt_plot, labelLines
from gpkit.tools.autosweep import autosweep_1d

N = 100
plt.rcParams.update({'font.size':15})
fig, ax = plt.subplots()

etamax = []
lines = []
midx = []
passing = True
for lat in range(20, 44, 1):
    if passing:
        hmax = 500
        M = Mission(latitude=lat)
        M.substitutions.update({"W_{pay}": 10})
        for vk in M.varkeys["\\eta_{prop}"]:
            M.substitutions.update({vk: 0.75})
        for vk in M.varkeys["p_{wind}"]:
            M.substitutions.update({vk: 90/100.0})
        del M.substitutions["h_{batt}"]
        M.substitutions.update({"\\eta_Mission, Aircraft, SolarCells": 0.4})
        M.cost = M["h_{batt}"]
        sol = M.solve("mosek")
        hmin = sol["cost"].magnitude + 1e-3
        del M.substitutions["\\eta_Mission, Aircraft, SolarCells"]
        M.cost = M["\\eta_Mission, Aircraft, SolarCells"]
        xmin_ = np.linspace(hmin, hmax, 100)
        tol = 0.01
        notpassing = True
        try:
            bst = autosweep_1d(M, tol, M["h_{batt}"], [hmin, hmax],
                               solver="mosek")
            if lat % 4 == 0:
                l = ax.plot(xmin_, bst.sample_at(xmin_)["cost"], "k",
                            label="%d" % lat)
                lines.append(l[0])
                etamax.append(max(bst.sample_at(xmin_)["cost"].magnitude))
                midx.append(np.median(xmin_))
            elif lat % 2 == 0:
                l = ax.plot(xmin_, bst.sample_at(xmin_)["cost"], "--", c="0.5",
                            label="%d" % lat)
        except RuntimeWarning:
            passing = False

# ax.fill_between(xmin_, bst.sample_at(xmin_)["cost"], max(etamax),
#                 edgecolor="r", lw=2, hatch="/", facecolor="None", zorder=100)
labelLines(lines, align=False, xvals=midx, zorder=[10]*len(lines))
# ax.text(425, 0.36, "Infeasible")
ax.set_ylabel("Solar Cell Efficiency")
ax.set_xlabel("Battery Specific Energy [Whr/kg]")
ax.set_xlim([250, 500])
ax.set_ylim([0.1, max(etamax)])
ax.grid()
fig.savefig("../../gassolarpaper/battsolarcontour.pdf", bbox_inches="tight")
