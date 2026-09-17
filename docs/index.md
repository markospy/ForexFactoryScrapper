# ForexFactoryScrapper

ForexFactoryScrapper is a Flask REST API service that aggregates and serves economic calendar events from financial portals including ForexFactory, CryptoCraft, EnergyExch, and MetalsMine.

## Quick Start

### Docker

```bash
docker build -t forexfactory-scrapper .
docker run -d -p 5000:5000 --name forexfactory-scrapper forexfactory-scrapper
curl -f http://localhost:5000/api/health
```

### Local Environment

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

The service binds to `http://0.0.0.0:5000` by default.

### Key Interfaces

- **Welcome Landing**: `http://localhost:5000/`
- **Interactive Swagger UI**: `http://localhost:5000/swagger`
- **OpenAPI 3.0 Specification**: `http://localhost:5000/openapi.json`
