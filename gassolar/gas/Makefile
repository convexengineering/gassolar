all:
	python -c 'import gpkit.tools; exec gpkit.tools.mdmake("gas.md")'
	pandoc --template ../default.latex gas.md.tex.md -o "gas.pdf"
