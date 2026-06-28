NAME = src

install:
	@uv sync

run:
	@uv run python -m $(NAME)

lint:
	@uv run flake8 .
	@uv run mypy . --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs

lint-strict:
	@uv run mypy . --strict

clean:
	@rm -rf */__pycache__ */.mypy_cache .mypy_cache __pycache__

debug:
	@uv run python -m pdb -m $(NAME)
