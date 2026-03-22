.PHONY: dev dev-backend dev-frontend lint lint-backend lint-frontend test test-backend test-frontend security-scan build

# Development
dev-backend:
	cd backend && uvicorn lighthouse_api.main:app --reload --host 0.0.0.0 --port 8000

dev-frontend:
	cd frontend && npm run dev

dev:
	$(MAKE) dev-backend & $(MAKE) dev-frontend

# Linting
lint-backend:
	cd backend && ruff check src/ tests/ && ruff format --check src/ tests/ && mypy src/

lint-frontend:
	cd frontend && npx eslint src/ && npx tsc --noEmit

lint: lint-backend lint-frontend

# Testing
test-backend:
	cd backend && pytest tests/ -v --cov=lighthouse_api --cov-report=term-missing

test-frontend:
	cd frontend && npx vitest run --coverage

test: test-backend test-frontend

# Security
security-scan:
	@echo "=== Python Security Scan ==="
	cd backend && bandit -r src/ -f json -o /tmp/bandit-report.json || true
	cd backend && pip-audit 2>/dev/null || true
	@echo "=== Frontend Security Scan ==="
	cd frontend && npm audit --audit-level=moderate 2>/dev/null || true
	cd frontend && npx eslint src/ --format json 2>/dev/null || true
	@echo "=== Security scan complete ==="

# Database
migrate:
	cd backend && alembic upgrade head

seed:
	cd backend && python -m lighthouse_api.seed.seed_datasets

# Docker
build-backend:
	docker build -t lighthouse-api backend/

build-frontend:
	docker build -t lighthouse-frontend frontend/

build: build-backend build-frontend

# Deploy
deploy:
	@echo "Use: make deploy SHA=<commit-sha>"
	kubectl set image deployment/lighthouse-api api=us-central1-docker.pkg.dev/personal-project-289714/lighthouse/api:$(SHA) -n lighthouse
	kubectl set image deployment/lighthouse-frontend frontend=us-central1-docker.pkg.dev/personal-project-289714/lighthouse/frontend:$(SHA) -n lighthouse
