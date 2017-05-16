pdf=".pdf"
eps=".eps"
ipe=".ipe"
for filename in ./*.pdf; do
     if ! [ -f "${filename//pdf/ipe}" ] ; then
         pdftops -eps $filename
     fi
done
