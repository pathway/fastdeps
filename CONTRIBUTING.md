# Contributing to FastDeps

We love your input! We want to make contributing to FastDeps as easy and transparent as possible.

## Development Process

We use GitHub to host code, to track issues and feature requests, as well as accept pull requests.

## Pull Requests

1. Fork the repo and create your branch from `main`.
2. If you've added code that should be tested, add tests.
3. If you've changed APIs, update the documentation.
4. Ensure the test suite passes.
5. Make sure your code follows the style guidelines.
6. Issue that pull request!

## Setting Up Development Environment

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/fastdeps.git
cd fastdeps

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode with dev dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install
```

## Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=fastdeps --cov-report=html

# Run specific test file
pytest tests/test_parser.py

# Run with verbose output
pytest -v
```

## Code Style

We use Black for code formatting and Ruff for linting:

```bash
# Format code
black fastdeps tests

# Check linting
ruff check fastdeps tests

# Type checking
mypy fastdeps
```

## Testing Guidelines

- Write tests for all new functionality
- Maintain test coverage above 90%
- Use descriptive test names
- Test edge cases and error conditions
- Keep tests fast and isolated

## Commit Message Guidelines

We follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation only changes
- `style:` Code style changes (formatting, etc)
- `refactor:` Code refactoring
- `test:` Adding or updating tests
- `perf:` Performance improvements
- `chore:` Changes to build process or tools

Examples:
```
feat: add support for Python 3.13
fix: correctly handle relative imports in packages
docs: update installation instructions
perf: optimize parallel processing for large codebases
```

## Reporting Issues

Use GitHub Issues to report bugs or suggest features.

### Bug Reports

Please include:
- Python version
- Operating system
- Minimal code to reproduce the issue
- Expected vs actual behavior
- Full error messages and stack traces

### Feature Requests

Please include:
- Clear use case
- Expected behavior
- Why this would be valuable to other users

## Code of Conduct

### Our Pledge

We pledge to make participation in our project a harassment-free experience for everyone.

### Our Standards

Examples of behavior that contributes to creating a positive environment:
- Using welcoming and inclusive language
- Being respectful of differing viewpoints
- Gracefully accepting constructive criticism
- Focusing on what is best for the community

### Enforcement

Instances of abusive, harassing, or otherwise unacceptable behavior may be reported by contacting the project team.

## License

By contributing, you agree that your contributions will be licensed under the MIT License.