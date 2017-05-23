export WORKSPACE=./

#Create a virtualenv to install everything into
virtualenv --system-site-packages $WORKSPACE/venv2_gpkit
. $WORKSPACE/venv2_gpkit/bin/activate

export PIP=`which pip`

# make sure pip is up to date
python $PIP install --upgrade pip

export PATH=$PATH:/Users/jenkins/mosek/8/tools/platform/osx64x86/bin
export DYLD_LIBRARY_PATH=$DYLD_LIBRARY_PATH:/Users/jenkins/mosek/8/tools/platform/osx64x86/bin
python /Users/jenkins/mosek/8/tools/platform/osx64x86/python/2/setup.py install

#Install packages needed for testing
python $PIP install --upgrade xmlrunner
python $PIP install --upgrade pint
python $PIP install --upgrade numpy
python $PIP install --upgrade scipy
python $PIP install --upgrade ctypesgen


export GPKITBUILD=$WORKSPACE/build_gpkit

python -c "import scipy; print scipy.__version__"
python -c "import numpy; print numpy.__version__"
python -c "import pint; print pint.__version__"

git clone --depth 1 https://github.com/hoburg/gpkit.git $WORKSPACE/gpkit
python $PIP install -v --no-cache-dir --no-deps -e $WORKSPACE/gpkit

# Run the research model tests
echo "from gpkit.tests.test_repo import test_repo; test_repo(xmloutput=True)" > jenkins_test.py
python jenkins_test.py
