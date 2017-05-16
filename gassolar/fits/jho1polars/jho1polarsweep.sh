AIRFOIL=jho1
Re="50 100 150 200 250 300 350 400 450 500 550 600"
for r in $Re
do
    ./genpolar.sh $AIRFOIL $r
done
