# Trading Dashboard

Central orchestration and visualization hub for autonomous trading system.

## Quick Start

### Prerequisites

- Python 3.8+ (tested with Python 3.13.7)
- Virtual environment recommended

### Setup

#### Quick Setup (Windows)

```bash
# Run the automated setup script
setup_venv.bat
```

#### Manual Setup

```bash
# 1. Clone and navigate to project
cd trading-dashboard

# 2. Create virtual environment
python -m venv venv

# 3. Activate virtual environment
# Windows:
venv\Scripts\activate.bat
# Linux/Mac:
source venv/bin/activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Configure environment (optional)
copy .env.example .env   # Windows
cp .env.example .env     # Linux/Mac
# Edit .env with your specific settings
```

#### Verify Installation

```bash
# Windows: Use the test script
test_setup.bat

# Or manually test:
python test_config_standalone.py
```

### Running Tests

#### Option 1: Using pytest (recommended)

```bash
# Run all tests
python -m pytest

# Run specific test file
python -m pytest tests/test_config.py

# Run with verbose output
python -m pytest -v
```

#### Option 2: Using the test runner

```bash
# Run all tests
python run_tests.py

# Run specific test
python run_tests.py tests/test_config.py

# Verbose output
python run_tests.py -v
```

#### Option 3: Standalone configuration test

```bash
# Test configuration system directly (no pytest required)
python test_config_standalone.py
```

### Configuration

The system uses environment-specific YAML configurations:

- **Development**: `config/environments/development.yaml`
- **Staging**: `config/environments/staging.yaml`
- **Production**: `config/environments/production.yaml`

Set environment with:

```bash
export TRADING_DASHBOARD_ENV=development  # Linux/Mac
set TRADING_DASHBOARD_ENV=development     # Windows
```

## Project Structure

```bash
trading-dashboard/
├── src/                    # Source code
│   ├── dashboard/          # Streamlit dashboard
│   ├── orchestrator/       # Agent management
│   ├── api_client/         # API communication
│   ├── models/             # Data models
│   └── utils/              # Utilities
├── config/                 # Configuration files
│   └── environments/       # Environment-specific configs
├── tests/                  # Test suites
├── docs/                   # Documentation
└── scripts/               # Utility scripts
```

## Development Status

### ✅ Phase 1: Foundation Setup

- **Step 1**: Project structure creation ✅
- **Step 2**: Configuration system implementation ✅
- **Step 3**: Basic Streamlit application (in progress)
- **Step 4**: Core utilities setup (pending)

## Features

### Configuration Management

- Environment-specific YAML configurations
- Environment variable overrides
- Comprehensive validation system
- Dot notation configuration access
- Secure .env file handling

### Testing

- Comprehensive test suite with pytest
- 11+ test cases covering all functionality
- Standalone test runners for CI/CD
- Mock and integration testing support

## License

This project is part of an autonomous trading system implementation.

---

**Note**: This dashboard is designed to work with multiple trading agents (Market Data, Pattern Recognition, Risk Management, Advisor, Backtest). Currently only the foundation and configuration system are implemented.
