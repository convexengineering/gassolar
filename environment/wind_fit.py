" fitting wind speed data "
import numpy as np
from wind_speeds import get_windspeed

def fit_setup(altitude=[50000, 70000], latitude=[30, 45], percentage=90):

    N = 20
    wind = []
    altitude = np.linspace(altitude[0], altitude[1], N)
    for l in range(latitude[0], latitude[1]+1, 1):
        wind.append(get_windspeed(l, percentage, altitude, 355))

    lats = range(latitude[0], latitude[1]+1, 1)*N
    alts = [[a]*(latitude[1]-latitude[0] + 1) for a in altitude]

    u1 = lats
    u2 = np.hstack(alts)
    u = [u1, u2]
    w = np.hstack(wind)
    x = np.log(u)
    y = np.log(w)

    return x, y

if __name__ == "__main__":
    x, y = fit_setup()


