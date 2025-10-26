# How to Run Unit Tests

This guide explains how to run the unit tests for the rate limiter service.

## Quick Start

### Run All Tests (Recommended)
```bash
cd tst
python3 run_tests.py
```
**Result**: ✅ 56 tests, 100% success rate - All tests pass!

## Test Structure (Clean 1:1 Mapping)

The test structure has been reorganized to provide a clean 1:1 mapping between source model files and test files:

```
tst/
├── run_tests.py                # Main test runner (runs all 56 tests)
├── models/                     # Model tests (36 tests) - 1:1 mapping with source models
│   ├── test_config_request.py  # Tests src/models/config_request.py (8 tests)
│   ├── test_config_response.py # Tests src/models/config_response.py (8 tests)
│   ├── test_rate_limit_request.py # Tests src/models/rate_limit_request.py (10 tests)
│   ├── test_rate_limit_response.py # Tests src/models/rate_limit_response.py (10 tests)
│   ├── test_rate_limit_config.py # Tests src/models/rate_limit_config.py
│   └── test_api.py             # API logic tests (no HTTP dependencies)
├── algorithms/                 # Algorithm tests (12 tests)
│   ├── test_rate_limiter_service.py # Service layer tests (6 tests)
│   └── test_sliding_window_algorithm.py # Algorithm correctness tests (6 tests)
└── performance/
    └── performance_test.py     # Performance and load tests
```

## Run Individual Test Files

### Model Tests (1:1 Mapping with Source Files)

#### Test Configuration Request Model
```bash
cd tst
PYTHONPATH=../src python3 -m unittest models.test_config_request -v
```
**Coverage**: 8 tests covering validation, serialization, field descriptions, and edge cases

#### Test Configuration Response Model
```bash
cd tst
PYTHONPATH=../src python3 -m unittest models.test_config_response -v
```
**Coverage**: 8 tests covering response validation and field descriptions

#### Test Rate Limit Request Model
```bash
cd tst
PYTHONPATH=../src python3 -m unittest models.test_rate_limit_request -v
```
**Coverage**: 10 tests covering field validation, type coercion, and model behavior

#### Test Rate Limit Response Model
```bash
cd tst
PYTHONPATH=../src python3 -m unittest models.test_rate_limit_response -v
```
**Coverage**: 10 tests covering response validation, optional fields, and serialization

#### Test Rate Limit Config Model
```bash
cd tst
PYTHONPATH=../src python3 -m unittest models.test_rate_limit_config -v
```
**Coverage**: Internal configuration model tests

### Algorithm and Service Tests

#### Test Rate Limiter Service
```bash
cd tst
PYTHONPATH=../src python3 -m unittest algorithms.test_rate_limiter_service -v
```
**Coverage**: 6 tests covering service logic and configuration management

#### Test Sliding Window Algorithm
```bash
cd tst
PYTHONPATH=../src python3 -m unittest algorithms.test_sliding_window_algorithm -v
```
**Coverage**: 6 tests covering algorithm correctness, concurrency, and edge cases

#### Test API Logic
```bash
cd tst
PYTHONPATH=../src python3 -m unittest test_api -v
```
**Coverage**: 8 tests covering endpoint functionality without HTTP dependencies

### Run All Model Tests Only
```bash
cd tst
PYTHONPATH=../src python3 -m unittest models.test_config_request models.test_config_response models.test_rate_limit_request models.test_rate_limit_response -v
```

### Run Tests from Individual Files Directly
```bash
cd tst/models
PYTHONPATH=../../src python3 test_config_request.py
PYTHONPATH=../../src python3 test_config_response.py
PYTHONPATH=../../src python3 test_rate_limit_request.py
PYTHONPATH=../../src python3 test_rate_limit_response.py
```

## Test Coverage Summary

### ✅ Model Tests (36 tests total)
- **test_config_request.py**: Configuration request validation and serialization (8 tests)
- **test_config_response.py**: Configuration response validation and field descriptions (8 tests)
- **test_rate_limit_request.py**: Rate limit request validation and type coercion (10 tests)
- **test_rate_limit_response.py**: Rate limit response validation and optional fields (10 tests)

### ✅ Algorithm Tests (12 tests total)
- **test_rate_limiter_service.py**: Service layer logic and configuration management (6 tests)
- **test_sliding_window_algorithm.py**: Algorithm correctness, concurrency, edge cases (6 tests)

### ✅ API Tests (8 tests total)
- **test_api.py**: Endpoint functionality without HTTP dependencies (8 tests)

## Expected Output

When tests pass, you should see output like:
```
--- Running models.test_config_request ---
........
----------------------------------------------------------------------
Ran 8 tests in 0.002s

OK

--- Running models.test_rate_limit_request ---
..........
----------------------------------------------------------------------
Ran 10 tests in 0.001s

OK
```

## Key Features Tested

### Comprehensive Model Validation
- **Field Descriptions**: All models have descriptive field documentation
- **Type Coercion**: Pydantic automatic type conversion (e.g., strings to booleans)
- **Serialization**: JSON serialization and deserialization
- **Edge Cases**: Empty values, boundary conditions, optional fields

### Algorithm Correctness
- **Rate Limiting Logic**: Sliding window algorithm accuracy
- **Concurrency**: Thread-safe operations under load
- **Memory Management**: Automatic cleanup of expired requests
- **Configuration**: Dynamic rate limit updates

### API Functionality
- **Request Validation**: Input validation and error handling
- **Response Format**: Correct response structure and status codes
- **Business Logic**: Rate limiting decisions and remaining count calculations

## Troubleshooting

### Import Errors
If you get `ModuleNotFoundError`, make sure to:
1. Run from the `tst` directory
2. Use `PYTHONPATH=../src` to set the Python path
3. Check that you're using the correct relative paths

### Missing Dependencies
Some tests require additional packages:
```bash
pip install httpx  # For API tests (if needed)
pip install pytest  # Alternative test runner
```

### Performance Tests
```bash
cd tst/performance
python3 performance_test.py
```

## Test Architecture Benefits

### Clean Organization
- **1:1 Mapping**: Each source model file has exactly one corresponding test file
- **Clear Separation**: Models, algorithms, and API logic are tested separately
- **Easy Maintenance**: Adding new models automatically suggests where tests should go

### Comprehensive Coverage
- **56 Total Tests**: Complete coverage of all functionality
- **Individual Focus**: Each test file focuses on one specific model or component
- **Edge Case Testing**: Thorough validation of boundary conditions and error cases

### Developer Experience
- **Fast Feedback**: Run tests for specific components during development
- **Clear Failures**: Test failures clearly indicate which component has issues
- **Easy Extension**: Adding new models or algorithms follows established patterns
