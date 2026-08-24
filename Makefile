# Douyin Project - Unified Build & Deployment Commands
# Usage: make <target>
#        make help          # Show all available targets

.PHONY: help up down restart build rebuild logs ps clean test lint format backup restore

# Default target
help:
	@echo "=========================================="
	@echo "  Douyin Project - Available Commands"
	@echo "=========================================="
	@echo ""
	@echo "🐳 Docker Compose:"
	@echo "  make up           - Start all services (detached)"
	@echo "  make up-logs      - Start all services with logs"
	@echo "  make down         - Stop and remove all containers"
	@echo "  make restart      - Restart all services"
	@echo "  make ps           - List running containers"
	@echo "  make logs         - Follow logs for all services"
	@echo "  make logs-monitor - Follow monitor service logs"
	@echo "  make logs-frontend- Follow frontend service logs"
	@echo "  make logs-celery  - Follow celery service logs"
	@echo ""
	@echo "🔨 Build:"
	@echo "  make build        - Build all service images"
	@echo "  make build-monitor- Build monitor service image"
	@echo "  make build-frontend- Build frontend service image"
	@echo "  make rebuild      - Rebuild all images (no cache)"
	@echo ""
	@echo "🧪 Testing & Quality:"
	@echo "  make test         - Run all tests"
	@echo "  make test-monitor - Run monitor service tests"
	@echo "  make test-frontend- Run frontend tests"
	@echo "  make lint         - Run all linters"
	@echo "  make lint-monitor - Run monitor linter (ruff)"
	@echo "  make lint-frontend- Run frontend linter (eslint)"
	@echo "  make format       - Format code (black + prettier)"
	@echo ""
	@echo "🧹 Maintenance:"
	@echo "  make clean        - Remove stopped containers, unused images, volumes"
	@echo "  make clean-all    - Deep clean (includes volumes)"
	@echo "  make prune        - Docker system prune"
	@echo "  make backup       - Backup project (exclude node_modules, .git, etc.)"
	@echo "  make restore      - Restore from backup"
	@echo ""
	@echo "🚀 Deployment:"
	@echo "  make deploy       - Deploy to production (with SSL)"
	@echo "  make deploy-dev   - Deploy to development"
	@echo "  make ssl-init     - Initialize SSL certificates (Let's Encrypt)"
	@echo "  make ssl-renew    - Renew SSL certificates"
	@echo ""
	@echo "📦 Database:"
	@echo "  make migrate      - Run database migrations"
	@echo "  make migrate-create- Create new migration"
	@echo ""
	@echo "=========================================="

# ==========================================
# Docker Compose Commands
# ==========================================
COMPOSE_FILE := docker-compose.yml
COMPOSE := docker compose -f $(COMPOSE_FILE)

up:
	$(COMPOSE) up -d

up-logs:
	$(COMPOSE) up

down:
	$(COMPOSE) down

restart:
	$(COMPOSE) restart

ps:
	$(COMPOSE) ps

logs:
	$(COMPOSE) logs -f

logs-monitor:
	$(COMPOSE) logs -f monitor

logs-frontend:
	$(COMPOSE) logs -f frontend

logs-celery:
	$(COMPOSE) logs -f celery_worker celery_beat

logs-nginx:
	$(COMPOSE) logs -f nginx

logs-redis:
	$(COMPOSE) logs -f redis

# ==========================================
# Build Commands
# ==========================================
build:
	$(COMPOSE) build

build-monitor:
	$(COMPOSE) build monitor

build-frontend:
	$(COMPOSE) build frontend

build-nginx:
	$(COMPOSE) build nginx

rebuild:
	$(COMPOSE) build --no-cache

# ==========================================
# Testing Commands
# ==========================================
test: test-monitor test-frontend

test-monitor:
	cd opt/douyin-platform/apps/monitor && python -m pytest tests/ -v --cov=app --cov-report=term-missing

test-frontend:
	cd frontend && npm test -- --watchAll=false --ci

# ==========================================
# Linting Commands
# ==========================================
lint: lint-monitor lint-frontend

lint-monitor:
	cd opt/douyin-platform/apps/monitor && ruff check . && ruff format --check .

lint-frontend:
	cd frontend && npm run lint

# ==========================================
# Formatting Commands
# ==========================================
format: format-monitor format-frontend

format-monitor:
	cd opt/douyin-platform/apps/monitor && ruff format .

format-frontend:
	cd frontend && npx prettier --write "src/**/*.{js,jsx,ts,tsx,json,css,md}"

# ==========================================
# Maintenance Commands
# ==========================================
clean:
	$(COMPOSE) down -v --remove-orphans
	docker container prune -f
	docker image prune -f

clean-all:
	$(COMPOSE) down -v --remove-orphans
	docker system prune -af --volumes

prune:
	docker system prune -af --volumes

# Backup project (exclude build artifacts, dependencies, git)
backup:
	@timestamp=$$(date +%Y%m%d_%H%M%S); \
	backup_name="douyin_backup_$$timestamp"; \
	echo "Creating backup: $$backup_name"; \
	tar --exclude='node_modules' \
	    --exclude='.git' \
	    --exclude='__pycache__' \
	    --exclude='*.pyc' \
	    --exclude='*.log' \
	    --exclude='*.tar.gz' \
	    --exclude='*.zip' \
	    --exclude='douyin_backup_*' \
	    --exclude='frontend/build' \
	    --exclude='opt/douyin-platform/apps/monitor/logs' \
	    --exclude='.venv' \
	    --exclude='venv' \
	    -czf "$$backup_name.tar.gz" .; \
	echo "Backup created: $$backup_name.tar.gz"

# ==========================================
# Deployment Commands
# ==========================================
deploy: build up
	@echo "✅ Production deployment complete!"
	@echo "   Frontend: https://wlkj-tech.cn"
	@echo "   API:      https://wlkj-tech.cn/api/v1"
	@echo "   Health:   https://wlkj-tech.cn/health"

deploy-dev:
	$(COMPOSE) -f docker-compose.yml up -d --build
	@echo "✅ Development deployment complete!"
	@echo "   Frontend: http://localhost:3000"
	@echo "   API:      http://localhost:5000/api/v1"
	@echo "   Health:   http://localhost/health"

# SSL certificate management (requires certbot)
ssl-init:
	@echo "Initializing SSL certificates..."
	docker run -it --rm \
		-v ./certbot/conf:/etc/letsencrypt \
		-v ./certbot/www:/var/www/certbot \
		certbot/certbot certonly --webroot \
		-w /var/www/certbot \
		-d wlkj-tech.cn -d www.wlkj-tech.cn \
		--email admin@wlkj-tech.cn --agree-tos --no-eff-email

ssl-renew:
	@echo "Renewing SSL certificates..."
	docker run -it --rm \
		-v ./certbot/conf:/etc/letsencrypt \
		-v ./certbot/www:/var/www/certbot \
		certbot/certbot renew --webroot -w /var/www/certbot
	$(COMPOSE) exec nginx nginx -s reload

# ==========================================
# Database Commands
# ==========================================
migrate:
	$(COMPOSE) exec monitor python -m alembic upgrade head

migrate-create:
	@read -p "Migration message: " msg; \
	$(COMPOSE) exec monitor python -m alembic revision --autogenerate -m "$$msg"

# ==========================================
# Development Helpers
# ==========================================
shell-monitor:
	$(COMPOSE) exec monitor sh

shell-frontend:
	$(COMPOSE) exec frontend sh

shell-redis:
	$(COMPOSE) exec redis redis-cli

shell-nginx:
	$(COMPOSE) exec nginx sh

# Install dependencies locally (for IDE support)
install-monitor:
	cd opt/douyin-platform/apps/monitor && pip install -r requirements.txt

install-frontend:
	cd frontend && npm install

install-all: install-monitor install-frontend

# Check service health
health:
	@echo "Checking service health..."
	@curl -sf http://localhost/health && echo "✅ Nginx/Health OK" || echo "❌ Nginx/Health FAILED"
	@curl -sf http://localhost:5000/api/v1/health && echo "✅ Monitor API OK" || echo "❌ Monitor API FAILED"
	@curl -sf http://localhost:3000/health && echo "✅ Frontend OK" || echo "❌ Frontend FAILED"

# Show service status
status:
	$(COMPOSE) ps
	@echo ""
	@make health