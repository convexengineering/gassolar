# Gas Simple Write Up

# Simple model of a Gas Powered Aircraft
```python
#inPDF: skip
from gassimple import Mission
from gassolar.gas.gas import Mission as Gas
from gassolar.environment.wind_speeds import get_windspeed
from gpkit.tools.autosweep import sweep_1d
import matplotlib.pyplot as plt
import numpy as np
plt.rcParams.update({'font.size':19})

END = False 
LAT = False 
COMP = True

""" Endurance """
if END:
    M = Mission()
    M.cost = M["MTOW"]
    M.substitutions.update({"W_{pay}": 10})
    for e in M.varkeys["\\eta_{prop}"]:
        M.substitutions.update({e: 0.75})
    for cd in M.varkeys["CDA_0"]:
        M.substitutions.update({cd: 0.01})
    fig, ax = plt.subplots()
    lower = 1
    upper = 10 
    xmin_ = np.linspace(lower, upper, 100)
    tol = 0.05
    for p in [85, 90, 95]:
        notpassing = True
        while notpassing:
            wind = get_windspeed(38, p, 15000, 355)
            cwind = get_windspeed(38, p, np.linspace(0, 15000, 11)[1:], 355)
            for vk in M.varkeys["V_{wind}"]:
                if "Climb" in vk.models:
                    M.substitutions.update({vk: cwind[vk.idx[0]]})
                else:
                    M.substitutions.update({vk: wind})
            try:
                bst = sweep_1d(M, tol, M["t_Mission, Loiter"], [lower, upper], solver="mosek")
                notpassing = False
            except RuntimeWarning:
                notpassing = True
                upper -= 0.1
                xmin_ = np.linspace(lower, upper, 100)
    
        ax.plot(xmin_, bst["cost"].__call__(xmin_))
    ax.grid()
    ax.set_ylim([0, 1000])
    ax.set_xlabel("Endurance [days]")
    ax.set_ylabel("Max Take Off Weight [lbf]")
    ax.legend(["%d Percentile Winds" % a for a in [85, 90, 95]], loc=2, fontsize=15)
    fig.savefig("../../../gassolarpaper/mtowvsendsimple.pdf", bbox_inches="tight")

""" Simple Detailed Comparison """

if COMP:
    M = Mission()
    G = Gas()
    M.cost = M["MTOW"]
    G.cost = G["MTOW"]
    M.substitutions.update({"W_{pay}": 10})
    G.substitutions.update({"W_{pay}": 10})
    for e in M.varkeys["\\eta_{prop}"]:
        M.substitutions.update({e: 0.75})
    for e in G.varkeys["\\eta_{prop}"]:
        G.substitutions.update({e: 0.75})
    for cd in M.varkeys["CDA_0"]:
        M.substitutions.update({cd: 0.01})
    fig, ax = plt.subplots()
    lower = 1
    upper = 10 
    xmin_ = np.linspace(lower, upper, 100)
    tol = 0.05
    notpassing = True
    while notpassing:
        wind = get_windspeed(38, 90, 15000, 355)
        cwind = get_windspeed(38, 90, np.linspace(0, 15000, 11)[1:], 355)
        for vk in M.varkeys["V_{wind}"]:
            if "Climb" in vk.models:
                M.substitutions.update({vk: cwind[vk.idx[0]]})
            else:
                M.substitutions.update({vk: wind})
        try:
            bst = sweep_1d(M, tol, M["t_Mission, Loiter"], [lower, upper], solver="mosek")
            notpassing = False
        except RuntimeWarning:
            notpassing = True
            upper -= 0.1
            xmin_ = np.linspace(lower, upper, 100)
    
    notpassing = True
    while notpassing:
        wind = get_windspeed(38, 90, 15000, 355)
        cwind = get_windspeed(38, 90, np.linspace(0, 15000, 11)[1:], 355)
        for vk in G.varkeys["V_{wind}"]:
            if "Climb" in vk.models:
                G.substitutions.update({vk: cwind[vk.idx[0]]})
            else:
                G.substitutions.update({vk: wind})
        try:
            bstg = sweep_1d(G, tol, G["t_Mission, Loiter"], [lower, upper], solver="mosek")
            notpassing = False
        except RuntimeWarning:
            notpassing = True
            upper -= 0.1
            xmin_ = np.linspace(lower, upper, 100)
    
    ax.plot(xmin_, bst["cost"].__call__(xmin_))
    ax.plot(xmin_, bstg["cost"].__call__(xmin_))
    ax.grid()
    ax.set_ylim([0, 1000])
    ax.set_xlabel("Endurance [days]")
    ax.set_ylabel("Max Take Off Weight [lbf]")
    ax.legend(["Simple", "Detailed"])
    fig.savefig("../../../gassolarpaper/simpdetcomp.pdf", bbox_inches="tight")

""" contour """
# av = 85
# for l in [35, 45]:
#     fig, ax = plt.subplots()
#     S = Mission(latitude=l, percent=av, altitude=60000, day=355)
#     S.substitutions.update({"f_{structures}": ("sweep", np.linspace(0.2, 0.5, 10))})
#     S.substitutions.update({"h_{batt}": ("sweep", np.linspace(250, 400, 10))})
#     S.substitutions.update({"W_{pay}": 10})
#     S.substitutions.update({"\\eta_{prop}": 0.75})
#     S.substitutions.update({"CDA_0": 0.002})
#     S.cost = S["b"]
#     sol = S.solve("mosek", skipsweepfailures=True)
#     x = np.reshape(sol("f_{structures}"), [10, 10])
#     y = np.reshape(sol("h_{batt}"), [10, 10])
#     z = np.reshape(sol("b"), [10, 10])
#     print z
#     levels = np.array(range(50, 2000, 50)+ [2300])
#     if av == 90:
#         v = np.array(range(50, 700, 50)+ [2300])
#     else:
#         v = np.array(range(50, 400, 50)+ [2300])
#     a = ax.contour(x, y, z, levels, colors="k")
#     ax.clabel(a, v, inline=1, fmt="%d [ft]")
#     ax.set_xlabel("Structural Fraction")
#     ax.set_ylabel("Battery Energy Density [Whr/kg]")
#     fig.savefig("bcontourl%da%d.pdf" % (l, 85), bbox_inches="tight")

""" latitutde """
# fig, ax = plt.subplots()
# lat = np.arange(0, 60, 1)
# for a in [80, 85, 90, 95]:
#     mtow = []
#     for l in lat:
#         S = Mission(latitude=l, percent=a, altitude=60000)
#         S.substitutions.update({"W_{pay}": 10})
#         S.substitutions.update({"\\eta_{prop}": 0.75})
#         S.substitutions.update({"CDA_0": 0.002})
#         try:
#             sol = S.solve("mosek")
#             mtow.append(sol("W").magnitude)
#         except RuntimeWarning:
#             mtow.append(np.nan)
#     ax.plot(lat, mtow)
# 
# ax.set_ylim([0, 1000])
# ax.grid()
# ax.set_xlabel("Latitude [deg]")
# ax.set_ylabel("Max take off weight [lbf]")
# ax.legend(["%d Percentile Winds" % a for a in [80, 85, 90, 95]], loc=2, fontsize=15)
# fig.savefig("mtowvslatsolar.pdf", bbox_inches="tight")

""" latitutde mtow """
if LAT:
    fig, ax = plt.subplots()
    lat = np.arange(0, 60, 1)
    M = Mission()
    M.substitutions.update({"W_{pay}": 10})
    for e in M.varkeys["\\eta_{prop}"]:
        M.substitutions.update({e: 0.75})
    for cd in M.varkeys["CDA_0"]:
        M.substitutions.update({cd: 0.01})
    M.substitutions.update({"t_Mission, Loiter": 7})
    M.cost = M["MTOW"]
    for a in [80, 90, 95]:
        mtow = []
        wind = []
        for l in lat:
            wind.append(get_windspeed(l, a, 15000, 355))
            maxwind = max(wind)
            for v in M.varkeys["V_{wind}"]:
                M.substitutions.update({v: maxwind})
            try:
                sol = M.solve("mosek")
                mtow.append(sol("MTOW").magnitude)
            except RuntimeWarning:
                mtow.append(np.nan)
        ax.plot(lat, mtow)
    
    ax.set_ylim([0, 1000])
    ax.grid()
    ax.set_xlabel("Latitude [deg]")
    ax.set_ylabel("Max Take Off Weight [lbf]")
    ax.legend(["%d Percentile Winds" % a for a in [80, 90, 95]], loc=2, fontsize=15)
    fig.savefig("../../../gassolarpaper/mtowvslatgassimple.pdf", bbox_inches="tight")
```
