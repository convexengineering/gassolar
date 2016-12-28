from gpfit.fit import fit
from gpfit.evaluate_fit import evaluate_fit
import matplotlib.pyplot as plt
import numpy as np

u = np.linspace(0.01, 1, 100)
w = np.arctan(u)

x = np.log(u)
y = np.log(w)

cn, rm = fit(x, y, 1, "MA")

yfit = evaluate_fit(cn, x, "MA")
fig, ax = plt.subplots()
ax.plot(u, w)
ax.plot(u, np.exp(yfit))
ax.grid()
ax.set_xlabel("$x$")
ax.set_ylabel("$\\arctan{x}$")
ax.legend(["Real Fucntion", "Monomial Approximation"])
fig.savefig("../../gassolarpaper/arctanfit.pdf")
