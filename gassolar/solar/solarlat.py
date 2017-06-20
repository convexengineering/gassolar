"solar latitude sweep"
import sys
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from gassolar.solar.solar import Mission

# pylint: disable=invalid-name

plt.rcParams.update({'font.size':15})
def solarlat(latrange, day=355):
    """
    sweeps of latitude
    INPUTS
        latrange:           range of desired latitude
                                list
        day=355:            day of the year (355=Dec 21st)
                                int
    OUTPUTS
        df:                 dataframe
    """
    data = {"latitude": latrange}
    for a in [80, 90, 95]:
        W = []
        runagain = True
        for l in latrange:
            if runagain:
                M = Mission(latitude=l, day=day)
                for vk in M.varkeys["p_{wind}"]:
                    M.substitutions.update({vk: a/100.0})
                M.cost = M["W_{total}"]
                try:
                    sol = M.solve("mosek")
                    W.append(sol("W_{total}").magnitude)
                except RuntimeWarning:
                    W.append(np.nan)
                    runagain = False
            else:
                W.append(np.nan)
        data["%d" % a] = W
    df = pd.DataFrame(data)
    return df

def plot_solarlat(df):
    " plot latitude sweep "

    fig, ax = plt.subplots()
    ax.plot(df["latitude"], df["80"], lw=1, c="b")
    ax.plot(df["latitude"], df["90"], lw=2, c="b")
    ax.plot(df["latitude"], df["95"], lw=1, c="b")

    i80 = df["80"][df["80"] == max(df["80"])].index[0]
    i90 = df["90"][df["90"] == max(df["90"])].index[0]
    i95 = df["95"][df["95"] == max(df["95"])].index[0]
    a = (df["80"][i80] - df["95"][i95])/(df["latitude"][i80] -
                                         df["latitude"][i95])
    b = df["95"][i95] - a*df["latitude"][i95]
    c = a*df["latitude"][i95 + 1:i80 + 1] + b
    df["95"][i95 + 1:i95 + 1 + len(c)] = c
    ax.fill_between(df["latitude"], df["80"], df["95"], alpha=0.3,
                    facecolor="b", edgecolor="None")

    ax.set_ylim([0, df["95"][i95]*2])
    ax.set_xlim([min(df["latitude"]), max(df["latitude"])])
    ax.grid()
    ax.set_xlabel("Latitude Requirement [deg]")
    ax.set_ylabel("Max Take Off Weight [lbf]")
    labels = ["$\\pm$" + item.get_text() for item in ax.get_xticklabels()]
    labels = ["$\\pm$%d" % l for l in
              np.linspace(min(df["latitude"]), max(df["latitude"]),
                          len(labels))]
    ax.set_xticklabels(labels)
    for ind, a in zip([i80, i90, i95], ["80", "90", "95"]):
        ax.text(df["latitude"][ind], df[a][ind], a + "%", fontsize=14)
    return fig, ax

def test():
    " unit test "
    _ = solarlat([15])

if __name__ == "__main__":

    GEN = False

    if GEN:
        Latrange = range(20, 41)
        d = solarlat(Latrange)
        d.to_csv("solarlat.generated.csv")
        Latrange = range(1, 26)
        dfsum = solarlat(Latrange, day=141)
        dfsum.to_csv("solarlatsum.generated.csv")
    else:
        d = pd.read_csv("solarlat.generated.csv")
        del d["Unnamed: 0"]
        dfsum = pd.read_csv("solarlatsum.generated.csv")
        del dfsum["Unnamed: 0"]

    f, _ = plot_solarlat(d)
    figsum, _ = plot_solarlat(dfsum)
    if len(sys.argv) > 1:
        path = sys.argv[1]
        f.savefig(path + "solarlat.pdf", bbox_inches="tight")
        figsum.savefig(path + "solarlatsum.pdf", bbox_inches="tight")
    else:
        f.savefig("solarlat.pdf", bbox_inches="tight")
        figsum.savefig("solarlatsum.pdf", bbox_inches="tight")
