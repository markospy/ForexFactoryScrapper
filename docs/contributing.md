# Contributing

We welcome contributions to ForexFactoryScrapper. Please follow these instructions to submit changes.

## Development Workflow

1. Fork the repository and create a feature branch:
   ```bash
   git checkout -b feat/new-capability
   ```
2. Implement your changes and add tests in `tests/`.
3. Verify the test suite passes locally:
   ```bash
   make test
   ```
4. Follow Conventional Commits format for all commit messages.
5. Submit a pull request targeting `main`.

## Conventional Commits

Commit messages should be formatted as:

```text
<type>(<scope>): <description>
```

Types:
- `feat`: New feature or endpoint.
- `fix`: Bug fix.
- `chore`: Dependency updates or build tooling.
- `docs`: Documentation updates.

## Local Commands

Run common developer tasks using `make`:

```bash
make install      # Install dependencies
make test         # Run pytest
make lint         # Run flake8 and black checks
make format       # Auto-format code
make run          # Start development server
make docs-serve   # Launch live documentation server
```
