# Gas Simple Write Up

# Simple model of a Gas Powered Aircraft
```python
#inPDF: skip
from gas import Mission
from gassolar.environment.wind_speeds import get_windspeed
import matplotlib.pyplot as plt
from gpkit.tools.autosweep import sweep_1d
import numpy as np
plt.rcParams.update({'font.size':19})

END = False
LAT = True
DRAG = False
BSFC = False

""" MTOW vs Endurance """

if END:
    plt.rcParams.update({'font.size':15})
    M = Mission()
    M.cost = M["MTOW"]
    fig, ax = plt.subplots()
    lower = 1
    upper = 12 
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
    fig.savefig("../../gassolarpaper/mtowvsendurance.pdf", bbox_inches="tight")

""" latitutde mtow """
if LAT:
    plt.rcParams.update({'font.size':15})
    fig, ax = plt.subplots()
    lat = np.arange(0, 60, 1)
    M = Mission()
    M.substitutions.update({"W_{pay}": 10})
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
    
    ax.set_ylim([0, 600])
    ax.set_xlim([20, 50])
    ax.grid()
    ax.set_xlabel("Latitude [deg]")
    ax.set_ylabel("Max Take Off Weight [lbf]")
    labels = ["$\\pm$" + item.get_text() for item in ax.get_xticklabels()]
    labels = ["$\\pm$%d" % l for l in np.linspace(20, 50, len(labels))]
    ax.set_xticklabels(labels)
    ax.legend(["%d Percentile Winds" % a for a in [80, 90, 95]], loc=2, fontsize=15)
    fig.savefig("../../gassolarpaper/mtowvslatgas.pdf", bbox_inches="tight")

if DRAG:
    M = Mission()
    M.cost = M["MTOW"]
    for e in M.varkeys["\\eta_{prop}"]:
        M.substitutions.update({e: 0.75})
    fig, ax = plt.subplots(3)
    wind = get_windspeed(38, 90, 15000, 355)
    cwind = get_windspeed(38, 90, np.linspace(0, 15000, 11)[1:], 355)
    for vk in M.varkeys["V_{wind}"]:
        if "Climb" in vk.models:
            M.substitutions.update({vk: cwind[vk.idx[0]]})
        else:
            M.substitutions.update({vk: wind})
    M.substitutions.update({"t_Mission, Loiter": ("sweep", np.linspace(1, 10, 10))})
    sol = M.solve("mosek", skipsweepfailures=True)
    
    ax[0].plot(sol("t_Mission, Loiter"), [np.average(sv) for sv in sol("CDA_Mission, Loiter, FlightSegment, AircraftPerf")])
    ax[0].plot([1,10], [0.01, 0.01])
    ax[0].legend(["Component Drag Build Up", "Simple Model Approximation"], loc=3)
    ax[0].set_ylabel("Non-wing Drag Coefficient $C_{d_0}$")
    ax[0].set_xlabel("Endurance [days]")
    ax[0].grid()
    ax[1].plot(sol("t_Mission, Loiter"), [sum([sol(sv)[i] for sv in sol("W") if len(M[sv].descr["models"])==3]).magnitude/sol("MTOW")[i].magnitude for i in range(10)])
    ax[2].plot(sol("t_Mission, Loiter"), [np.average(sol("BSFC_Mission, Loiter, FlightSegment, AircraftPerf, EnginePerf")[i]) for i in range(10)])
    fig.savefig("analysis.pdf", bbox_inches="tight")

if BSFC:
    M = Mission()
    M.cost = M["MTOW"]
    for e in M.varkeys["\\eta_{prop}"]:
        M.substitutions.update({e: 0.75})
    fig, ax = plt.subplots()
    wind = get_windspeed(38, 90, 15000, 355)
    cwind = get_windspeed(38, 90, np.linspace(0, 15000, 11)[1:], 355)
    for vk in M.varkeys["V_{wind}"]:
        if "Climb" in vk.models:
            M.substitutions.update({vk: cwind[vk.idx[0]]})
        else:
            M.substitutions.update({vk: wind})
    M.substitutions.update({"t_Mission, Loiter": 7})
    sol = M.solve("mosek")
    t = [sum(sol("t_Mission, Loiter, FlightSegment, BreguetEndurance")[:i]).magnitude for i in range(1,6)]
    ax.plot(t, sol("BSFC_Mission, Loiter, FlightSegment, AircraftPerf, EnginePerf"))
    ax.set_ylabel("Brake Specific Fuel Consumption $BSFC$ [lb/hp/hr]")
    ax.set_xlabel("Elapsed Mission Time [days]")
    ax.grid()
    fig.savefig("../../gassolarpaper/bsfcmission.pdf", bbox_inches="tight")
```
