# NERC Rates
This repository stores rates and invoicing configuration for the New England
Research Cloud.

## Rates

The values are stored in `rates.yaml` as a list with each item under the
following format. Each item in the list contains a `name` and `history`.
`history` is itself a list containing `value` (required), `from` (required),
and `until` (optional).

```yaml
- name: CPU SU Rate
  history:
    - value: 0.013
      from: 2023-06
      until: 2024-06
    - value: 0.15
      from: 2024-07
```

To make use of the rates, install the package and import the module:
```python
from nerc_rates import rates
rates_data = rates.load_from_url()
rates_data.get_value_at("CPU SU Rate", "2024-06")

# Or for backward compatibility:
from nerc_rates import load_from_url
rates = load_from_url()
rates.get_value_at("CPU SU Rate", "2024-06")
```

## Outages

Outage information is stored in `outages.yaml` with information about planned
service interruptions. Each outage contains a `name`, `url`, and `timeframes`.

```yaml
- name: MGHPCC Shutdown 2024
  url: https://nerc.mghpcc.org/event/mghpcc-annual-power-shutdown-2024/
  timeframes:
    - from: "2024-05-22T08:00:00Z"
      until: "2024-05-28T23:00:00Z"
      affected_services:
        - NERC OpenStack
        - NERC OpenShift
```

To use outages data:
```python
from nerc_rates import outages
outages_data = outages.load_from_url()
outages_list = outages_data.get_outages_during("2024-05-01", "2024-06-01", "NERC OpenStack")
```

## Validation

Both rates and outages files can be validated using the included command-line tool:

```bash
validate-file --type rates rates.yaml
validate-file --type outages outages.yaml
```

## Code Structure

The `nerc-rates` package is organized into several key modules to ensure a clean and scalable design. This separation of concerns makes the code easier to maintain and understand.

### Core Components

The core logic is divided into two main domains: `rates` and `outages`. Each domain has its own data models and loaders, ensuring that they can be developed independently.

- **`nerc_rates/rates/`**: Handles all rate-related data, including validation and time-based lookups.
- **`nerc_rates/outages/`**: Manages outage information, providing tools to query outages by date and service.

### Shared Logic: The `base` Module

To avoid code duplication, shared components are centralized in the `nerc_rates/base/` module.

- **`base/loader.py`**: A generic data loader that can fetch and validate data from both URLs and local files. This loader is used by both the `rates` and `outages` modules.
- **`base/models.py`**: Contains a base Pydantic model with common configurations, ensuring consistent behavior across all data models.

### Data Validation with Pydantic

All data is validated using Pydantic models. This ensures that the data loaded from `rates.yaml` and `outages.yaml` conforms to the expected structure and data types. This approach prevents common data-related errors and improves the reliability of the system.

### Command-Line Tools

The package includes simple command-line tools for validating the data files, which are located in the `nerc_rates/cmd/` directory. These tools make it easy to verify the integrity of the data files before deploying changes.
