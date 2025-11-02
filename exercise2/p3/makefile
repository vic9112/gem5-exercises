#////////////////////////////////////////////////////////
# Design: Makefile for GEM5 simulation
# Author: Kuan-Hsi(Vic) Chen
# Email : s179038@gmail.com
# Update: [2025/11/01]: Automatically sweep variables
#////////////////////////////////////////////////////////

PYTHON ?= python3
GEM5   ?= gem5

# Python Scripts
CLASSIC ?= scripts/classic.py
CHI     ?= scripts/chi.py
PARSER  ?= scripts/parse.py

# Output Folders
OUT_CLASSIC ?= log/fs_classic
OUT_CHI     ?= log/fs_chi

.PHONY: all chi_fs

all: chi_fs classic_fs parse

classic_fs:
	echo "== Classic Full-System Start =="
	$(GEM5) --outdir=$(OUT_CLASSIC) $(CLASSIC)

chi_fs:
	echo "== CHI Full-System Start =="
	$(GEM5) --outdir=$(OUT_CHI) $(CHI)
	
parse:
	$(PYTHON) $(PARSER)