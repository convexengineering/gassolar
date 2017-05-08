import numpy as np
import pandas as pd
from gas import Mission
from gpkit.small_scripts import unitstr
from gpkit import Variable
from gen_tex import find_submodels
import xlsxwriter

def sketch_params(M, sol, varnames, othervars=None, pointmasses=None):

    data = {}
    for vname in varnames:
        uts = unitstr(M[vname].descr["units"])
        if "ft" not in uts and uts != "":
            spt = uts.split("*")
            spt[0] = "ft"
            uts = "".join(spt)
        data[vname.replace(", ", "-").replace("\\", "")] = [sol(vname).to(uts).magnitude, uts,
                                          M[vname].descr["label"]]

    if othervars:
        data.update(othervars)

    if hasattr(M, "get_cgs"):
        xnp, xcg, SM = M.get_cgs()
        data["x_{np}"] = [xnp.magnitude, xnp.units, "neutral point"]
        data["x_{cg}"] = [xcg.magnitude, xcg.units, "center of gravity"]
        data["SM"] = [SM.magnitude, "-", "static margin"]

    if pointmasses:
        for pm in pointmasses:
            data[pm] = []

    df = pd.DataFrame(data)
    df = df.transpose()
    df.columns = ["Value", "Units", "Label"]
    return df

if __name__ == "__main__":
    M = Mission()
    M.cost = 1/M["t_Mission/Loiter"]
    sol = M.solve("mosek")

    sketchvars = [
        "R_Mission/Aircraft/Fuselage",
        "S_Mission/Aircraft/Wing", "b_Mission/Aircraft/Wing",
        "l_Mission/Aircraft/Empennage/TailBoom", "d_0",
        "b_Mission/Aircraft/Empennage/HorizontalTail",
        "S_Mission/Aircraft/Empennage/HorizontalTail",
        "b_Mission/Aircraft/Empennage/VerticalTail",
        "S_Mission/Aircraft/Empennage/VerticalTail",
        "\\tau_Mission/Aircraft/Wing", "k_{nose}", "k_{body}", "k_{bulk}",
        "\\lambda_Mission/Aircraft/Wing",
        "\\lambda_Mission/Aircraft/Empennage/HorizontalTail",
        "\\lambda_Mission/Aircraft/Empennage/VerticalTail"]
    df = sketch_params(M, sol, sketchvars)

    df.to_csv("sketcher/16_82viewer/sketch_params.csv")
