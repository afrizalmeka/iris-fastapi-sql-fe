VENV_DIR ?= .venv

ifeq ($(OS),Windows_NT)
PYTHON ?= python
VENV_BIN := $(VENV_DIR)/Scripts
else
PYTHON ?= python3
VENV_BIN := $(VENV_DIR)/bin
endif

VENV_PY := $(VENV_BIN)/python

.PHONY: build run up

build:
	$(PYTHON) -m venv --clear $(VENV_DIR)
	$(VENV_PY) -m pip install -r requirements.txt

run: up

up:
	$(VENV_BIN)/uvicorn main:app --reload
