import pandas as pd

df = pd.read_csv("windaltfitdata.csv")
PRINT = False

if PRINT:
    filename = "../../gassolarpaper/windfitdata.generated.tex"
else:
    filename = "windfitdata.generated.tex"

with open(filename, "w") as f:
    f.write("\\begin{longtable}{lccccccccccccc}\n")
    f.write("\\caption{Wind Fit Data}\\\\\n")
    f.write("\\toprule\n")
    f.write("\\toprule\n")
    f.write("\\label{t:windvals}\n")
    f.write("Latitude & $c_1$ & $e_{1,1}$ & $e_{1,2}$ & $c_2$ & $e_{2,1}$ & $e_{2,2}$& $c_3$ & $e_{3,1}$ & $e_{3,2}$& $c_3$ & $e_{3,1}$ & $e_{3,2}$ & $\\alpha$\\\\\n")
    f.write("\\midrule\n")
    for i in range(1, len(df)+1):
        d = [df[i-1:i][n].iloc[0] for n in df[i-1:i]]
        vals = " & ".join(["%.3g" % v for v in d[1:]])
        f.write(vals + "\\\\\n")
    f.write("\\bottomrule\n")
    f.write("\\end{longtable}")
