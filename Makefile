NAME = main.py

PYTHON = python3

PIP = pip install

REQUIREMENTS = -r requirements.txt

SOURCES =	main.py \
			exceptions.py \
			models.py \
			parser.py \
			map.py \
			map_draw.py

CACHE = __pycache__ \
		*/__pycache__ \
		.mypy_cache

RM = rm -rf

LINT = flake8 $(SOURCES) && mypy $(SOURCES)


install:
	uv sync

run: install
	uv run $(NAME)

debug: install
	$(PYTHON) -m pdb $(NAME) $(CONFIG)

clean:
	$(RM) $(CACHE)

lint: install
	$(LINT) --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs

lint-strict: install
	$(LINT) --strict

.PHONY: install run debug clean lint lint-strict
