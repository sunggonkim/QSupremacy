PDF=main.pdf
TEX=main.tex
BIB=references.bib

.PHONY: all clean

all: $(PDF)

$(PDF): $(TEX) $(BIB)
	pdflatex -interaction=nonstopmode $(TEX)
	bibtex main
	pdflatex -interaction=nonstopmode $(TEX)
	pdflatex -interaction=nonstopmode $(TEX)

clean:
	rm -f *.aux *.bbl *.blg *.log *.out $(PDF)
