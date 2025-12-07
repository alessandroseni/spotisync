.PHONY: help install sync radio clean setup

.DEFAULT_GOAL := help

help: ## Show available commands
	@echo "Spotisync & Lot Radio Finder"
	@echo "============================"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  make %-10s %s\n", $$1, $$2}'
	@echo ""

install: ## Install dependencies via pipenv
	@command -v pipenv >/dev/null 2>&1 || { echo "❌ pipenv not found. Install with: pip install pipenv"; exit 1; }
	pipenv install

setup: ## Copy .env.example to .env (if missing)
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo "✅ Created .env from .env.example - please configure your credentials"; \
	else \
		echo "⚠️  .env already exists"; \
	fi

sync: ## Run Spotisync (sync liked songs to playlist)
	@if [ ! -f .env ]; then \
		echo "❌ .env file not found! Run: make setup"; \
		exit 1; \
	fi
	@echo "🎵 Spotisync - Syncing your liked songs..."
	@echo "============================================"
	pipenv run python spotisync.py

radio: ## Run Lot Radio Artist Finder
	@if [ ! -f .env ]; then \
		echo "❌ .env file not found! Run: make setup"; \
		exit 1; \
	fi
	@echo "🎵📻 Lot Radio Artist Finder"
	@echo "============================================"
	pipenv run python lot_radio_finder.py

clean: ## Remove cache files
	@echo "🧹 Cleaning cache files..."
	rm -rf __pycache__ .cache* *.pyc
	@echo "✅ Done"
