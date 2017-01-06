# Solar Simple Write Up

# Simple model of a Gas Powered Aircraft
```python
#inPDF: skip
from solar import Mission
import matplotlib.pyplot as plt
import numpy as np
from plotting import windalt_plot
plt.rcParams.update({'font.size':19})

LATITUDE = False
LOADING = False
WIND = True

""" loading """
if LOADING:
    M = Mission(latitude=31)
    M.cost = M["W_{total}"]
    sol = M.solve("mosek")
    eta = np.linspace(0, 1, 100)
    gbar = 4/np.pi*(1+(sol("W_{cent}")/sol("W_{wing}")).magnitude)*(1-eta)**0.5
    print "f_{cent/wing} = %.3f" % (sol("W_{cent}")/sol("W_{wing}")).magnitude
    l = sol("\\lambda_Mission, Aircraft, Wing")
    cbar = 2/(1+l)*((l-1)*eta + 1)
    fig, ax = plt.subplots()
    ax.plot(eta, cbar)
    ax.plot(eta, gbar)
    ax.set_xlabel("$2y/b$")
    ax.set_ylabel("local $c_l$ / local chord")
    ax.legend(["local chord", "local $c_l$"])
    ax.grid()
    fig.savefig("../../gassolarpaper/gustvschord.pdf")

""" latitutde """
if LATITUDE:
    fig, ax = plt.subplots()
    lat = np.arange(20, 60, 1)
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
                M.cost = M["W_{total}"]
                try:
                    sol = M.solve("mosek")
                    W.append(sol("W_{total}").magnitude)
                except RuntimeWarning:
                    W.append(np.nan)
                    runagain = False
            else:
                W.append(np.nan)
        ax.plot(lat, W)
    
    ax.set_ylim([0, 400])
    ax.set_xlim([20, 60])
    ax.grid()
    ax.set_xlabel("Latitude [deg]")
    ax.set_ylabel("Max Take Off Weight [lbf]")
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


