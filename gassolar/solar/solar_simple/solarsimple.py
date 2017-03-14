" Simple Solar-Electric Powered Aircraft Model "
from gassolar.environment.solar_irradiance import get_Eirr
from gpkit import Model, Variable
from gpkitmodels.GP.aircraft.wing.wing import WingAero
from gassolar.solar.solar import FlightState

class Aircraft(Model):
    "vehicle"
    def setup(self):

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
        AR = Variable("AR", 27, "-", "aspect ratio")
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
                       b**2 == S*AR,
                       cmac == S/b,
                       eta_solar == eta_solar,
                       eta_charge == eta_charge,
                       eta_discharge == eta_discharge]

        return constraints

    def flight_model(self, state):
        return AircraftPerf(self, state)

class AircraftPerf(Model):
    "aircraft performance"
    def setup(self, static, state):

        self.wing = WingAero(static, state)

        CD = Variable("C_D", "-", "aircraft drag coefficient")
        cda0 = Variable("CDA_0", 0.005, "-", "non-wing drag coefficient")
        Pshaft = Variable("P_{shaft}", "hp", "shaft power")

        constraints = [CD >= cda0 + self.wing["C_d"],
                       Pshaft == Pshaft]

        return self.wing, constraints

class FlightSegment(Model):
    "flight segment"
    def setup(self, aircraft, etap=0.7, latitude=35, day=355):

        self.aircraft = aircraft
        self.fs = FlightState(latitude, day)
        self.aircraftPerf = self.aircraft.flight_model(self.fs)
        self.slf = SteadyLevelFlight(self.fs, self.aircraft,
                                     self.aircraftPerf, etap)
        self.power = Power(self.aircraft, self.fs)

        self.submodels = [self.fs, self.aircraftPerf, self.slf, self.power]

        constraints = [
            self.power["P_{oper}"] >= self.power["P_{acc}"] + self.aircraftPerf["P_{shaft}"]
            ]

        return self.aircraft, self.submodels, constraints

class SteadyLevelFlight(Model):
    "steady level flight model"
    def setup(self, state, aircraft, perf, etap, **kwargs):

        T = Variable("T", "N", "thrust")
        etaprop = Variable("\\eta_{prop}", etap, "-", "propulsive efficiency")

        constraints = [
            aircraft["W"] <= (
                0.5*state["\\rho"]*state["V"]**2*perf["C_L"]
                * aircraft["S"]),
            T >= (0.5*state["\\rho"]*state["V"]**2*perf["C_D"]
                  *aircraft["S"]),
            perf["P_{shaft}"] >= T*state["V"]/etaprop]

        return constraints

class Power(Model):
    def setup(self, static, state):

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
        return constraints

class Mission(Model):
    "define mission for aircraft"
    def setup(self, etap=0.7, latitude=35, day=355):
        # http://sky-sailor.ethz.ch/docs/Conceptual_Design_of_Solar_Powered_Airplanes_for_continuous_flight2.pdf

        solarsimple = Aircraft()
        mission = []
        for l in range(20, latitude+1, 1):
            mission.append(FlightSegment(solarsimple, etap, l, day))

        return solarsimple, mission

def test():
    M = Mission()
    M.cost = M["W"]
    M.solve()

if __name__ == "__main__":
    M = Mission()
    M.cost = M["W"]
    sol = M.solve("mosek")
