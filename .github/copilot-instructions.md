# Copilot Instructions for sonic-py-swsssdk

## Project Overview

sonic-py-swsssdk is the Python SDK for accessing SONiC's Switch State Service (SwSS) Redis databases. It provides `SonicV2Connector` and related classes for connecting to and operating on the Redis database instances that form SONiC's inter-process communication backbone (CONFIG_DB, APPL_DB, ASIC_DB, COUNTERS_DB, STATE_DB, etc.).

## Architecture

```
sonic-py-swsssdk/
├── src/
│   └── swsssdk/
│       ├── __init__.py          # Package init and SonicV2Connector
│       ├── interface.py         # Database interface abstraction
│       ├── dbconnector.py       # Redis connection management
│       ├── configDBConnector.py # CONFIG_DB-specific connector
│       └── ...                  # Additional modules
├── test/                        # pytest test suite
├── setup.py                     # Package setup
├── setup.cfg                    # Package configuration
├── pytest.ini                   # Pytest configuration
├── azure-pipelines.yml          # CI pipeline
└── README.md
```

### Key Concepts
- **SonicV2Connector**: Primary class for connecting to SONiC Redis databases
- **ConfigDBConnector**: Specialized connector for CONFIG_DB operations with table/key/field abstraction
- **Database instances**: Each SONiC DB (CONFIG_DB=4, APPL_DB=0, ASIC_DB=1, COUNTERS_DB=2, STATE_DB=6) runs on a specific Redis DB number
- **Unix socket**: Connects to Redis via `/var/run/redis/redis.sock` on SONiC switches

## Language & Style

- **Primary language**: Python
- **Python version**: Python 3
- **Indentation**: 4 spaces
- **Naming conventions**:
  - Classes: `PascalCase` (e.g., `SonicV2Connector`, `ConfigDBConnector`)
  - Methods: `snake_case` (e.g., `get_entry`, `mod_entry`)
  - Constants: `UPPER_CASE`
- **Docstrings**: Use docstrings for public API methods

## Build & Install

```bash
# Install in development mode
pip install -e .

# Build package
python setup.py sdist bdist_wheel

# Build Debian package
dpkg-buildpackage -rfakeroot -b -us -uc
```

## Testing

```bash
# Run tests
pytest test/ -v

# Run with coverage
pytest test/ -v --cov=swsssdk
```

## PR Guidelines

- **Signed-off-by**: Required on all commits
- **CLA**: Sign Linux Foundation EasyCLA
- **Testing**: Include tests for new database access patterns
- **Backward compatibility**: This SDK is used by many SONiC components — avoid breaking changes
- **CI**: Azure pipeline checks must pass
- **PR description template**: Fill out all sections of the [PR template](.github/pull_request_template.md) when submitting a pull request:
  - **Description of PR**: Summary of the change, motivation/context, reviewer entry point, and dependencies; reference issues with `fixes #xxxx` / `closes #xxxx`.
  - **Type of change**: Mark the box(es) that apply — bug fix, new feature, refactor / cleanup, documentation update, test improvement.
  - **Approach**: Motivation; how you did it; how you verified/tested it; any platform-specific notes.
  - **Documentation**: Link to wiki / doc updates relevant to new features or test cases.

## Example Usage

```python
import swsssdk

# Connect to SONiC databases
conn = swsssdk.SonicV2Connector()
conn.connect(conn.CONFIG_DB)

# Read from CONFIG_DB
conn.get_all(conn.CONFIG_DB, "PORT|Ethernet0")

# ConfigDBConnector for table-oriented access
config_db = swsssdk.ConfigDBConnector()
config_db.connect()
port_config = config_db.get_entry("PORT", "Ethernet0")
```

## Gotchas

- **Redis dependency**: Requires a running Redis instance — tests may need a mock or test Redis
- **Database schema**: Table/key formats must match SONiC's DB schema conventions
- **Socket path**: Default Unix socket path is SONiC-specific — may need configuration in test environments
- **Thread safety**: Redis connections are not thread-safe by default — use connection pools for concurrent access
- **Deprecation**: Some functionality has moved to sonic-swss-common's Python bindings — check for overlap
- **Encoding**: Handle Redis byte string responses properly (decode to str)
