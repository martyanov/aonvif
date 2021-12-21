.DEFAULT: help
.PHONY: help bootstrap build lint outdated test testcov testreport upload clean

VENV = .venv
PYTHON_BIN ?= python3
PYTHON = $(VENV)/bin/$(PYTHON_BIN)

help:
	@echo "Please use \`$(MAKE) <target>' where <target> is one of the following:"
	@echo "  help       - show help information"
	@echo "  bootstrap  - setup packaging dependencies and initialize venv"
	@echo "  build      - build project packages"
	@echo "  lint       - inspect project source code for errors"
	@echo "  outdated   - list outdated project requirements"
	@echo "  test       - run project tests"
	@echo "  testcov    - run project tests with coverage file report"
	@echo "  testreport - run project tests and open HTML coverage report"
	@echo "  upload     - upload built packages to package repository"
	@echo "  clean      - clean up project environment and all the build artifacts"

bootstrap: $(VENV)/bin/activate
$(VENV)/bin/activate:
	$(PYTHON_BIN) -m venv $(VENV)
	$(PYTHON) -m pip install -U pip==21.3.1 setuptools==60.0.3 wheel==0.37.0
	$(PYTHON) -m pip install -e .[dev,test]

build: bootstrap
	$(PYTHON) setup.py sdist bdist_wheel

lint: bootstrap
	$(PYTHON) -m flake8 examples onvif tests

outdated: bootstrap
	$(PYTHON) -m pip list --outdated --format=columns

test: bootstrap
	$(PYTHON) -m pytest

testcov: bootstrap
	$(PYTHON) -m pytest --cov-report=xml

testreport: bootstrap
	$(PYTHON) -m pytest --cov-report=html
	xdg-open htmlcov/index.html

upload: build
	$(PYTHON) -m twine upload dist/*

clean:
	rm -rf *.egg-info .eggs .pytest_cache coverage.xml build dist htmlcov $(VENV)
