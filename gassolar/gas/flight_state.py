" flight state of gas powered aircraft "
from gpkit import Model, Variable
from gassolar.environment.wind_speeds import get_windspeed
from gassolar.environment.air_properties import get_airvars
class FlightState(Model):
    """
    environmental state of aircraft

    inputs
    ------
    latitude: earth latitude [deg]
    altitude: flight altitude [ft]
    percent: percentile wind speeds [%]
    day: day of the year [Jan 1st = 1]
    """
    def setup(self, Vwind, latitude=45, percent=90, altitude=15000, day=355):

        # wind = get_windspeed(latitude, percent, altitude, day)
        density, vis = get_airvars(altitude)

        # Vwind = Variable("V_{wind}", wind, "m/s", "wind velocity")
        mfac = Variable("m_{fac}", 1.0, "-", "wind speed margin factor")
        V = self.V = Variable("V", "m/s", "true airspeed")
        rho = self.rho = Variable("\\rho", density, "kg/m**3", "air density")
        mu = self.mu = Variable("\\mu", vis, "N*s/m**2", "dynamic viscosity")
        h = Variable("h", altitude, "ft", "flight altitude")
        href = Variable("h_{ref}", 15000, "ft", "reference altitude")
        qne = self.qne = Variable("qne", "kg/s^2/m",
                                  "never exceed dynamic pressure")
        Vne = Variable("Vne", 40, "m/s", "never exceed velocity")
        rhosl = Variable("rhosl", 1.225, "kg/m^3", "air density at sea level")

        constraints = [V/mfac >= Vwind,
                       rho == rho,
                       mu == mu,
                       h == h,
                       qne == 0.5*rhosl*Vne**2,
                       href == href]

        return constraints
