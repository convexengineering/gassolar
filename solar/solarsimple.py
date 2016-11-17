" Simple Solar-Electric Powered Aircraft Model "
from gpkit import Model, Variable, vectorize
from gpkitmodels.aircraft.GP_submodels.wing import WingAero
from gpkitmodels.environment.wind_speeds import get_windspeed
from gpkitmodels.environment.air_properties import get_airvars
import numpy as np
import matplotlib.pyplot as plt
from solar_irradiance import get_Eirr

class Aircraft(Model):
    "vehicle"
    def __init__(self):

        self.flight_model = AircraftPerf

        Wstructures = Variable("W_{structures}", "lbf", "structural weight")
        fstructures = Variable("f_{structures}", 0.35, "-",
                               "fractional structural weight")
        Wpay = Variable("W_{pay}", 10, "lbf", "payload")
        Wsolar = Variable("W_{solar}", "lbf", "solar cell weight")
        Wbatt = Variable("W_{batt}", "lbf", "battery weight")
        W = Variable("W", "lbf", "aircraft weight")
        S = Variable("S", "ft**2", "planform area")
        b = Variable("b", "ft", "wing span")
        cmac = Variable("c_{MAC}", "ft", "mean aerodynamic chord")
        A = Variable("A", 27, "-", "aspect ratio")
        W = Variable("W", "lbf", "aircraft weight")
        Ssolar = Variable("S_{solar}", "ft**2", "solar cell area")
        eta_solar = Variable("\\eta_{solar}", 0.2, "-",
                             "Solar cell efficiency")
        eta_charge = Variable("\\eta_{charge}", 0.98, "-",
                              "Battery charging efficiency")
        eta_discharge = Variable("\\eta_{discharge}", 0.98, "-",
                                 "Battery discharging efficiency")
        hbatt = Variable("h_{batt}", 350, "W*hr/kg", "battery energy density")
        Ebatt = Variable("E_{batt}", "J", "total battery energy")
        rhosolar = Variable("\\rho_{solar}", 0.3, "kg/m^2",
                            "solar cell area density")
        g = Variable("g", 9.81, "m/s**2", "gravitational constant")

        constraints = [Wstructures >= W*fstructures,
                       W >= Wstructures + Wsolar + Wbatt + Wpay,
                       Wsolar >= rhosolar*Ssolar*g,
                       Wbatt >= Ebatt/hbatt*g,
                       Ssolar <= S,
                       b**2 == S*A,
                       cmac == S/b,
                       eta_solar == eta_solar,
                       eta_charge == eta_charge,
                       eta_discharge == eta_discharge]

        Model.__init__(self, None, constraints)

class AircraftPerf(Model):
    "aircraft performance"
    def __init__(self, static, state):

        self.wing = WingAero(static, state)

        CD = Variable("C_D", "-", "aircraft drag coefficient")
        cda0 = Variable("CDA_0", 0.005, "-", "non-wing drag coefficient")
        Pshaft = Variable("P_{shaft}", "hp", "shaft power")

        constraints = [CD >= cda0 + self.wing["C_d"],
                       Pshaft == Pshaft]

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

        Model.__init__(self, None, constraints)

class FlightSegment(Model):
    "flight segment"
    def __init__(self, aircraft, etap=0.7, latitude=35, percent=80,
                 altitude=60000, day=355):

        self.aircraft = aircraft
        self.fs = FlightState(latitude, percent, altitude, day)
        self.aircraftPerf = self.aircraft.flight_model(self.aircraft,
                                                       self.fs)
        self.slf = SteadyLevelFlight(self.fs, self.aircraft,
                                     self.aircraftPerf, etap)
        self.power = Power(self.aircraft, self.fs)

        self.submodels = [self.fs, self.aircraftPerf, self.slf, self.power]

        constraints = [
            self.power["P_{oper}"] >= self.power["P_{acc}"] + self.aircraftPerf["P_{shaft}"]
            ]

        Model.__init__(self, None, [self.aircraft, self.submodels, constraints])

class SteadyLevelFlight(Model):
    "steady level flight model"
    def __init__(self, state, aircraft, perf, etap, **kwargs):

        T = Variable("T", "N", "thrust")
        etaprop = Variable("\\eta_{prop}", etap, "-", "propulsive efficiency")

        constraints = [
            aircraft["W"] <= (
                0.5*state["\\rho"]*state["V"]**2*perf["C_L"]
                * aircraft["S"]),
            T >= (0.5*state["\\rho"]*state["V"]**2*perf["C_D"]
                  *aircraft["S"]),
            perf["P_{shaft}"] >= T*state["V"]/etaprop]

        Model.__init__(self, None, constraints, **kwargs)

class Power(Model):
    def __init__(self, static, state, **kwargs):

        Poper = Variable("P_{oper}", "W", "Aircraft operating power")
        Pacc = Variable("P_{acc}", 0.0, "W", "Accessory power draw")

        constraints = [
            state["(E/S)_{irr}"]*static["\\eta_{solar}"]*static["S_{solar}"] >= (
                Poper*state["t_{day}"] + static["E_{batt}"]
                / static["\\eta_{discharge}"]),
            Poper == Poper,
            Pacc == Pacc,
            static["E_{batt}"] >= (Poper*state["t_{night}"]
                                   / static["\\eta_{discharge}"])
            ]
        Model.__init__(self, None, constraints, **kwargs)

class Mission(Model):
    def __init__(self):
        # http://sky-sailor.ethz.ch/docs/Conceptual_Design_of_Solar_Powered_Airplanes_for_continuous_flight2.pdf

        solarsimple = Aircraft()
        fs = FlightSegment(solarsimple)

        cost = solarsimple["W"]

        Model.__init__(self, cost, [solarsimple, fs])

if __name__ == "__main__":
    M = Mission()
    sol = M.solve("mosek")
