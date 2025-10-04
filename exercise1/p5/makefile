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

# Choose CPU: timing | o3
CPU ?= timing

# Outdirs
OUT_SE ?= out_se_$(CPU)
OUT_FS ?= out_fs_$(CPU)

CSV ?= p5-summary.csv

.PHONY: all se fs parse clean clobber both cpus

all: both parse

se:
	@mkdir -p $(OUT_SE)
	$(GEM5) --outdir=$(OUT_SE) $(SE) --cpu $(CPU)

fs:
	@mkdir -p $(OUT_FS)
	$(GEM5) --outdir=$(OUT_FS) $(FS) --cpu $(CPU)

# Convenience: run both CPUs and parse
both:
	@$(MAKE) CPU=timing  se fs
	@$(MAKE) CPU=o3      se fs
	@$(MAKE) parse

parse:
	$(PYTHON) $(PAR) --roots "$(OUT_SE)" "$(OUT_FS)" --out $(CSV)

clean:
	@rm -f $(CSV)
	@rm -rf out_*
