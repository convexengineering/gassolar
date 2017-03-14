from gpfit.fit import fit
import pandas as pd
import sys
import os
import numpy as np
import matplotlib.pyplot as plt

plt.rcParams.update({'font.size':15})
WEIGHT = 10.0
POWER = 10.0
PATH = (os.path.abspath(__file__).replace(os.path.basename(__file__), "")
        + os.sep)

def plot_powerlaw(csv):
    df = pd.read_csv(csv)
    u = np.array(df["lbs"]/WEIGHT)
    w = np.array(df["hp"]/POWER)

    x = np.log(u)
    y = np.log(w)

    cn, rm = fit(x, y, 1, "MA")
    weight = np.linspace(min(df["lbs"]), max(df["lbs"]), 100)
    yfit = cn.evaluate(np.log(weight/WEIGHT))

    fig, ax = plt.subplots()
    ax.plot(u*WEIGHT, w*POWER, "o", mfc="None", mew=1.5)
    ax.plot(weight, np.exp(yfit)*POWER, lw=2)
    ax.set_xlabel("Engine Weight [lbs]")
    ax.set_ylabel("Maximum Shaft Power [hp]")
    ax.legend(["UND Engine Data", "Power Law Fit"], loc=2)
    ax.grid()
    return fig, ax

if __name__ == "__main__":
    csvname = PATH + "powervsweight.csv"
    fig, ax = plot_powerlaw(csvname)
    if len(sys.argv) > 1:
        path = sys.argv[1]
        fig.savefig(path + "powervsweightfit.pdf", bbox_inches="tight")
    else:
        fig.savefig("powervsweightfit.pdf", bbox_inches="tight")

