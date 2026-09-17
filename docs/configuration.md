# Configuration

ForexFactoryScrapper loads settings through system environment variables or a local `.env` file via `python-dotenv`.

## Environment Variables

| Variable | Type | Default | Required | Description |
| :--- | :--- | :--- | :---: | :--- |
| `HOST` | String | `0.0.0.0` | No | Network interface address to bind HTTP listener. |
| `PORT` | Integer | `5000` | No | Port number for incoming HTTP connections. |
| `DEBUG` | Boolean | `True` | No | Enables Flask debug mode and reload on code changes. |
| `DOTENV_PATH` | String (Path) | None | No | Explicit file path to load environment variables from. |

## Example Configuration

Create a `.env` file in the root directory:

```bash
cp .env.example .env
```

Default `.env` contents:

```ini
# Host and port for Flask HTTP API
HOST=0.0.0.0
PORT=5000

# Debug mode: True or False
DEBUG=True
```
