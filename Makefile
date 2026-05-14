PYTHON ?= python3
AAC_VERIFIER_PATH ?= ../agent-assurance-case/verifier/verify.py
SIGNED_AAC_DIR ?= dist/signed-aac

.PHONY: install verify write-signed pytest-safety clean

install:
	$(PYTHON) -m pip install -r runner/requirements.txt

verify:
	PYTHONDONTWRITEBYTECODE=1 AAC_VERIFIER_PATH=$(AAC_VERIFIER_PATH) $(PYTHON) runner/verify_fixtures.py

write-signed:
	PYTHONDONTWRITEBYTECODE=1 AAC_VERIFIER_PATH=$(AAC_VERIFIER_PATH) $(PYTHON) runner/verify_fixtures.py --write-signed $(SIGNED_AAC_DIR)
	$(PYTHON) -c "from pathlib import Path; import hashlib; d=Path('$(SIGNED_AAC_DIR)'); rows=[hashlib.sha256(p.read_bytes()).hexdigest()+'  '+p.name for p in sorted(d.glob('*-signed-aac.json'))]; (d/'SHA256SUMS').write_text('\n'.join(rows)+'\n', encoding='utf-8')"

pytest-safety:
	rm -f /tmp/dvaac_hidden_test_payload.txt
	PYTHONDONTWRITEBYTECODE=1 $(PYTHON) -m pytest --collect-only -q || test $$? -eq 5
	test ! -e /tmp/dvaac_hidden_test_payload.txt

clean:
	rm -rf dist .pytest_cache .ruff_cache
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
