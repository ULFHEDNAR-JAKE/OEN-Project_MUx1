# Test Suite

This directory contains the test suite for the OEN-Project_MUx1 authentication system.

## Running Tests

### Install Test Dependencies

```bash
pip install -r requirements.txt
```

### Run All Tests

```bash
# From project root
pytest tests/ -v

# With coverage report
pytest tests/ --cov=server --cov-report=html --cov-report=term
```

### Run Specific Test Classes

```bash
# Test validation functions
pytest tests/test_api.py::TestValidation -v

# Test signup endpoint
pytest tests/test_api.py::TestSignupEndpoint -v

# Test login endpoint
pytest tests/test_api.py::TestLoginEndpoint -v

# Test user model
pytest tests/test_api.py::TestUserModel -v
```

## Test Coverage

Current test coverage:
- Input validation functions: ✅ Comprehensive
- Health check endpoint: ✅ Basic
- Signup endpoint: ✅ Comprehensive
- Login endpoint: ✅ Basic
- Email verification: ⏳ Planned
- User model: ✅ Comprehensive

## Test Structure

```
tests/
├── __init__.py          # Package initialization
├── test_api.py          # API endpoint and validation tests
└── README.md            # This file
```

## Writing New Tests

Follow the existing patterns:

1. **Use pytest fixtures** for test clients and database setup
2. **Group related tests** in classes (e.g., TestSignupEndpoint)
3. **Use descriptive names** that explain what is being tested
4. **Include docstrings** explaining the test scenario
5. **Test both success and failure** cases

### Example Test

```python
class TestMyFeature:
    """Test my new feature"""
    
    def test_feature_success(self, client):
        """Test successful feature execution"""
        response = client.post('/api/my-feature', json={
            'param': 'value'
        })
        assert response.status_code == 200
        data = response.get_json()
        assert data['result'] == 'expected'
    
    def test_feature_validation(self, client):
        """Test feature input validation"""
        response = client.post('/api/my-feature', json={})
        assert response.status_code == 400
```

## Continuous Integration

Tests should be run automatically on every commit. Add this to your CI/CD pipeline:

```yaml
# .github/workflows/tests.yml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      - run: pip install -r requirements.txt
      - run: pytest tests/ --cov=server --cov-report=xml
      - uses: codecov/codecov-action@v2
```

## Test Database

Tests use an in-memory SQLite database (`sqlite:///:memory:`) to ensure:
- Tests are isolated and don't affect production data
- Tests run quickly
- No cleanup required between test runs
- Parallel test execution is possible

## Known Limitations

Current test coverage gaps (planned for Phase 2):
- [ ] Email verification endpoint tests
- [ ] JWT token validation tests
- [ ] Rate limiting tests
- [ ] Socket.IO event tests
- [ ] Integration tests for complete auth flows
- [ ] Security tests (SQL injection, XSS)
