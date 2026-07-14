SHELL=/bin/bash

PDF=main.pdf
TEX=0.Main.tex
BIB=references.bib
TEX_SOURCES=$(wildcard *.tex)
FIGURE_SOURCES=$(wildcard figures/*.pdf)
PYTHON?=python3
LOAD_TEXLIVE=if ! command -v pdflatex >/dev/null 2>&1; then source /etc/profile.d/zzz-lmod.sh >/dev/null 2>&1 || true; module load texlive/2024 >/dev/null 2>&1; fi

.PHONY: all figures audit clean

all: $(PDF)

figures:
	cd .. && PYTHON="$${PYTHON:-./.venv-qre/bin/python}" bash scripts/regenerate_paper_artifacts.sh

$(PDF): $(TEX_SOURCES) $(BIB) $(FIGURE_SOURCES)
	$(LOAD_TEXLIVE) && pdflatex -jobname=main -interaction=nonstopmode $(TEX)
	$(LOAD_TEXLIVE) && bibtex main
	$(LOAD_TEXLIVE) && pdflatex -jobname=main -interaction=nonstopmode $(TEX)
	$(LOAD_TEXLIVE) && pdflatex -jobname=main -interaction=nonstopmode $(TEX)

audit: all
	cd .. && $(PYTHON) scripts/audit_quality_qualified_targets.py
	cd .. && $(PYTHON) scripts/audit_dependency_schedule_coverage.py
	cd .. && $(PYTHON) scripts/audit_statistical_robustness.py
	cd .. && $(PYTHON) scripts/audit_ft_reliability_budget.py
	cd .. && $(PYTHON) scripts/run_component_replacement_case_studies.py
	cd .. && $(PYTHON) scripts/audit_joint_dse.py
	cd .. && $(PYTHON) scripts/audit_projection_invariants.py
	cd .. && $(PYTHON) scripts/generate_strong_accept_manifest.py
	cd .. && $(PYTHON) scripts/audit_paper_evidence.py
	cd .. && $(PYTHON) scripts/audit_previous_paper_alignment.py
	cd .. && $(PYTHON) scripts/audit_previous_paper_deep_trace.py
	cd .. && $(PYTHON) scripts/audit_previous_paper_style.py
	cd .. && $(PYTHON) scripts/audit_submission_readiness.py

clean:
	rm -f *.aux *.bbl *.blg *.log *.out $(PDF)
