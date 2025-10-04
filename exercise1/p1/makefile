#////////////////////////////////////////////////////////
# Design: Makefile for GEM5 simulation
# Author: Kuan-Hsi(Vic) Chen
# Email : s179038@gmail.com
# Update: [2025/09/29]: Automatically sweep variables
#////////////////////////////////////////////////////////

GEM5   ?= gem5-mesi
PYTHON ?= python3
RUNPY  ?= p1.py

# --- sweeps (change ONE knob at a time) ---
ISSUES ?= 2 4 6
ROBS   ?= 64 128 192
LQS    ?= 16 32 64
SQS    ?= 16 32 64

BASE_T := out_timing
BASE_O3:= out_o3_default
O3_I   := $(foreach v,$(ISSUES),out_o3_issue$(v))
O3_R   := $(foreach v,$(ROBS),  out_o3_rob$(v))
O3_LQ  := $(foreach v,$(LQS),   out_o3_lq$(v))
O3_SQ  := $(foreach v,$(SQS),   out_o3_sq$(v))

.PHONY: all sweep parse clean clobber
all: sweep parse

sweep: $(BASE_T) $(BASE_O3) $(O3_I) $(O3_R) $(O3_LQ) $(O3_SQ)

# Baseline: TimingSimpleCPU (no micro-arch knobs)
$(BASE_T):
	@mkdir -p $@
	$(GEM5) --outdir=$@ $(RUNPY) --cpu timing

# O3 default (uses width=4, rob=128, lq=64, sq=64)
$(BASE_O3):
	@mkdir -p $@
	$(GEM5) --outdir=$@ $(RUNPY) --cpu o3

# O3: vary each knob separately
out_o3_issue%:
	@mkdir -p $@
	$(GEM5) --outdir=$@ $(RUNPY) --cpu o3 --width $*

out_o3_rob%:
	@mkdir -p $@
	$(GEM5) --outdir=$@ $(RUNPY) --cpu o3 --rob $*

out_o3_lq%:
	@mkdir -p $@
	$(GEM5) --outdir=$@ $(RUNPY) --cpu o3 --lq $*

out_o3_sq%:
	@mkdir -p $@
	$(GEM5) --outdir=$@ $(RUNPY) --cpu o3 --sq $*

parse:
	$(PYTHON) parse.py

clean:
	@rm -f results.csv
	@rm -rf out_*
