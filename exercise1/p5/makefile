#////////////////////////////////////////////////////////
# Design: Makefile for GEM5 simulation
# Author: Kuan-Hsi(Vic) Chen
# Email : s179038@gmail.com
# Update: [2025/09/29]: Automatically sweep variables
#////////////////////////////////////////////////////////

PYTHON ?= python3
GEM5   ?= gem5

SE  ?= p5_1/p5_1.py
FS  ?= p5_2/p5_2.py
PAR ?= parse.py

# Choose CPU
CPU ?= timing

OUT_SE ?= se_$(CPU)
OUT_FS ?= fs_$(CPU)

CSV ?= p5-summary.csv

.PHONY: all se fs parse clean both cpus

all: both parse

se:
	$(GEM5) --outdir=log/$(OUT_SE) $(SE) --cpu $(CPU)

fs:
	$(GEM5) --outdir=log/$(OUT_FS) $(FS) --cpu $(CPU)

# run both CPUs and parse
both:
	@$(MAKE) CPU=timing  se fs
	@$(MAKE) CPU=o3      se fs
	@$(MAKE) parse

parse:
	$(PYTHON) $(PAR) --roots "log/*" --out $(CSV)

clean:
	@rm -f $(CSV)
	@rm -rf log
