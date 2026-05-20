PYTHON ?= python3

.PHONY: test-fast audit

test-fast:
	$(PYTHON) -m unittest tests.test_loader tests.test_coordinates tests.test_spot_integrity

audit: test-fast
	$(PYTHON) scripts/spot_audit.py
