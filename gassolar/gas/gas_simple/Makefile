all:
	python -c 'import gpkit.tools; exec gpkit.tools.mdmake("gassimple.md")'
	pandoc --template ../default.latex gassimple.md.tex.md -o "gassimple.pdf"
