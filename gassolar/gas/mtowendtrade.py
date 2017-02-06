"mtow vs endurance trade"
import matplotlib.pyplot as plt
import numpy as np
from gassolar.gas.gas import Mission
from gassolar.environment.wind_speeds import get_windspeed
from gpkit.tools.autosweep import sweep_1d

plt.rcParams.update({'font.size':15})
M = Mission()
M.cost = M["MTOW"]
fig, ax = plt.subplots()
x = np.linspace(1, 12, 500)
tol = 0.05
ws = []
xs = []
for p in [85, 90, 95]:
    wind = get_windspeed(38, p, 15000, 355)
    cwind = get_windspeed(38, p, np.linspace(0, 15000, 11)[1:], 355)
    for vk in M.varkeys["V_{wind}"]:
        if "Climb" in vk.models:
            M.substitutions.update({vk: cwind[vk.idx[0]]})
        else:
            M.substitutions.update({vk: wind})

    M.substitutions.update({"MTOW": 1000})
    M.cost = 1/M["t_Mission, Loiter"]
    sol = M.solve("mosek")
    upper = sol("t_Mission, Loiter").magnitude
    xmin_ = x[x < upper + 0.03]
    xs.append(xmin_)

    del M.substitutions["MTOW"]
    M.cost = M["MTOW"]
    bst = sweep_1d(M, tol, M["t_Mission, Loiter"], [1, xmin_[-1]],
                   solver="mosek")
    ws.append(bst["cost"].__call__(xmin_))
    del M.substitutions["t_Mission, Loiter"]

ax.fill_between(xs[0], ws[0],
                np.append(ws[2], [1000]*(len(xs[0])-len(xs[2]))),
                facecolor="b", edgecolor="None", alpha=0.3)
ax.plot(xs[0], ws[0], "b")
ax.plot(xs[1], ws[1], "b", lw=2)
ax.plot(xs[2], ws[2], "b")
for i, p in enumerate(["80%", "90%", "95%"]):
    weight = ws[i].magnitude
    we = 500 + min(abs(weight-500))
    if we not in weight:
        we = 500 - min(abs(weight-500))
    end = xs[i][weight == we][0]
    ax.annotate(p, xy=(end, we), xytext=(end+0.3, we+0.01),
                arrowprops=dict(arrowstyle="-"), fontsize=12)
ax.grid()
ax.set_ylim([0, 1000])
ax.set_xlabel("Endurance [days]")
ax.set_ylabel("Max Take Off Weight [lbf]")
fig.savefig("../../gassolarpaper/mtowvsendurance.pdf", bbox_inches="tight")
