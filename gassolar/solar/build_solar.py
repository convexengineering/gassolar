" build solar "
from solar import Mission

def build_solar(lat=15, day=140, sp=True):
    " try different battery specific energies "
    M = Mission(latitude=lat, day=day, sp=sp)
    M.cost = M["W_{total}"]
    M.substitutions.update({"W_{pay}": 0})
    for vk in M.varkeys["P_{avn}"]:
        M.substitutions.update({vk: 50})

    for h in [150, 200, 260]:
        M.substitutions.update({"h_{batt}": h})
        try:
            sol = M.localsolve("mosek", verbosity=2) if sp else M.solve("mosek")
            print sol.table(["W_{total}", "b_Mission/Aircraft/Wing", "S",
                             "W_Mission/Aircraft/Wing",
                             "W_Mission/Aircraft/Battery",
                             "P_{oper}"])
        except RuntimeWarning:
            print "Not feasible"

    return M

if __name__ == "__main__":
    m = build_solar()
