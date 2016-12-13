" fitting wind speed data "
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from gassolar.environment.wind_speeds import get_windspeed, interpolate
from gpfit.fit import fit
from gpfit.evaluate_fit import evaluate_fit
from gpfit.max_affine import max_affine
from gpfit.softmax_affine import softmax_affine
from gpfit.implicit_softmax_affine import implicit_softmax_affine
plt.rc("text", usetex=True)

def fit_setup(altitude=(40000, 80000), latitude=45):
    """
    Function that sets up the fit for altitude versus density. Density in
    10^-1 kg/m^3

    Inputs
    ------
    altitude: tuple - two values for the upper and lower bound of altitude
              range (ex. (40000, 80000)). Altitude in ft
    latitude: int - latitude of earth in degrees
    percentage: int - percentile wind speeds

    Outputs
    ------
    x: 1D array of x values for fit
    y: 1D array of y values for fit

    """

    N = 20
    percentiles = range(75, 100, 5) + [99]
    altitude = np.linspace(altitude[0], altitude[1], N)
    df = pd.read_csv("usstd_atm.csv")
    wind = []
    ps = []
    for p in percentiles:
        wind.append(get_windspeed(latitude, p, altitude, 355))
        ps.append([p]*len(altitude))

    hm = altitude*0.3048
    density = []
    for h in hm:
        indh = df["Altitude"][df["Altitude"] > h].index[0]
        indl = indh-1
        xs = [df["Altitude"][indl], df["Altitude"][indh]]
        ys = [df["Density"][indl], df["Density"][indh]]
        density.append(interpolate(xs, ys, h))

    u1 = np.hstack([density]*len(percentiles))
    u2 = np.hstack(ps)
    w = np.hstack(wind)
    x = np.log([u1, u2])
    y = np.log(w)

    return x, y

def plot_fits(xdata, ydata, yfit):

    x1 = np.flipud(np.unique(xdata[0]))
    x2 = np.unique(xdata[1])
    colors = ["b", "r", "g", "m", "k", "y"]
    assert len(colors) == len(x2)
    fig, ax = plt.subplots()
    for p, y, yf, cl in zip(x2, ydata.reshape(len(x2), len(x1)),
                            yfit.reshape(len(x2), len(x1)), colors):
        ax.plot(np.exp(x1), np.exp(y), "o", c=cl)
        ax.plot(np.exp(x1), np.exp(yf), c=cl,
                label="%d Percentile Winds" % np.rint(np.exp(p)))
    ax.legend(fontsize=8)
    ax.set_xlabel("Air Density $10^{-1}$ [kg/m$^3$]")
    ax.set_ylabel("Wind Speed [m/s]")
    ax.grid()
    return fig, ax

if __name__ == "__main__":

    X, Y = fit_setup()
    cns, rm = fit(X, Y, 4, "SMA")

    yfit = evaluate_fit(cns, X, "SMA")
    fig, ax = plot_fits(X, Y, yfit)

    fig.savefig("testfit.pdf")
