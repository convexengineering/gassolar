"contour map"
import matplotlib.pyplot as plt
import numpy as np
from gassolar.solar.solar_simple.solarsimple import Mission

plt.rcParams.update({'font.size':19})
for av in [85, 90, 95]:
    for l in [35, 40, 45]:
        fig, ax = plt.subplots()
        M = Mission(latitude=l)
        M.substitutions.update({"f_{structures}":
                               ("sweep", np.linspace(0.2, 0.5, 10))})
        M.substitutions.update({"h_{batt}":
                               ("sweep", np.linspace(250, 400, 10))})
        M.substitutions.update({"W_{pay}": 10})
        for vk in M.varkeys["\\eta_{prop}"]:
            M.substitutions.update({vk: 0.75})
        for vk in M.varkeys["p_{wind}"]:
            M.substitutions.update({vk: av/100.0})
        for vk in M.varkeys["CDA_0"]:
            M.substitutions.update({vk: 0.002})
        M.cost = M["b"]
        sol = M.solve("mosek", skipsweepfailures=True)
        x = np.reshape(sol("f_{structures}"), [10, 10])
        y = np.reshape(sol("h_{batt}"), [10, 10])
        z = np.reshape(sol("b"), [10, 10])
        levels = np.array(range(50, 2000, 50)+ [2300])
        if av == 90:
            v = np.array(range(50, 700, 50)+ [2300])
        else:
            v = np.array(range(50, 400, 50)+ [2300])
        a = ax.contour(x, y, z, levels, colors="k")
        ax.clabel(a, v, inline=1, fmt="%d [ft]")
        ax.set_xlabel("Structural Fraction")
        ax.set_ylabel("Battery Energy Density [Whr/kg]")
        fig.savefig("../../../gassolarpaper/bcontourl%da%d.pdf" % (l, 85),
                    bbox_inches="tight")
