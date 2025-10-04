#////////////////////////////////////////////////////////
# Design: Makefile for GEM5 simulation
# Author: Kuan-Hsi(Vic) Chen
# Email : s179038@gmail.com
# Update: [2025/09/29]: Automatically sweep variables
#////////////////////////////////////////////////////////

PYTHON ?= python3
GEM5   ?= gem5-mesi

SINGLE ?= p3_1/p3_1.py
DUAL   ?= p3_2/p3_2.py
CMP    ?= p3_3/p3_3.py
PARSER ?= parse.py

# Baseline assignment: RandomGenerator, r=80, 32 GiB/s, 512 MiB
GEN      ?= RandomGenerator
READPCT  ?= 80
BW       ?= 32GiB/s
SIZE     ?= 512MiB

# Comparison sets (bandwidth & read% sweeps) for p3_3
RATES     ?= 16GiB/s 32GiB/s
READPCTS  ?= 50 100

# Output log
OUT_SINGLE ?= out_single
OUT_DUAL   ?= out_dual
OUT_CMP    ?= out_cmp

OUTCSV   ?= p3-summary.csv

.PHONY: all p3_1 p3_2 compare parse clean clobber \
        p3_3_ddr4 p3_3_simple p3_3_bw p3_3_read

all: p3_1 p3_2 compare parse

# --- Required single/dual DDR4 experiments ---
p3_1:  # single-channel DDR4-2400
	@mkdir -p $(OUT_SINGLE)
	$(GEM5) --outdir=$(OUT_SINGLE) $(SINGLE) -c $(GEN) -r $(READPCT) -b $(BW) --size $(SIZE)

p3_2:  # dual-channel DDR4-2400 (uses NoCache inside p3_2.py)
	@mkdir -p $(OUT_DUAL)
	$(GEM5) --outdir=$(OUT_DUAL) $(DUAL) -c $(GEN) -r $(READPCT) -b $(BW) --size $(SIZE)

# --- SimpleMemory vs DDR4 at SAME size/bandwidth (baseline) ---
p3_3_ddr4:
	@mkdir -p $(OUT_CMP)/ddr4
	$(GEM5) --outdir=$(OUT_CMP)/ddr4 $(CMP) --mem ddr4 -c $(GEN) -r $(READPCT) -b $(BW) --size $(SIZE)

p3_3_simple:
	@mkdir -p $(OUT_CMP)/simple
	$(GEM5) --outdir=$(OUT_CMP)/simple $(CMP) --mem simple -c $(GEN) -r $(READPCT) -b $(BW) --size $(SIZE) \
	        --simple-bw $(BW)

# --- Parameter comparisons for Problem 3 (bandwidth & read%) ---
# Sweep bandwidth: 16 vs 32 GiB/s for BOTH memories
p3_3_bw:
	@for b in $(RATES); do \
	  od1=$(OUT_CMP)/ddr4_bw$$(echo $$b | tr -d '/');  mkdir -p $$od1; \
	  od2=$(OUT_CMP)/simple_bw$$(echo $$b | tr -d '/'); mkdir -p $$od2; \
	  echo "== DDR4 @ $$b r=$(READPCT) =="; \
	  $(GEM5) --outdir=$$od1 $(CMP) --mem ddr4   -c $(GEN) -r $(READPCT) -b $$b --size $(SIZE); \
	  echo "== SIMPLE @ $$b r=$(READPCT) =="; \
	  $(GEM5) --outdir=$$od2 $(CMP) --mem simple -c $(GEN) -r $(READPCT) -b $$b --size $(SIZE) --simple-bw $$b; \
	done

# Sweep read%: 50 vs 100 for BOTH memories
p3_3_read:
	@for p in $(READPCTS); do \
	  od1=$(OUT_CMP)/ddr4_r$$p;  mkdir -p $$od1; \
	  od2=$(OUT_CMP)/simple_r$$p; mkdir -p $$od2; \
	  echo "== DDR4 @ $(BW) r=$$p =="; \
	  $(GEM5) --outdir=$$od1 $(CMP) --mem ddr4   -c $(GEN) -r $$p -b $(BW) --size $(SIZE); \
	  echo "== SIMPLE @ $(BW) r=$$p =="; \
	  $(GEM5) --outdir=$$od2 $(CMP) --mem simple -c $(GEN) -r $$p -b $(BW) --size $(SIZE) --simple-bw $(BW); \
	done

compare: p3_3_ddr4 p3_3_simple p3_3_bw p3_3_read

parse:
	$(PYTHON) $(PARSER) --roots $(OUT_SINGLE) $(OUT_DUAL) $(OUT_CMP)/*  --out $(OUTCSV)

clean:
	@rm -f $(OUTCSV)
	@rm -rf out_*
