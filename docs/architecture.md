# System Architecture

ForexFactoryScrapper decouples HTTP API routing and presentation from web scraping logic.

## Decoupled Architecture

All HTML extraction and DOM parsing is managed upstream by the [`forex-pytory`](https://github.com/AtaCanYmc/forex-pytory) package. ForexFactoryScrapper delegates data fetching entirely to that library and focuses solely on providing an HTTP REST API interface.

### Architectural Rationale

- **Modularity**: The scraping engine and the web server operate as independent modules.
- **Maintainability**: Markup alterations on target financial calendars only necessitate updates in `forex-pytory`, leaving API routes untouched.
- **Type Safety**: Validation and schema serialization are managed strictly with Pydantic models at the library layer.

## Component Flow

```mermaid
flowchart TD
    Client["Client / API Consumer / Swagger UI"] -->|"HTTP GET"| App["Flask Application (src/app.py)"]
    App --> Blueprints["Route Blueprints (src/routes/)"]
    Blueprints --> Validation["Parameter & Paging Validator"]
    Validation --> Engine["forex-pytory (Parsing Engine & Pydantic Models)"]
    Engine -->|"Scrape HTML"| FF["ForexFactory"]
    Engine -->|"Scrape HTML"| CC["CryptoCraft"]
    Engine -->|"Scrape HTML"| MM["MetalsMine"]
    Engine -->|"Scrape HTML"| EE["EnergyExch"]
```
