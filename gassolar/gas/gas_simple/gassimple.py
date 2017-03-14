" Simple Gas Powered Aircraft Model"
from gassolar.gas.loiter import Loiter
from gpkit import Model, Variable
from gpkitmodels.GP.aircraft.wing.wing import WingAero

class Aircraft(Model):
    "vehicle"
    def setup(self):

        self.wing = Wing()

        Wstructures = Variable("W_{structures}", "lbf", "structural weight")
        fstructures = Variable("f_{structures}", 0.35, "-",
                               "fractional structural weight")
        Wpay = Variable("W_{pay}", 10, "lbf", "payload")
        Wzfw = Variable("W_{zfw}", "lbf", "zero fuel weight")
        etaprop = Variable("\\eta_{prop}", 0.75, "-", "propulsive efficiency")

        constraints = [Wstructures == Wstructures,
                       fstructures == fstructures,
                       Wzfw >= Wstructures + Wpay]

        return self.wing, constraints

    def flight_model(self, state):
        return AircraftPerf(self, state)

class Wing(Model):
    "wing model"
    def setup(self):

        S = Variable("S", "ft**2", "planform area")
        b = Variable("b", "ft", "wing span")
        cmac = Variable("c_{MAC}", "ft", "mean aerodynamic chord")
        AR = Variable("AR", 27, "-", "aspect ratio")

        constraints = [b**2 == S*AR,
                       cmac == S/b]

        return constraints

    def flight_model(self, state):
        return WingAero(self, state)

class AircraftPerf(Model):
    "aircraft performance"
    def setup(self, static, state):

        self.wing = static.wing.flight_model(state)

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

        return self.wing, constraints

class Mission(Model):
    "create a mission for the flight"
    def setup(self):

        gassimple = Aircraft()

        loiter = Loiter(gassimple)
        mission = [loiter]

        mtow = Variable("MTOW", "lbf", "max take off weight")
        Wfueltot = Variable("W_{fuel-tot}", "lbf", "total fuel weight")

        constraints = [
            mtow == loiter["W_{start}"][0],
            mtow >= Wfueltot + gassimple["W_{zfw}"],
            Wfueltot >= sum([fs["W_{fuel-fs}"] for fs in mission]),
            mission[-1]["W_{end}"][-1] >= gassimple["W_{zfw}"],
            gassimple["W_{structures}"] >= mtow*gassimple["f_{structures}"]
            ]

        return gassimple, mission, constraints

def test():
    M = Mission()
    M.cost = 1/M["t_Mission, Loiter"]
    M.solve()

if __name__ == "__main__":
    M = Mission()
    M.cost = 1/M["t_Mission, Loiter"]
    sol = M.solve("mosek")
