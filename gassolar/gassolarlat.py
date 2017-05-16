"sweep latitude for gas and solar"
from gassolar.solar.solar import Mission as Msolar
from gassolar.gas.gas import Mission as Mgas
from gassolar.environment.wind_speeds import get_windspeed
from gassolar.solar.battsolarcon import find_sols
import matplotlib.pyplot as plt
import numpy as np
import os
import sys

FIGPATH = (os.path.abspath(__file__).replace(os.path.basename(__file__), "")
           + "figs" + os.sep)

plt.rcParams.update({'font.size':15})

def plot_lats():
    fig, ax = plt.subplots()
    lat = np.arange(20, 41, 1)
    Mg = Mgas()
    Mg.substitutions.update({"W_{pay}": 10})
    Mg.substitutions.update({"t_Mission/Loiter": 7})
    Mg.cost = Mg["MTOW"]
    psolar = []
    pgas = []
    faillat = []
    gtime = 0.0
    gnsols = 0
    stime = 0.0
    snsols = 0.0
    for a in [80, 90, 95]:
        wg = []
        ws = []
        runagains = True
        highestwind = 0
        for l in lat:
            if runagains:
                Ms = Msolar(latitude=l)
                Ms.substitutions.update({"W_{pay}": 10})
                for vk in Ms.varkeys["p_{wind}"]:
                    Ms.substitutions.update({vk: a/100.0})
                Ms.cost = Ms["W_{total}"]
                try:
                    sol = Ms.solve("mosek")
                    stime += sol["soltime"]
                    snsols += 1
                    ws.append(sol("W_{total}").magnitude)
                except RuntimeWarning:
                    ws.append(np.nan)
                    faillat.append(l)
                    runagains = False
            else:
                ws.append(np.nan)

            wind = get_windspeed(l, a, 15000, 355)
            cwind = get_windspeed(l, a, np.linspace(0, 15000, 11)[1:], 355)
            if wind > highestwind:
                highestwind = wind
                for vk in Mg.varkeys["V_{wind}"]:
                    if "Climb" in vk.models:
                        Mg.substitutions.update({vk: cwind[vk.idx[0]]})
                    else:
                        Mg.substitutions.update({vk: wind})
            try:
                sol = Mg.solve("mosek")
                gtime += sol["soltime"]
                gnsols += 1
                wg.append(sol("MTOW").magnitude)
            except RuntimeWarning:
                wg.append(np.nan)
                print "Fail, Lat: %d" % l

        pgas.append(wg)
        psolar.append(ws)


    print "Solar: %d solves in %.4f seconds" % (snsols, stime)
    print "Gas: %d solves in %.4f seconds" % (gnsols, gtime)

    indl = psolar[0].index(max(psolar[0]))
    indh = psolar[2].index(max(psolar[2]))
    a = (psolar[2][indh]-psolar[0][indl])/(lat[indh]-lat[indl])
    b = psolar[0][indl]-a*lat[indl]
    c = a*lat[indh+1:indl+1] + b
    ax.fill_between(lat[0:indl+1], psolar[0][0:indl+1], np.append(np.array(psolar[-1][0:indh+1]), c), alpha=0.3, facecolor="b", edgecolor="None")
    psolar[1][np.where(lat == 31)[0][0]] = np.nan
    ax.plot(lat, psolar[1], "b", lw=2)
    ax.plot(lat, pgas[1], "r", lw=2)
    ax.plot(lat, psolar[0], "b")
    ax.plot(lat, psolar[2], "b")
    ax.fill_between(lat, pgas[0], pgas[2], alpha=0.3, facecolor="r", edgecolor="None")
    ax.plot(lat, pgas[0], "r")
    ax.plot(lat, pgas[2], "r")

    for i, p in enumerate(["80%", "90%", "95%"]):
        ax.annotate(p, xy=(36,pgas[i][np.where(lat==36)[0][0]]), xytext=(0.1,-20), textcoords="offset points", arrowprops=dict(arrowstyle="-"), fontsize=12)

    ax.annotate("80%", xy=(30,psolar[0][np.where(lat==30)[0][0]]), xytext=(15,15), textcoords="offset points", arrowprops=dict(arrowstyle="-"), fontsize=12)
    ax.annotate("90%", xy=(28, psolar[1][np.where(lat==28)[0][0]]), xytext=(15,15), textcoords="offset points", arrowprops=dict(arrowstyle="-"), fontsize=12)
    ax.annotate("95%", xy=(27,psolar[2][np.where(lat==27)[0][0]]), xytext=(-30,15), textcoords="offset points", arrowprops=dict(arrowstyle="-"), fontsize=12)

    ax.set_ylim([0, 350])
    ax.set_xlim([20, 40])
    ax.grid()
    ax.set_xlabel("Latitude Requirement [deg]")
    ax.set_ylabel("Max Take Off Weight [lbf]")
    labels = ["$\\pm$" + item.get_text() for item in ax.get_xticklabels()]
    labels = ["$\\pm$%d" % l for l in np.linspace(20, 40, len(labels))]
    ax.set_xticklabels(labels)
    ax.legend(["Solar-electric Powered", "Gas Powered"], fontsize=15, loc=2)
    return fig, ax

if __name__ == "__main__":
    fig, ax = plot_lats()
    if len(sys.argv) > 1:
        path = sys.argv[1]
        fig.savefig(path + "mtowvslat.pdf", bbox_inches="tight")
    else:
        fig.savefig("mtowvslat.pdf", bbox_inches="tight")
