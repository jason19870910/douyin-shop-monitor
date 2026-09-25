.PHONY: install build serve lint test ci

install:
	@echo "Installing dependencies..."
	npm ci

build:
	@echo "Building docs..."
	node convert.js

serve:
	@echo "Serving docs at http://localhost:3000"
	npx serve dist

lint:
	@echo "Linting Markdown..."
	npx markdownlint "**/*.md"

test:
	@echo "Running tests..."
	npm test

ci: lint test build