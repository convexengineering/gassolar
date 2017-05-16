from gassolar.solar.solar import Mission
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from relaxed_constants import relaxed_constants
import sys

GENERATE = False

def season():
    days = [80, 52, 21, 355]
    months = ["mar", "feb", "jan", "dec"]

    lats = range(25, 35, 2)
    data = {}
    for l in lats:
        failed = False
        mtows = []
        for d, m in zip(days, months):
            if failed:
                mtows = mtows + [np.nan]*(4-len(mtows))
                break
            M = Mission(latitude=l, day=d, month=m)
            M.cost = M["W_{total}"]
            try:
                sol = M.solve("mosek")
                mtow = sol("W_{total}").magnitude
                mtows.append(mtow)
            except RuntimeWarning:
                feas = relaxed_constants(M)
                sol = feas.solve("mosek")
                bdvars = [d for d in sol.program.varlocs if "Relax" in d.models
                          and sol.program.result(d) >= 1.00001]
                if not bdvars:
                    mtows.append(sol["cost"].magnitude)
                else:
                    mtows.append(np.nan)
                    failed = True

        mtows = np.hstack(mtows)
        data[l] = mtows

    df = pd.DataFrame(data)
    return df

def plot_season(df):
    fig, ax = plt.subplots()
    colors = ["#014636", "#016c59", "#02818a", "#3690c0", "#67a9cf"]
    for d, cl in zip(df, colors):
        ax.plot(range(1, 5), df[d], c=cl, ls="dashed", marker="o", label=d + "$^{\circ}$ Lat")

    ax.set_xlim([0.5, 4.5])
    ax.set_ylim([0, 200])
    ax.set_ylabel("Max Take-off Weight")
    ax.set_xticklabels(["", "6-months", "", "8-months", "", "10-months", "", "12-months"], rotation=-45, ha="left")
    ax.grid()
    ax.legend(loc=2, fontsize=15, numpoints=1)
    return fig, ax

if __name__ == "__main__":

    if len(sys.argv) > 1:
        path = sys.argv[1]
    else:
        path = ""

    if GENERATE:
        df = season()
        df.to_csv("season.generated.csv")
    else:
        df = pd.read_csv("season.generated.csv")
        del df["Unnamed: 0"]

    fig, ax = plot_season(df)
    fig.savefig(path + "season.pdf", bbox_inches="tight")


