NAME = main.py

VENV = .venv

PYTHON = $(VENV)/bin/python3

ACTIVATE = source .venv/bin/activate

PIP = pip install

REQUIREMENTS = -r requirements.txt

SOURCES =	main.py \
			models.py \
			map.py \
			parser.py

CACHE = __pycache__ \
		*/__pycache__ \
		.mypy_cache

RM = rm -rf

LINT = flake8 $(SOURCES) && mypy $(SOURCES)


install:
	$(PYTHON) -m $(VENV) && $(ACTIVATE) && $(PIP) $(REQUIREMENTS)

run:
	$(PYTHON) $(NAME)

debug:
	$(PYTHON) -m pdb $(NAME) $(CONFIG)

clean:
	$(RM) $(CACHE)

lint:
	$(LINT) --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs

lint-strict:
	$(LINT) --strict

.PHONY: install run debug clean lint lint-strict
