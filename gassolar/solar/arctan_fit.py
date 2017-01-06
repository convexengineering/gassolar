from gpfit.fit import fit
from gpfit.evaluate_fit import evaluate_fit
import matplotlib.pyplot as plt
import numpy as np
plt.rcParams.update({'font.size':19})

u = np.linspace(0.01, 1, 100)
w = np.arctan(u)

x = np.log(u)
y = np.log(w)

cn, rm = fit(x, y, 1, "MA")

yfit = evaluate_fit(cn, x, "MA")
fig, ax = plt.subplots()
ax.plot(u, w)
ax.plot(u, np.exp(yfit))
ax.set_xlim([0, 0.7])
ax.grid()
ax.set_xlabel("$V_{gust}/V$")
ax.set_ylabel("$\\arctan{( V_{gust}/V)}$")
ax.legend(["Arctan Fucntion", "Monomial Approximation"])
fig.savefig("../../gassolarpaper/arctanfit.pdf", bbox_inches="tight")
