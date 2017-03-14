"wind structural model comparison"
from gassolar.solar.plotting import windalt_plot
import matplotlib.pyplot as plt
import sys

def plot_structm(num, lat=29):
    if num == 0:
        fig, ax = windalt_plot(lat)
    elif num == 1:
        from gassolar.solar.solar import Mission
        M = Mission(latitude=lat)
        M.cost = M["W_{total}"]
        sol2 = M.solve("mosek")
        fig, ax = windalt_plot(lat, sol1=sol2)
        ax.annotate("detailed structural model", xy=(58, 50), xytext=(61, 65),
                    arrowprops=dict(facecolor='black', shrink=0.05, width=1.5,
                                    headwidth=10))
    elif num == 2:
        from gassolar.solar.solar_simple.solarsimple import Mission
        M = Mission(latitude=lat)
        for vk in M.varkeys["CDA_0"]:
            M.substitutions.update({vk: 0.002})
        M.cost = M["W"]
        sol1 = M.solve("mosek")
        from gassolar.solar.solar import Mission
        M = Mission(latitude=lat)
        M.cost = M["W_{total}"]
        sol2 = M.solve("mosek")
        fig, ax = windalt_plot(lat, sol1, sol2)
        ax.annotate("structural weight fraction", xy=(66.2, 30), xytext=(46, 10),
                    arrowprops=dict(facecolor='black', shrink=0.05, width=1.5,
                                    headwidth=10))
        ax.annotate("detailed structural model", xy=(58, 50), xytext=(61, 65),
                    arrowprops=dict(facecolor='black', shrink=0.05, width=1.5,
                                    headwidth=10))

    return fig, ax

if __name__ == "__main__":
    for num in [0, 1, 2]:
        fig, ax = plot_structm(num)
        if len(sys.argv) > 1:
            path = sys.argv[1]
            fig.savefig(path + "windaltoper%d.pdf" % num, bbox_inches="tight")
        else:
            fig.savefig("windaltoper.pdf", bbox_inches="tight")
