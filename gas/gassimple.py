" Simple Gas Powered Aircraft Model"
from gpkit import Model, Variable, vectorize
from gpkitmodels.aircraft.GP_submodels.wing import WingAero
from gpkitmodels.aircraft.GP_submodels.breguet_endurance import BreguetEndurance
from gpkitmodels.environment.wind_speeds import get_windspeed
from gpkitmodels.environment.air_properties import get_airvars

class Aircraft(Model):
    "vehicle"
    def __init__(self):

        self.flight_model = AircraftPerf

        Wstructures = Variable("W_{structures}", "lbf", "structural weight")
        fstructures = Variable("f_{structures}", 0.35, "-",
                               "fractional structural weight")
        Wpay = Variable("W_{pay}", 10, "lbf", "payload")
        Wzfw = Variable("W_{zfw}", "lbf", "zero fuel weight")
        S = Variable("S", "ft**2", "planform area")
        b = Variable("b", "ft", "wing span")
        cmac = Variable("c_{MAC}", "ft", "mean aerodynamic chord")
        A = Variable("A", 27, "-", "aspect ratio")

        constraints = [Wstructures == Wstructures,
                       fstructures == fstructures,
                       Wzfw >= Wstructures + Wpay,
                       b**2 == S*A,
                       cmac == S/b]

        Model.__init__(self, None, constraints)

class AircraftPerf(Model):
    "aircraft performance"
    def __init__(self, static, state):

        self.wing = WingAero(static, state)

        CD = Variable("C_D", "-", "aircraft drag coefficient")
        cda0 = Variable("CDA_0", 0.005, "-", "non-wing drag coefficient")
        Wstart = Variable("W_{start}", "lbf", "vector-begin weight")
        Wend = Variable("W_{end}", "lbf", "vector-end weight")
        Pshaft = Variable("P_{shaft}", "hp", "shaft power")
        Ptot = Variable("P_{total}", "hp", "shaft power")
        bsfc = Variable("BSFC", 0.6, "lb/hp/hr",
                        "break specific fuel consumption")

        constraints = [CD >= cda0 + self.wing["C_d"],
                       Wstart == Wstart,
                       Wend == Wend,
                       Ptot >= Pshaft,
                       bsfc == bsfc]

        Model.__init__(self, None, [self.wing, constraints])

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
    def __init__(self, latitude=45, percent=90, altitude=15000, day=355):

        wind = get_windspeed(latitude, percent, altitude, day)
        density, vis = get_airvars(altitude)

        Vwind = Variable("V_{wind}", wind, "m/s", "wind velocity")
        V = Variable("V", "m/s", "true airspeed")
        rho = Variable("\\rho", density, "kg/m**3", "air density")
        mu = Variable("\\mu", vis, "N*s/m**2", "dynamic viscosity")

        constraints = [V >= Vwind,
                       rho == rho,
                       mu == mu]

        Model.__init__(self, None, constraints)

class FlightSegment(Model):
    "flight segment"
    def __init__(self, aircraft, N=5, etap=0.7, latitude=45, percent=90,
                 altitude=15000, day=355):

        self.aircraft = aircraft
        with vectorize(N):
            self.fs = FlightState(latitude, percent, altitude, day)
            self.aircraftPerf = self.aircraft.flight_model(self.aircraft,
                                                           self.fs)
            self.slf = SteadyLevelFlight(self.fs, self.aircraft,
                                         self.aircraftPerf, etap)
            self.be = BreguetEndurance(self.aircraftPerf)

        self.submodels = [self.fs, self.aircraftPerf, self.slf, self.be]
        Wfuelfs = Variable("W_{fuel-fs}", "lbf", "flight segment fuel weight")

        self.constraints = [Wfuelfs >= self.be["W_{fuel}"].sum()]

        if N > 1:
            self.constraints.extend([self.aircraftPerf["W_{end}"][:-1] >=
                                     self.aircraftPerf["W_{start}"][1:]])

        Model.__init__(self, None, [self.aircraft, self.submodels,
                                    self.constraints])

class Loiter(Model):
    "loiter segment"
    def __init__(self, aircraft, N=5, etap=0.7, latitude=45, percent=90,
                 altitude=15000, day=355):
        fs = FlightSegment(aircraft, N, etap, latitude, percent, altitude, day)

        t = Variable("t", "days", "loitering time")
        constraints = [fs.be["t"] >= t/N]

        Model.__init__(self, None, [fs, constraints])

class SteadyLevelFlight(Model):
    "steady level flight model"
    def __init__(self, state, aircraft, perf, etap, **kwargs):

        T = Variable("T", "N", "thrust")
        etaprop = Variable("\\eta_{prop}", etap, "-", "propulsive efficiency")

        constraints = [
            (perf["W_{end}"]*perf["W_{start}"])**0.5 <= (
                0.5*state["\\rho"]*state["V"]**2*perf["C_L"]
                * aircraft["S"]),
            T >= (0.5*state["\\rho"]*state["V"]**2*perf["C_D"]
                  *aircraft["S"]),
            perf["P_{shaft}"] >= T*state["V"]/etaprop]

        Model.__init__(self, None, constraints, **kwargs)

class Mission(Model):
    "create a mission for the flight"
    def __init__(self):

        gassimple = Aircraft()

        loiter = Loiter(gassimple)
        mission = [loiter]

        mtow = Variable("MTOW", 200, "lbf", "max take off weight")
        Wfueltot = Variable("W_{fuel-tot}", "lbf", "total fuel weight")

        constraints = [
            mtow >= loiter["W_{start}"][0],
            mtow >= Wfueltot + gassimple["W_{zfw}"],
            Wfueltot >= sum([fs["W_{fuel-fs}"] for fs in mission]),
            mission[-1]["W_{end}"][-1] >= gassimple["W_{zfw}"],
            gassimple["W_{structures}"] >= mtow*gassimple["f_{structures}"]
            ]

        cost = 1/loiter["t_Mission, Loiter"]

        Model.__init__(self, cost, [gassimple, mission, constraints])

if __name__ == "__main__":
    M = Mission()
    sol = M.solve("mosek")
