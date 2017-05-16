"mtow vs endurance trade"
import matplotlib.pyplot as plt
import numpy as np
from gassolar.gas.gas import Mission
from gassolar.environment.wind_speeds import get_windspeed
from gassolar.solar.battsolarcon import find_sols
from gpkit.tools.autosweep import autosweep_1d
import sys

plt.rcParams.update({'font.size':15})

def mtow_plot(model):
    model.cost = model["MTOW"]
    fig, ax = plt.subplots()
    x = np.linspace(1, 15, 500)
    tol = 0.05
    time = 0.0
    nsolves = 0
    ws = []
    xs = []
    for p in [85, 90, 95]:
        wind = get_windspeed(38, p, 15000, 355)
        cwind = get_windspeed(38, p, np.linspace(0, 15000, 11)[1:], 355)
        for vk in model.varkeys["V_{wind}"]:
            if "Climb" in vk.models:
                model.substitutions.update({vk: cwind[vk.idx[0]]})
            else:
                model.substitutions.update({vk: wind})

        model.substitutions.update({"MTOW": 1000})
        model.cost = 1/model["t_Mission/Loiter"]
        sol = model.solve("mosek")
        time += sol["soltime"]
        nsolves += 1
        upper = sol("t_Mission/Loiter").magnitude
        xmin_ = x[x < upper + 0.03]
        xs.append(xmin_)

        del model.substitutions["MTOW"]
        model.cost = model["MTOW"]
        bst = autosweep_1d(model, tol, model["t_Mission/Loiter"],
                           [1, xmin_[-1]], solver="mosek")
        bsts = find_sols([bst])
        sols = np.hstack([b.sols for b in bsts])
        time += sum(np.unique([s["soltime"] for s in sols]))
        nsolves += bst.nsols
        ws.append(bst.sample_at(xmin_)["cost"])

    print "%d solves in %.4f seconds" % (nsolves, time)
    ax.fill_between(xs[0], ws[0],
                    np.append(ws[2], [1000]*(len(xs[0])-len(xs[2]))),
                    facecolor="r", edgecolor="None", alpha=0.3)
    ax.plot(xs[0], ws[0], "r")
    ax.plot(xs[1], ws[1], "r", lw=2)
    ax.plot(xs[2], ws[2], "r")
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
    return fig, ax

if __name__ == "__main__":
    M = Mission()
    fig, ax = mtow_plot(M)
    if len(sys.argv) > 1:
        path = sys.argv[1]
        fig.savefig(path + "mtowvsendurance.pdf", bbox_inches="tight")
    else:
        fig.savefig("mtowvsendurance.pdf", bbox_inches="tight")
