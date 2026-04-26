SHELL := /bin/zsh

.PHONY: frontend-dev backend-dev dev-stable

frontend-dev:
	CHOKIDAR_USEPOLLING=true CHOKIDAR_INTERVAL=250 npm --prefix "./frontend" run dev:stable

backend-dev:
	WATCHFILES_FORCE_POLLING=true ./.venv311/bin/python -m uvicorn app.main:app --reload --app-dir "./backend" --host 127.0.0.1 --port 8000

dev-stable:
	@echo "Run frontend and backend in separate terminals:"
	@echo "  make frontend-dev"
	@echo "  make backend-dev"
