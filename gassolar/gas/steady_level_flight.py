" steady level flight model "
from gpkit import Model, Variable

class SteadyLevelFlight(Model):
    "steady level flight model"
    def setup(self, state, aircraft, perf):

        T = Variable("T", "N", "thrust")

        constraints = [
            (perf["W_{end}"]*perf["W_{start}"])**0.5 <= (
                0.5*state["\\rho"]*state["V"]**2*perf["C_L"]
                * aircraft.wing["S"]),
            T >= (0.5*state["\\rho"]*state["V"]**2*perf["C_D"]
                  *aircraft.wing["S"]),
            perf["P_{shaft}"] >= T*state["V"]/aircraft["\\eta_{prop}"]]

        return constraints
