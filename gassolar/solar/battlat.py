" contour plots "
import matplotlib.pyplot as plt
import numpy as np
from solar import Mission
from plotting import windalt_plot, labelLines
from gpkit.tools.autosweep import autosweep_1d

N = 100
plt.rcParams.update({'font.size':19})
fig, ax = plt.subplots()

bmax = []
lines = []
for lat in range(20, 31, 2):
    hmax = 500
    M = Mission(latitude=lat)
    M.substitutions.update({"W_{pay}": 10})
    for vk in M.varkeys["\\eta_{prop}"]:
        M.substitutions.update({vk: 0.75})
    for vk in M.varkeys["p_{wind}"]:
        M.substitutions.update({vk: 90/100.0})
    del M.substitutions["h_{batt}"]
    M.cost = M["h_{batt}"]
    sol = M.solve("mosek")
    hmin = sol["cost"].magnitude + 1e-3
    M.cost = M["b_Mission, Aircraft, Wing"]
    xmin_ = np.linspace(hmin, hmax, 100)
    tol = 0.01
    bst = autosweep_1d(M, tol, M["h_{batt}"], [hmin, hmax], solver="mosek")
    l = ax.plot(xmin_, bst.sample_at(xmin_)["cost"], "k", label="%d" % lat)
    lines.append(l[0])
    bmax.append(max(bst.sample_at(xmin_)["cost"].magnitude))

labelLines(lines, align=False, xvals=[270, 290, 310, 330, 360, 390],
           zorder=[10]*len(lines))
ax.set_ylabel("Span [ft]")
ax.set_xlabel("Battery Specific Energy [Whr/kg]")
ax.set_xlim([250, 400])
ax.set_ylim([20, max(bmax)-5])
ax.grid()
fig.savefig("test.pdf", bbox_inches="tight")
