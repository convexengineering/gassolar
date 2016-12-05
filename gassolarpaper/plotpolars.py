import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
plt.rcParams.update({'font.size':19})

# df = pd.read_csv("sd7032polar.csv")
# cl = np.arange(0.4, 1.5, 0.1)
# cd = 0.006 + 0.003*cl**1.5 + 0.002*cl**3 + 0.00023*cl**10
# # cd = 0.006 + 0.005*cl**2 + 0.00012*cl**10
#
# fig, ax = plt.subplots()
# ax.plot(df["CL"][df["CL"]>=0.4], df["CD"][df["CL"]>=0.4], "o", markersize=10, markerfacecolor="None")
# ax.plot(cl, cd)
# ax.set_xlabel("$C_L$")
# ax.set_ylabel("$C_D$")
# ax.legend(["XFOIL Data", "Drag Polar Fit"])
# ax.grid()
# fig.savefig("sd7032polar.pdf", bbox_inches="tight")

df = pd.read_csv("jh01polar.csv")
cl = np.arange(0.4, 1.5, 0.1)
cd = (0.33*cl**-0.0809 + 0.645*cl**0.045 + 7.35e-5*cl**12)**(1./0.00544)

fig, ax = plt.subplots()
ax.plot(df["CL"][df["CL"]>=0.4], df["CD"][df["CL"]>=0.4], "o", markersize=10, markerfacecolor="None")
ax.plot(cl, cd)
ax.set_xlabel("$C_L$")
ax.set_ylabel("$C_D$")
ax.legend(["XFOIL Data", "Drag Polar Fit"])
ax.grid()
fig.savefig("jh01polar.pdf", bbox_inches="tight")
