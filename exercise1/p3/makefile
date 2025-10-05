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

# RandomGenerator, r=80, 32 GiB/s, 512 MiB
GEN      ?= RandomGenerator
READPCT  ?= 80
BW       ?= 32GiB/s
SIZE     ?= 512MiB

# bandwidth & read% sweeps for p3_3
RATES     ?= 16GiB/s 32GiB/s
READPCTS  ?= 50 100

OUT_SINGLE ?= single
OUT_DUAL   ?= dual
OUT_CMP    ?= cmp

OUTCSV   ?= p3-summary.csv

.PHONY: all p3_1 p3_2 compare parse clean \
        p3_3_ddr4 p3_3_simple p3_3_bw p3_3_read

all: p3_1 p3_2 compare parse

# --- single/dual DDR4 ---
p3_1:  # single-channel DDR4-2400
	$(GEM5) --outdir=log/$(OUT_SINGLE) $(SINGLE) -c $(GEN) -r $(READPCT) -b $(BW) --size $(SIZE)

p3_2:  # dual-channel DDR4-2400
	$(GEM5) --outdir=log/$(OUT_DUAL) $(DUAL) -c $(GEN) -r $(READPCT) -b $(BW) --size $(SIZE)

# --- SimpleMemory vs DDR4 ---
p3_3_ddr4:
	$(GEM5) --outdir=log/$(OUT_CMP)_ddr4 $(CMP) --mem ddr4 -c $(GEN) -r $(READPCT) -b $(BW) --size $(SIZE)

p3_3_simple:
	$(GEM5) --outdir=log/$(OUT_CMP)_simple $(CMP) --mem simple -c $(GEN) -r $(READPCT) -b $(BW) --size $(SIZE) \
	        --simple-bw $(BW)

# --- Parameter comparisons for bandwidth & read% ---
p3_3_bw:
	@for b in $(RATES); do \
	  od1=$(OUT_CMP)_ddr4_bw$$(echo $$b | tr -d '/');  \
	  od2=$(OUT_CMP)_simple_bw$$(echo $$b | tr -d '/'); \
	  echo "== DDR4 @ $$b r=$(READPCT) =="; \
	  $(GEM5) --outdir=log/$$od1 $(CMP) --mem ddr4   -c $(GEN) -r $(READPCT) -b $$b --size $(SIZE); \
	  echo "== SIMPLE @ $$b r=$(READPCT) =="; \
	  $(GEM5) --outdir=log/$$od2 $(CMP) --mem simple -c $(GEN) -r $(READPCT) -b $$b --size $(SIZE) --simple-bw $$b; \
	done

p3_3_read:
	@for p in $(READPCTS); do \
	  od1=$(OUT_CMP)_ddr4_r$$p; \
	  od2=$(OUT_CMP)_simple_r$$p; \
	  echo "== DDR4 @ $(BW) r=$$p =="; \
	  $(GEM5) --outdir=log/$$od1 $(CMP) --mem ddr4   -c $(GEN) -r $$p -b $(BW) --size $(SIZE); \
	  echo "== SIMPLE @ $(BW) r=$$p =="; \
	  $(GEM5) --outdir=log/$$od2 $(CMP) --mem simple -c $(GEN) -r $$p -b $(BW) --size $(SIZE) --simple-bw $(BW); \
	done

compare: p3_3_ddr4 p3_3_simple p3_3_bw p3_3_read

parse:
	$(PYTHON) $(PARSER) --roots "log/*"  --out $(OUTCSV)

clean:
	@rm -f $(OUTCSV)
	@rm -rf log
