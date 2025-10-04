#////////////////////////////////////////////////////////
# Design: Makefile for GEM5 simulation
# Author: Kuan-Hsi(Vic) Chen
# Email : s179038@gmail.com
# Update: [2025/09/29]: Automatically sweep variables
#////////////////////////////////////////////////////////

PYTHON ?= python3
GEM5   ?= gem5

P41    ?= p4_1/p4_1.py
P42    ?= p4_2/p4_2.py
PARSER ?= parse.py

OUT_P41_TIMING ?= out_timing
OUT_P41_O3     ?= out_o3
OUT_P42_KVM    ?= out_kvm

CSV_OUT ?= p4-summary.csv

.PHONY: all p4_1_timing p4_1_o3 p4_2_kvm parse clean clobber

all: p4_1_timing p4_1_o3 p4_2_kvm parse

# Method 1: KVM → switch to TimingSimpleCPU at 2nd m5 exit
p4_1_timing:
	@mkdir -p $(OUT_P41_TIMING)
	$(GEM5) --outdir=$(OUT_P41_TIMING) $(P41) --detailed timing

# Method 1: KVM → switch to X86O3CPU at 2nd m5 exit
p4_1_o3:
	@mkdir -p $(OUT_P41_O3)
	$(GEM5) --outdir=$(OUT_P41_O3) $(P41) --detailed o3

# Method 2: KVM only (no switch)
p4_2_kvm:
	@mkdir -p $(OUT_P42_KVM)
	$(GEM5) --outdir=$(OUT_P42_KVM) $(P42)

parse:
	$(PYTHON) $(PARSER) --roots "$(OUT_P41_TIMING)" "$(OUT_P41_O3)" "$(OUT_P42_KVM)" --out $(CSV_OUT)

clean:
	@rm -f $(CSV_OUT)
	@rm -rf $(OUT_P41_TIMING) $(OUT_P41_O3) $(OUT_P42_KVM)
