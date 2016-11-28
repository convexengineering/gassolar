" fitting wind speed data "
import numpy as np
from gpfit.fit import fit
from wind_speeds import get_windspeed
import matplotlib.pyplot as plt

def fit_setup(altitude=[50000, 70000], latitude=[30, 45], percentage=90):

    N = 20
    wind = []
    altitude = np.linspace(altitude[0], altitude[1], N)
    for l in range(latitude[0], latitude[1]+1, 1):
        wind.append(get_windspeed(l, percentage, altitude, 355))

    lats = range(latitude[0], latitude[1]+1, 1)*N
    alts = [[a]*(latitude[1]-latitude[0] + 1) for a in altitude]

    u1 = lats
    u2 = np.hstack(alts)/1000
    if np.diff(latitude)[0] == 0:
        u = u2
    else:
        u = [u1, u2]
    w = np.hstack(wind)
    x = np.log(u)
    y = np.log(w)

    return x, y

def sweep_lats(lat_low, K=3, fn="SMA"):

    error = []
    for l in lat_low:
        x, y = fit_setup(latitude=[l, 45])
        cn, rm = fit(x, y, K, fn)
        error.append(rm)

    return error

def plot_errors(x, y, xlabel, ylabel):
    fig, ax = plt.subplots()
    ax.plot(x, y)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    return fig, ax

def return_fitSMA(u_1):

    "K=3"
    # w = (132960 * (u_1)**-2.38864 + 9.23163e-05 * (u_1)**2.73706
    #      + 8356.28 * (u_1)**-4.01751)**(1/0.763341)
    "K=4, RMS=0.004059"
    w = (1.16012e+180 * (u_1)**-97.6238 + 7.97629e+134 * (u_1)**-120.996
         + 2.31229e-93 * (u_1)**123.733
         + 3.24369e+213 * (u_1)**-46.4295)**(1/86.4913)

    "K=5, RMS=0.0154"
    # w = (3540.95 * (u_1)**-2.26982 + 4681.92 * (u_1)**-2.26415
    #      + 3345.87 * (u_1)**-1.95286 + 1.60184 * (u_1)**-3.46449
    #      + 0.00256264 * (u_1)**1.67464)**(1/0.420148)
    return w

def return_fitMA(u):

    w = []
    for u_1 in u:
        w1 = 0.946766 * (u_1)**0.809363
        w2 = 48550.4 * (u_1)**-1.80477
        w.append(max([w1, w2]))
    return w

def plot_fit(altitude):

    alt = np.linspace(50, 70, 100)
    fig, ax = plt.subplots()
    wfit = return_fitSMA(alt)
    wdata = get_windspeed(45, 90, altitude*1000, 355)
    ax.plot(wdata, altitude, "bo")
    ax.plot(wfit, alt, "b-")
    ax.set_xlabel("wind speed [m/s]")
    ax.set_ylabel("altitude [kft]")
    ax.set_xlim([0, max(np.concatenate((wdata, wfit)))])
    ax.grid()
    return fig, ax

if __name__ == "__main__":
    # RMS = sweep_lats(range(30, 46, 1))
    # F, A = plot_errors(range(30, 46, 1), RMS, "lower lat", "RMS")
    # F.savefig("laterror.pdf")
    # X, Y = fit_setup(latitude=[45, 45])
    # cn, rm = fit(X, Y, 3, "SMA")

    # F, A = plot_fit(np.linspace(50, 70, 20))
    # F.savefig("windaltfit.pdf")
    fig, ax = plt.subplots()
    wind = []
    for l in range(20, 46, 1):
        wind.append(get_windspeed(l, 90, 50000, 355))
    ax.loglog(wind, range(20, 46, 1))
    fig.savefig("windlatlog.pdf")
    u = range(20, 46, 1)
    w = wind
    x = np.log(u)
    y = np.log(w)
    cn, rm = fit(x, y, 1, "SMA")



