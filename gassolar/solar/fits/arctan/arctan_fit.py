from gpfit.fit import fit
from gpfit.evaluate_fit import evaluate_fit
import matplotlib.pyplot as plt
import numpy as np
import sys
plt.rcParams.update({'font.size':15})

def arctanfit():
    u = np.linspace(0.01, 0.7, 100)
    w = np.arctan(u)

    x = np.log(u)
    y = np.log(w)

    cn, rm = fit(x, y, 1, "MA")
    print "RMS error: %.4f" % rm

    yfit = evaluate_fit(cn, x, "MA")
    fig, ax = plt.subplots()
    ax.plot(u, w, lw=2)
    ax.plot(u, np.exp(yfit), "--", lw=2)
    ax.set_xlim([0, 0.7])
    ax.grid()
    ax.set_xlabel("$V_{\\mathrm{gust}}/V$")
    ax.set_ylabel("$\\alpha_{\\mathrm{gust}}$")
    ax.legend(["$\\arctan{(V_{\\mathrm{gust}}/V)}$",
               "$0.905 (V_{\\mathrm{gust}}/V)^{0.961}$"], loc=2, fontsize=15)
    return fig, ax

if __name__ == "__main__":
    fig, ax = arctanfit()
    if len(sys.argv) > 1:
        path = sys.argv[1]
        fig.savefig(path + "arctanfit.pdf", bbox_inches="tight")
    else:
        fig.savefig("arctanfit.pdf", bbox_inches="tight")
