"wind structural model comparison"
from gassolar.solar.solar_simple.solarsimple import Mission
from gassolar.solar.plotting import windalt_plot
import matplotlib.pyplot as plt

lat = 29
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
fig.savefig("../../gassolarpaper/windaltoper.pdf", bbox_inches="tight")
