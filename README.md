# NERC Rates
This repository stores rates, outages and invoicing configuration for the New England
Research Cloud.

To make use of the rates and outages data, install the package and import the modules:

## Usage

### Loading Rates
```python
from nerc_rates import rates
rate_data = rates.load_from_url()
rate_data.get_value_at("CPU SU Rate", "2024-06", Decimal)
```

### Loading Outages
```python
from nerc_rates import outages
outage_data = outages.load_from_url()
outage_data.get_outages_during("2024-05-01", "2024-06-01", "NERC OpenStack")
```

### Loading Rates from file
```python
from nerc_rates import rates
rate_data = rates.load_from_file("rates.yaml")
rate_data.get_value_at("CPU SU Rate", "2024-06", Decimal)
```

### Loading Outages from file
```python
from nerc_rates import outages
outage_data = outages.load_from_file("outages.yaml")
outage_data.get_outages_during("2024-05-01", "2024-06-01", "NERC OpenStack")
```

## How To Verify Rates and Outages Data

This guide explains how the system automatically verifies the integrity and correctness of rates and outages data when it is loaded. The data models are designed with built-in validation rules to catch common errors, such as overlapping date ranges, incorrect data types, or duplicate entries.

### How Verification Works

When you load data using `rates.load_from_file()` or `outages.load_from_file()`, the system attempts to parse your YAML data into its internal data models. During this process, several validation checks are performed automatically:

*   **Rates Verification Checks**:
    *   **Date Range Order**: Ensures that `date_until` is always after `date_from` within a `RateValue`.
    *   **No Overlapping Date Ranges**: Verifies that there are no overlapping timeframes for `RateValue` entries within a `RateItem`'s `history`.
    *   **Rate Type Consistency**: Checks that `value` strings can be correctly converted to the `RateType` specified for the `RateItem` (e.g., a `Decimal` rate is a valid number, `bool` rates are "true" or "false").
    *   **Unique Rate Names**: Ensures that each `RateItem` has a unique `name` across the entire rates list.

*   **Outages Verification Checks**:
    *   **Time Range Order**: Ensures that `time_until` is always after `time_from` within an `OutageTimeFrames`.
    *   **Unique Affected Services**: Verifies that `affected_services` within an `OutageTimeFrames` do not contain duplicate service names.
    *   **Unique Outage URLs**: Checks for duplicate `url` entries across all `OutageItem`s in the outages list.
    *   **UTC Timezone Enforcement**: Ensures all outage `datetime` values (`time_from`, `time_until`) are provided with UTC timezone information and are not naive datetimes.

If any of these validation rules are violated, the loading process will raise a `ValueError` or `TypeError`, providing a clear message about what went wrong and where.

### Example: Rates Verification

Let's say you have a `rates.yaml` file with an overlapping date range, which is an invalid configuration:

```yaml
- name: CPU SU Rate
  history:
    - value: 0.013
      from: 2023-06
      until: 2024-06
    - value: 0.15
      from: 2024-05 # This date range overlaps with the previous one
```

When you try to load this data, you would see an error like this:

```python
from nerc_rates import rates
try:
    rate_data = rates.load_from_file("rates.yaml")
except ValueError as e:
    print(f"Rates data validation failed: {e}")
```

Expected Output:

```
Rates data validation failed: date ranges overlap
```

### Example: Outages Verification

Similarly, if your `outages.yaml` contains an outage with a naive datetime (missing timezone information), it will trigger a validation error:

```yaml
- url: http://example.com/outage-1
  timeframes:
    - from: 2024-01-01T12:00:00 # Missing timezone info (e.g., Z or +00:00)
      until: 2024-01-01T14:00:00Z
      affected_services: ["NERC OpenStack"]
```

Loading this file would result in:

```python
from nerc_rates import outages
try:
    outage_data = outages.load_from_file("outages.yaml")
except ValueError as e:
    print(f"Outages data validation failed: {e}")
```

Expected Output:

```
Outages data validation failed: Naive datetime without timezone information is not allowed. Please provide timezone information (e.g., '2024-01-01T12:00:00Z' or '2024-01-01T12:00:00+00:00')
```

## How To Run Tests

This section guides you through setting up and running the test suite for this project using `pytest`. Running tests is crucial for verifying that all components of the system are working as expected and that any changes introduced do not break existing functionality.

### Prerequisites

*   Python 3.8+ installed
*   `pip` installed for dependency management

### Steps

1.  **Install Dependencies**:
    Navigate to the root directory of the project in your terminal and install the project dependencies.

    ```bash
    pip install -r requirements.txt
    pip install -r test-requirements.txt
    ```

2.  **Run Tests**:
    After installing the dependencies, you can run the test suite from the project's root directory:

    ```bash
    pytest
    ```

    This command will discover and execute all tests located in the `tests/` directory.

## Additional Information

*   **Specific Tests**: To run a specific test file or test case, you can provide its path to `pytest`:
    ```bash
    pytest tests/test_rates.py
    pytest tests/test_rates.py::test_get_cpu_rate
    ```
*   **Verbose Output**: Use the `-v` flag for more detailed output during test execution:
    ```bash
    pytest -v
    ```
