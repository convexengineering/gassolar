all:
	python -c 'import gpkit.tools; exec gpkit.tools.mdmake("solarsimple.md")'
	pandoc --template ../default.latex solarsimple.md.tex.md -o "solarsimple.pdf"
