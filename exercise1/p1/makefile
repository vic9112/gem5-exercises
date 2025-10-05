#////////////////////////////////////////////////////////
# Design: Makefile for GEM5 simulation
# Author: Kuan-Hsi(Vic) Chen
# Email : s179038@gmail.com
# Update: [2025/09/29]: Automatically sweep variables
#////////////////////////////////////////////////////////

GEM5   ?= gem5-mesi
PYTHON ?= python3
RUNPY  ?= p1.py

# --- sweep parameters ---
ISSUES ?= 2 4 6
ROBS   ?= 64 128 192
LQS    ?= 16 32 64
SQS    ?= 16 32 64

BASE_T := timing
BASE_O3:= default
O3_I   := $(foreach v,$(ISSUES),o3_issue$(v))
O3_R   := $(foreach v,$(ROBS),  o3_rob$(v))
O3_LQ  := $(foreach v,$(LQS),   o3_lq$(v))
O3_SQ  := $(foreach v,$(SQS),   o3_sq$(v))

.PHONY: all sweep parse clean
all: sweep parse

sweep: $(BASE_T) $(BASE_O3) $(O3_I) $(O3_R) $(O3_LQ) $(O3_SQ)

# TimingSimpleCPU
$(BASE_T):
	$(GEM5) --outdir=log/$(BASE_T) $(RUNPY) --cpu timing

# O3 default (uses width=4, rob=128, lq=64, sq=64)
$(BASE_O3):
	$(GEM5) --outdir=log/$(BASE_O3) $(RUNPY) --cpu o3

# vary each separately
o3_issue%:
	$(GEM5) --outdir=log/$@ $(RUNPY) --cpu o3 --width $*

o3_rob%:
	$(GEM5) --outdir=log/$@ $(RUNPY) --cpu o3 --rob $*

o3_lq%:
	$(GEM5) --outdir=log/$@ $(RUNPY) --cpu o3 --lq $*

o3_sq%:
	$(GEM5) --outdir=log/$@ $(RUNPY) --cpu o3 --sq $*

parse:
	$(PYTHON) parse.py

clean:
	@rm -f results.csv
	@rm -rf log
