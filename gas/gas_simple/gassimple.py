" Simple Gas Powered Aircraft Model"
from gas.loiter import Loiter
from gpkit import Model, Variable
from gpkitmodels.aircraft.GP_submodels.wing import WingAero

class Aircraft(Model):
    "vehicle"
    def __init__(self):

        self.flight_model = AircraftPerf
        self.wing = Wing()

        Wstructures = Variable("W_{structures}", "lbf", "structural weight")
        fstructures = Variable("f_{structures}", 0.35, "-",
                               "fractional structural weight")
        Wpay = Variable("W_{pay}", 10, "lbf", "payload")
        Wzfw = Variable("W_{zfw}", "lbf", "zero fuel weight")

        constraints = [Wstructures == Wstructures,
                       fstructures == fstructures,
                       Wzfw >= Wstructures + Wpay]

        Model.__init__(self, None, [self.wing, constraints])

class Wing(Model):
    "wing model"
    def __init__(self):

        S = Variable("S", "ft**2", "planform area")
        b = Variable("b", "ft", "wing span")
        cmac = Variable("c_{MAC}", "ft", "mean aerodynamic chord")
        AR = Variable("AR", 27, "-", "aspect ratio")

        self.flight_model = WingAero

        constraints = [b**2 == S*AR,
                       cmac == S/b]

        Model.__init__(self, None, constraints)

class AircraftPerf(Model):
    "aircraft performance"
    def __init__(self, static, state):

        self.wing = static.wing.flight_model(static.wing, state)

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
    Sol = M.solve("mosek")
