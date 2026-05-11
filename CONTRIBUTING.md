# Contributing to Agentic CRM

Thank you for your interest in contributing to Agentic CRM!

## How to Contribute

### Reporting Bugs

- Search existing issues before reporting a new bug
- Use the bug report template when opening an issue
- Include reproduction steps, expected vs actual behavior, and environment details

### Suggesting Features

- Open a feature request issue with a clear description
- Explain the use case and why it would benefit the project
- Tag it as a feature request

### Pull Requests

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature-name`
3. Make your changes
4. Add tests for new functionality
5. Run linting and tests: `make lint && make test`
6. Commit with a clear commit message
7. Open a pull request against `main`

### Development Setup

```bash
# Clone the repository
git clone https://github.com/artflarex/agentic-crm.git
cd agentic-crm

# Copy environment variables
cp .env.example .env

# Start all services
make up

# Run tests
make test
```

### Code Style

- Python: Follow `black` formatting and `ruff` linting rules
- TypeScript/JavaScript: Follow the project's ESLint configuration
- Write type-safe code (TypeScript strict mode)
- Add docstrings for public functions and classes

### Testing

All new features must include tests. Run the test suite:

```bash
make test
```

### Commit Messages

- Use clear, descriptive commit messages
- Start with a verb (Add, Fix, Update, Remove, etc.)
- Keep the first line short (< 72 characters)
- Add body text for complex changes

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
