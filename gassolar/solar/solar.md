# Solar Simple Write Up

# Simple model of a Gas Powered Aircraft
```python
#inPDF: skip
from solar import Mission
import matplotlib.pyplot as plt
import numpy as np
from plotting import windalt_plot, labelLines

LATITUDE = True
WIND = False
CON = False
COMP = False

""" contour """

if CON:
    plt.rcParams.update({'font.size':19})
    etasolar = np.linspace(0.15, 0.5, 15)
    hbatts = np.linspace(250, 400, 15)
    x = np.array([etasolar]*15)
    y = np.array([hbatts]*15).T
    z = np.zeros([15, 15])
    for av in [80, 85, 90, 95]:
        for l in [25, 30, 35, 40]:
            fig, ax = plt.subplots()
            M = Mission(latitude=l)
            M.substitutions.update({"W_{pay}": 10})
            for vk in M.varkeys["\\eta_{prop}"]:
                M.substitutions.update({vk: 0.75})
            for vk in M.varkeys["p_{wind}"]:
                M.substitutions.update({vk: av/100.0})
            M.cost = M["b_Mission, Aircraft, Wing"]
            for i, etas in enumerate(etasolar):
                for vk in M.varkeys["\\eta_{solar}"]: 
                    M.substitutions.update({vk: etas})
                for j, hbs in enumerate(hbatts):
                    M.substitutions.update({"h_{batt}": hbs})
                    try:
                        sol = M.solve("mosek")
                        z[i, j] = sol("b_Mission, Aircraft, Wing").magnitude
                        print "Pass: Latitude = %d, Percentile Winds = %d" % (l, av)
                    except RuntimeWarning:
                        z[i, j] = np.nan
                        print "Fail: Latitude = %d, Percentile Winds = %d" % (l, av)
            levels = np.array(range(30, 2000, 10)+ [2300])
            if av == 90:
                v = np.array(range(30, 700, 10)+ [2300])
            else:
                v = np.array(range(30, 400, 10)+ [2300])
            a = ax.contour(x, y, z, levels, colors="k")
            ax.clabel(a, v, inline=1, fmt="%d [ft]")
            ax.set_xlabel("Solar Cell Efficiency")
            ax.set_ylabel("Battery Energy Density [Whr/kg]")
            fig.savefig("../../gassolarpaper/bcontourl%da%d.pdf" % (l, av), 
                        bbox_inches="tight")

""" objective comparison """
if COMP:
    plt.rcParams.update({'font.size':15})
    fig, ax = plt.subplots()
    ax2 = ax.twinx()
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
                M.substitutions.update({"\\rho_{solar}": 0.25})
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
            la = "Obj: $b$"
            ty = ""
        else:
            la = "Obj: $S_{\\mathrm{solar}}$"
            ty = "--"
        ll = ax.plot(lat, W, "b%s" % ty, label=la)
        ll1 = ax2.plot(lat, SS, 'r%s' % ty, label=la)
        if obj[0] == "b":
            l1.append(ll)
            l2.append(ll1)
        else:
            l1.append(ll1)
            l2.append(ll)
    
    for tl in ax.get_yticklabels():
        tl.set_color('b')
    for tl in ax2.get_yticklabels():
        tl.set_color('r')
    ax.set_ylim([0, 200])
    ax.set_xlim([20, 40])
    l1 = [l[0] for l in l1]
    l2 = [l[0] for l in l2]
    labelLines(l1, fontsize=10, zorder=2.5, va="top", color="k", align=False, xvals=[25.5, 29])
    labelLines(l2, fontsize=10, zorder=2.5, va="bottom", color="k", align=False, xvals=[29, 25.5])
    # ax.text(22.5, 55, "Wing Span [ft]")
    # ax.text(30.5, 10, "Solar Cells Area [ft$^2$]")
    ax.grid()
    ax.set_xlabel("Latitude Requirement [deg]")
    ax.set_ylabel("Wing Span $b$ [ft]", color="b")
    ax2.set_ylabel("Solar Cell Area $S_{\\mathrm{solar}}$ [ft$^2$]", color="r")
    labels = ["$\\pm$" + item.get_text() for item in ax.get_xticklabels()]
    labels = ["$\\pm$%d" % l for l in np.linspace(20, 40, len(labels))]
    ax.set_xticklabels(labels)
    # ax.legend(["Objective: Wing Span", "Objective: Solar Cell Area"], loc=2, fontsize=15)
    fig.savefig("../../gassolarpaper/solarobjcomp.pdf", bbox_inches="tight")

""" latitutde """
if LATITUDE:
    plt.rcParams.update({'font.size':15})
    fig, ax = plt.subplots()
    lat = np.arange(21, 60, 1)
    for a in [80, 90, 95]:
        W = []
        runagain = True
        for l in lat:
            if runagain:
                M = Mission(latitude=l)
                M.substitutions.update({"W_{pay}": 10})
                for vk in M.varkeys["p_{wind}"]:
                    M.substitutions.update({vk: a/100.0})
                M.substitutions.update({"\\rho_{solar}": 0.25})
                # M.cost = M["b_Mission, Aircraft, Wing"]
                M.cost = M["W_{total}"]
                try:
                    sol = M.solve("mosek")
                    # W.append(sol("b_Mission, Aircraft, Wing").magnitude)
                    mn = [max(M[sv].descr["modelnums"]) for sv in sol("(E/S)_{irr}") if abs(sol["sensitivities"]["constants"][sv]) > 0.01][0]
                    Poper = [sol(sv) for sv in sol("P_{oper}") if mn in 
                             M[sv].descr["modelnums"]][0]
                    print Poper/sol("\\eta_{solar}")/sol("S_Mission, Aircraft, SolarCells")
                    W.append(sol("W_{total}").magnitude)
                except RuntimeWarning:
                    W.append(np.nan)
                    runagain = False
            else:
                W.append(np.nan)
        ax.plot(lat, W)
    
    ax.set_ylim([0, 600])
    ax.set_xlim([20, 45])
    ax.grid()
    ax.set_xlabel("Latitude Requirement [deg]")
    ax.set_ylabel("Max Take Off Weight [lbf]")
    labels = ["$\\pm$" + item.get_text() for item in ax.get_xticklabels()]
    labels = ["$\\pm$%d" % l for l in np.linspace(20, 45, len(labels))]
    ax.set_xticklabels(labels)
    ax.legend(["%d Percentile Winds" % a for a in [80, 90, 95]], loc=2, fontsize=15)
    fig.savefig("../../gassolarpaper/mtowvslatsolar.pdf", bbox_inches="tight")

""" wind operating """
if WIND:
    M = Mission(latitude=31)
    M.substitutions.update({"W_{pay}": 10})
    M.substitutions.update({"\\rho_{solar}": 0.25})
    M.cost = M["W_{total}"]
    sol = M.solve("mosek")
    fig, ax = windalt_plot(31, sol)
    fig.savefig("../../gassolarpaper/windaltoper.pdf", bbox_inches="tight")


