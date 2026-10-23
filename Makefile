# AvokatIM — Open Agent Hackathon 2026
# Komanda te shpejta per gjykuesin dhe per mua.

PY ?= python3
CORPUS ?= $(HOME)/oa-korpus/k-a

.PHONY: help test corpus-check corpus-size demo demo-offline

help:
	@echo "make test          - testet e kontrates se korpusit (offline)"
	@echo "make corpus-check  - verifiko sha256 e korpusit K-a"
	@echo "make corpus-size   - madhesia dhe numri i skedareve"
	@echo "make demo          - si xhirohet demoja (kërkon AVOKATIM_DSN)"

test:
	$(PY) -m pytest tests -q

corpus-check:
	cd $(CORPUS) && sha256sum -c SHA256SUMS

corpus-size:
	du -sh $(CORPUS)
	find $(CORPUS) -type f | wc -l

demo-offline:
	cd backend && $(PY) hackathon/demo_corpus.py "Kush u ankua per dezinsektimin e Prizrenit dhe cka vendosi paneli?"

demo:
	@echo "Demo kerkon Postgres me korpusin e ngarkuar:"
	@echo "  cd backend && AVOKATIM_DSN=<dsn> $(PY) hackathon/demo.py \"pyetja\""
	@echo "Harness:"
	@echo "  cd backend && AVOKATIM_DSN=<dsn> $(PY) hackathon/harness_v5.py"
