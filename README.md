# gas_solar_trade
Trade off analysis between solar and gas powered long endurance aircraft

[![Build Status](https://acdl.mit.edu/csi/buildStatus/icon?job=gpkit_ResearchModel_gas_solar_trade_Push)](https://acdl.mit.edu/csi/job/gpkit_ResearchModel_gas_solar_trade_Push)

Geometric programming is used to evaulating the trade space and quantitatively weigh the trade offs between various archictures and configurations for long endurance aircraft.  Models include the effect of solar irradiance, wind speeds, engine performance, structural component sizing, and aerodynamic effects. 

The gas and solar models respectively live in:

```
./gassolar/gas/gas.py
./gassolar/solar/solar.py
```

In order to run these models this repository must be installed as well as 2 additional repositories:

[Gpkit](https://github.com/hoburg/gpkit)
[gpkit-models](https://github.com/hoburg/gpkit-models)

More documentation is available on these repos, but essentially [Gpkit](https://github.com/hoburg/gpkit) is a python based program that facilitates the use of geometric programming as an optimization routine.  [gpkit-models](https://github.com/hoburg/gpkit-models) is a repository with existing geometric and signomial models some of which are shared by the gas and solar powered aircraft. Both repositories can be installed using

```
python setup.py install
pip install -e
```

This project has inspired a paper, "Solar-Electric and Gas Powered, Long-Endurance UAV Sizing via Geometric Programming," which can be generated here using the following commands:

`cd ./gassolar/` 
`make` generates all figures in document (will take about 45-60 min)

All figures are saved in `./docs/figs/`

`cd ./docs/`
`make` to generate latex documents, including a presentation

The fitted function data for wind speed and solar irradiance by latitude is included in this repository:

```
./gassolar/environment/windaltfitdata.csv
./gassolar/environment/solarirrdata.csv
```

If you wish to generate this data yourself, change the `GENERATE=True` flag in:

```
./gassolar/environment/wind_fit.py
./gassolar/environment/solar_irradiance.py
```
 and run each file. 

 Please report and issues with the installation, makefiles, or models.
