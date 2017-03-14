all:
	$(MAKE) -C solar
	$(MAKE) -C gas 
	$(MAKE) -C fits
	$(MAKE) -C environment
	$(MAKE) -C solar/fits
	$(MAKE) -C gas/fits
	ipython gassolarlat.py ../docs/figs/
