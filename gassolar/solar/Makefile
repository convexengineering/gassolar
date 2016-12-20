all:
	python -c 'import gpkit.tools; exec gpkit.tools.mdmake("solar.md")'
	pandoc --template ../default.latex solar.md.tex.md -o "solar.pdf"
