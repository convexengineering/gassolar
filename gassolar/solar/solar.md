# Solar Simple Write Up

# Simple model of a Gas Powered Aircraft
```python
#inPDF: skip
from solar import Mission
import matplotlib.pyplot as plt
import numpy as np
plt.rcParams.update({'font.size':19})

LATITUDE = True

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
                M.cost = M["b_Mission, Aircraft, Wing"]
                try:
                    sol = M.solve("mosek")
                    W.append(sol("b_Mission, Aircraft, Wing").magnitude)
                except RuntimeWarning:
                    W.append(np.nan)
                    runagain = False
            else:
                W.append(np.nan)
        ax.plot(lat, W)
    
    ax.set_ylim([0, 200])
    ax.grid()
    ax.set_xlabel("Latitude [deg]")
    ax.set_ylabel("Span [ft]")
    ax.legend(["%d Percentile Winds" % a for a in [80, 90, 95]], loc=2, fontsize=15)
    fig.savefig("bvslatsolar.pdf", bbox_inches="tight")
