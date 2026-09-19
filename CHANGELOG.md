# Changelog

## 1.0.0 (2026-09-19)


### Features

* add .env.example and update main.py for environment variable support ([d6a6be1](https://github.com/markospy/ForexFactoryScrapper/commit/d6a6be19cf0f103b45facfbee9dfd99d743dd54d))
* add bundle endpoint to fetch combined economic events from multiple sources; update README with endpoint details ([fc1e20c](https://github.com/markospy/ForexFactoryScrapper/commit/fc1e20c9812298247f98e1861c43bcf57be55430))
* add common utilities for scrapers; refactor existing scrapers to use shared functions ([4b459e3](https://github.com/markospy/ForexFactoryScrapper/commit/4b459e3fd9f97f88a948d031199849df07e6c123))
* add cryptocraft daily endpoint with pagination and validation; include tests for various scenarios ([b694184](https://github.com/markospy/ForexFactoryScrapper/commit/b694184d70d6f3dabcd0b35dd255636f806c261c))
* add energyexch daily endpoint with pagination and validation; include tests for various scenarios ([dea0cf9](https://github.com/markospy/ForexFactoryScrapper/commit/dea0cf99d09921602e23a40b2c4798195008a26d))
* add historical fundamentals export script and update README with usage instructions ([e14a961](https://github.com/markospy/ForexFactoryScrapper/commit/e14a961109eb4a3f65ef0693dbb7281a0578c3b3))
* add metalsmine daily endpoint with pagination and validation; include tests for various scenarios ([5be0eb5](https://github.com/markospy/ForexFactoryScrapper/commit/5be0eb5965c0b3fed3aa671d686dc32422356e24))
* add optional paging support to /api/forex/daily endpoint with limit and offset parameters ([95e726a](https://github.com/markospy/ForexFactoryScrapper/commit/95e726a0d909b339ad46e6f21083eec906521300))
* add Postman collection for Forex API with test scripts ([1e8c104](https://github.com/markospy/ForexFactoryScrapper/commit/1e8c10499db5f6e3a162d68c3d0a9dfdc7d0367b))
* add root route and welcome page; implement basic navigation links to API endpoints ([312cdd8](https://github.com/markospy/ForexFactoryScrapper/commit/312cdd81d6bd7488ca5d4055b8178551a9ef54b7))
* add route blueprints for various data sources; implement helper functions for record retrieval and pagination ([362897e](https://github.com/markospy/ForexFactoryScrapper/commit/362897edcb752cb1c351c977c6706805508ac584))
* add ROW_ID attribute for unique event identification; refactor related code for clarity and consistency ([ff2a87d](https://github.com/markospy/ForexFactoryScrapper/commit/ff2a87d8b363e5759d3e95f64d573c1be68227d2))
* add sitemap functionality to fetch and parse ForexFactory sitemaps; implement API endpoint for paginated sitemap URLs ([6d90abe](https://github.com/markospy/ForexFactoryScrapper/commit/6d90abe0899d039f3734a2af31aa5bedcbbe9d60))
* add validation helpers for date and paging parameters; refactor routes to improve error handling and code clarity ([8f106ca](https://github.com/markospy/ForexFactoryScrapper/commit/8f106ca81cf8007ba0e9d1521ccac9bbf8a847e4))
* allow top-level main module to provide scraper function overrides; refactor helper resolution logic ([984b0c1](https://github.com/markospy/ForexFactoryScrapper/commit/984b0c1cac9e3ad47d51a2eb4248d41b02002211))
* configure CORS to allow all origins for Swagger UI requests to prevent cross-origin issues ([3cbc38b](https://github.com/markospy/ForexFactoryScrapper/commit/3cbc38bd8f9065055b4a0f2e1b72f13d9fde9a02))
* enhance download fundamentals script with raw HTML extraction and improve event normalization ([2fa12b1](https://github.com/markospy/ForexFactoryScrapper/commit/2fa12b1e077f75afdab6809d45ddb177aeb8e125))
* enhance error logging in various routes and helper functions for better debugging ([70c8a59](https://github.com/markospy/ForexFactoryScrapper/commit/70c8a5986ba4a76b4a18922fd2900213ae466236))
* enhance event parsing and normalization; introduce impact value normalization and update API response structure ([ac0ee74](https://github.com/markospy/ForexFactoryScrapper/commit/ac0ee7400ecd47d334c4b115a3f00ff68104f994))
* enhance OpenAPI spec with additional metadata and endpoints; add root route and improve documentation ([a42f570](https://github.com/markospy/ForexFactoryScrapper/commit/a42f570b5f372441b66ca53bd4e520c592c80232))
* enhance sitemap parsing to handle XML namespaces; update README with sitemap endpoint details ([53b80e1](https://github.com/markospy/ForexFactoryScrapper/commit/53b80e19f81f6ccfa8896e10fafc498e49afc29c))
* enhance Swagger UI initialization to support inline OpenAPI spec; improve error handling and fallback for template rendering ([0a8882c](https://github.com/markospy/ForexFactoryScrapper/commit/0a8882c998a5a60b4ac526267b1401051a013956))
* enhance timestamp parsing by adding additional date formats for scheduled events ([c431a37](https://github.com/markospy/ForexFactoryScrapper/commit/c431a37ff953a51156bc5afd22178ce5958081f1))
* enhance timestamp parsing for scheduled events and streamline consolidation logic ([46af0e7](https://github.com/markospy/ForexFactoryScrapper/commit/46af0e70337e8bbc542ddd09c4c309f17d365938))
* implement centralized error handling for Flask app and add tests for error responses ([a90eedb](https://github.com/markospy/ForexFactoryScrapper/commit/a90eedb402bbe0a03a3260eac1a8a846f452d3ea))
* implement pagination for /api/forex/daily endpoint and add OpenAPI spec with Swagger UI ([b0eaf78](https://github.com/markospy/ForexFactoryScrapper/commit/b0eaf7832317842f67e5f15be62e12d00d3f5a99))
* introduce date_to_string utility function; refactor time formatting in event records for improved clarity ([dd8253c](https://github.com/markospy/ForexFactoryScrapper/commit/dd8253c328d5b5798f4211ae219b4953285caf9c))
* introduce helper functions for cell value normalization and safe text extraction; improve code modularity and readability ([7ffe9a4](https://github.com/markospy/ForexFactoryScrapper/commit/7ffe9a474577400d492b02843249956315ddfdfb))
* introduce shared constants and utility functions for scrapers; refactor existing code for modularity ([52df947](https://github.com/markospy/ForexFactoryScrapper/commit/52df9474ca174b88b7b7e4c1c200f5f6dd5743d1))
* refactor api_routes and app to use consistent naming conventions for get_records and get_url; improve code readability and maintainability ([a8a2ac3](https://github.com/markospy/ForexFactoryScrapper/commit/a8a2ac37abcf99b7584f756fabd0da1340973ab1))
* refactor application structure and migrate to app.py with Flask routes ([ede7da5](https://github.com/markospy/ForexFactoryScrapper/commit/ede7da5cc18c384c1b252a5158fa57947a713cc3))
* refactor calendar parsing logic into modular functions for improved readability and maintainability ([2310a2b](https://github.com/markospy/ForexFactoryScrapper/commit/2310a2ba9f19b2451b694685f868c6006830ee42))
* refactor class name handling in parser and tests for consistency; improve readability and maintainability ([a8bd883](https://github.com/markospy/ForexFactoryScrapper/commit/a8bd8832e65f41205282c312207a7f207375ecc1))
* refactor error handling and middleware registration; move correlation-id handling to middleware ([309e6c4](https://github.com/markospy/ForexFactoryScrapper/commit/309e6c4ec961f141a65f8d8421bcb2aa1a1dcc23))
* refactor parsing logic for calendar events; introduce helper functions for improved readability and maintainability ([af202cd](https://github.com/markospy/ForexFactoryScrapper/commit/af202cd8eac0833fc1260745c81dfe8eb5026883))
* refactor scrapper functions for consistent naming conventions; improve readability and maintainability ([ded7e59](https://github.com/markospy/ForexFactoryScrapper/commit/ded7e595fd01a665189df93931bf42ca373b39bb))
* refactor scrapper functions to use consistent naming conventions; improve readability and maintainability ([76f56a2](https://github.com/markospy/ForexFactoryScrapper/commit/76f56a20dab02ea0c71207f040d0d64569cc85d6))
* remove debug print statements from time parsing logic; clean up code for better readability ([2f91b32](https://github.com/markospy/ForexFactoryScrapper/commit/2f91b32e2e14da1378e8d35a16ba5d48813c8c62))
* update Swagger UI integration to use Jinja2 template and enhance OpenAPI spec with pagination schemas ([92b0dfd](https://github.com/markospy/ForexFactoryScrapper/commit/92b0dfd8545e2ba475814e694c1a11374f6e78f9))
* update time column identification logic in parser; streamline handling of time index and improve robustness ([13aa2bf](https://github.com/markospy/ForexFactoryScrapper/commit/13aa2bf67541b8f9adce486ae28e2ec7b85457e9))


### Bug Fixes

* update openapi_spec.py for /bundle endpoint ([7ac8e6b](https://github.com/markospy/ForexFactoryScrapper/commit/7ac8e6bc09cf7275f0b7aa787976a59ce294c399))
