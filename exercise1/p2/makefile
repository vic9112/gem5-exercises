#////////////////////////////////////////////////////////
# Design: Makefile for GEM5 simulation
# Author: Kuan-Hsi(Vic) Chen
# Email : s179038@gmail.com
# Update: [2025/09/29]: Automatically sweep variables
#////////////////////////////////////////////////////////

PYTHON      ?= python3
GEM5        ?= gem5
GEM5_MESI   ?= gem5-mesi

# Scripts
RUBY_PY     ?= p2_1/p2_1.py
CLASSIC_PY  ?= p2_2/p2_2.py
PARSER      ?= parse.py

# Output roots
OUT_RUBY    ?= out_ruby
OUT_CLASSIC ?= out_classic
CSV_OUT     ?= p2-summary.csv

# Sweeps (ignore cache line size)
SIZES  ?= 128kB 256kB 512kB 1MB
ASSOCS ?= 8 16 32

.PHONY: all sweep parse clean clobber \
        run-ruby-size run-ruby-assoc run-classic-size run-classic-assoc

all: sweep parse

# ---- Ruby sweeps (MESI two-level) ----
run-ruby-size:
	@set -e; for s in $(SIZES); do \
	  echo "== Ruby L2 size $$s =="; \
	  $(GEM5_MESI) --outdir=$(OUT_RUBY)/l2_$$s $(RUBY_PY) --l2-size $$s; \
	done

run-ruby-assoc:
	@set -e; for a in $(ASSOCS); do \
	  echo "== Ruby L2 assoc $$a =="; \
	  $(GEM5_MESI) --outdir=$(OUT_RUBY)/l2a_$$a $(RUBY_PY) --l2-assoc $$a; \
	done

# ---- Classic sweeps (Private L1 + shared L2) ----
run-classic-size:
	@set -e; for s in $(SIZES); do \
	  echo "== Classic L2 size $$s =="; \
	  $(GEM5) --outdir=$(OUT_CLASSIC)/l2_$$s $(CLASSIC_PY) --l2-size $$s; \
	done

run-classic-assoc:
	@set -e; for a in $(ASSOCS); do \
	  echo "== Classic L2 assoc $$a =="; \
	  $(GEM5) --outdir=$(OUT_CLASSIC)/l2a_$$a $(CLASSIC_PY) --l2-assoc $$a; \
	done

# Convenience aggregate targets
sweep: run-ruby-size run-classic-size

parse:
	$(PYTHON) $(PARSER) --roots $(OUT_RUBY) $(OUT_CLASSIC) --out $(CSV_OUT)

clean:
	@rm -f $(CSV_OUT)

clobber: clean
	@rm -rf $(OUT_RUBY) $(OUT_CLASSIC)
