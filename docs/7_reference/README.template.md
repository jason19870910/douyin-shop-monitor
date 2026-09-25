# `[[PROJECT_NAME]]`

[[PROJECT_DESCRIPTION]]

## ✨ Features

- [[Feature 1]]
- [[Feature 2]]
- [[Feature 3]]

## 🚀 Quick Start

### Prerequisites

- Node.js 20+ (or Python 3.10+)
- Git

### Installation

```bash
npm ci  # or pip install -r requirements.lock.txt
```

### Configuration

Copy `.env.example` to `.env` and fill in required values:

```bash
cp .env.example .env
```

### Development

```bash
# Run with hot-reload (if supported)
npm run dev

# Lint
npm run lint

# Format
npm run format

# Test
npm test
```

### Production Build

```bash
npm run build
```

### Deployment

```bash
# Using systemd (Linux)
sudo cp deploy/doudian_monitor.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable doudian_monitor
sudo systemctl start doudian_monitor

# Using Docker
docker build -t [[PROJECT_NAME]] .
docker run -d --restart unless-stopped --env-file .env -p 3000:3000 [[PROJECT_NAME]]
```

## 📈 Monitoring

- Health check: `GET /.health` or `GET /health`
- Metrics: `GET /metrics` (Prometheus format)

## 📝 License

Internal use only.