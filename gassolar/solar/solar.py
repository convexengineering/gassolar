" Simple Solar-Electric Powered Aircraft Model "
from solar_irradiance import get_Eirr
from gpkit import Model, Variable
from gpkitmodels.aircraft.GP_submodels.wing import WingAero, Wing
from gassolar.environment.wind_speeds import get_windspeed
from gassolar.environment.air_properties import get_airvars
from gpkitmodels.helpers import summing_vars

class Aircraft(Model):
    "vehicle"
    def setup(self):

        self.solarcells = SolarCells()
        self.wing = Wing(hollow=True)
        self.battery = Battery()

        self.components = [self.solarcells, self.wing, self.battery]

        Wpay = Variable("W_{pay}", 10, "lbf", "payload")
        Wtotal = Variable("W_{total}", "lbf", "aircraft weight")

        constraints = [
            Wtotal >= (Wpay + sum(summing_vars(self.components, "W"))),
            self.solarcells["S"] <= self.wing["S"]]

        return constraints, self.components

    def flight_model(self, state):
        return AircraftPerf(self, state)

    def loading(self, Wcent):
        return AircraftLoading(self, Wcent)

class AircraftLoading(Model):
    "aircraft loading cases"
    def setup(self, aircraft, Wcent):

        loading = aircraft.wing.loading(Wcent)

        return loading

class Battery(Model):
    "battery model"
    def setup(self):

        W = Variable("W", "lbf", "battery weight")
        eta_charge = Variable("\\eta_{charge}", 0.98, "-",
                              "Battery charging efficiency")
        eta_discharge = Variable("\\eta_{discharge}", 0.98, "-",
                                 "Battery discharging efficiency")
        E = Variable("E", "J", "total battery energy")
        g = Variable("g", 9.81, "m/s**2", "gravitational constant")
        hbatt = Variable("h_{batt}", 350, "W*hr/kg", "battery energy density")

        constraints = [W >= E/hbatt*g,
                       eta_charge == eta_charge,
                       eta_discharge == eta_discharge]

        return constraints

    def flight_model(self, state):
        return BatteryPerf(self, state)

class BatteryPerf(Model):
    "battery performance model"
    def setup(self, static, state):

        Poper = Variable("P_{oper}", "W", "operating power")

        constraints = [
            static["E"] >= Poper*state["t_{night}"]/static["\\eta_{discharge}"]]

        return constraints

# class Wing(Model):
#     "simple wing model"
#     def setup(self):
#
#         S = Variable("S", "ft**2", "planform area")
#         b = Variable("b", "ft", "wing span")
#         cmac = Variable("c_{MAC}", "ft", "mean aerodynamic chord")
#         AR = Variable("AR", 27, "-", "aspect ratio")
#         W = Variable("W", "lbf", "structural weight")
#         f = Variable("f", 0.35, "-", "fractional structural weight")
#
#         constraints = [b**2 == S*AR,
#                        cmac == S/b,
#                        W == W,
#                        f == f]
#
#         return constraints
#
#     def flight_model(self, state):
#         return WingAero(self, state)

class SolarCells(Model):
    "solar cell model"
    def setup(self):

        rhosolar = Variable("\\rho_{solar}", 0.3, "kg/m^2",
                            "solar cell area density")
        g = Variable("g", 9.81, "m/s**2", "gravitational constant")
        S = Variable("S", "ft**2", "solar cell area")
        W = Variable("W", "lbf", "solar cell weight")

        constraints = [W >= rhosolar*S*g]

        return constraints

    def flight_model(self, state):
        return SolarCellPerf(self, state)

class SolarCellPerf(Model):
    "collecting solar cell energy"
    def setup(self, static, state):

        E = Variable("E", "J", "solar cell energy collected")
        etasolar = Variable("\\eta_{solar}", 0.2, "-",
                            "Solar cell efficiency")

        constraints = [
            state["(E/S)_{irr}"]*etasolar*static["S"] >= E]

        return constraints

class AircraftPerf(Model):
    "aircraft performance"
    def setup(self, static, state):

        self.wing = static.wing.flight_model(state)
        self.solarcells = static.solarcells.flight_model(state)
        self.battery = static.battery.flight_model(state)

        self.flight_models = [self.wing, self.solarcells, self.battery]

        CD = Variable("C_D", "-", "aircraft drag coefficient")
        cda0 = Variable("CDA_0", 0.005, "-", "non-wing drag coefficient")
        Pshaft = Variable("P_{shaft}", "hp", "shaft power")
        Pacc = Variable("P_{acc}", 0.0, "W", "Accessory power draw")
        constraints = [
            ]

        constraints = [
            CD >= cda0 + self.wing["C_d"],
            self.solarcells["E"] >= (
                self.battery["P_{oper}"]*state["t_{day}"]
                + self.battery["E"]/static.battery["\\eta_{discharge}"]),
            self.battery["P_{oper}"] >= Pacc + Pshaft
            ]

        return self.flight_models, constraints

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
    def setup(self, latitude=45, percent=90, altitude=15000, day=355):

        wind = get_windspeed(latitude, percent, altitude, day)
        density, vis = get_airvars(altitude)
        esirr, td, tn = get_Eirr(latitude, day)

        Vwind = Variable("V_{wind}", wind, "m/s", "wind velocity")
        V = Variable("V", "m/s", "true airspeed")
        rho = Variable("\\rho", density, "kg/m**3", "air density")
        mu = Variable("\\mu", vis, "N*s/m**2", "dynamic viscosity")
        ESirr = Variable("(E/S)_{irr}", esirr, "W*hr/m^2",
                         "Average daytime solar energy")
        tday = Variable("t_{day}", td, "hr", "Daylight span")
        tnight = Variable("t_{night}", tn, "hr", "Night span")

        constraints = [V >= Vwind,
                       rho == rho,
                       mu == mu,
                       ESirr == ESirr,
                       tday == tday,
                       tnight == tnight]

        return constraints

class FlightSegment(Model):
    "flight segment"
    def setup(self, aircraft, etap=0.7, latitude=35, percent=80,
                 altitude=60000, day=355):

        self.aircraft = aircraft
        self.fs = FlightState(latitude, percent, altitude, day)
        self.aircraftPerf = self.aircraft.flight_model(self.fs)
        self.slf = SteadyLevelFlight(self.fs, self.aircraft,
                                     self.aircraftPerf, etap)

        self.submodels = [self.fs, self.aircraftPerf, self.slf]

        return self.aircraft, self.submodels

class SteadyLevelFlight(Model):
    "steady level flight model"
    def setup(self, state, aircraft, perf, etap):

        T = Variable("T", "N", "thrust")
        etaprop = Variable("\\eta_{prop}", etap, "-", "propulsive efficiency")

        constraints = [
            aircraft["W_{total}"] <= (
                0.5*state["\\rho"]*state["V"]**2*perf["C_L"]
                * aircraft.wing["S"]),
            T >= (0.5*state["\\rho"]*state["V"]**2*perf["C_D"]
                  *aircraft.wing["S"]),
            perf["P_{shaft}"] >= T*state["V"]/etaprop]

        return constraints

class Mission(Model):
    "define mission for aircraft"
    def setup(self, etap=0.7, latitude=35, percent=80, altitude=60000, day=355):
        # http://sky-sailor.ethz.ch/docs/Conceptual_Design_of_Solar_Powered_Airplanes_for_continuous_flight2.pdf

        Wcent = Variable("W_{cent}", "lbf", "center weight")

        self.solar = Aircraft()
        fs = FlightSegment(self.solar, etap, latitude, percent, altitude, day)
        loading = AircraftLoading(self.solar, Wcent)
        loading.substitutions.update({"N_{max}": 5})

        constraints = [Wcent >= self.solar["W_{pay}"] + self.solar.battery["W"]]

        return self.solar, fs, loading, constraints

if __name__ == "__main__":
    M = Mission()
    M.cost = M["W_{total}"]
    sol = M.solve("mosek")
