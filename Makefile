PYTHON ?= python3
UV ?= uv
AAC_VERIFIER_PATH ?= $(shell if [ -f ../agent-assurance-case/verifier/verify.py ]; then printf '%s' ../agent-assurance-case/verifier/verify.py; elif [ -f ../agent-assurance-case-spec/verifier/verify.py ]; then printf '%s' ../agent-assurance-case-spec/verifier/verify.py; else printf '%s' ../agent-assurance-case/verifier/verify.py; fi)
SIGNED_AAC_DIR ?= dist/signed-aac

.PHONY: install verify write-signed validate-scorecard pytest-safety publication-ready clean

install:
	$(UV) pip install --python $(PYTHON) -r runner/requirements.txt
	$(UV) pip install --python $(PYTHON) -r runner/requirements-dev.txt

verify:
	PYTHONDONTWRITEBYTECODE=1 AAC_VERIFIER_PATH=$(AAC_VERIFIER_PATH) $(PYTHON) runner/verify_fixtures.py

write-signed:
	PYTHONDONTWRITEBYTECODE=1 AAC_VERIFIER_PATH=$(AAC_VERIFIER_PATH) $(PYTHON) runner/verify_fixtures.py --write-signed $(SIGNED_AAC_DIR)
	PYTHONDONTWRITEBYTECODE=1 $(PYTHON) runner/write_release_manifest.py --aac-verifier "$(AAC_VERIFIER_PATH)" $(SIGNED_AAC_DIR)

validate-scorecard:
	@test -n "$(SCORECARD)" || { echo "usage: make validate-scorecard SCORECARD=path/to/scorecard.json"; exit 2; }
	@PYTHONDONTWRITEBYTECODE=1 $(PYTHON) runner/validate_scorecard.py "$(SCORECARD)"

pytest-safety:
	rm -f /tmp/dvaac_hidden_test_payload.txt
	@matches="$$(find fixtures -type f \( -name 'test_*.py' -o -name '*_test.py' -o -name 'conftest.py' \) -print)"; test -z "$$matches" || { echo "$$matches"; exit 1; }
	PYTHONDONTWRITEBYTECODE=1 $(PYTHON) -m pytest --collect-only -q || test $$? -eq 5
	test ! -e /tmp/dvaac_hidden_test_payload.txt

publication-ready:
	./VERIFY-PUBLICATION-READY.sh

clean:
	rm -rf dist .pytest_cache .ruff_cache .hypothesis
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
