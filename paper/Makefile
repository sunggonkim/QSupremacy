SHELL=/bin/bash

PDF=main.pdf
TEX=0.Main.tex
BIB=references.bib
LOAD_TEXLIVE=source /etc/profile.d/zzz-lmod.sh && module load texlive/2024

.PHONY: all clean

all: $(PDF)

$(PDF): $(TEX) $(BIB)
	$(LOAD_TEXLIVE) && pdflatex -jobname=main -interaction=nonstopmode $(TEX)
	$(LOAD_TEXLIVE) && bibtex main
	$(LOAD_TEXLIVE) && pdflatex -jobname=main -interaction=nonstopmode $(TEX)
	$(LOAD_TEXLIVE) && pdflatex -jobname=main -interaction=nonstopmode $(TEX)

clean:
	rm -f *.aux *.bbl *.blg *.log *.out $(PDF)
