"latitude sweep"
import matplotlib.pyplot as plt
import numpy as np
from gassolar.gas.gas import Mission
from gassolar.environment.wind_speeds import get_windspeed
import sys

def gas_lat(model, cost, subs=None):
    plt.rcParams.update({'font.size':15})
    fig, ax = plt.subplots()
    lat = np.arange(0, 60, 1)
    model.substitutions.update(subs)
    model.cost = model[cost]
    for a in [80, 90, 95]:
        mtow = []
        wind = []
        for l in lat:
            wind.append(get_windspeed(l, a, 15000, 355))
            maxwind = max(wind)
            for v in model.varkeys["V_{wind}"]:
                model.substitutions.update({v: maxwind})
            try:
                sol = model.solve("mosek")
                mtow.append(sol(cost).magnitude)
            except RuntimeWarning:
                mtow.append(np.nan)
        ax.plot(lat, mtow, lw=2)

    ax.set_xlabel("Latitude [deg]")
    labels = ["$\\pm$" + item.get_text() for item in ax.get_xticklabels()]
    labels = ["$\\pm$%d" % l for l in np.linspace(20, 45, len(labels))]
    ax.set_xticklabels(labels)
    ax.legend(["%d Percentile Winds" % a for a in [80, 90, 95]], loc=2, fontsize=15)

    return fig, ax

if __name__ == "__main__":
    M = Mission()
    cost = "MTOW"
    subs = {"W_{pay}": 10, "t_Mission/Loiter": 7}
    fig, ax = gas_lat(M, cost, subs=subs)

    ax.set_ylim([0, 500])
    ax.set_xlim([20, 45])
    ax.grid()
    ax.set_ylabel("Max Take Off Weight [lbf]")

    if len(sys.argv) > 1:
        path = sys.argv[1]
        fig.savefig(path + "mtowvslatgas.pdf", bbox_inches="tight")
    else:
        fig.savefig("mtowvslatgas.pdf", bbox_inches="tight")
